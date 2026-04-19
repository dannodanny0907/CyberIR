# File: app.py - Main Flask application routing and core logic
import os
import sys

# Allow running from other context properly
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)


try:
    from weasyprint import HTML as WeasyHTML
    PDF_LIBRARY = 'weasyprint'
except (ImportError, Exception):
    try:
        from xhtml2pdf import pisa
        PDF_LIBRARY = 'xhtml2pdf'
    except ImportError:
        PDF_LIBRARY = None

def generate_pdf_from_html(html_string):
    if PDF_LIBRARY == 'weasyprint':
        pdf_bytes = WeasyHTML(string=html_string).write_pdf()
        return pdf_bytes
    elif PDF_LIBRARY == 'xhtml2pdf':
        from io import BytesIO
        result = BytesIO()
        pisa.CreatePDF(html_string, dest=result)
        return result.getvalue()
    else:
        return None

import csv
from io import StringIO, BytesIO
from flask import render_template_string
import base64

def get_logo_base64():
    logo_path = os.path.join(ROOT, 'src', 'cut_logo.png')
    if os.path.exists(logo_path):
        try:
            with open(logo_path, "rb") as image_file:
                return "data:image/png;base64," + base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            print(f"Error loading logo: {e}")
            return ""
    return ""

from flask import (Flask, render_template,
    redirect, url_for, flash, request, jsonify, Response)
from flask_login import (login_required, current_user)
from auth import auth, login_manager
from database import (get_db_connection, init_db,
    create_default_admin)

ROOT = os.path.dirname(BACKEND_DIR)

app = Flask(__name__,
    template_folder=os.path.join(ROOT, 'frontend', 'templates'),
    static_folder=os.path.join(ROOT, 'frontend', 'static'))
app.secret_key = 'cyberir-secret-key-2026'

login_manager.init_app(app)
login_manager.login_view = 'auth.login'
app.register_blueprint(auth)

def sanitize_input(val, max_len):
    if not val: return ''
    return str(val).strip()[:max_len]

@app.context_processor
# Inject common variables like unread alert count into all templates
def inject_globals():
    try:
        if current_user.is_authenticated:
            conn = get_db_connection()
            unread_alerts_count = conn.execute(
                """SELECT COUNT(*) as c FROM alerts
                   WHERE (recipient_id=? 
                     OR recipient_role=?)
                   AND is_read=0 
                   AND dismissed=0""",
                [current_user.id,
                 current_user.role]
            ).fetchone()['c']
            active_clusters = conn.execute(
                """SELECT COUNT(*) as c 
                   FROM incident_clusters
                   WHERE status='Active'"""
            ).fetchone()['c']
            conn.close()
            return {
                'unread_alerts_count': unread_alerts_count,
                'active_correlation_clusters': active_clusters,
                'app_version': '1.0.0',
                'app_name': 'CyberIR'
            }
    except:
        pass
    return {
        'unread_alerts_count': 0,
        'active_correlation_clusters': 0,
        'app_version': '1.0.0',
        'app_name': 'CyberIR'
    }

# ─── REDIRECT ROUTES ───────────────────────────

@app.route('/')
# Redirect root URL to the dashboard or login page
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('auth.login'))

@app.route('/login')
# Handle user authentication and session creation
def login_page():
    return redirect(url_for('auth.login'))

# ─── DASHBOARD ─────────────────────────────────

@app.route('/dashboard')
@login_required
# Render main dashboard with summary statistics and charts
def dashboard():
    if current_user.role == 'CIRT':
        flash('Access restricted to CIRT portal.', 'error')
        return redirect(url_for('cirt_incidents'))
    try:
        conn = get_db_connection()
        total_incidents = conn.execute(
            'SELECT COUNT(*) as c FROM incidents'
        ).fetchone()['c']
        open_incidents = conn.execute(
            "SELECT COUNT(*) as c FROM incidents WHERE status='Open'"
        ).fetchone()['c']
        investigating_incidents = conn.execute(
            "SELECT COUNT(*) as c FROM incidents WHERE status='Investigating'"
        ).fetchone()['c']
        resolved_incidents = conn.execute(
            "SELECT COUNT(*) as c FROM incidents WHERE status IN ('Resolved','Closed')"
        ).fetchone()['c']
        critical_incidents = conn.execute(
            "SELECT COUNT(*) as c FROM incidents WHERE priority='Catastrophic' AND status NOT IN ('Resolved','Closed')"
        ).fetchone()['c']
        active_clusters = conn.execute(
            "SELECT COUNT(*) as c FROM incident_clusters WHERE status='Active'"
        ).fetchone()['c']
        total_correlated = conn.execute(
            "SELECT COUNT(*) as c FROM incidents WHERE cluster_id IS NOT NULL"
        ).fetchone()['c']
        incidents_by_status = [dict(r) for r in conn.execute(
            "SELECT status, COUNT(*) as count FROM incidents GROUP BY status"
        ).fetchall()]
        incidents_by_severity = [dict(r) for r in conn.execute(
            "SELECT priority, COUNT(*) as count FROM incidents WHERE priority IS NOT NULL GROUP BY priority"
        ).fetchall()]
        incidents_by_type = [dict(r) for r in conn.execute(
            "SELECT incident_type, COUNT(*) as count FROM incidents GROUP BY incident_type ORDER BY count DESC"
        ).fetchall()]
        daily_trend = [dict(r) for r in conn.execute(
            "SELECT DATE(reported_date) as date, COUNT(*) as count FROM incidents WHERE reported_date >= DATE('now','-14 days') GROUP BY DATE(reported_date) ORDER BY date ASC"
        ).fetchall()]
        resolution_by_type = [dict(r) for r in conn.execute(
            "SELECT incident_type, ROUND(AVG(resolution_time_minutes)/60.0,1) as avg_hours FROM incidents WHERE resolution_time_minutes IS NOT NULL AND status IN ('Resolved','Closed') GROUP BY incident_type ORDER BY avg_hours DESC"
        ).fetchall()]
        top_incidents = conn.execute(
            "SELECT i.*, u.full_name as assigned_name FROM incidents i LEFT JOIN users u ON i.assigned_to=u.id WHERE i.status IN ('Open','Investigating') ORDER BY i.risk_score DESC LIMIT 5"
        ).fetchall()
        recent_clusters = conn.execute(
            "SELECT * FROM incident_clusters ORDER BY last_updated DESC LIMIT 5"
        ).fetchall()
        recent_incidents = conn.execute(
            "SELECT * FROM incidents ORDER BY reported_date DESC LIMIT 5"
        ).fetchall()
        total_similarity_matches = conn.execute(
            "SELECT COUNT(*) as c FROM incidents WHERE similar_incident_id IS NOT NULL"
        ).fetchone()['c']
        high_confidence_matches = conn.execute(
            "SELECT COUNT(*) as c FROM incidents WHERE similarity_score >= 0.75"
        ).fetchone()['c']
        solutions_applied = conn.execute(
            "SELECT COUNT(*) as c FROM incidents WHERE solution_applied_from IS NOT NULL"
        ).fetchone()['c']
        recent_similarity = conn.execute(
            "SELECT i.*, si.title as matched_title FROM incidents i LEFT JOIN incidents si ON i.similar_incident_id=si.incident_id WHERE i.similar_incident_id IS NOT NULL ORDER BY i.reported_date DESC LIMIT 5"
        ).fetchall()
        today_count = conn.execute(
            "SELECT COUNT(*) as c FROM incidents WHERE DATE(reported_date)=DATE('now')"
        ).fetchone()['c']
        conn.close()
        return render_template('dashboard.html',
            total_incidents=total_incidents,
            open_incidents=open_incidents,
            investigating_incidents=investigating_incidents,
            resolved_incidents=resolved_incidents,
            critical_incidents=critical_incidents,
            active_clusters=active_clusters,
            total_correlated=total_correlated,
            incidents_by_status=incidents_by_status,
            incidents_by_severity=incidents_by_severity,
            incidents_by_type=incidents_by_type,
            daily_trend=daily_trend,
            resolution_by_type=resolution_by_type,
            top_incidents=top_incidents,
            recent_clusters=recent_clusters,
            recent_incidents=recent_incidents,
            total_similarity_matches=total_similarity_matches,
            high_confidence_matches=high_confidence_matches,
            solutions_applied=solutions_applied,
            recent_similarity=recent_similarity,
            today_count=today_count,
            active_page='dashboard')
    except Exception as e:
        import traceback
        traceback.print_exc()
        return render_template('dashboard.html',
            total_incidents=0, open_incidents=0,
            investigating_incidents=0,
            resolved_incidents=0,
            critical_incidents=0,
            active_clusters=0, total_correlated=0,
            incidents_by_status=[],
            incidents_by_severity=[],
            incidents_by_type=[],
            daily_trend=[], resolution_by_type=[],
            top_incidents=[], recent_clusters=[],
            recent_incidents=[],
            total_similarity_matches=0,
            high_confidence_matches=0,
            solutions_applied=0,
            recent_similarity=[],
            today_count=0,
            active_page='dashboard')

# ─── CIRT INCIDENTS ─────────────────────────────

@app.route('/cirt/incidents')
@login_required
def cirt_incidents():
    if current_user.role != 'CIRT':
        flash('Access denied. This page is for CIRT members only.', 'error')
        return redirect(url_for('dashboard'))
        
    conn = get_db_connection()
    status_filter = request.args.get('status', 'All Statuses')
    severity_filter = request.args.get('severity', 'All Severities')
    search_query = request.args.get('search', '').strip()
    sort_raw = request.args.get('sort', 'detected_datetime')
    order_raw = request.args.get('order', 'desc').lower()
    
    valid_sort_columns = ['incident_id', 'title', 'priority', 'status', 'risk_score', 'detected_datetime', 'reported_date']
    sort_column = sort_raw if sort_raw in valid_sort_columns else 'detected_datetime'
    order_dir = 'DESC' if order_raw != 'asc' else 'ASC'
    
    query = "SELECT *, priority AS severity FROM incidents WHERE escalated_to_cirt = 1"
    params = []
    
    if status_filter != 'All Statuses':
        if status_filter in ['Resolved', 'Closed']:
            query += " AND status = ?"
            params.append(status_filter)
        elif status_filter in ['Open', 'Investigating']:
            query += " AND status = ?"
            params.append(status_filter)
            
    if severity_filter != 'All Severities':
        query += " AND priority = ?"
        params.append(severity_filter)
        
    if search_query:
        query += " AND (incident_id LIKE ? OR title LIKE ?)"
        params.extend([f"%{search_query}%", f"%{search_query}%"])
        
    query += f" ORDER BY {sort_column} {order_dir}"
    
    page = request.args.get('page', 1, type=int)
    per_page = 20
    offset = (page - 1) * per_page
    
    count_query = query.replace('SELECT *, priority AS severity', 'SELECT COUNT(*) as c').split('ORDER BY')[0]
    total_count = conn.execute(count_query, params).fetchone()['c']
    total_pages = (total_count + per_page - 1) // per_page
    
    query += f" LIMIT ? OFFSET ?"
    params.extend([per_page, offset])
    
    incidents = conn.execute(query, params).fetchall()
    
    # Stats
    total_cirt = conn.execute("SELECT COUNT(*) as c FROM incidents WHERE escalated_to_cirt = 1").fetchone()['c']
    catastrophic_count = conn.execute("SELECT COUNT(*) as c FROM incidents WHERE priority = 'Catastrophic' AND escalated_to_cirt = 1").fetchone()['c']
    major_count = conn.execute("SELECT COUNT(*) as c FROM incidents WHERE priority = 'Major' AND escalated_to_cirt = 1").fetchone()['c']
    open_cirt = conn.execute("SELECT COUNT(*) as c FROM incidents WHERE escalated_to_cirt = 1 AND status IN ('Open', 'Investigating')").fetchone()['c']
    
    conn.close()
    
    return render_template('cirt_incidents.html',
                         active_page='cirt_incidents',
                         incidents=incidents,
                         total_cirt=total_cirt,
                         catastrophic_count=catastrophic_count,
                         major_count=major_count,
                         open_cirt=open_cirt,
                         status=status_filter,
                         severity=severity_filter,
                         search=search_query,
                         sort=sort_column,
                         order=order_raw,
                         page=page,
                         per_page=per_page,
                         total_count=total_count,
                         total_pages=total_pages)


