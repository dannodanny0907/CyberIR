# File: similarity_engine.py - Engine to find similar past incidents and historical solutions
from database import get_db_connection
from difflib import SequenceMatcher
import re

# Handle logic for clean_text
def clean_text(text):
    if not text:
        return ""
    cleaned = re.sub(r'[^a-z0-9\s]', ' ', text.lower())
    return ' '.join(cleaned.split())

# Handle logic for get_keywords
def get_keywords(text):
    cleaned = clean_text(text)
    if not cleaned:
        return set()
    stop_words = {
      'the','a','an','and','or','but','in','on','at','to',
      'for','of','with','by','from','is','was','are','were',
      'been','be','have','has','had','this','that','these',
      'those','it','its','as','into','through','during',
      'before','after','above','below','between','out',
      'off','over','under','again','then','once','here',
      'there','when','where','which','who','what','how',
      'all','both','each','few','more','most','other',
      'some','such','no','not','only','same','so','than',
      'too','very','just','because','if','while','although'
    }
    words = cleaned.split()
    return set([w for w in words if w not in stop_words and len(w) >= 3])

# Handle logic for calculate_text_similarity
def calculate_text_similarity(text_a, text_b):
    kw_a = get_keywords(text_a)
    kw_b = get_keywords(text_b)
    if not kw_a or not kw_b:
        return 0.0
    intersection = kw_a & kw_b
    union = kw_a | kw_b
    jaccard = len(intersection) / len(union) if union else 0.0
    seq_sim = SequenceMatcher(None, clean_text(text_a), clean_text(text_b)).ratio()
    return round((jaccard * 0.6) + (seq_sim * 0.4), 4)

# Handle logic for calculate_asset_similarity
def calculate_asset_similarity(asset_a, asset_b):
    if not asset_a or not asset_b:
        return 0.0
    direct = SequenceMatcher(None, asset_a.lower(), asset_b.lower()).ratio()
    words_a = set(asset_a.lower().split())
    words_b = set(asset_b.lower().split())
    if words_a and words_b:
        overlap = len(words_a & words_b) / len(words_a | words_b)
    else:
        overlap = 0.0
    return round((direct * 0.7) + (overlap * 0.3), 4)

# Handle logic for calculate_similarity_score
def calculate_similarity_score(new_incident, historical_incident):
    system_score = calculate_asset_similarity(
        new_incident.get('affected_asset'), historical_incident.get('affected_asset'))
    type_score = 1.0 if new_incident.get('incident_type') == historical_incident.get('incident_type') else 0.0
    description_score = calculate_text_similarity(
        new_incident.get('description') or '', historical_incident.get('description') or '')
    priority_score = 1.0 if new_incident.get('priority') == historical_incident.get('priority') else 0.0
    
    final_score = (
        system_score * 0.40 +
        type_score * 0.30 +
        description_score * 0.20 +
        priority_score * 0.10
    )
    return round(final_score, 4)

# Handle logic for explain_similarity
def explain_similarity(new_incident, historical_incident, score):
    explanations = []
    if new_incident.get('incident_type') == historical_incident.get('incident_type'):
        explanations.append(f"Same incident type: {new_incident.get('incident_type')}")
        
    asset_sim = calculate_asset_similarity(new_incident.get('affected_asset'), historical_incident.get('affected_asset'))
    if asset_sim >= 0.8:
        explanations.append(f"Same affected system: {new_incident.get('affected_asset')}")
    elif asset_sim >= 0.5:
        explanations.append(f"Similar affected systems: {new_incident.get('affected_asset')} ≈ {historical_incident.get('affected_asset')}")
        
    if new_incident.get('priority') == historical_incident.get('priority'):
        explanations.append(f"Same priority level: {new_incident.get('priority')}")
        
    kw_new = get_keywords(new_incident.get('description') or '')
    kw_hist = get_keywords(historical_incident.get('description') or '')
    shared = kw_new & kw_hist
    if shared:
        top_shared = list(shared)[:4]
        explanations.append(f"Shared keywords: {', '.join(top_shared)}")
        
    da = new_incident.get('affected_department')
    db = historical_incident.get('affected_department')
    if da and db and da == db:
        explanations.append(f"Same department: {da}")
        
    if not explanations:
        explanations.append(f"Overall similarity score: {round(score * 100)}%")
        
    return explanations

