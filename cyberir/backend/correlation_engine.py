from database import get_db_connection
from datetime import datetime, timedelta
from difflib import SequenceMatcher
import json
from collections import Counter

def fuzzy_match(string_a, string_b):
    if not string_a or not string_b:
        return 0.0
    return SequenceMatcher(None, string_a.lower(), string_b.lower()).ratio()

def compare_indicators(indicators_a, indicators_b):
    if not indicators_a or not indicators_b:
        return 0.0
    set_a = {x.strip().lower() for x in indicators_a.split(',')}
    set_b = {x.strip().lower() for x in indicators_b.split(',')}
    if not set_a and not set_b:
        return 0.0
    intersection = set_a & set_b
    union = set_a | set_b
    if not union:
        return 0.0
    return len(intersection) / len(union)

def calculate_time_score(date_a, date_b):
    if not date_a or not date_b:
        return 0.0
    fmt = '%Y-%m-%d %H:%M:%S'
    try:
        da = datetime.strptime(str(date_a).replace('T', ' ')[:19], fmt)
        db = datetime.strptime(str(date_b).replace('T', ' ')[:19], fmt)
    except Exception:
        return 0.0
    diff_hours = abs((da - db).total_seconds()) / 3600.0
    if diff_hours <= 2: return 1.0
    elif diff_hours <= 6: return 0.8
    elif diff_hours <= 12: return 0.6
    elif diff_hours <= 24: return 0.4
    elif diff_hours <= 48: return 0.2
    else: return 0.0

def calculate_correlation_score(incident_a, incident_b):
    time_score = calculate_time_score(incident_a.get('reported_date'), incident_b.get('reported_date'))
    type_score = 1.0 if incident_a.get('incident_type') == incident_b.get('incident_type') else 0.0
    
    da = incident_a.get('affected_department')
    db = incident_b.get('affected_department')
    dept_score = 1.0 if (da and db and da == db) else 0.0
    
    system_score = fuzzy_match(incident_a.get('affected_asset'), incident_b.get('affected_asset'))
    indicator_score = compare_indicators(incident_a.get('attack_indicators'), incident_b.get('attack_indicators'))
    
    final_score = (
        time_score * 0.30 +
        type_score * 0.25 +
        dept_score * 0.20 +
        system_score * 0.15 +
        indicator_score * 0.10
    )
    return round(final_score, 4)

def get_next_cluster_id():
    conn = get_db_connection()
    row = conn.execute("SELECT MAX(cluster_id) as max_id FROM incident_clusters").fetchone()
    if not row or not row['max_id']:
        return "CLU-001"
    last_id = row['max_id']
    try:
        num = int(last_id.split('-')[1])
        return f"CLU-{(num + 1):03d}"
    except Exception:
        return "CLU-001"