@app.route('/cirt/incidents/export')
@login_required
def export_cirt_incidents():
    if current_user.role != 'CIRT':
        return redirect(url_for('cirt_incidents'))
        
    conn = get_db_connection()
    incidents = conn.execute("SELECT * FROM incidents WHERE escalated_to_cirt = 1 ORDER BY reported_date DESC").fetchall()
    conn.execute("INSERT INTO activity_logs (user_id,action_type,target_type,details) VALUES (?,'UPDATE_INCIDENT','Incidents','Exported CIRT incidents to CSV')",[current_user.id])
    conn.commit()
    conn.close()
    
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['incident_id', 'title', 'incident_type', 'priority', 'status', 'risk_score', 'affected_asset', 'affected_department', 'detected_datetime', 'reported_date', 'assigned_name'])
    
    for inc in incidents:
        cw.writerow([
            inc['incident_id'],
            inc['title'],
            inc['incident_type'],
            inc['priority'],
            inc['status'],
            inc['risk_score'],
            inc['affected_asset'],
            inc['affected_department'],
            inc['detected_datetime'],
            inc['reported_date'],
            inc['assigned_to'] # mapped to name ideally, but let's just dump what's there
        ])
        
    output = si.getvalue()
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=cirt_incidents_export.csv"}
    )


@app.route('/incidents')
@login_required
def incidents():
    if current_user.role == 'CIRT':
        flash('Access restricted to CIRT portal.', 'error')
        return redirect(url_for('cirt_incidents'))
    try:
        conn = get_db_connection()
        status_filter = request.args.get('status','')
        severity_filter = request.args.get('severity','')
        type_filter = request.args.get('incident_type','')
        search = request.args.get('search','')
        sort = request.args.get('sort','reported_date')
        order = request.args.get('order','desc').lower()
        page = int(request.args.get('page',1))
        per_page = int(request.args.get('per_page',25))

        where_clauses = []
        params = []

        if status_filter and status_filter not in ('', 'All Statuses'):
            where_clauses.append("i.status=?")
            params.append(status_filter)
        if severity_filter and severity_filter not in ('', 'All Priorities'):
            where_clauses.append("i.priority=?")
            params.append(severity_filter)
        if type_filter and type_filter not in ('', 'All Types'):
            where_clauses.append("i.incident_type=?")
            params.append(type_filter)
        if search:
            where_clauses.append("(i.title LIKE ? OR i.incident_id LIKE ? OR i.affected_asset LIKE ?)")
            params.extend([f'%{search}%']*3)

        where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

        allowed = ['reported_date','risk_score','priority','status','incident_id','title','incident_type','affected_asset']
        if sort not in allowed: sort = 'reported_date'
        if order not in ('asc','desc'): order = 'desc'
        order_sql = 'DESC' if order == 'desc' else 'ASC'

        base_q = f"SELECT i.*, u.full_name as assigned_name FROM incidents i LEFT JOIN users u ON i.assigned_to=u.id {where_sql}"
        count_q = f"SELECT COUNT(*) as count FROM incidents i {where_sql}"

        total_count = conn.execute(count_q, params).fetchone()['count']
        offset = (page-1)*per_page
        incidents_list = conn.execute(
            f"{base_q} ORDER BY i.{sort} {order_sql} LIMIT ? OFFSET ?",
            params + [per_page, offset]
        ).fetchall()

        all_count   = conn.execute("SELECT COUNT(*) as c FROM incidents").fetchone()['c']
        open_count  = conn.execute("SELECT COUNT(*) as c FROM incidents WHERE status='Open'").fetchone()['c']
        inv_count   = conn.execute("SELECT COUNT(*) as c FROM incidents WHERE status='Investigating'").fetchone()['c']
        res_count   = conn.execute("SELECT COUNT(*) as c FROM incidents WHERE status IN ('Resolved','Closed')").fetchone()['c']
        analysts    = conn.execute("SELECT id, full_name FROM users WHERE role IN ('Admin','Analyst') AND is_active=1").fetchall()
        conn.close()

        return render_template('incidents.html',
            incidents=incidents_list,
            total_count=total_count,
            stats={'total': all_count, 'open': open_count,
                   'investigating': inv_count, 'resolved': res_count},
            analysts=analysts,
            page=page, per_page=per_page,
            sort=sort, order=order,
            active_filters=len(where_clauses),
            active_page='incidents')
    except Exception as e:
        import traceback; traceback.print_exc()
        flash('Error loading incidents.','error')
        return redirect(url_for('dashboard'))