# Handle logic for run_similarity
def run_similarity(new_incident_id):
    conn = get_db_connection()
    try:
        new_inc_row = conn.execute('SELECT * FROM incidents WHERE id = ?', (new_incident_id,)).fetchone()
        if not new_inc_row:
            return {"found": False, "matches": []}
            
        new_incident = dict(new_inc_row)
        
        hist_rows = conn.execute('''
            SELECT * FROM incidents
            WHERE id != ?
            AND status IN ('Resolved', 'Closed')
            AND resolution_notes IS NOT NULL
            AND resolution_notes != ''
            ORDER BY resolved_date DESC
            LIMIT 200
        ''', (new_incident_id,)).fetchall()
        
        historical_incidents = [dict(r) for r in hist_rows]
        
        try:
            settings_row = conn.execute("SELECT setting_value FROM settings WHERE setting_key = 'similarity_threshold'").fetchone()
            similarity_threshold = float(settings_row['setting_value']) if settings_row else 0.50
        except Exception:
            similarity_threshold = 0.50

        matches = []
        for hist in historical_incidents:
            score = calculate_similarity_score(new_incident, hist)
            if score >= similarity_threshold:
                exps = explain_similarity(new_incident, hist, score)
                matches.append({
                    'incident_id': hist['incident_id'],
                    'id': hist['id'],
                    'title': hist['title'],
                    'incident_type': hist['incident_type'],
                    'affected_asset': hist['affected_asset'],
                    'priority': hist['priority'],
                    'resolution_notes': hist['resolution_notes'],
                    'resolved_date': hist['resolved_date'],
                    'resolution_time_minutes': hist.get('resolution_time_minutes'),
                    'score': score,
                    'score_percent': round(score * 100),
                    'explanations': exps
                })
                
        matches.sort(key=lambda x: x['score'], reverse=True)
        top_matches = matches[:5]
        
        suggestion = None
        if top_matches:
            best_match = top_matches[0]
            conn.execute('''
                UPDATE incidents SET similar_incident_id = ?, similarity_score = ?
                WHERE id = ?
            ''', (best_match['incident_id'], best_match['score'], new_incident_id))
            
            times = [m['resolution_time_minutes'] for m in top_matches if m.get('resolution_time_minutes') is not None]
            avg_res_time = sum(times)/len(times) if times else None
            
            suggestion = {
                'confidence': best_match['score_percent'],
                'based_on_incident': best_match['incident_id'],
                'resolution': best_match['resolution_notes'],
                'avg_resolution_minutes': avg_res_time,
                'total_similar_found': len(top_matches)
            }
            
        if top_matches and top_matches[0]['score'] >= 0.75:
            best_match = top_matches[0]
            existing = conn.execute('''
                SELECT id FROM alerts WHERE alert_type = 'SIMILARITY' AND incident_id = ?
            ''', (new_incident_id,)).fetchone()
            
            if not existing:
                recip_id = new_incident.get('assigned_to')
                recip_role = None if recip_id else 'Analyst'
                msg = f"Similar incident found: {best_match['incident_id']} ({best_match['score_percent']}% match) — Suggested solution available"
                
                conn.execute('''
                    INSERT INTO alerts (alert_type, severity, message, incident_id, recipient_id, recipient_role, is_read, created_at)
                    VALUES ('SIMILARITY', 'INFO', ?, ?, ?, ?, 0, CURRENT_TIMESTAMP)
                ''', (msg, new_incident_id, recip_id, recip_role))
                
        conn.commit()
        return {
            "found": len(top_matches) > 0,
            "matches": top_matches,
            "suggestion": suggestion,
            "new_incident_id": new_incident['incident_id']
        }
    except Exception as e:
        print(f"Similarity error: {e}")
        return {"found": False, "matches": [], "suggestion": None, "error": str(e)}

# Handle logic for get_cached_similarity
def get_cached_similarity(incident_id_str):
    conn = get_db_connection()
    inc = conn.execute('SELECT id, similar_incident_id, similarity_score, reported_date FROM incidents WHERE incident_id = ?', (incident_id_str,)).fetchone()
    if not inc:
        return {"found": False, "matches": []}
        
    return run_similarity(inc['id'])
