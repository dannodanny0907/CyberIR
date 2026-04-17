import os, re

base_dir = r"c:\Users\PDM\Pictures\CYBER\cyberir"
app_path = os.path.join(base_dir, "backend", "app.py")

with open(app_path, "r", encoding="utf-8") as f:
    app_text = f.read()

# 1. Add /cirt/incidents and /cirt/incidents/export
cirt_routes = """
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

import csv
from io import StringIO
from flask import Response

@app.route('/cirt/incidents/export')
@login_required
def export_cirt_incidents():
    if current_user.role != 'CIRT':
        return redirect(url_for('cirt_incidents'))
        
    conn = get_db_connection()
    incidents = conn.execute("SELECT * FROM incidents WHERE escalated_to_cirt = 1 ORDER BY reported_date DESC").fetchall()
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
"""

if "def cirt_incidents():" not in app_text:
    app_text = app_text.replace("\ndef incidents():", cirt_routes + "\n\n@app.route('/incidents')\n@login_required\ndef incidents():")

# 2. Restrict roles on routes
# We'll prepend `if current_user.role == 'CIRT': flash('Access restricted to CIRT portal.'); return redirect(url_for('cirt_incidents'))` to functions
restrict_logic = """    if current_user.role == 'CIRT':
        flash('Access restricted to CIRT portal.', 'error')
        return redirect(url_for('cirt_incidents'))\n"""

# Functions to restrict: dashboard, incidents, correlation, similarity, reports, settings, users
funcs = ["def dashboard():\n", "def incidents():\n", "def correlation():\n", "def similarity():\n", "def reports():\n", "def settings():\n", "def users():\n", "def add_user():\n"]
for f in funcs:
    if f + restrict_logic not in app_text:
        app_text = app_text.replace(f, f + restrict_logic)


# 3. Restrict editing inside edit_incident()
# "For POST /incidents/edit/<incident_id>: Add this check BEFORE processing the edit"
edit_restrict = """
        conn = get_db_connection()
        incident = conn.execute('SELECT * FROM incidents WHERE incident_id=?', [incident_id]).fetchone()
        conn.close()
        if incident and incident['escalated_to_cirt'] and current_user.role == 'Analyst' and not current_user.has_admin_privileges:
            flash('Escalated incidents can only be edited by Admin or privileged staff.', 'error')
            return redirect(f'/incidents/{incident_id}')
"""
if "Escalated incidents can only be edited by Admin" not in app_text:
    app_text = app_text.replace(
        "    if request.method == 'POST':\n        title",
        "    if request.method == 'POST':" + edit_restrict + "\n        title"
    )

# 4. Restrict delete
delete_restrict = """    if current_user.role == 'CIRT':
        return jsonify({"success": False, "message": "CIRT members cannot delete incidents"}), 403\n"""
if "CIRT members cannot delete incidents" not in app_text:
    app_text = app_text.replace("def delete_incident(incident_id):\n", "def delete_incident(incident_id):\n" + delete_restrict)

with open(app_path, "w", encoding="utf-8") as f:
    f.write(app_text)

print("done")