@app.route('/incidents/log', methods=['GET','POST'])
@login_required
# Process new incident ticket submissions
def log_incident():
    if current_user.role == 'Viewer':
        flash('No permission to log incidents.','error')
        return redirect(url_for('incidents'))
    try:
        conn = get_db_connection()
        if request.method == 'POST':
            title = request.form.get('title','').strip()
            
            # Contact Information
            contact_full_name = sanitize_input(request.form.get('contact_full_name'), 200)
            contact_job_title = sanitize_input(request.form.get('contact_job_title'), 200)
            contact_office = sanitize_input(request.form.get('contact_office'), 200)
            contact_work_phone = sanitize_input(request.form.get('contact_work_phone'), 50)
            contact_mobile_phone = sanitize_input(request.form.get('contact_mobile_phone'), 50)
            contact_additional = sanitize_input(request.form.get('contact_additional'), 500)
            
            # Detection Method
            detection_method = sanitize_input(request.form.get('detection_method'), 100)
            detection_method_other = sanitize_input(request.form.get('detection_method_other'), 200)
            
            # Incident Type
            incident_type_list = request.form.getlist('incident_type')
            incident_type = ', '.join(incident_type_list) if incident_type_list else ''
            incident_type_other = sanitize_input(request.form.get('incident_type_other'), 200)

            # Impact of Incident
            impact_list = request.form.getlist('impact_selections')
            impact_selections = ', '.join(impact_list) if impact_list else None
            impact_other = sanitize_input(request.form.get('impact_other'), 200)
            impact_additional = sanitize_input(request.form.get('impact_additional'), 1000)

            # Data Sensitivity
            sensitivity_list = request.form.getlist('data_sensitivity_selections')
            data_sensitivity_selections = ', '.join(sensitivity_list) if sensitivity_list else None
            data_sensitivity_other = sanitize_input(request.form.get('data_sensitivity_other'), 200)
            data_sensitivity_additional = sanitize_input(request.form.get('data_sensitivity_additional'), 1000)

            # Systems Affected
            detected_datetime = request.form.get('detected_datetime') or None
            incident_occurred_datetime = request.form.get('incident_occurred_datetime') or None
            attack_source = sanitize_input(request.form.get('attack_source'), 20)
            affected_system_ips = sanitize_input(request.form.get('affected_system_ips'), 500)
            attack_source_ips = sanitize_input(request.form.get('attack_source_ips'), 500)
            affected_system_functions = sanitize_input(request.form.get('affected_system_functions'), 500)
            affected_system_os = sanitize_input(request.form.get('affected_system_os'), 500)
            affected_system_location = sanitize_input(request.form.get('affected_system_location'), 500)
            affected_system_security_software = sanitize_input(request.form.get('affected_system_security_software'), 500)
            affected_systems_count_val = request.form.get('affected_systems_count')
            affected_systems_count = int(affected_systems_count_val) if affected_systems_count_val and affected_systems_count_val.isdigit() else None
            third_parties_involved = sanitize_input(request.form.get('third_parties_involved'), 500)

            description = request.form.get('description','')
            affected_asset = request.form.get('affected_asset','').strip()
            affected_department = request.form.get('affected_department','')
            users_affected = int(request.form.get('users_affected',0) or 0)
            ip_address = request.form.get('ip_address','')
            attack_indicators = request.form.get('attack_indicators','')
            asset_criticality = int(request.form.get('asset_criticality',1) or 1)
            threat_severity = int(request.form.get('threat_severity',1) or 1)
            vulnerability_exposure = int(request.form.get('vulnerability_exposure',1) or 1)
            is_repeat = 1 if request.form.get('is_repeat') else 0
            assigned_to = request.form.get('assigned_to') or None
            reported_date = request.form.get('reported_date') or None
            resolution_notes = request.form.get('resolution_notes','')
            ua = (1 if users_affected==0 else 2 if users_affected<=5 else 3 if users_affected<=20 else 4 if users_affected<=100 else 5)
            raw = (asset_criticality*0.30 + threat_severity*0.30 + vulnerability_exposure*0.15 + ua*0.20 + (5 if is_repeat else 1)*0.05)
            risk_score = round((raw/5)*100,2)
            severity = ('Catastrophic' if risk_score>=75 else 'Major' if risk_score>=50 else 'Moderate' if risk_score>=25 else 'Minor')
            from database import get_next_incident_id
            incident_id = get_next_incident_id()
            cursor = conn.execute(
                "INSERT INTO incidents (incident_id,title,description,incident_type,affected_asset,affected_department,users_affected,ip_address,attack_indicators,asset_criticality,threat_severity,vulnerability_exposure,is_repeat,risk_score,priority,status,assigned_to,reported_date,resolution_notes,created_by,created_at,updated_at, contact_full_name, contact_job_title, contact_office, contact_work_phone, contact_mobile_phone, contact_additional, detection_method, detection_method_other, incident_type_other, impact_selections, impact_other, impact_additional, data_sensitivity_selections, data_sensitivity_other, data_sensitivity_additional, detected_datetime, incident_occurred_datetime, attack_source, affected_system_ips, attack_source_ips, affected_system_functions, affected_system_os, affected_system_location, affected_system_security_software, affected_systems_count, third_parties_involved) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,'Open',?,?,?,?,datetime('now'),datetime('now'), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (incident_id,title,description,incident_type,affected_asset,affected_department,users_affected,ip_address,attack_indicators,asset_criticality,threat_severity,vulnerability_exposure,is_repeat,risk_score,severity,assigned_to,reported_date,resolution_notes,current_user.id, contact_full_name, contact_job_title, contact_office, contact_work_phone, contact_mobile_phone, contact_additional, detection_method, detection_method_other, incident_type_other, impact_selections, impact_other, impact_additional, data_sensitivity_selections, data_sensitivity_other, data_sensitivity_additional, detected_datetime, incident_occurred_datetime, attack_source, affected_system_ips, attack_source_ips, affected_system_functions, affected_system_os, affected_system_location, affected_system_security_software, affected_systems_count, third_parties_involved))
            new_id = cursor.lastrowid
            conn.execute("INSERT INTO activity_logs (user_id,action_type,target_type,target_id,details) VALUES (?,'CREATE_INCIDENT','Incident',?,?)",[current_user.id,new_id,f"Created new incident {incident_id}: {title}"])
            
            if severity in ['Major', 'Catastrophic']:
                conn.execute('UPDATE incidents SET escalated_to_cirt = 1 WHERE id = ?', [new_id])
                cirt_users = conn.execute("SELECT id FROM users WHERE role = 'CIRT' AND is_active = 1").fetchall()
                for cirt_user in cirt_users:
                    conn.execute(
                        '''INSERT INTO alerts
                           (alert_type, severity, message, incident_id, recipient_id, is_read)
                           VALUES (?,?,?,?,?,0)''',
                        ('ESCALATION', 'CRITICAL', f'Incident {incident_id} has been escalated to CIRT — Severity: {severity}', new_id, cirt_user['id'])
                    )
            conn.commit()
            conn.close()
            try:
                from correlation_engine import run_correlation
                run_correlation(new_id)
            except: pass
            try:
                from similarity_engine import run_similarity
                run_similarity(new_id)
            except: pass
            flash(f'Incident {incident_id} logged successfully.','success')
            return redirect(url_for('incidents'))
        analysts = conn.execute("SELECT id, full_name FROM users WHERE role IN ('Admin','Analyst') AND is_active=1").fetchall()
        conn.close()
        return render_template('log_incident.html', analysts=analysts, active_page='incidents')
    except Exception as e:
        import traceback; traceback.print_exc()
        flash(f'Error logging incident: {str(e)}','error')
        return redirect(url_for('incidents'))

@app.route('/incidents/pdf-data/<incident_id>')
@login_required
def get_pdf_data(incident_id):
    conn = get_db_connection()
    incident = conn.execute("SELECT * FROM incidents WHERE incident_id=?", [incident_id]).fetchone()
    if not incident:
        conn.close()
        return jsonify({"success": False, "message": "Incident not found"}), 404
        
    user_row = conn.execute("SELECT full_name FROM users WHERE id=?", [incident['assigned_to']]).fetchone()
    assigned_name = user_row['full_name'] if user_row else ''
    
    eng = conn.execute("SELECT setting_value FROM settings WHERE setting_key='pdf_cybersecurity_engineer'").fetchone()
    mgr = conn.execute("SELECT setting_value FROM settings WHERE setting_key='pdf_technical_services_manager'").fetchone()
    conn.close()
    
    return jsonify({
        "success": True,
        "incident": dict(incident),
        "assigned_name": assigned_name,
        "default_engineer": eng['setting_value'] if eng else 'CHABVUTAGONDO .T.',
        "default_manager": mgr['setting_value'] if mgr else 'MUCHOVO .R.',
        "logo_data": get_logo_base64()
    })

@app.route('/incidents/generate-pdf/<incident_id>', methods=['POST'])
@login_required
def generate_pdf(incident_id):
    data = request.json
    engineer_name = data.get('engineer_name', '')
    manager_name = data.get('manager_name', '')
    
    conn = get_db_connection()
    incident = conn.execute("SELECT * FROM incidents WHERE incident_id=?", [incident_id]).fetchone()
    user_row = conn.execute("SELECT full_name FROM users WHERE id=?", [incident['assigned_to']]).fetchone() if incident and incident['assigned_to'] else None
    assigned_name = user_row['full_name'] if user_row else ''
    if incident:
        conn.execute("INSERT INTO activity_logs (user_id,action_type,target_type,target_id,details) VALUES (?,'UPDATE_INCIDENT','Incident',?,?)",[current_user.id, incident['id'], f"Exported incident {incident_id} as PDF"])
        conn.commit()
    conn.close()
    
    if not incident:
        return jsonify({"success": False, "message": "Not found"}), 404
        
    html_content = render_template('incident_pdf.html',
        incident=dict(incident),
        assigned_name=assigned_name,
        engineer_name=engineer_name,
        manager_name=manager_name,
        logo_data=get_logo_base64()
    )
    
    pdf_bytes = generate_pdf_from_html(html_content)
    if pdf_bytes is None:
        return jsonify({"success": False, "message": "PDF library not installed"}), 500
        
    return Response(pdf_bytes, mimetype='application/pdf', headers={'Content-Disposition': f'attachment; filename="{incident_id}_report.pdf"'})

@app.template_filter('format_date')
def format_date_filter(value):
    if not value: return '—'
    try:
        from datetime import datetime
        if isinstance(value, str): dt = datetime.fromisoformat(value.replace('Z',''))
        else: dt = value
        return dt.strftime('%d %B %Y, %H:%M')
    except:
        return str(value)

@app.route('/incidents/<incident_id>')
@login_required
def incident_detail(incident_id):
    try:
        conn = get_db_connection()
        incident = conn.execute(
            "SELECT i.*, u.full_name as assigned_name, c.full_name as creator_name FROM incidents i LEFT JOIN users u ON i.assigned_to=u.id LEFT JOIN users c ON i.created_by=c.id WHERE i.incident_id=?",
            [incident_id]).fetchone()
        if not incident:
            flash('Incident not found.','error')
            return redirect(url_for('incidents'))
        incident = dict(incident)
        for f in ['risk_score','correlation_score','similarity_score']:
            incident[f] = float(incident.get(f) or 0)
        for f in ['asset_criticality','threat_severity','vulnerability_exposure','users_affected','resolution_time_minutes','is_repeat']:
            incident[f] = int(incident.get(f) or 0)
        activity = conn.execute(
            "SELECT al.*, u.full_name FROM activity_logs al JOIN users u ON al.user_id=u.id WHERE al.target_id=? AND al.target_type='incident' ORDER BY al.created_at DESC",
            [incident['id']]).fetchall()
        analysts = conn.execute("SELECT id, full_name FROM users WHERE role IN ('Admin','Analyst') AND is_active=1").fetchall()
        incident_data = incident
        
        # Make sure these fields are present and not being lost
        print("cluster_id:", incident_data.get('cluster_id'))
        print("similar_incident_id:", incident_data.get('similar_incident_id'))
        print("similarity_score:", incident_data.get('similarity_score'))

        cluster = None
        if incident_data.get('cluster_id'):
            cluster = conn.execute(
                '''SELECT * FROM incident_clusters 
                   WHERE cluster_id = ?''',
                [incident_data['cluster_id']]).fetchone()
            if cluster:
                cluster = dict(cluster)

        similar_incident = None
        if incident_data.get('similar_incident_id'):
            similar_incident = conn.execute(
                '''SELECT incident_id, title, 
                   incident_type, status
                   FROM incidents 
                   WHERE incident_id = ?''',
                [incident_data['similar_incident_id']]
            ).fetchone()
            if similar_incident:
                similar_incident = dict(similar_incident)

        conn.close()
        return render_template(
            'incident_detail.html',
            incident=incident_data,
            cluster=cluster,
            similar_incident=similar_incident,
            activity=activity,
            analysts=analysts,
            active_page='incidents'
        )
    except Exception as e:
        import traceback; traceback.print_exc()
        flash('Error loading incident.','error')
        return redirect(url_for('incidents'))

@app.route('/incidents/<incident_id>/edit', methods=['GET','POST'])
@login_required
# Update existing incident details in the database
def edit_incident(incident_id):
    if current_user.role == 'Viewer':
        flash('No permission to edit incidents.','error')
        return redirect(url_for('incidents'))
    try:
        conn = get_db_connection()
        incident = conn.execute("SELECT * FROM incidents WHERE incident_id=?",[incident_id]).fetchone()
        if not incident:
            flash('Incident not found.','error')
            return redirect(url_for('incidents'))
        if request.method == 'POST':
            title = request.form.get('title','').strip()
            
            # Contact Information
            contact_full_name = sanitize_input(request.form.get('contact_full_name'), 200)
            contact_job_title = sanitize_input(request.form.get('contact_job_title'), 200)
            contact_office = sanitize_input(request.form.get('contact_office'), 200)
            contact_work_phone = sanitize_input(request.form.get('contact_work_phone'), 50)
            contact_mobile_phone = sanitize_input(request.form.get('contact_mobile_phone'), 50)
            contact_additional = sanitize_input(request.form.get('contact_additional'), 500)
            
            # Detection Method
            detection_method = sanitize_input(request.form.get('detection_method'), 100)
            detection_method_other = sanitize_input(request.form.get('detection_method_other'), 200)
            
            # Incident Type
            incident_type_list = request.form.getlist('incident_type')
            incident_type = ', '.join(incident_type_list) if incident_type_list else ''
            incident_type_other = sanitize_input(request.form.get('incident_type_other'), 200)

            # Impact of Incident
            impact_list = request.form.getlist('impact_selections')
            impact_selections = ', '.join(impact_list) if impact_list else None
            impact_other = sanitize_input(request.form.get('impact_other'), 200)
            impact_additional = sanitize_input(request.form.get('impact_additional'), 1000)

            # Data Sensitivity
            sensitivity_list = request.form.getlist('data_sensitivity_selections')
            data_sensitivity_selections = ', '.join(sensitivity_list) if sensitivity_list else None
            data_sensitivity_other = sanitize_input(request.form.get('data_sensitivity_other'), 200)
            data_sensitivity_additional = sanitize_input(request.form.get('data_sensitivity_additional'), 1000)

            # Systems Affected
            detected_datetime = request.form.get('detected_datetime') or None
            incident_occurred_datetime = request.form.get('incident_occurred_datetime') or None
            attack_source = sanitize_input(request.form.get('attack_source'), 20)
            affected_system_ips = sanitize_input(request.form.get('affected_system_ips'), 500)
            attack_source_ips = sanitize_input(request.form.get('attack_source_ips'), 500)
            affected_system_functions = sanitize_input(request.form.get('affected_system_functions'), 500)
            affected_system_os = sanitize_input(request.form.get('affected_system_os'), 500)
            affected_system_location = sanitize_input(request.form.get('affected_system_location'), 500)
            affected_system_security_software = sanitize_input(request.form.get('affected_system_security_software'), 500)
            affected_systems_count_val = request.form.get('affected_systems_count')
            affected_systems_count = int(affected_systems_count_val) if affected_systems_count_val and affected_systems_count_val.isdigit() else None
            third_parties_involved = sanitize_input(request.form.get('third_parties_involved'), 500)

            description = request.form.get('description','')
            affected_asset = request.form.get('affected_asset','').strip()
            affected_department = request.form.get('affected_department','')
            users_affected = int(request.form.get('users_affected',0) or 0)
            ip_address = request.form.get('ip_address','')
            attack_indicators = request.form.get('attack_indicators','')
            asset_criticality = int(request.form.get('asset_criticality',1) or 1)
            threat_severity = int(request.form.get('threat_severity',1) or 1)
            vulnerability_exposure = int(request.form.get('vulnerability_exposure',1) or 1)
            is_repeat = 1 if request.form.get('is_repeat') else 0
            assigned_to = request.form.get('assigned_to') or None
            reported_date = request.form.get('reported_date') or None
            ua = (1 if users_affected==0 else 2 if users_affected<=5 else 3 if users_affected<=20 else 4 if users_affected<=100 else 5)
            raw = (asset_criticality*0.30 + threat_severity*0.30 + vulnerability_exposure*0.15 + ua*0.20 + (5 if is_repeat else 1)*0.05)
            risk_score = round((raw/5)*100,2)
            severity = ('Catastrophic' if risk_score>=75 else 'Major' if risk_score>=50 else 'Moderate' if risk_score>=25 else 'Minor')
            conn.execute(
                "UPDATE incidents SET title=?,description=?,incident_type=?,affected_asset=?,affected_department=?,users_affected=?,ip_address=?,attack_indicators=?,asset_criticality=?,threat_severity=?,vulnerability_exposure=?,is_repeat=?,risk_score=?,priority=?,assigned_to=?,reported_date=?,updated_at=datetime('now'),updated_by=?,contact_full_name=?,contact_job_title=?,contact_office=?,contact_work_phone=?,contact_mobile_phone=?,contact_additional=?,detection_method=?,detection_method_other=?,incident_type_other=?,impact_selections=?,impact_other=?,impact_additional=?,data_sensitivity_selections=?,data_sensitivity_other=?,data_sensitivity_additional=?,detected_datetime=?,incident_occurred_datetime=?,attack_source=?,affected_system_ips=?,attack_source_ips=?,affected_system_functions=?,affected_system_os=?,affected_system_location=?,affected_system_security_software=?,affected_systems_count=?,third_parties_involved=? WHERE incident_id=?",
                (title,description,incident_type,affected_asset,affected_department,users_affected,ip_address,attack_indicators,asset_criticality,threat_severity,vulnerability_exposure,is_repeat,risk_score,severity,assigned_to,reported_date,current_user.id,contact_full_name,contact_job_title,contact_office,contact_work_phone,contact_mobile_phone,contact_additional,detection_method,detection_method_other,incident_type_other,impact_selections,impact_other,impact_additional,data_sensitivity_selections,data_sensitivity_other,data_sensitivity_additional,detected_datetime,incident_occurred_datetime,attack_source,affected_system_ips,attack_source_ips,affected_system_functions,affected_system_os,affected_system_location,affected_system_security_software,affected_systems_count,third_parties_involved,incident_id))
            
            changes = []
            if incident['title'] != title: changes.append('title')
            if incident['incident_type'] != incident_type: changes.append('type')
            if str(incident['assigned_to'] or '') != str(assigned_to or ''):
                u = conn.execute("SELECT full_name FROM users WHERE id=?",[assigned_to]).fetchone() if assigned_to else None
                changes.append(f"reassigned to {u['full_name'] if u else 'Unassigned'}")
            if incident['priority'] != severity: changes.append(f'priority to {severity}')
            if incident['status'] != 'Open' and not changes: changes.append('general details')
            
            diff_text = f"Updated incident {incident['incident_id']}: modified " + ", ".join(changes) if changes else f"Updated incident {incident_id}"
            conn.execute("INSERT INTO activity_logs (user_id,action_type,target_type,target_id,details) VALUES (?,'UPDATE_INCIDENT','Incident',?,?)",[current_user.id,incident['id'],diff_text])
            conn.commit()
            conn.close()
            flash(f'Incident {incident_id} updated.','success')
            return redirect(url_for('incident_detail',incident_id=incident_id))
        analysts = conn.execute("SELECT id, full_name FROM users WHERE role IN ('Admin','Analyst') AND is_active=1").fetchall()
        conn.close()
        return render_template('edit_incident.html',
            incident=dict(incident),
            analysts=analysts,
            active_page='incidents')
    except Exception as e:
        import traceback; traceback.print_exc()
        flash(f'Error editing incident: {str(e)}','error')
        return redirect(url_for('incidents'))

@app.route('/incidents/assign/<incident_id>', methods=['POST'])
@login_required
# Assign or reassign an incident to a specific analyst
def assign_incident(incident_id):
    try:
        conn = get_db_connection()
        assigned_to = request.form.get('assigned_to') or None
        conn.execute("UPDATE incidents SET assigned_to=?,updated_at=datetime('now'),updated_by=? WHERE incident_id=?",[assigned_to,current_user.id,incident_id])
        assigned_name = 'Unassigned'
        if assigned_to:
            u = conn.execute("SELECT full_name FROM users WHERE id=?",[assigned_to]).fetchone()
            if u: assigned_name = u['full_name']
        conn.execute("INSERT INTO activity_logs (user_id,action_type,target_type,details) VALUES (?,'ASSIGN_INCIDENT','Incident',?)",[current_user.id,f'Assigned incident {incident_id} to {assigned_name}'])
        conn.commit()
        conn.close()
        return jsonify({'success':True,'assigned_name':assigned_name})
    except Exception as e:
        return jsonify({'success':False,'message':str(e)})

@app.route('/incidents/update-status/<incident_id>', methods=['POST'])
@login_required
# Progress the lifecycle status of an incident
def update_incident_status(incident_id):
    try:
        conn = get_db_connection()
        new_status = request.form.get('new_status','')
        updates = "status=?,updated_at=datetime('now'),updated_by=?"
        params = [new_status, current_user.id]
        if new_status == 'Investigating':
            updates += ",investigating_started_date=datetime('now')"
        elif new_status == 'Closed':
            updates += ",closed_date=datetime('now')"
        params.append(incident_id)
        conn.execute(f"UPDATE incidents SET {updates} WHERE incident_id=?", params)
        conn.execute("INSERT INTO activity_logs (user_id,action_type,target_type,details) VALUES (?,'UPDATE_INCIDENT','Incident',?)",[current_user.id,f"Updated incident {incident_id}: changed status to {new_status}"])
        conn.commit()
        conn.close()
        return jsonify({'success':True})
    except Exception as e:
        return jsonify({'success':False,'message':str(e)})

@app.route('/incidents/resolve/<incident_id>', methods=['POST'])
@login_required
# Mark an incident as resolved and record mitigation notes
def resolve_incident(incident_id):
    try:
        conn = get_db_connection()
        resolution_notes = request.form.get('resolution_notes','').strip()
        if not resolution_notes:
            return jsonify({'success':False,'message':'Resolution notes required'})
        incident = conn.execute("SELECT * FROM incidents WHERE incident_id=?",[incident_id]).fetchone()
        reported = incident['reported_date']
        conn.execute(
            "UPDATE incidents SET status='Resolved',resolved_date=datetime('now'),resolution_notes=?,updated_at=datetime('now'),updated_by=? WHERE incident_id=?",
            [resolution_notes,current_user.id,incident_id])
        conn.execute("INSERT INTO activity_logs (user_id,action_type,target_type,details) VALUES (?,'RESOLVE_INCIDENT','Incident',?)",[current_user.id,f"Resolved incident {incident_id} with resolution notes"])
        conn.commit()
        conn.close()
        return jsonify({'success':True})
    except Exception as e:
        return jsonify({'success':False,'message':str(e)})

@app.route('/incidents/delete/<incident_id>', methods=['POST'])
@login_required
# Permanently remove an incident and its associated alerts
def delete_incident(incident_id):
    if current_user.role == 'CIRT':
        return jsonify({"success": False, "message": "CIRT members cannot delete incidents"}), 403
    if current_user.role != 'Admin':
        return jsonify({'success':False,'message':'Admin only'})
    try:
        conn = get_db_connection()
        incident = conn.execute("SELECT * FROM incidents WHERE incident_id=?",[incident_id]).fetchone()
        if not incident:
            return jsonify({'success':False,'message':'Not found'})
        if incident['cluster_id']:
            return jsonify({'success':False,'message':'Cannot delete a correlated incident'})
        conn.execute("DELETE FROM alerts WHERE incident_id=?",[incident['id']])
        conn.execute("DELETE FROM incidents WHERE incident_id=?",[incident_id])
        conn.execute("INSERT INTO activity_logs (user_id,action_type,target_type,details) VALUES (?,'DELETE_INCIDENT','Incident',?)",[current_user.id,f"Deleted incident {incident_id}"])
        conn.commit()
        conn.close()
        return jsonify({'success':True,'redirect':url_for('incidents')})
    except Exception as e:
        return jsonify({'success':False,'message':str(e)})

@app.route('/incidents/remove-from-cluster/<incident_id>', methods=['POST'])
@login_required
# Detach a specific incident from its correlation cluster
def remove_from_cluster(incident_id):
    if current_user.role != 'Admin':
        return jsonify({'success':False})
    try:
        from correlation_engine import remove_from_cluster as rfc
        incident = get_db_connection().execute("SELECT id FROM incidents WHERE incident_id=?",[incident_id]).fetchone()
        result = rfc(incident['id'])
        return jsonify({'success':True})
    except Exception as e:
        return jsonify({'success':False,'message':str(e)})

@app.route('/incidents/apply-solution/<incident_id>', methods=['POST'])
@login_required
# Auto-apply resolution notes from a historically similar incident
def apply_solution(incident_id):
    try:
        data = request.get_json(silent=True) or request.form
        source_id = data.get('source_incident_id','')
        notes = data.get('resolution_notes','')
        conn = get_db_connection()
        conn.execute(
            "UPDATE incidents SET resolution_notes=?,solution_applied_from=?,updated_at=datetime('now'),updated_by=? WHERE incident_id=?",
            [notes,source_id,current_user.id,incident_id])
        conn.execute("INSERT INTO activity_logs (user_id,action_type,target_type,details) VALUES (?,'UPDATE_INCIDENT','Incident',?)",[current_user.id,f"Updated incident {incident_id}: auto-applied resolution from {source_id}"])
        conn.commit()
        conn.close()
        return jsonify({'success':True})
    except Exception as e:
        return jsonify({'success':False,'message':str(e)})

# ─── CORRELATION ───────────────────────────────

@app.route('/correlation')
@login_required
# List active incident correlation clusters
def correlation():
    if current_user.role == 'CIRT':
        flash('Access restricted to CIRT portal.', 'error')
        return redirect(url_for('cirt_incidents'))
    try:
        conn = get_db_connection()
        clusters = conn.execute("SELECT * FROM incident_clusters ORDER BY last_updated DESC").fetchall()
        clusters_list = []
        for cl in clusters:
            d = dict(cl)
            d['incidents'] = conn.execute("SELECT * FROM incidents WHERE cluster_id=? ORDER BY reported_date DESC",[cl['cluster_id']]).fetchall()
            clusters_list.append(d)
        stats = {
            'total_clusters': conn.execute("SELECT COUNT(*) as c FROM incident_clusters").fetchone()['c'],
            'active_clusters': conn.execute("SELECT COUNT(*) as c FROM incident_clusters WHERE status='Active'").fetchone()['c'],
            'investigating_clusters': conn.execute("SELECT COUNT(*) as c FROM incident_clusters WHERE status='Investigating'").fetchone()['c'],
            'resolved_clusters': conn.execute("SELECT COUNT(*) as c FROM incident_clusters WHERE status='Resolved'").fetchone()['c'],
            'total_correlated_incidents': conn.execute("SELECT COUNT(*) as c FROM incidents WHERE cluster_id IS NOT NULL").fetchone()['c'],
        }
        conn.close()
        return render_template('correlation.html',
            clusters=clusters_list,
            stats=stats,
            active_page='correlation')
    except Exception as e:
        import traceback; traceback.print_exc()
        flash('Error loading correlation.','error')
        return redirect(url_for('dashboard'))

@app.route('/correlation/<cluster_id>')
@login_required
# Show incidents grouped within a specific correlation cluster
def correlation_detail(cluster_id):
    try:
        conn = get_db_connection()
        cluster = conn.execute("SELECT * FROM incident_clusters WHERE cluster_id=?",[cluster_id]).fetchone()
        if not cluster:
            flash('Cluster not found.','error')
            return redirect(url_for('correlation'))
        cluster = dict(cluster)
        cluster['incident_count'] = int(cluster.get('incident_count') or 0)
        cluster['severity'] = cluster.get('severity') or 'Moderate'
        cluster['status'] = cluster.get('status') or 'Active'
        cluster['notes'] = cluster.get('notes') or ''
        incidents_in = conn.execute("SELECT i.*, u.full_name as assigned_name FROM incidents i LEFT JOIN users u ON i.assigned_to=u.id WHERE i.cluster_id=? ORDER BY i.reported_date ASC",[cluster_id]).fetchall()
        incidents_list = []
        for inc in incidents_in:
            d = dict(inc)
            d['risk_score'] = float(d.get('risk_score') or 0)
            d['correlation_score'] = float(d.get('correlation_score') or 0)
            incidents_list.append(d)
        cluster_alerts = conn.execute("SELECT * FROM alerts WHERE cluster_id=? ORDER BY created_at DESC LIMIT 5",[cluster_id]).fetchall()
        analysts = conn.execute("SELECT id, full_name FROM users WHERE role IN ('Admin','Analyst') AND is_active=1").fetchall()
        assigned_user = None
        if cluster.get('assigned_to'):
            assigned_user = conn.execute("SELECT full_name FROM users WHERE id=?",[cluster['assigned_to']]).fetchone()
        conn.close()
        return render_template('correlation_detail.html',
            cluster=cluster,
            incidents=incidents_list,
            cluster_alerts=cluster_alerts,
            analysts=analysts,
            assigned_user=assigned_user,
            active_page='correlation')
    except Exception as e:
        import traceback; traceback.print_exc()
        flash(f'Error loading cluster: {str(e)}','error')
        return redirect(url_for('correlation'))

@app.route('/correlation/update-status/<cluster_id>', methods=['POST'])
@login_required
# Change the resolution status of an entire incident cluster
def update_cluster_status(cluster_id):
    try:
        data = request.get_json(silent=True) or request.form
        new_status = data.get('new_status','')
        conn = get_db_connection()
        conn.execute("UPDATE incident_clusters SET status=?,last_updated=datetime('now') WHERE cluster_id=?",[new_status,cluster_id])
        conn.commit()
        conn.close()
        return jsonify({'success':True})
    except Exception as e:
        return jsonify({'success':False,'message':str(e)})

@app.route('/correlation/assign/<cluster_id>', methods=['POST'])
@login_required
# Assign an entire incident cluster to an analyst
def assign_cluster(cluster_id):
    try:
        data = request.get_json(silent=True) or request.form
        assigned_to = data.get('assigned_to') or None
        conn = get_db_connection()
        conn.execute("UPDATE incident_clusters SET assigned_to=? WHERE cluster_id=?",[assigned_to,cluster_id])
        conn.commit()
        assigned_name = 'Unassigned'
        if assigned_to:
            u = conn.execute("SELECT full_name FROM users WHERE id=?",[assigned_to]).fetchone()
            if u: assigned_name = u['full_name']
        conn.close()
        return jsonify({'success':True,'assigned_name':assigned_name})
    except Exception as e:
        return jsonify({'success':False,'message':str(e)})

@app.route('/correlation/add-note/<cluster_id>', methods=['POST'])
@login_required
# Append analyst notes to a correlation cluster
def add_cluster_note(cluster_id):
    try:
        data = request.get_json(silent=True) or request.form
        note = data.get('note','').strip()
        if not note:
            return jsonify({'success':False,'message':'Note required'})
        conn = get_db_connection()
        cluster = conn.execute("SELECT notes FROM incident_clusters WHERE cluster_id=?",[cluster_id]).fetchone()
        existing = cluster['notes'] or ''
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        new_notes = f"{existing}\n[{timestamp}] {current_user.full_name}: {note}".strip()
        conn.execute("UPDATE incident_clusters SET notes=?,last_updated=datetime('now') WHERE cluster_id=?",[new_notes,cluster_id])
        conn.commit()
        conn.close()
        return jsonify({'success':True,'note':f'[{timestamp}] {current_user.full_name}: {note}'})
    except Exception as e:
        return jsonify({'success':False,'message':str(e)})

# ─── SIMILARITY ────────────────────────────────

@app.route('/similarity')
@login_required
# Display instances of similar incidents across the database
def similarity():
    if current_user.role == 'CIRT':
        flash('Access restricted to CIRT portal.', 'error')
        return redirect(url_for('cirt_incidents'))
    try:
        conn = get_db_connection()
        rows = conn.execute("""
            SELECT i.*,
                   si.incident_id  as similar_to_id,
                   si.title        as similar_to_title,
                   si.status       as similar_status,
                   si.resolution_notes as similar_resolution
            FROM incidents i
            LEFT JOIN incidents si ON i.similar_incident_id = si.incident_id
            WHERE i.similar_incident_id IS NOT NULL
            ORDER BY i.similarity_score DESC, i.reported_date DESC
        """).fetchall()
        # convert to dicts so templates can access by name
        incidents_list = []
        for r in rows:
            d = dict(r)
            d['similarity_score'] = float(d.get('similarity_score') or 0.0)
            d['severity'] = d.get('priority') or 'Minor'
            d['status'] = d.get('status') or 'Open'
            d['similar_status'] = d.get('similar_status') or 'Unknown'
            d['title'] = d.get('title') or 'Untitled'
            d['similar_to_title'] = d.get('similar_to_title') or 'Unknown Incident'
            d['similar_resolution'] = d.get('similar_resolution') or ''
            incidents_list.append(d)
        total_with_similarity = conn.execute("SELECT COUNT(*) as c FROM incidents WHERE similar_incident_id IS NOT NULL").fetchone()['c']
        high_confidence = conn.execute("SELECT COUNT(*) as c FROM incidents WHERE similarity_score >= 0.75").fetchone()['c']
        solution_applied = conn.execute("SELECT COUNT(*) as c FROM incidents WHERE solution_applied_from IS NOT NULL").fetchone()['c']
        avg_val = conn.execute("SELECT AVG(similarity_score) as a FROM incidents WHERE similar_incident_id IS NOT NULL").fetchone()['a']
        avg_similarity = round((avg_val or 0) * 100, 1)  # template shows as percentage
        conn.close()
        return render_template('similarity.html',
            incidents=incidents_list,
            total_with_similarity=total_with_similarity,
            high_confidence=high_confidence,
            solution_applied=solution_applied,
            avg_similarity=avg_similarity,
            active_page='similarity')
    except Exception as e:
        import traceback; traceback.print_exc()
        flash('Error loading similarity.','error')
        return redirect(url_for('dashboard'))

@app.route('/api/similarity/<incident_id>')
@login_required
# Provide JSON payload of similar incidents for front-end rendering
def api_similarity(incident_id):
    try:
        conn = get_db_connection()
        incident = conn.execute("SELECT * FROM incidents WHERE incident_id=?",[incident_id]).fetchone()
        conn.close()
        if not incident:
            return jsonify({'found':False,'matches':[]})
        from similarity_engine import run_similarity
        result = run_similarity(incident['id'])
        return jsonify(result)
    except Exception as e:
        return jsonify({'found':False,'matches':[],'error':str(e)})

# ─── ALERTS ────────────────────────────────────

@app.route('/alerts')
@login_required
# Render the alerts and notifications page
def alerts():
    try:
        conn = get_db_connection()
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        offset = (page - 1) * per_page
        alerts_list = conn.execute(
            "SELECT * FROM alerts WHERE (recipient_id=? OR recipient_role=?) AND dismissed=0 ORDER BY created_at DESC LIMIT ? OFFSET ?",
            [current_user.id, current_user.role, per_page, offset]
        ).fetchall()
        total_count  = conn.execute("SELECT COUNT(*) as c FROM alerts WHERE (recipient_id=? OR recipient_role=?) AND dismissed=0",[current_user.id,current_user.role]).fetchone()['c']
        unread_count = conn.execute("SELECT COUNT(*) as c FROM alerts WHERE (recipient_id=? OR recipient_role=?) AND is_read=0 AND dismissed=0",[current_user.id,current_user.role]).fetchone()['c']
        catastrophic_count = conn.execute("SELECT COUNT(*) as c FROM alerts WHERE (recipient_id=? OR recipient_role=?) AND severity='CRITICAL' AND is_read=0 AND dismissed=0",[current_user.id,current_user.role]).fetchone()['c']
        conn.close()
        return render_template('alerts.html',
            alerts=alerts_list,
            total_count=total_count,
            unread_count=unread_count,
            catastrophic_count=catastrophic_count,
            page=page,
            per_page=per_page,
            active_page='alerts')
    except Exception as e:
        import traceback; traceback.print_exc()
        flash('Error loading alerts.','error')
        return redirect(url_for('dashboard'))

@app.route('/alerts/mark-read/<int:alert_id>', methods=['POST'])
@login_required
# Update a specific alert's status to read
def mark_alert_read(alert_id):
    try:
        conn = get_db_connection()
        conn.execute("UPDATE alerts SET is_read=1,read_at=datetime('now') WHERE id=?",[alert_id])
        conn.commit(); conn.close()
        return jsonify({'success':True})
    except: return jsonify({'success':False})

@app.route('/alerts/mark-all-read', methods=['POST'])
@login_required
# Bulk update all user alerts to read status
def mark_all_alerts_read():
    try:
        conn = get_db_connection()
        conn.execute("UPDATE alerts SET is_read=1,read_at=datetime('now') WHERE (recipient_id=? OR recipient_role=?) AND is_read=0 AND dismissed=0",[current_user.id,current_user.role])
        conn.commit(); conn.close()
        return jsonify({'success':True})
    except: return jsonify({'success':False})

@app.route('/alerts/dismiss/<int:alert_id>', methods=['POST'])
@login_required
# Hide a specific alert from the user's view
def dismiss_alert(alert_id):
    try:
        conn = get_db_connection()
        conn.execute("UPDATE alerts SET dismissed=1,dismissed_at=datetime('now') WHERE id=?",[alert_id])
        conn.commit(); conn.close()
        return jsonify({'success':True})
    except: return jsonify({'success':False})

@app.route('/alerts/dismiss-all-read', methods=['POST'])
@login_required
# Hide all read alerts to clear the notification queue
def dismiss_all_read_alerts():
    try:
        conn = get_db_connection()
        conn.execute("UPDATE alerts SET dismissed=1,dismissed_at=datetime('now') WHERE (recipient_id=? OR recipient_role=?) AND is_read=1 AND dismissed=0",[current_user.id,current_user.role])
        conn.commit(); conn.close()
        return jsonify({'success':True})
    except: return jsonify({'success':False})

# ─── REPORTS ───────────────────────────────────

@app.route('/reports')
@login_required
# Render the reporting interface for KPI generation with optional filters
def reports():
    if current_user.role == 'CIRT':
        flash('Access restricted to CIRT portal.', 'error')
        return redirect(url_for('cirt_incidents'))
    if current_user.role != 'Admin' and not current_user.has_admin_privileges:
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard'))
    try:
        conn = get_db_connection()

        # Read URL filter params
        status_filter   = request.args.get('status', '').strip()
        severity_filter = request.args.get('severity', '').strip()
        type_filter     = request.args.get('type', '').strip()

        active_filters = {
            'status':   status_filter,
            'severity': severity_filter,
            'type':     type_filter,
        }

        # Build filtered incidents query
        inc_query = """
            SELECT i.incident_id, i.title, i.incident_type, i.priority,
                   i.status, i.risk_score, i.reported_date,
                   u.full_name as assigned_name
            FROM incidents i
            LEFT JOIN users u ON i.assigned_to = u.id
            WHERE 1=1
        """
        inc_params = []
        if status_filter:
            inc_query += " AND i.status = ?"
            inc_params.append(status_filter)
        if severity_filter:
            inc_query += " AND i.priority = ?"
            inc_params.append(severity_filter)
        if type_filter:
            inc_query += " AND i.incident_type = ?"
            inc_params.append(type_filter)
        inc_query += " ORDER BY i.reported_date DESC"
        filtered_incidents = conn.execute(inc_query, inc_params).fetchall()

        # Existing metrics dict — unchanged
        metrics = {
            'total_clusters_created':     conn.execute("SELECT COUNT(*) as c FROM incident_clusters").fetchone()['c'],
            'active_clusters':            conn.execute("SELECT COUNT(*) as c FROM incident_clusters WHERE status='Active'").fetchone()['c'],
            'resolved_clusters':          conn.execute("SELECT COUNT(*) as c FROM incident_clusters WHERE status='Resolved'").fetchone()['c'],
            'avg_cluster_size':           round(conn.execute("SELECT AVG(incident_count) as a FROM incident_clusters").fetchone()['a'] or 0, 1),
            'total_correlated_incidents': conn.execute("SELECT COUNT(*) as c FROM incidents WHERE cluster_id IS NOT NULL").fetchone()['c'],
            'largest_cluster':            conn.execute("SELECT MAX(incident_count) as m FROM incident_clusters").fetchone()['m'] or 0,
            'total_matches_found':        conn.execute("SELECT COUNT(*) as c FROM incidents WHERE similar_incident_id IS NOT NULL").fetchone()['c'],
            'high_confidence':            conn.execute("SELECT COUNT(*) as c FROM incidents WHERE similarity_score >= 0.75").fetchone()['c'],
            'medium_confidence':          conn.execute("SELECT COUNT(*) as c FROM incidents WHERE similarity_score >= 0.50 AND similarity_score < 0.75").fetchone()['c'],
            'solutions_applied':          conn.execute("SELECT COUNT(*) as c FROM incidents WHERE solution_applied_from IS NOT NULL").fetchone()['c'],
            'avg_similarity_score':       round(conn.execute("SELECT AVG(similarity_score) as a FROM incidents WHERE similar_incident_id IS NOT NULL").fetchone()['a'] or 0, 2),
            'total_incidents':            conn.execute("SELECT COUNT(*) as c FROM incidents").fetchone()['c'],
            'open_count':                 conn.execute("SELECT COUNT(*) as c FROM incidents WHERE status='Open'").fetchone()['c'],
            'investigating_count':        conn.execute("SELECT COUNT(*) as c FROM incidents WHERE status='Investigating'").fetchone()['c'],
            'resolved_count':             conn.execute("SELECT COUNT(*) as c FROM incidents WHERE status='Resolved'").fetchone()['c'],
            'closed_count':               conn.execute("SELECT COUNT(*) as c FROM incidents WHERE status='Closed'").fetchone()['c'],
            'avg_resolution_time':        conn.execute("SELECT AVG(resolution_time_minutes) as a FROM incidents WHERE resolution_time_minutes IS NOT NULL").fetchone()['a'] or 0,
            'catastrophic_count':             conn.execute("SELECT COUNT(*) as c FROM incidents WHERE priority='Catastrophic'").fetchone()['c'],
            'major_count':                 conn.execute("SELECT COUNT(*) as c FROM incidents WHERE priority='Major'").fetchone()['c'],
            'moderate_count':               conn.execute("SELECT COUNT(*) as c FROM incidents WHERE priority='Moderate'").fetchone()['c'],
            'minor_count':                  conn.execute("SELECT COUNT(*) as c FROM incidents WHERE priority='Minor'").fetchone()['c'],
        }

        recent_activity = conn.execute(
            "SELECT al.*, u.full_name, u.role FROM activity_logs al JOIN users u ON al.user_id=u.id ORDER BY al.created_at DESC LIMIT 20"
        ).fetchall()
        conn.close()

        return render_template('reports.html',
            metrics=metrics,
            recent_activity=recent_activity,
            active_filters=active_filters,
            filtered_incidents=filtered_incidents,
            active_page='reports')
    except Exception as e:
        import traceback; traceback.print_exc()
        flash('Error loading reports.', 'error')
        return redirect(url_for('dashboard'))

@app.route('/reports/export/incidents')
@login_required
# Generate downloadable CSV export of incident data with optional filters
def export_incidents():
    import csv
    from io import StringIO
    from flask import Response

    status_filter   = request.args.get('status', '').strip()
    severity_filter = request.args.get('severity', '').strip()
    type_filter     = request.args.get('type', '').strip()

    conn = get_db_connection()
    query = """
        SELECT i.incident_id, i.title, i.incident_type, i.priority,
               i.status, i.risk_score, i.affected_asset, i.affected_department,
               u.full_name as assigned_to, i.cluster_id, i.similar_incident_id,
               i.similarity_score, i.reported_date, i.resolved_date,
               i.resolution_time_minutes
        FROM incidents i
        LEFT JOIN users u ON i.assigned_to = u.id
        WHERE 1=1
    """
    params = []
    if status_filter:
        query += " AND i.status = ?"
        params.append(status_filter)
    if severity_filter:
        query += " AND i.priority = ?"
        params.append(severity_filter)
    if type_filter:
        query += " AND i.incident_type = ?"
        params.append(type_filter)
    query += " ORDER BY i.reported_date DESC"

    rows = conn.execute(query, params).fetchall()
    conn.execute("INSERT INTO activity_logs (user_id,action_type,target_type,details) VALUES (?,'UPDATE_INCIDENT','Incidents','Exported incidents report to CSV')",[current_user.id])
    conn.commit()
    conn.close()

    si = StringIO()
    w = csv.writer(si)
    w.writerow(['incident_id','title','incident_type','priority','status',
                'risk_score','affected_asset','affected_department','assigned_to',
                'cluster_id','similar_incident_id','similarity_score',
                'reported_date','resolved_date','resolution_time_minutes'])
    for r in rows:
        w.writerow(list(r))

    parts = ['incidents']
    if status_filter:   parts.append(status_filter)
    if severity_filter: parts.append(severity_filter)
    if type_filter:     parts.append(type_filter.replace(' ', '_'))
    filename = '_'.join(parts) + '_export.csv'

    return Response(si.getvalue(), mimetype='text/csv',
                    headers={'Content-Disposition': f'attachment;filename={filename}'})

@app.route('/reports/export/clusters')
@login_required
# Generate downloadable CSV export of cluster data
def export_clusters():
    import csv
    from io import StringIO
    from flask import Response
    conn = get_db_connection()
    rows = conn.execute("SELECT cluster_id,cluster_name,incident_count,primary_type,severity,status,first_detected,last_updated FROM incident_clusters").fetchall()
    conn.execute("INSERT INTO activity_logs (user_id,action_type,target_type,details) VALUES (?,'UPDATE_INCIDENT','Clusters','Exported clusters report to CSV')",[current_user.id])
    conn.commit()
    conn.close()
    si = StringIO()
    w = csv.writer(si)
    w.writerow(['cluster_id','cluster_name','incident_count','primary_type','severity','status','first_detected','last_updated'])
    for r in rows: w.writerow(list(r))
    return Response(si.getvalue(), mimetype='text/csv', headers={'Content-Disposition':'attachment;filename=clusters_export.csv'})

@app.route('/reports/activity_logs')
@login_required
def activity_logs():
    if current_user.role == 'CIRT':
        flash('Access restricted to CIRT portal.', 'error')
        return redirect(url_for('cirt_incidents'))
    if current_user.role != 'Admin' and not current_user.has_admin_privileges:
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard'))
    try:
        conn = get_db_connection()
        logs = conn.execute(
            "SELECT al.*, u.full_name, u.role FROM activity_logs al JOIN users u ON al.user_id=u.id ORDER BY al.created_at DESC"
        ).fetchall()
        conn.close()
        return render_template('activity.html', logs=logs, active_page='reports')
    except Exception as e:
        import traceback; traceback.print_exc()
        flash('Error loading activity logs.', 'error')
        return redirect(url_for('dashboard'))

@app.route('/reports/export/activity')
@login_required
# Generate downloadable CSV report of user activity logs
def export_activity():
    import csv
    from io import StringIO
    from flask import Response
    conn = get_db_connection()
    rows = conn.execute("SELECT u.full_name,al.action_type,al.target_type,al.target_id,al.details,al.ip_address,al.created_at FROM activity_logs al JOIN users u ON al.user_id=u.id ORDER BY al.created_at DESC").fetchall()
    conn.execute("INSERT INTO activity_logs (user_id,action_type,target_type,details) VALUES (?,'UPDATE_INCIDENT','Activity_Logs','Exported activity logs to CSV')",[current_user.id])
    conn.commit()
    conn.close()
    si = StringIO()
    w = csv.writer(si)
    w.writerow(['user_name','action_type','target_type','target_id','details','ip_address','created_at'])
    for r in rows: w.writerow(list(r))
    return Response(si.getvalue(), mimetype='text/csv', headers={'Content-Disposition':'attachment;filename=activity_export.csv'})

# ─── SETTINGS ──────────────────────────────────

@app.route('/settings/pdf-config', methods=['POST'])
@login_required
def save_pdf_config():
    if current_user.role != 'Admin':
        return jsonify({"success": False, "message": "Access denied"}), 403
    data = request.json
    engineer = data.get('pdf_cybersecurity_engineer', '')
    manager = data.get('pdf_technical_services_manager', '')
    
    conn = get_db_connection()
    # update or insert
    for k, v in [('pdf_cybersecurity_engineer', engineer), ('pdf_technical_services_manager', manager)]:
        row = conn.execute("SELECT setting_key FROM settings WHERE setting_key=?", [k]).fetchone()
        if row:
            conn.execute("UPDATE settings SET setting_value=? WHERE setting_key=?", [v, k])
        else:
            conn.execute("INSERT INTO settings (setting_key, setting_value) VALUES (?, ?)", [k, v])
            
    conn.execute("INSERT INTO activity_logs (user_id, action_type, target_type, details) VALUES (?, 'UPDATE_SETTINGS', 'Settings', 'Updated PDF Configuration')", [current_user.id])
    conn.commit()
    conn.close()
    return jsonify({"success": True})


@app.route('/settings')
@login_required
def settings():
    if current_user.role == 'CIRT':
        flash('Access restricted to CIRT portal.', 'error')
        return redirect(url_for('cirt_incidents'))
    if current_user.role != 'Admin':
        flash('Access denied.','error')
        return redirect(url_for('dashboard'))
    try:
        conn = get_db_connection()
        rows = conn.execute("SELECT * FROM settings").fetchall()
        settings_dict = {r['setting_key']:r['setting_value'] for r in rows}
        system_info = {
            'total_incidents': conn.execute("SELECT COUNT(*) as c FROM incidents").fetchone()['c'],
            'total_users': conn.execute("SELECT COUNT(*) as c FROM users WHERE is_active=1").fetchone()['c'],
            'total_clusters': conn.execute("SELECT COUNT(*) as c FROM incident_clusters").fetchone()['c'],
            'total_alerts': conn.execute("SELECT COUNT(*) as c FROM alerts").fetchone()['c'],
            'total_logs': conn.execute("SELECT COUNT(*) as c FROM activity_logs").fetchone()['c'],
        }
        conn.close()
        return render_template('settings.html',
            settings=settings_dict,
            system_info=system_info,
            active_page='settings')
    except Exception as e:
        import traceback; traceback.print_exc()
        flash('Error loading settings.','error')
        return redirect(url_for('dashboard'))

@app.route('/settings/algorithm', methods=['POST'])
@login_required
# Update thresholds for the correlation and similarity algorithms
def save_algorithm_settings():
    if current_user.role != 'Admin':
        return jsonify({'success':False,'message':'Admin only'})
    try:
        data = request.get_json(silent=True) or request.form
        conn = get_db_connection()
        for key in ['correlation_threshold','correlation_time_window_hours','similarity_threshold','similarity_result_limit']:
            val = data.get(key)
            if val is not None:
                conn.execute("UPDATE settings SET setting_value=?,updated_by=?,updated_at=datetime('now') WHERE setting_key=?",[val,current_user.id,key])
        conn.execute("INSERT INTO activity_logs (user_id,action_type,target_type,details) VALUES (?,'UPDATE_SETTINGS','Settings','Updated algorithm configurations')",[current_user.id])
        conn.commit(); conn.close()
        return jsonify({'success':True,'message':'Algorithm settings saved'})
    except Exception as e:
        return jsonify({'success':False,'message':str(e)})

@app.route('/settings/sla', methods=['POST'])
@login_required
# Update Service Level Agreement timeframes in the system
def save_sla_settings():
    if current_user.role != 'Admin':
        return jsonify({'success':False})
    try:
        data = request.get_json(silent=True) or request.form
        conn = get_db_connection()
        for key in ['critical_sla_hours','high_sla_hours','medium_sla_hours','low_sla_hours']:
            val = data.get(key)
            if val is not None:
                conn.execute("UPDATE settings SET setting_value=?,updated_by=?,updated_at=datetime('now') WHERE setting_key=?",[val,current_user.id,key])
        conn.execute("INSERT INTO activity_logs (user_id,action_type,target_type,details) VALUES (?,'UPDATE_SETTINGS','Settings','Updated SLA timeframes')",[current_user.id])
        conn.commit(); conn.close()
        return jsonify({'success':True})
    except Exception as e:
        return jsonify({'success':False,'message':str(e)})

@app.route('/settings/system', methods=['POST'])
@login_required
# Update core system application preferences
def save_system_settings():
    if current_user.role != 'Admin':
        return jsonify({'success':False})
    try:
        data = request.get_json(silent=True) or request.form
        conn = get_db_connection()
        for key in ['organization_name','incident_id_prefix']:
            val = data.get(key)
            if val is not None:
                conn.execute("INSERT INTO settings (setting_key,setting_value,setting_type) VALUES (?,?,'string') ON CONFLICT(setting_key) DO UPDATE SET setting_value=?,updated_by=?,updated_at=datetime('now')",[key,val,val,current_user.id])
        conn.execute("INSERT INTO activity_logs (user_id,action_type,target_type,details) VALUES (?,'UPDATE_SETTINGS','Settings','Updated core system preferences')",[current_user.id])
        conn.commit(); conn.close()
        return jsonify({'success':True})
    except Exception as e:
        return jsonify({'success':False,'message':str(e)})

@app.route('/settings/reset-defaults', methods=['POST'])
@login_required
# Restore system configurations to their factory defaults
def reset_settings():
    if current_user.role != 'Admin':
        return jsonify({'success':False})
    try:
        conn = get_db_connection()
        defaults = [('correlation_threshold','0.65'),('correlation_time_window_hours','48'),('similarity_threshold','0.50'),('similarity_result_limit','5'),('critical_sla_hours','4'),('high_sla_hours','24'),('medium_sla_hours','72'),('low_sla_hours','168'),('organization_name','CyberIR'),('incident_id_prefix','INC-')]
        for key,val in defaults:
            conn.execute("UPDATE settings SET setting_value=? WHERE setting_key=?",[val,key])
        conn.execute("INSERT INTO activity_logs (user_id,action_type,target_type,details) VALUES (?,'UPDATE_SETTINGS','Settings','Reset system configurations to factory defaults')",[current_user.id])
        conn.commit(); conn.close()
        return jsonify({'success':True})
    except Exception as e:
        return jsonify({'success':False,'message':str(e)})

@app.route('/settings/test-correlation')
@login_required
# Manually trigger the correlation engine test scan
def test_correlation():
    if current_user.role != 'Admin':
        return jsonify({'error':'Admin only'}),403
    try:
        incident_id = request.args.get('incident_id')
        conn = get_db_connection()
        inc = conn.execute("SELECT id FROM incidents WHERE incident_id=?",[incident_id]).fetchone()
        conn.close()
        if not inc: return jsonify({'error':'Not found'}),404
        from correlation_engine import run_correlation
        result = run_correlation(inc['id'])
        return jsonify(result)
    except Exception as e:
        return jsonify({'error':str(e)})

@app.route('/settings/test-similarity')
@login_required
# Manually trigger the similarity engine test scan
def test_similarity():
    if current_user.role != 'Admin':
        return jsonify({'error':'Admin only'}),403
    try:
        incident_id = request.args.get('incident_id')
        conn = get_db_connection()
        inc = conn.execute("SELECT id FROM incidents WHERE incident_id=?",[incident_id]).fetchone()
        conn.close()
        if not inc: return jsonify({'error':'Not found'}),404
        from similarity_engine import run_similarity
        result = run_similarity(inc['id'])
        return jsonify(result)
    except Exception as e:
        return jsonify({'error':str(e)})

# ─── USERS ─────────────────────────────────────

@app.route('/users')
@login_required
# Render the user management interface for administrators
def users():
    if current_user.role == 'CIRT':
        flash('Access restricted to CIRT portal.', 'error')
        return redirect(url_for('cirt_incidents'))
    if current_user.role != 'Admin':
        flash('Access denied.','error')
        return redirect(url_for('dashboard'))
    try:
        conn = get_db_connection()
        users_list = conn.execute("SELECT * FROM users ORDER BY created_at ASC").fetchall()
        conn.close()
        return render_template('users.html',
            users=users_list,
            active_page='users')
    except Exception as e:
        import traceback; traceback.print_exc()
        flash('Error loading users.','error')
        return redirect(url_for('dashboard'))

@app.route('/users/add', methods=['POST'])
@login_required
# Register a new user account into the system
def add_user():
    if current_user.role == 'CIRT':
        flash('Access restricted to CIRT portal.', 'error')
        return redirect(url_for('cirt_incidents'))
    if current_user.role != 'Admin':
        return jsonify({'success':False,'message':'Admin only'})
    try:
        from werkzeug.security import generate_password_hash
        # Accept both JSON (from fetch) and form data
        data = request.get_json(silent=True) or request.form
        full_name = (data.get('full_name') or '').strip()
        email = (data.get('email') or '').strip()
        role = data.get('role') or 'Analyst'
        password = data.get('password') or ''
        phone = data.get('phone_number') or ''
        has_priv = 1 if data.get('has_admin_privileges') in (True, 'true', 'True', '1', 1) else 0
        if not full_name:
            return jsonify({'success':False,'message':'Full name is required'})
        if not email:
            return jsonify({'success':False,'message':'Email is required'})
        if len(password) < 8:
            return jsonify({'success':False,'message':'Password must be at least 8 characters'})
        conn = get_db_connection()
        if conn.execute("SELECT id FROM users WHERE email=?",[email]).fetchone():
            conn.close()
            return jsonify({'success':False,'message':'Email already exists'})
        cursor = conn.execute(
            "INSERT INTO users (full_name,email,password_hash,role,has_admin_privileges,phone_number,is_active,created_by) VALUES (?,?,?,?,?,?,1,?)",
            (full_name,email,generate_password_hash(password),role,has_priv,phone,current_user.id))
        new_id = cursor.lastrowid
        conn.execute("INSERT OR IGNORE INTO user_preferences (user_id) VALUES (?)",[new_id])
        conn.execute("INSERT INTO activity_logs (user_id,action_type,target_type,target_id,details) VALUES (?,'CREATE_USER','User Profile',?,?)",[current_user.id,new_id,f"Created new user: {email} ({role})"])
        conn.commit(); conn.close()
        return jsonify({'success':True,'message':'User created successfully'})
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'success':False,'message':str(e)})