def run_correlation(new_incident_id):
    conn = get_db_connection()
    try:
        # STEP 1
        new_incident_row = conn.execute('SELECT * FROM incidents WHERE id = ?', (new_incident_id,)).fetchone()
        if not new_incident_row:
            return {"clustered": False, "cluster_id": None, "matches": []}
        new_incident = dict(new_incident_row)
        
        # STEP 2
        candidates_rows = conn.execute('''
            SELECT * FROM incidents 
            WHERE id != ? 
            AND reported_date >= datetime('now', '-48 hours')
            AND status != 'Closed'
        ''', (new_incident_id,)).fetchall()
        
        candidates = [dict(row) for row in candidates_rows]
        
        # STEP 3
        correlation_threshold = 0.65
        matches = []
        for candidate in candidates:
            score = calculate_correlation_score(new_incident, candidate)
            if score >= correlation_threshold:
                matches.append({"incident": candidate, "score": score})
                
        matches.sort(key=lambda x: x['score'], reverse=True)
        
        # STEP 4
        if not matches:
            return {"clustered": False, "cluster_id": None, "matches": []}
            
        existing_clusters = [m['incident']['cluster_id'] for m in matches if m['incident'].get('cluster_id')]
        
        if existing_clusters:
            most_common = Counter(existing_clusters).most_common(1)[0][0]
            cluster_id = most_common
            action = "joined"
        else:
            cluster_id = get_next_cluster_id()
            action = "created"
            
        # STEP 5
        highest_score = matches[0]['score']
        conn.execute('UPDATE incidents SET cluster_id = ?, correlation_score = ? WHERE id = ?',
                     (cluster_id, highest_score, new_incident_id))
                     
        # STEP 6
        for m in matches:
            if not m['incident'].get('cluster_id'):
                conn.execute('UPDATE incidents SET cluster_id = ? WHERE id = ?',
                             (cluster_id, m['incident']['id']))
                             
        # STEP 7
        if action == "created":
            incidents_in_cluster = conn.execute('SELECT priority, incident_type, affected_department FROM incidents WHERE cluster_id = ?', (cluster_id,)).fetchall()
            priorities = [i['priority'] for i in incidents_in_cluster]
            
            if 'Critical' in priorities: severity = 'Critical'
            elif 'High' in priorities: severity = 'High'
            elif 'Medium' in priorities: severity = 'Medium'
            else: severity = 'Low'
            
            types = [i['incident_type'] for i in incidents_in_cluster]
            primary_type = Counter(types).most_common(1)[0][0] if types else 'Unknown'
            
            depts = [i['affected_department'] for i in incidents_in_cluster if i['affected_department']]
            if depts:
                dept_counts = Counter(depts)
                if len(dept_counts) > 1:
                    dept_str = 'Multiple Depts'
                else:
                    dept_str = dept_counts.most_common(1)[0][0]
            else:
                dept_str = 'Multiple Depts'
                
            cluster_name = f"{primary_type} Campaign — {dept_str}"
            incident_count = len(incidents_in_cluster)
            
            conn.execute('''
                INSERT INTO incident_clusters (
                    cluster_id, cluster_name, incident_count, primary_type, severity,
                    first_detected, last_updated, status
                ) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, 'Active')
            ''', (cluster_id, cluster_name, incident_count, primary_type, severity, new_incident['reported_date']))
            
        elif action == "joined":
            incidents_in_cluster = conn.execute('SELECT priority FROM incidents WHERE cluster_id = ?', (cluster_id,)).fetchall()
            priorities = [i['priority'] for i in incidents_in_cluster]
            if 'Critical' in priorities: new_severity = 'Critical'
            elif 'High' in priorities: new_severity = 'High'
            elif 'Medium' in priorities: new_severity = 'Medium'
            else: new_severity = 'Low'
            
            conn.execute('''
                UPDATE incident_clusters SET
                    incident_count = (SELECT COUNT(*) FROM incidents WHERE cluster_id = ?),
                    last_updated = CURRENT_TIMESTAMP,
                    severity = ?
                WHERE cluster_id = ?
            ''', (cluster_id, new_severity, cluster_id))
            
        # STEP 8
        count_val = conn.execute('SELECT COUNT(*) as c FROM incidents WHERE cluster_id = ?', (cluster_id,)).fetchone()['c']
        
        if count_val >= 2:
            clus_row = conn.execute('SELECT severity, primary_type, cluster_name FROM incident_clusters WHERE cluster_id = ?', (cluster_id,)).fetchone()
            c_sev = clus_row['severity'] if clus_row else 'Medium'
            c_type = clus_row['primary_type'] if clus_row else 'Unknown'
            c_dept = clus_row['cluster_name'].split('—')[-1].strip() if clus_row and '—' in clus_row['cluster_name'] else 'Multiple'
            
            alert_sev = 'CRITICAL' if c_sev in ['Critical', 'High'] else 'WARNING'
            msg = f"Correlation detected: {count_val} related incidents grouped in cluster {cluster_id} ({c_type} — {c_dept})"
            
            conn.execute('''
                INSERT INTO alerts (alert_type, severity, message, cluster_id, incident_id, recipient_role, is_read, created_at)
                VALUES (?, ?, ?, ?, ?, ?, 0, CURRENT_TIMESTAMP)
            ''', ('CORRELATION', alert_sev, msg, cluster_id, new_incident_id, 'Admin'))
            
            conn.execute('''
                INSERT INTO alerts (alert_type, severity, message, cluster_id, incident_id, recipient_role, is_read, created_at)
                VALUES (?, ?, ?, ?, ?, ?, 0, CURRENT_TIMESTAMP)
            ''', ('CORRELATION', alert_sev, msg, cluster_id, new_incident_id, 'Analyst'))
            
        conn.commit()
        return {
            "clustered": True,
            "cluster_id": cluster_id,
            "action": action,
            "matches": [m['incident']['incident_id'] for m in matches]
        }
    except Exception as e:
        print(f"Correlation error: {e}")
        return {"clustered": False, "cluster_id": None, "matches": [], "error": str(e)}

def recalculate_cluster(cluster_id):
    conn = get_db_connection()
    incidents_in_cluster = conn.execute('SELECT priority, incident_type FROM incidents WHERE cluster_id = ?', (cluster_id,)).fetchall()
    count = len(incidents_in_cluster)
    
    if count <= 1:
        if count == 1:
            conn.execute('UPDATE incidents SET cluster_id = NULL, correlation_score = NULL WHERE cluster_id = ?', (cluster_id,))
        conn.execute('DELETE FROM incident_clusters WHERE cluster_id = ?', (cluster_id,))
        conn.commit()
        return {"dissolved": True}
        
    priorities = [i['priority'] for i in incidents_in_cluster]
    if 'Critical' in priorities: severity = 'Critical'
    elif 'High' in priorities: severity = 'High'
    elif 'Medium' in priorities: severity = 'Medium'
    else: severity = 'Low'
    
    types = [i['incident_type'] for i in incidents_in_cluster]
    primary_type = Counter(types).most_common(1)[0][0] if types else 'Unknown'
    
    conn.execute('''
        UPDATE incident_clusters SET
            incident_count = ?,
            severity = ?,
            primary_type = ?,
            last_updated = CURRENT_TIMESTAMP
        WHERE cluster_id = ?
    ''', (count, severity, primary_type, cluster_id))
    
    conn.commit()
    return {"dissolved": False, "count": count}

def remove_from_cluster(incident_integer_id):
    conn = get_db_connection()
    incident = conn.execute('SELECT cluster_id FROM incidents WHERE id = ?', (incident_integer_id,)).fetchone()
    
    if not incident or not incident['cluster_id']:
        return {"success": False}
        
    cluster_id = incident['cluster_id']
    conn.execute('UPDATE incidents SET cluster_id = NULL, correlation_score = NULL WHERE id = ?', (incident_integer_id,))
    conn.commit()
    
    result = recalculate_cluster(cluster_id)
    return {"success": True, "cluster_dissolved": result.get('dissolved', False)}