@app.route('/users/edit/<int:user_id>', methods=['POST'])
@login_required
# Update an existing user's profile and roles
def edit_user(user_id):
    if current_user.role != 'Admin':
        return jsonify({'success':False,'message':'Admin only'})
    try:
        from werkzeug.security import generate_password_hash
        # Accept both JSON (from fetch) and form data
        data = request.get_json(silent=True) or request.form
        full_name = (data.get('full_name') or '').strip()
        email = (data.get('email') or '').strip()
        phone = data.get('phone_number') or ''
        role = data.get('role') or 'Analyst'
        has_priv = 1 if data.get('has_admin_privileges') in (True, 'true', 'True', '1', 1) else 0
        password = data.get('password') or ''
        if not full_name:
            return jsonify({'success':False,'message':'Full name is required'})
        conn = get_db_connection()
        old_user = conn.execute("SELECT * FROM users WHERE id=?", [user_id]).fetchone()
        
        # Build differences logic for detailed logging
        changes = []
        if old_user:
            if old_user['full_name'] != full_name: changes.append(f"name to {full_name}")
            if user_id != 1 and old_user['email'] != email: changes.append(f"email to {email}")
            if user_id != 1 and old_user['role'] != role: changes.append(f"role to {role}")
            if bool(old_user['has_admin_privileges']) != bool(has_priv):
                changes.append("granted admin privileges" if has_priv else "revoked admin privileges")
            if password: changes.append("reset password")
            
        # Protect admin email from being changed
        if user_id == 1:
            conn.execute(
                "UPDATE users SET full_name=?,phone_number=?,has_admin_privileges=? WHERE id=?",
                [full_name,phone,has_priv,user_id])
        elif password:
            conn.execute(
                "UPDATE users SET full_name=?,email=?,phone_number=?,role=?,has_admin_privileges=?,password_hash=? WHERE id=?",
                [full_name,email,phone,role,has_priv,generate_password_hash(password),user_id])
        else:
            conn.execute(
                "UPDATE users SET full_name=?,email=?,phone_number=?,role=?,has_admin_privileges=? WHERE id=?",
                [full_name,email,phone,role,has_priv,user_id])
                
        user_display = old_user['full_name'] if old_user else email
        details_text = f"Updated user profile for {user_display}: " + (", ".join(changes) if changes else "modified general profile details")
        conn.execute("INSERT INTO activity_logs (user_id,action_type,target_type,target_id,details) VALUES (?,'UPDATE_USER','User Profile',?,?)",[current_user.id,user_id,details_text])
        conn.commit(); conn.close()
        return jsonify({'success':True,'message':'User updated successfully'})
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'success':False,'message':str(e)})

@app.route('/users/toggle-status/<int:user_id>', methods=['POST'])
@login_required
# Activate or deactivate a user account
def toggle_user_status(user_id):
    if current_user.role != 'Admin': return jsonify({'success':False})
    if user_id == 1 or user_id == current_user.id:
        return jsonify({'success':False,'message':'Cannot deactivate this user'})
    try:
        conn = get_db_connection()
        u = conn.execute("SELECT is_active FROM users WHERE id=?",[user_id]).fetchone()
        new_s = 0 if u['is_active'] else 1
        conn.execute("UPDATE users SET is_active=? WHERE id=?",[new_s,user_id])
        conn.commit(); conn.close()
        return jsonify({'success':True,'status':'active' if new_s else 'inactive'})
    except Exception as e:
        return jsonify({'success':False,'message':str(e)})

@app.route('/users/delete/<int:user_id>', methods=['POST'])
@login_required
# Permanently remove a user account from the system
def delete_user(user_id):
    if current_user.role != 'Admin': return jsonify({'success':False})
    if user_id == 1 or user_id == current_user.id:
        return jsonify({'success':False,'message':'Cannot delete this user'})
    try:
        conn = get_db_connection()
        del_user = conn.execute("SELECT email FROM users WHERE id=?",[user_id]).fetchone()
        email = del_user['email'] if del_user else f"ID {user_id}"
        conn.execute("DELETE FROM user_preferences WHERE user_id=?",[user_id])
        conn.execute("DELETE FROM users WHERE id=?",[user_id])
        conn.execute("INSERT INTO activity_logs (user_id,action_type,target_type,details) VALUES (?,'DELETE_USER','User Profile',?)",[current_user.id,f"Deleted user: {email}"])
        conn.commit(); conn.close()
        return jsonify({'success':True})
    except Exception as e:
        return jsonify({'success':False,'message':str(e)})

# ─── PROFILE ───────────────────────────────────

@app.route('/profile')
@login_required
# Render the logged-in user's profile page
def profile():
    try:
        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE id=?",[current_user.id]).fetchone()
        prefs = conn.execute("SELECT * FROM user_preferences WHERE user_id=?",[current_user.id]).fetchone()
        if not prefs:
            conn.execute("INSERT OR IGNORE INTO user_preferences (user_id) VALUES (?)",[current_user.id])
            conn.commit()
            prefs = conn.execute("SELECT * FROM user_preferences WHERE user_id=?",[current_user.id]).fetchone()
        stats = {
            'incidents_created': conn.execute("SELECT COUNT(*) as c FROM incidents WHERE created_by=?",[current_user.id]).fetchone()['c'],
            'incidents_assigned': conn.execute("SELECT COUNT(*) as c FROM incidents WHERE assigned_to=?",[current_user.id]).fetchone()['c'],
            'incidents_resolved': conn.execute("SELECT COUNT(*) as c FROM incidents WHERE assigned_to=? AND status IN ('Resolved','Closed')",[current_user.id]).fetchone()['c'],
            'alerts_unread': conn.execute("SELECT COUNT(*) as c FROM alerts WHERE (recipient_id=? OR recipient_role=?) AND is_read=0 AND dismissed=0",[current_user.id,current_user.role]).fetchone()['c'],
        }
        recent_activity = conn.execute("SELECT * FROM activity_logs WHERE user_id=? ORDER BY created_at DESC LIMIT 10",[current_user.id]).fetchall()
        conn.close()
        return render_template('profile.html',
            user=user, prefs=prefs, stats=stats,
            recent_activity=recent_activity,
            active_page='profile')
    except Exception as e:
        import traceback; traceback.print_exc()
        flash('Error loading profile.','error')
        return redirect(url_for('dashboard'))

@app.route('/profile/update', methods=['POST'])
@login_required
# Save changes to the logged-in user's personal details
def update_profile():
    try:
        data = request.get_json(silent=True) or request.form
        full_name = data.get('full_name','').strip()
        phone = data.get('phone_number','')
        if not full_name:
            return jsonify({'success':False,'message':'Name required'})
        conn = get_db_connection()
        old = conn.execute("SELECT full_name, phone_number FROM users WHERE id=?",[current_user.id]).fetchone()
        changes = []
        if old and old['full_name'] != full_name: changes.append("name")
        if old and old['phone_number'] != phone: changes.append("phone number")
        
        conn.execute("UPDATE users SET full_name=?,phone_number=? WHERE id=?",[full_name,phone,current_user.id])
        txt = "Updated personal profile: modified " + " and ".join(changes) if changes else "Updated personal profile details"
        conn.execute("INSERT INTO activity_logs (user_id,action_type,target_type,details) VALUES (?,'UPDATE_USER','Profile',?)",[current_user.id,txt])
        conn.commit(); conn.close()
        return jsonify({'success':True,'message':'Profile updated','new_name':full_name})
    except Exception as e:
        return jsonify({'success':False,'message':str(e)})

@app.route('/profile/change-password', methods=['POST'])
@login_required
# Update the logged-in user's authentication password
def change_password():
    try:
        from werkzeug.security import (check_password_hash,
            generate_password_hash)
        data = request.get_json(silent=True) or request.form
        current_pwd = data.get('current_password','')
        new_pwd = data.get('new_password','')
        confirm_pwd = data.get('confirm_password','')
        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE id=?",[current_user.id]).fetchone()
        if not check_password_hash(user['password_hash'],current_pwd):
            conn.close()
            return jsonify({'success':False,'field':'current_password','message':'Current password is incorrect'})
        if len(new_pwd) < 8:
            conn.close()
            return jsonify({'success':False,'field':'new_password','message':'Minimum 8 characters'})
        if new_pwd != confirm_pwd:
            conn.close()
            return jsonify({'success':False,'field':'confirm_password','message':'Passwords do not match'})
        conn.execute("UPDATE users SET password_hash=? WHERE id=?",[generate_password_hash(new_pwd),current_user.id])
        conn.execute("INSERT INTO activity_logs (user_id,action_type,target_type,details) VALUES (?,'UPDATE_USER','Profile','Changed personal account password')",[current_user.id])
        conn.commit(); conn.close()
        return jsonify({'success':True,'message':'Password changed'})
    except Exception as e:
        return jsonify({'success':False,'message':str(e)})

@app.route('/profile/update-preferences', methods=['POST'])
@login_required
# Save the logged-in user's notification preferences
def update_preferences():
    try:
        data = request.get_json(silent=True) or request.form
        conn = get_db_connection()
        conn.execute(
            """INSERT INTO user_preferences 
               (user_id,email_notifications,
                email_critical_alerts,
                email_assignments,
                email_correlation_alerts,
                email_daily_summary,
                in_app_alert_sound,dark_mode,
                items_per_page)
               VALUES (?,?,?,?,?,?,?,?,?)
               ON CONFLICT(user_id) DO UPDATE SET
               email_notifications=excluded.email_notifications,
               email_critical_alerts=excluded.email_critical_alerts,
               email_assignments=excluded.email_assignments,
               email_correlation_alerts=excluded.email_correlation_alerts,
               email_daily_summary=excluded.email_daily_summary,
               in_app_alert_sound=excluded.in_app_alert_sound,
               dark_mode=excluded.dark_mode,
               items_per_page=excluded.items_per_page""",
            [current_user.id,
             int(data.get('email_notifications',1)),
             int(data.get('email_critical_alerts',1)),
             int(data.get('email_assignments',1)),
             int(data.get('email_correlation_alerts',1)),
             int(data.get('email_daily_summary',0)),
             int(data.get('in_app_alert_sound',1)),
             int(data.get('dark_mode',0)),
             int(data.get('items_per_page',25))])
        conn.execute("INSERT INTO activity_logs (user_id,action_type,target_type,details) VALUES (?,'UPDATE_USER','Preferences','Updated notification and interface preferences')",[current_user.id])
        conn.commit(); conn.close()
        return jsonify({'success':True})
    except Exception as e:
        return jsonify({'success':False,'message':str(e)})

@app.route('/profile/update-avatar-color', methods=['POST'])
@login_required
# Change the visual color of the user's avatar icon
def update_avatar_color():
    try:
        data = request.get_json(silent=True) or request.form
        color = data.get('avatar_color','#2563eb')
        conn = get_db_connection()
        try:
            conn.execute("ALTER TABLE users ADD COLUMN avatar_color TEXT DEFAULT '#2563eb'")
            conn.commit()
        except: pass
        conn.execute("UPDATE users SET avatar_color=? WHERE id=?",[color,current_user.id])
        conn.commit(); conn.close()
        return jsonify({'success':True})
    except Exception as e:
        return jsonify({'success':False,'message':str(e)})

# ─── API ROUTES ────────────────────────────────

@app.route('/api/alert-count')
@login_required
# Provide unread alert count via polling endpoint
def api_alert_count():
    try:
        conn = get_db_connection()
        count = conn.execute("SELECT COUNT(*) as c FROM alerts WHERE (recipient_id=? OR recipient_role=?) AND is_read=0 AND dismissed=0",[current_user.id,current_user.role]).fetchone()['c']
        conn.close()
        return jsonify({'count':count})
    except: return jsonify({'count':0})

@app.route('/api/dashboard-stats')
@login_required
# Provide dynamic dashboard metrics via JSON endpoint
def api_dashboard_stats():
    try:
        conn = get_db_connection()
        data = {
            'active_clusters': conn.execute("SELECT COUNT(*) as c FROM incident_clusters WHERE status='Active'").fetchone()['c'],
            'open_incidents': conn.execute("SELECT COUNT(*) as c FROM incidents WHERE status='Open'").fetchone()['c'],
            'critical_incidents': conn.execute("SELECT COUNT(*) as c FROM incidents WHERE priority='Catastrophic' AND status NOT IN ('Resolved','Closed')").fetchone()['c'],
            'total_incidents': conn.execute("SELECT COUNT(*) as c FROM incidents").fetchone()['c'],
            'unread_alerts': conn.execute("SELECT COUNT(*) as c FROM alerts WHERE (recipient_id=? OR recipient_role=?) AND is_read=0 AND dismissed=0",[current_user.id,current_user.role]).fetchone()['c'],
            'total_similarity_matches': conn.execute("SELECT COUNT(*) as c FROM incidents WHERE similar_incident_id IS NOT NULL").fetchone()['c'],
            'solutions_applied': conn.execute("SELECT COUNT(*) as c FROM incidents WHERE solution_applied_from IS NOT NULL").fetchone()['c'],
            'investigating_incidents': conn.execute("SELECT COUNT(*) as c FROM incidents WHERE status='Investigating'").fetchone()['c'],
            'resolved_incidents': conn.execute("SELECT COUNT(*) as c FROM incidents WHERE status IN ('Resolved','Closed')").fetchone()['c'],
        }
        conn.close()
        return jsonify(data)
    except: return jsonify({'active_clusters':0,'open_incidents':0,'critical_incidents':0,'total_incidents':0,'unread_alerts':0})

@app.route('/health')
# Basic application health check endpoint
def health():
    try:
        conn = get_db_connection()
        counts = {
            'users': conn.execute("SELECT COUNT(*) as c FROM users").fetchone()['c'],
            'incidents': conn.execute("SELECT COUNT(*) as c FROM incidents").fetchone()['c'],
            'clusters': conn.execute("SELECT COUNT(*) as c FROM incident_clusters").fetchone()['c'],
            'alerts': conn.execute("SELECT COUNT(*) as c FROM alerts").fetchone()['c'],
        }
        conn.close()
        return jsonify({'status':'healthy','app':'CyberIR','version':'1.0.0','database':'connected','tables':counts})
    except Exception as e:
        return jsonify({'status':'unhealthy','database':'error','error':str(e)})

@app.route('/admin/rerun-algorithms/<incident_id>', methods=['POST'])
@login_required
# Handle logic for rerun_algorithms
def rerun_algorithms(incident_id):
    if current_user.role != 'Admin':
        return jsonify({'success':False}),403
    try:
        conn = get_db_connection()
        inc = conn.execute("SELECT id FROM incidents WHERE incident_id=?",[incident_id]).fetchone()
        conn.close()
        if not inc: return jsonify({'success':False,'message':'Not found'}),404
        from correlation_engine import run_correlation
        from similarity_engine import run_similarity
        corr = run_correlation(inc['id'])
        sim = run_similarity(inc['id'])
        return jsonify({'success':True,'correlation':corr,'similarity':sim})
    except Exception as e:
        return jsonify({'success':False,'message':str(e)})

# ─── ERROR HANDLERS ────────────────────────────

@app.errorhandler(404)
# Handle logic for not_found
def not_found(e):
    if request.is_json:
        return jsonify({'error':'Not found','code':404}),404
    return render_template('errors/404.html'),404

@app.errorhandler(403)
# Handle logic for forbidden
def forbidden(e):
    if request.is_json:
        return jsonify({'error':'Forbidden','code':403}),403
    return render_template('errors/403.html'),403

@app.errorhandler(500)
# Handle logic for server_error
def server_error(e):
    if request.is_json:
        return jsonify({'error':'Internal server error','code':500}),500
    return render_template('errors/500.html'),500

# ─── END OF APP ───────────────────────────────────
