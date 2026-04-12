import html as html_module
import logging
from flask import Flask, redirect, url_for, render_template, g, request, jsonify, flash, session
from flask_login import LoginManager, login_required, current_user
from database import init_db, create_default_admin, get_db_connection, get_next_incident_id
from correlation_engine import run_correlation, remove_from_cluster
from similarity_engine import run_similarity, get_cached_similarity
import os
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

app = Flask(__name__)

APP_VERSION = "1.0.0"
APP_NAME = "CyberIR"

# PART 7: SESSION SECURITY
app.secret_key = os.environ.get('SECRET_KEY', 'cyberir-secret-key-change-in-production-2026')
if not app.secret_key or app.secret_key == 'dev':
    app.secret_key = os.urandom(24)

app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=60)
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

logging.basicConfig(level=logging.INFO)

# PART 1: GLOBAL ERROR HANDLING IN app.py
@app.errorhandler(404)
def not_found(e):
    if request.is_json or 'application/json' in request.headers.get('Accept', ''):
        return jsonify({"error": "Not found", "code": 404}), 404
    return render_template('errors/404.html'), 404

@app.errorhandler(403)
def forbidden(e):
    if request.is_json or 'application/json' in request.headers.get('Accept', ''):
        return jsonify({"error": "Forbidden", "code": 403}), 403
    return render_template('errors/403.html'), 403

@app.errorhandler(500)
def server_error(e):
    if request.is_json or 'application/json' in request.headers.get('Accept', ''):
        return jsonify({"error": "Internal server error", "code": 500}), 500
    return render_template('errors/500.html'), 500

@app.before_request
def check_session_timeout():
    if current_user.is_authenticated:
        session.permanent = True
        try:
            timeout_setting = get_db_connection().execute(
                "SELECT setting_value FROM settings WHERE setting_key='session_timeout'"
            ).fetchone()
            if timeout_setting:
                minutes = int(timeout_setting['setting_value'])
                app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=minutes)
        except:
            pass

@app.before_request
def log_request():
    if current_user.is_authenticated:
        app.logger.info(f'{current_user.email} → {request.method} {request.path}')

# PART 6: INPUT SANITIZATION IN app.py
def sanitize_input(value, max_length=None):
    if value is None:
        return None
    value = str(value).strip()
    value = html_module.escape(value)
    if max_length and len(value) > max_length:
        value = value[:max_length]
    return value

def sanitize_int(value, default=0, min_val=None, max_val=None):
    try:
        result = int(value)
        if min_val is not None and result < min_val:
            return min_val
        if max_val is not None and result > max_val:
            return max_val
        return result
    except (ValueError, TypeError):
        return default

def sanitize_float(value, default=0.0, min_val=None, max_val=None):
    try:
        result = float(value)
        if min_val is not None and result < min_val:
            return min_val
        if max_val is not None and result > max_val:
            return max_val
        return result
    except (ValueError, TypeError):
        return default

# Setup Flask-Login
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(app)

from auth import auth, get_user_from_db
app.register_blueprint(auth, url_prefix='')

@login_manager.user_loader
def load_user(user_id):
    return get_user_from_db(user_id)

@app.context_processor
def inject_globals():
    if not current_user.is_authenticated:
        return {'unread_alerts_count': 0, 'active_page': '', 'app_version': APP_VERSION, 'app_name': APP_NAME}
        
    db = get_db_connection()
    count_row = db.execute('''
        SELECT COUNT(*) as count 
        FROM alerts 
        WHERE is_read = 0 AND dismissed = 0 
        AND (recipient_id = ? OR recipient_role = ?)
    ''', (current_user.id, current_user.role)).fetchone()
    
    clusters_row = db.execute("SELECT COUNT(*) as count FROM incident_clusters WHERE status = 'Active'").fetchone()
    sim_count = db.execute("SELECT COUNT(*) as count FROM incidents WHERE similar_incident_id IS NOT NULL").fetchone()
    
    return {
        'unread_alerts_count': count_row['count'] if count_row else 0,
        'active_correlation_clusters': clusters_row['count'] if clusters_row else 0,
        'similarity_matches_count': sim_count['count'] if sim_count else 0,
        'active_page': '',
        'app_version': APP_VERSION,
        'app_name': APP_NAME
    }

def get_request_data():
    if request.is_json:
        return request.get_json()
    return request.form

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('auth.login'))

@app.route('/dashboard')
@login_required
def dashboard():
    try:
        db = get_db_connection()
        
        # Incident stats
        total_incidents = db.execute("SELECT COUNT(*) as c FROM incidents").fetchone()['c']
        open_incidents = db.execute("SELECT COUNT(*) as c FROM incidents WHERE status = 'Open'").fetchone()['c']
        investigating_incidents = db.execute("SELECT COUNT(*) as c FROM incidents WHERE status = 'Investigating'").fetchone()['c']
        resolved_incidents = db.execute("SELECT COUNT(*) as c FROM incidents WHERE status IN ('Resolved','Closed')").fetchone()['c']
        critical_incidents = db.execute("SELECT COUNT(*) as c FROM incidents WHERE priority = 'Critical' AND status NOT IN ('Resolved','Closed')").fetchone()['c']
        
        # Correlation stats
        active_clusters = db.execute("SELECT COUNT(*) as c FROM incident_clusters WHERE status = 'Active'").fetchone()['c']
        total_correlated = db.execute("SELECT COUNT(*) as c FROM incidents WHERE cluster_id IS NOT NULL").fetchone()['c']
        
        # Top 5 highest risk open incidents
        top_incidents = db.execute('''
            SELECT i.incident_id, i.title, i.incident_type, i.risk_score, 
                   i.priority, i.status, i.affected_asset, i.reported_date,
                   u.full_name as assigned_name
            FROM incidents i
            LEFT JOIN users u ON i.assigned_to = u.id
            WHERE i.status IN ('Open','Investigating')
            ORDER BY i.risk_score DESC
            LIMIT 5
        ''').fetchall()
        
        # Recent correlation clusters
        recent_clusters = db.execute('''
            SELECT cluster_id, cluster_name, incident_count, 
                   primary_type, severity, status, first_detected, last_updated
            FROM incident_clusters
            ORDER BY last_updated DESC
            LIMIT 5
        ''').fetchall()
        
        # Recent incidents
        recent_incidents = db.execute('''
            SELECT incident_id, title, incident_type, priority, 
                   status, risk_score, reported_date
            FROM incidents
            ORDER BY reported_date DESC
            LIMIT 5
        ''').fetchall()
        
        # Incidents by status
        inc_by_status = [dict(row) for row in db.execute("SELECT status, COUNT(*) as count FROM incidents GROUP BY status").fetchall()]
        
        # Incidents by type
        inc_by_type = [dict(row) for row in db.execute("SELECT incident_type, COUNT(*) as count FROM incidents GROUP BY incident_type ORDER BY count DESC").fetchall()]
        
        # Incidents by priority
        inc_by_priority = [dict(row) for row in db.execute("SELECT priority, COUNT(*) as count FROM incidents GROUP BY priority").fetchall()]
        
        # Daily trend 14 days
        daily_trend = [dict(row) for row in db.execute('''
            SELECT DATE(reported_date) as date, COUNT(*) as count
            FROM incidents
            WHERE reported_date >= DATE('now', '-14 days')
            GROUP BY DATE(reported_date)
            ORDER BY date ASC
        ''').fetchall()]

        # Phase 4: Similarity Stats
        total_similarity_matches = db.execute("SELECT COUNT(*) as c FROM incidents WHERE similar_incident_id IS NOT NULL").fetchone()['c']
        high_confidence_matches = db.execute("SELECT COUNT(*) as c FROM incidents WHERE similarity_score >= 0.75").fetchone()['c']
        solutions_applied_count = db.execute("SELECT COUNT(*) as c FROM incidents WHERE solution_applied_from IS NOT NULL").fetchone()['c']
        
        recent_similarity_matches = db.execute('''
            SELECT 
                i.incident_id,
                i.title,
                i.incident_type,
                i.priority,
                i.status,
                i.similarity_score,
                i.similar_incident_id,
                i.solution_applied_from,
                si.title as matched_title
            FROM incidents i
            LEFT JOIN incidents si ON i.similar_incident_id = si.incident_id
            WHERE i.similar_incident_id IS NOT NULL
            ORDER BY i.reported_date DESC
            LIMIT 5
        ''').fetchall()

        resolution_by_type = db.execute('''
            SELECT incident_type,
                   ROUND(AVG(resolution_time_minutes) / 60.0, 1) as avg_hours
            FROM incidents
            WHERE resolution_time_minutes IS NOT NULL
            AND status IN ('Resolved', 'Closed')
            GROUP BY incident_type
            ORDER BY avg_hours DESC
        ''').fetchall()

        today_count = db.execute('''
            SELECT COUNT(*) as c FROM incidents
            WHERE DATE(reported_date) = DATE('now')
        ''').fetchone()['c']

        return render_template('dashboard.html', 
            active_page='dashboard',
            today_count=today_count,
            resolution_by_type=[dict(row) for row in resolution_by_type],
            total_incidents=total_incidents,
            open_incidents=open_incidents,
            investigating_incidents=investigating_incidents,
            resolved_incidents=resolved_incidents,
            critical_incidents=critical_incidents,
            active_clusters=active_clusters,
            total_correlated=total_correlated,
            top_incidents=[dict(row) for row in top_incidents],
            recent_clusters=[dict(row) for row in recent_clusters],
            recent_incidents=[dict(row) for row in recent_incidents],
            incidents_by_status=inc_by_status,
            incidents_by_type=inc_by_type,
            incidents_by_priority=inc_by_priority,
            daily_trend=daily_trend,
            total_similarity_matches=total_similarity_matches,
            high_confidence_matches=high_confidence_matches,
            solutions_applied=solutions_applied_count,
            recent_similarity_matches=[dict(row) for row in recent_similarity_matches]
        )

    except Exception as e:
        app.logger.error(f'Error in dashboard: {str(e)}')
        if request.is_json:
            return jsonify({'success': False, 'message': 'An error occurred'}), 500
        flash('An error occurred. Please try again.', 'error')
        return redirect(url_for('dashboard'))
@app.route('/users')
@login_required
def users():
    if current_user.role != 'Admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
        
    db = get_db_connection()
    users_list = db.execute('SELECT * FROM users ORDER BY created_at ASC').fetchall()
    return render_template('users.html', active_page='users', users=users_list)

@app.route('/users/add', methods=['POST'])
@login_required
def add_user():
    if current_user.role != 'Admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
    data = request.json
    full_name = data.get('full_name')
    email = data.get('email')
    phone_number = data.get('phone_number', '')
    role = data.get('role')
    password = data.get('password')
    confirm_password = data.get('confirm_password')
    has_admin_privileges = data.get('has_admin_privileges', False)
    
    if not all([full_name, email, role, password]):
        return jsonify({'success': False, 'message': 'Please fill all required fields.'})
        
    if role not in ['Analyst', 'Viewer']:
        return jsonify({'success': False, 'message': 'Invalid role.'})
        
    if role != 'Analyst':
        has_admin_privileges = False
        
    if password != confirm_password:
        return jsonify({'success': False, 'message': 'Passwords do not match.'})
        
    if len(password) < 8:
        return jsonify({'success': False, 'message': 'Password must be at least 8 characters.'})
        
    db = get_db_connection()
    
    # Check email uniqueness
    existing = db.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone()
    if existing:
        return jsonify({'success': False, 'message': 'Email already exists.'})
        
    password_hash = generate_password_hash(password)
    
    cursor = db.cursor()
    cursor.execute('''
        INSERT INTO users (full_name, email, phone_number, password_hash, role, has_admin_privileges, created_by)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (full_name, email, phone_number, password_hash, role, has_admin_privileges, current_user.id))
    
    new_user_id = cursor.lastrowid
    
    # Insert user_preferences
    cursor.execute('INSERT INTO user_preferences (user_id) VALUES (?)', (new_user_id,))
    
    # Log activity
    ip_addr = request.remote_addr
    cursor.execute('''
        INSERT INTO activity_logs (user_id, action_type, target_type, target_id, details, ip_address)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (current_user.id, 'CREATE_USER', 'users', new_user_id, f'Created user {email}', ip_addr))
    
    db.commit()
    return jsonify({'success': True, 'message': 'User created successfully'})

@app.route('/users/edit/<int:user_id>', methods=['POST'])
@login_required
def edit_user(user_id):
    if current_user.role != 'Admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
    data = request.json
    full_name = data.get('full_name')
    email = data.get('email')
    phone_number = data.get('phone_number', '')
    role = data.get('role')
    password = data.get('password')
    has_admin_privileges = data.get('has_admin_privileges', False)
    
    db = get_db_connection()
    user_to_edit = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    if not user_to_edit:
        return jsonify({'success': False, 'message': 'User not found.'})
        
    # Protection for System Administrator
    if user_id == 1:
        role = user_to_edit['role']
        email = user_to_edit['email']
        
    if role != 'Analyst':
        has_admin_privileges = False
        
    if email != user_to_edit['email']:
        existing = db.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone()
        if existing:
            return jsonify({'success': False, 'message': 'Email already exists.'})
            
    cursor = db.cursor()
    
    if password:
        if len(password) < 8:
            return jsonify({'success': False, 'message': 'Password must be at least 8 characters.'})
        password_hash = generate_password_hash(password)
        cursor.execute('''
            UPDATE users SET full_name=?, email=?, phone_number=?, role=?, has_admin_privileges=?, password_hash=?, updated_by=?
            WHERE id=?
        ''', (full_name, email, phone_number, role, has_admin_privileges, password_hash, current_user.id, user_id))
    else:
        cursor.execute('''
            UPDATE users SET full_name=?, email=?, phone_number=?, role=?, has_admin_privileges=?, updated_by=?
            WHERE id=?
        ''', (full_name, email, phone_number, role, has_admin_privileges, current_user.id, user_id))
        
    cursor.execute('''
        INSERT INTO activity_logs (user_id, action_type, target_type, target_id, details, ip_address)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (current_user.id, 'UPDATE_USER', 'users', user_id, f'Updated user {user_id}', request.remote_addr))
    
    db.commit()
    return jsonify({'success': True})

@app.route('/users/toggle-status/<int:user_id>', methods=['POST'])
@login_required
def toggle_user_status(user_id):
    if current_user.role != 'Admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
    if user_id == 1:
        return jsonify({'success': False, 'message': 'Cannot deactivate System Administrator.'})
        
    if user_id == current_user.id:
        return jsonify({'success': False, 'message': 'Cannot deactivate yourself.'})
        
    db = get_db_connection()
    user = db.execute('SELECT is_active FROM users WHERE id = ?', (user_id,)).fetchone()
    if not user:
        return jsonify({'success': False, 'message': 'User not found.'})
        
    new_status = 0 if user['is_active'] else 1
    
    cursor = db.cursor()
    cursor.execute('UPDATE users SET is_active = ? WHERE id = ?', (new_status, user_id))
    cursor.execute('''
        INSERT INTO activity_logs (user_id, action_type, target_type, target_id, details, ip_address)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (current_user.id, 'UPDATE_USER', 'users', user_id, f'Toggled user {user_id} status', request.remote_addr))
    
    db.commit()
    return jsonify({'success': True, 'status': 'active' if new_status else 'inactive'})

@app.route('/users/delete/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if current_user.role != 'Admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
    if user_id == 1:
        return jsonify({'success': False, 'message': 'Cannot delete System Administrator.'})
        
    if user_id == current_user.id:
        return jsonify({'success': False, 'message': 'Cannot delete yourself.'})
        
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute('DELETE FROM user_preferences WHERE user_id = ?', (user_id,))
    cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
    
    cursor.execute('''
        INSERT INTO activity_logs (user_id, action_type, target_type, target_id, details, ip_address)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (current_user.id, 'DELETE_USER', 'users', user_id, f'Deleted user {user_id}', request.remote_addr))
    
    db.commit()
    return jsonify({'success': True})

@app.route('/incidents/log', methods=['GET', 'POST'])
@login_required
def log_incident():
    if current_user.role not in ['Admin', 'Analyst']:
        flash('You do not have permission to log incidents', 'error')
        return redirect('/incidents')
        
    db = get_db_connection()
    if request.method == 'GET':
        analysts = db.execute("SELECT * FROM users WHERE role IN ('Admin', 'Analyst') AND is_active = 1").fetchall()
        return render_template('log_incident.html', active_page='incidents', analysts=analysts)
        
    if request.method == 'POST':
        title = sanitize_input(request.form.get('title'), 200)
        incident_type = request.form.get('incident_type')
        description = sanitize_input(request.form.get('description'), 2000)
        reported_date = request.form.get('reported_date') or datetime.utcnow().strftime('%Y-%m-%dT%H:%M')
        
        # Format for sqlite standard
        reported_date = reported_date.replace('T', ' ')
        
        affected_asset = sanitize_input(request.form.get('affected_asset'), 200)
        affected_department = sanitize_input(request.form.get('affected_department'), 100)
        users_affected = sanitize_int(request.form.get('users_affected'), 0, 0)
        ip_address = sanitize_input(request.form.get('ip_address'), 50)
        attack_indicators = sanitize_input(request.form.get('attack_indicators'), 500)
        
        asset_criticality = sanitize_int(request.form.get('asset_criticality'), 1, 1, 5)
        threat_severity = sanitize_int(request.form.get('threat_severity'), 1, 1, 5)
        vulnerability_exposure = sanitize_int(request.form.get('vulnerability_exposure'), 1, 1, 5)
        is_repeat = 1 if request.form.get('is_repeat') else 0
        
        assigned_to = request.form.get('assigned_to')
        assigned_to = int(assigned_to) if assigned_to else None
        resolution_notes = request.form.get('initial_notes')
        
        if users_affected == 0: u_score = 1
        elif users_affected <= 5: u_score = 2
        elif users_affected <= 20: u_score = 3
        elif users_affected <= 100: u_score = 4
        else: u_score = 5
        
        repeat_penalty = 5 if is_repeat else 1
        
        raw_score = (
            asset_criticality * 0.30 +
            threat_severity * 0.30 +
            vulnerability_exposure * 0.15 +
            u_score * 0.20 +
            repeat_penalty * 0.05
        )
        risk_score = round((raw_score / 5.0) * 100, 2)
        
        if risk_score >= 75: priority = 'Critical'
        elif risk_score >= 50: priority = 'High'
        elif risk_score >= 25: priority = 'Medium'
        else: priority = 'Low'
        
        incident_id = get_next_incident_id()
        status = 'Open'
        
        cursor = db.cursor()
        cursor.execute('''
            INSERT INTO incidents (
                incident_id, title, description, incident_type, affected_asset,
                affected_department, users_affected, asset_criticality, threat_severity,
                vulnerability_exposure, is_repeat, risk_score, priority, status,
                assigned_to, attack_indicators, ip_address, reported_date, resolution_notes,
                created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            incident_id, title, description, incident_type, affected_asset,
            affected_department, users_affected, asset_criticality, threat_severity,
            vulnerability_exposure, is_repeat, risk_score, priority, status,
            assigned_to, attack_indicators, ip_address, reported_date, resolution_notes,
            current_user.id
        ))
        
        new_inc_id = cursor.lastrowid
        cursor.execute('''
            INSERT INTO activity_logs (user_id, action_type, target_type, target_id, details, ip_address)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (current_user.id, 'CREATE_INCIDENT', 'incidents', new_inc_id, f'Created incident {incident_id}', request.remote_addr))
        
        db.commit()
        
        create_high_priority_alert(new_inc_id, incident_id, priority)
        create_assignment_alert(new_inc_id, incident_id, assigned_to, current_user.full_name)
        
        try:
            correlation_result = run_correlation(new_inc_id)
            if correlation_result['clustered']:
                flash(f"Incident grouped into cluster {correlation_result['cluster_id']}", 'info')
        except Exception as e:
            pass  # Don't fail incident logging if correlation fails
            
        try:
            similarity_result = run_similarity(new_inc_id)
            if (similarity_result['found'] and 
                similarity_result['matches'] and
                similarity_result['matches'][0]['score'] >= 0.75):
                flash(
                    f"Similar incident found: "
                    f"{similarity_result['matches'][0]['incident_id']} "
                    f"({similarity_result['matches'][0]['score_percent']}"
                    f"% match)", 'info')
        except Exception as e:
            pass  # Don't fail incident logging if similarity fails
        
        flash(f'Incident {incident_id} logged successfully', 'success')
        return redirect('/incidents')

@app.route('/incidents')
@login_required
def incidents():
    try:
        status = request.args.get('status', '')
        priority = request.args.get('priority', '')
        incident_type = request.args.get('incident_type', '')
        assigned_to = request.args.get('assigned_to', '')
        search = request.args.get('search', '')
        sort = request.args.get('sort', 'reported_date')
        order = request.args.get('order', 'desc').lower()
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 25))
        
        if order not in ['asc', 'desc']: order = 'desc'
        valid_sorts = ['incident_id', 'title', 'incident_type', 'priority', 'status', 'risk_score', 'affected_asset', 'reported_date']
        if sort not in valid_sorts: sort = 'reported_date'
        
        where_clauses = []
        params = []
        
        if status and status != 'All Statuses':
            if status == 'Resolved,Closed':
                where_clauses.append("status IN ('Resolved', 'Closed')")
            else:
                where_clauses.append("status = ?")
                params.append(status)
                
        if priority and priority != 'All Priorities':
            where_clauses.append("priority = ?")
            params.append(priority)
            
        if incident_type and incident_type != 'All Types':
            where_clauses.append("incident_type = ?")
            params.append(incident_type)
            
        if assigned_to and assigned_to != 'Anyone':
            if assigned_to == 'Unassigned':
                where_clauses.append("assigned_to IS NULL")
            else:
                where_clauses.append("assigned_to = ?")
                params.append(assigned_to)
                
        if search:
            where_clauses.append("(title LIKE ? OR incident_id LIKE ? OR affected_asset LIKE ?)")
            params.extend([f'%{search}%', f'%{search}%', f'%{search}%'])
            
        where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        
        offset = (page - 1) * per_page
        
        db = get_db_connection()
        
        query = f"""
            SELECT i.*, u.full_name as assigned_name 
            FROM incidents i 
            LEFT JOIN users u ON i.assigned_to = u.id 
            {where_sql} 
            ORDER BY i.{sort} {order} 
            LIMIT ? OFFSET ?
        """
        
        total_query = f"SELECT COUNT(*) as count FROM incidents i {where_sql}"
        total_count = db.execute(total_query, params).fetchone()['count']
        
        inc_params = params + [per_page, offset]
        incidents_list = db.execute(query, inc_params).fetchall()
        
        all_count = db.execute("SELECT COUNT(*) as count FROM incidents").fetchone()['count']
        open_count = db.execute("SELECT COUNT(*) as count FROM incidents WHERE status='Open'").fetchone()['count']
        inv_count = db.execute("SELECT COUNT(*) as count FROM incidents WHERE status='Investigating'").fetchone()['count']
        res_count = db.execute("SELECT COUNT(*) as count FROM incidents WHERE status IN ('Resolved', 'Closed')").fetchone()['count']
        
        analysts = db.execute("SELECT id, full_name FROM users WHERE role IN ('Admin', 'Analyst') AND is_active = 1").fetchall()
        
        return render_template('incidents.html', 
            active_page='incidents', 
            incidents=incidents_list,
            total_count=total_count,
            stats={'total': all_count, 'open': open_count, 'investigating': inv_count, 'resolved': res_count},
            analysts=analysts,
            page=page, per_page=per_page, sort=sort, order=order,
            active_filters=len(where_clauses)
        )

    except Exception as e:
        app.logger.error(f'Error in incidents: {str(e)}')
        if request.is_json:
            return jsonify({'success': False, 'message': 'An error occurred'}), 500
        flash('An error occurred. Please try again.', 'error')
        return redirect(url_for('dashboard'))
@app.route('/incidents/<incident_id_str>')
@login_required
def incident_detail(incident_id_str):
    db = get_db_connection()
    incident = db.execute('''
        SELECT i.*, 
               u1.full_name as assigned_name, u1.role as assigned_role,
               u2.full_name as created_name,
               u3.full_name as resolved_by_name
        FROM incidents i
        LEFT JOIN users u1 ON i.assigned_to = u1.id
        LEFT JOIN users u2 ON i.created_by = u2.id
        LEFT JOIN users u3 ON i.updated_by = u3.id
        WHERE i.incident_id = ?
    ''', (incident_id_str,)).fetchone()
    
    if not incident:
        flash('Incident not found', 'error')
        return redirect('/incidents')
        
    activities = db.execute('''
        SELECT a.*, u.full_name as user_name 
        FROM activity_logs a
        LEFT JOIN users u ON a.user_id = u.id
        WHERE a.target_type = 'incidents' AND a.target_id = ?
        ORDER BY a.created_at DESC
    ''', (incident['id'],)).fetchall()
    
    alerts = db.execute('SELECT * FROM alerts WHERE incident_id = ?', (incident['id'],)).fetchall()
    analysts = db.execute("SELECT id, full_name FROM users WHERE role IN ('Admin', 'Analyst') AND is_active = 1").fetchall()
    
    other_incidents_in_cluster = []
    if incident['cluster_id']:
        other_incidents_in_cluster = db.execute('''
            SELECT incident_id 
            FROM incidents 
            WHERE cluster_id = ? AND id != ?
            ORDER BY reported_date DESC
            LIMIT 4
        ''', (incident['cluster_id'], incident['id'])).fetchall()
    
    incident_data = dict(incident)
    incident_data['risk_score'] = incident['risk_score'] or 0
    incident_data['asset_criticality'] = incident['asset_criticality'] or 0
    incident_data['threat_severity'] = incident['threat_severity'] or 0
    incident_data['vulnerability_exposure'] = incident['vulnerability_exposure'] or 0
    incident_data['users_affected'] = incident['users_affected'] or 0
    incident_data['resolution_time_minutes'] = incident['resolution_time_minutes'] or 0
    incident_data['correlation_score'] = incident['correlation_score'] or 0
    incident_data['similarity_score'] = incident['similarity_score'] or 0
    incident_data['is_repeat'] = incident['is_repeat'] or 0

    return render_template('incident_detail.html', 
        active_page='incidents', 
        incident=incident_data, 
        activities=activities, 
        alerts=alerts,
        analysts=analysts,
        other_incidents_in_cluster=[dict(r) for r in other_incidents_in_cluster]
    )

@app.route('/incidents/assign/<incident_id_str>', methods=['POST'])
@login_required
def assign_incident(incident_id_str):
    if current_user.role not in ['Admin', 'Analyst']:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
    assigned_to = request.form.get('assigned_to')
    assigned_to = int(assigned_to) if assigned_to else None
    
    db = get_db_connection()
    incident = db.execute('SELECT id FROM incidents WHERE incident_id = ?', (incident_id_str,)).fetchone()
    if not incident: return jsonify({'success': False, 'message': 'Incident not found'})
    
    db.execute('UPDATE incidents SET assigned_to = ?, updated_at = CURRENT_TIMESTAMP, updated_by = ? WHERE incident_id = ?', 
               (assigned_to, current_user.id, incident_id_str))
               
    assigned_name = "Unassigned"
    if assigned_to:
        u = db.execute('SELECT full_name FROM users WHERE id = ?', (assigned_to,)).fetchone()
        assigned_name = u['full_name'] if u else "Unknown"
        
    db.execute('''
        INSERT INTO activity_logs (user_id, action_type, target_type, target_id, details, ip_address)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (current_user.id, 'ASSIGN_INCIDENT', 'incidents', incident['id'], f'Assigned to {assigned_name}', request.remote_addr))
    
    db.commit()
    
    create_assignment_alert(incident['id'], incident_id_str, assigned_to, current_user.full_name)
    
    return jsonify({'success': True, 'assigned_name': assigned_name})

@app.route('/incidents/update-status/<incident_id_str>', methods=['POST'])
@login_required
def update_status(incident_id_str):
    if current_user.role not in ['Admin', 'Analyst']:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
    new_status = request.form.get('new_status')
    if new_status not in ['Open', 'Investigating', 'Resolved', 'Closed']:
        return jsonify({'success': False, 'message': 'Invalid status'})
        
    db = get_db_connection()
    incident = db.execute('SELECT id, status FROM incidents WHERE incident_id = ?', (incident_id_str,)).fetchone()
    if not incident: return jsonify({'success': False, 'message': 'Incident not found'})
    
    query = 'UPDATE incidents SET status = ?, updated_at = CURRENT_TIMESTAMP, updated_by = ?'
    params = [new_status, current_user.id]
    
    if new_status == 'Investigating' and incident['status'] != 'Investigating':
        query += ', investigating_started_date = CURRENT_TIMESTAMP'
    elif new_status == 'Closed':
        query += ', closed_date = CURRENT_TIMESTAMP'
        
    query += ' WHERE incident_id = ?'
    params.append(incident_id_str)
    
    db.execute(query, params)
    
    db.execute('''
        INSERT INTO activity_logs (user_id, action_type, target_type, target_id, details, ip_address)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (current_user.id, 'UPDATE_INCIDENT', 'incidents', incident['id'], f'Status changed to {new_status}', request.remote_addr))
    
    db.commit()
    return jsonify({'success': True})

@app.route('/incidents/resolve/<incident_id_str>', methods=['POST'])
@login_required
def resolve_incident(incident_id_str):
    if current_user.role not in ['Admin', 'Analyst']:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
    resolution_notes = request.form.get('resolution_notes')
    if not resolution_notes:
        return jsonify({'success': False, 'message': 'Resolution notes are required'})
        
    db = get_db_connection()
    incident = db.execute('SELECT id, reported_date FROM incidents WHERE incident_id = ?', (incident_id_str,)).fetchone()
    if not incident: return jsonify({'success': False, 'message': 'Incident not found'})
    
    now = datetime.utcnow()
    fmt = '%Y-%m-%d %H:%M:%S'
    reports = str(incident['reported_date'])
    try:
        rep_date = datetime.strptime(reports.replace('T', ' ')[:19], fmt)
        mins = int((now - rep_date).total_seconds() / 60)
    except Exception:
        mins = 0
        
    db.execute('''
        UPDATE incidents 
        SET status = 'Resolved', resolved_date = CURRENT_TIMESTAMP, 
            resolution_notes = ?, resolution_time_minutes = ?,
            updated_at = CURRENT_TIMESTAMP, updated_by = ?
        WHERE incident_id = ?
    ''', (resolution_notes, mins, current_user.id, incident_id_str))
    
    db.execute('''
        INSERT INTO activity_logs (user_id, action_type, target_type, target_id, details, ip_address)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (current_user.id, 'RESOLVE_INCIDENT', 'incidents', incident['id'], 'Incident marked as Resolved', request.remote_addr))
    
    db.commit()
    return jsonify({'success': True})

@app.route('/incidents/edit/<incident_id_str>', methods=['GET', 'POST'])
@login_required
def edit_incident(incident_id_str):
    if current_user.role not in ['Admin', 'Analyst']:
        flash('You do not have permission to edit incidents', 'error')
        return redirect('/incidents')
        
    db = get_db_connection()
    incident = db.execute('SELECT * FROM incidents WHERE incident_id = ?', (incident_id_str,)).fetchone()
    
    if not incident:
        flash('Incident not found', 'error')
        return redirect('/incidents')
        
    if incident['status'] == 'Closed':
        flash('Closed incidents cannot be edited', 'error')
        return redirect(f'/incidents/{incident_id_str}')
        
    if request.method == 'GET':
        analysts = db.execute("SELECT * FROM users WHERE role IN ('Admin', 'Analyst') AND is_active = 1").fetchall()
        return render_template('edit_incident.html', active_page='incidents', incident=incident, analysts=analysts)
        
    if request.method == 'POST':
        title = sanitize_input(request.form.get('title'), 200)
        incident_type = request.form.get('incident_type')
        description = sanitize_input(request.form.get('description'), 2000)
        reported_date = request.form.get('reported_date') 
        reported_date = reported_date.replace('T', ' ') if reported_date else incident['reported_date']
        
        affected_asset = sanitize_input(request.form.get('affected_asset'), 200)
        affected_department = sanitize_input(request.form.get('affected_department'), 100)
        users_affected = sanitize_int(request.form.get('users_affected'), 0, 0)
        ip_address = sanitize_input(request.form.get('ip_address'), 50)
        attack_indicators = sanitize_input(request.form.get('attack_indicators'), 500)
        
        asset_criticality = sanitize_int(request.form.get('asset_criticality'), 1, 1, 5)
        threat_severity = sanitize_int(request.form.get('threat_severity'), 1, 1, 5)
        vulnerability_exposure = sanitize_int(request.form.get('vulnerability_exposure'), 1, 1, 5)
        is_repeat = 1 if request.form.get('is_repeat') else 0
        
        assigned_to = request.form.get('assigned_to')
        assigned_to = int(assigned_to) if assigned_to else None
        
        if users_affected == 0: u_score = 1
        elif users_affected <= 5: u_score = 2
        elif users_affected <= 20: u_score = 3
        elif users_affected <= 100: u_score = 4
        else: u_score = 5
        
        repeat_penalty = 5 if is_repeat else 1
        
        raw_score = (
            asset_criticality * 0.30 +
            threat_severity * 0.30 +
            vulnerability_exposure * 0.15 +
            u_score * 0.20 +
            repeat_penalty * 0.05
        )
        risk_score = round((raw_score / 5.0) * 100, 2)
        
        if risk_score >= 75: priority = 'Critical'
        elif risk_score >= 50: priority = 'High'
        elif risk_score >= 25: priority = 'Medium'
        else: priority = 'Low'
        
        cursor = db.cursor()
        cursor.execute('''
            UPDATE incidents SET 
                title=?, description=?, incident_type=?, affected_asset=?,
                affected_department=?, users_affected=?, ip_address=?,
                attack_indicators=?, asset_criticality=?, threat_severity=?,
                vulnerability_exposure=?, is_repeat=?, risk_score=?, priority=?,
                assigned_to=?, reported_date=?, updated_at=CURRENT_TIMESTAMP, updated_by=?
            WHERE id=?
        ''', (
            title, description, incident_type, affected_asset,
            affected_department, users_affected, ip_address,
            attack_indicators, asset_criticality, threat_severity,
            vulnerability_exposure, is_repeat, risk_score, priority,
            assigned_to, reported_date, current_user.id, incident['id']
        ))
        
        cursor.execute('''
            INSERT INTO activity_logs (user_id, action_type, target_type, target_id, details, ip_address)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (current_user.id, 'UPDATE_INCIDENT', 'incidents', incident['id'], f'Incident edited by {current_user.full_name}', request.remote_addr))
        
        db.commit()
        
        flash(f'Incident {incident_id_str} updated successfully', 'success')
        return redirect(f'/incidents/{incident_id_str}')

@app.route('/incidents/delete/<incident_id_str>', methods=['POST'])
@login_required
def delete_incident(incident_id_str):
    if current_user.role != 'Admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
    db = get_db_connection()
    incident = db.execute('SELECT id, cluster_id FROM incidents WHERE incident_id = ?', (incident_id_str,)).fetchone()
    
    if not incident:
        return jsonify({'success': False, 'message': 'Incident not found'})
        
    if incident['cluster_id'] is not None:
        return jsonify({'success': False, 'message': 'Cannot delete a correlated incident. Remove from cluster first.'})
        
    cursor = db.cursor()
    cursor.execute('DELETE FROM alerts WHERE incident_id = ?', (incident['id'],))
    cursor.execute('DELETE FROM incidents WHERE id = ?', (incident['id'],))
    
    cursor.execute('''
        INSERT INTO activity_logs (user_id, action_type, target_type, target_id, details, ip_address)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (current_user.id, 'DELETE_INCIDENT', 'incidents', incident['id'], f'Deleted incident {incident_id_str}', request.remote_addr))
    
    db.commit()
    return jsonify({'success': True, 'redirect': '/incidents'})

@app.route('/incidents/remove-from-cluster/<incident_id_str>', methods=['POST'])
@login_required
def remove_incident_from_cluster(incident_id_str):
    if current_user.role != 'Admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
    db = get_db_connection()
    inc = db.execute('SELECT id FROM incidents WHERE incident_id = ?', (incident_id_str,)).fetchone()
    if not inc:
        return jsonify({'success': False, 'message': 'Incident not found'})
        
    result = remove_from_cluster(inc['id'])
    return jsonify(result)


@app.route('/correlation')
@login_required
def correlation():
    try:
        status = request.args.get('status', '')
        severity = request.args.get('severity', '')
        cluster_type = request.args.get('type', '')
        search = request.args.get('search', '')
        
        where_clauses = []
        params = []
        
        if status and status != 'All Statuses':
            where_clauses.append("status = ?")
            params.append(status)
        if severity and severity != 'All Severities':
            where_clauses.append("severity = ?")
            params.append(severity)
        if cluster_type and cluster_type != 'All Types':
            where_clauses.append("primary_type = ?")
            params.append(cluster_type)
        if search:
            where_clauses.append("(cluster_id LIKE ? OR cluster_name LIKE ?)")
            params.extend([f'%{search}%', f'%{search}%'])
            
        where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        
        db = get_db_connection()
        
        query = f"""
            SELECT c.*, u.full_name as assigned_name 
            FROM incident_clusters c
            LEFT JOIN users u ON c.assigned_to = u.id
            {where_sql}
            ORDER BY c.last_updated DESC
        """
        clusters = [dict(row) for row in db.execute(query, params).fetchall()]
        
        for c in clusters:
            c['incidents'] = db.execute('SELECT * FROM incidents WHERE cluster_id = ? ORDER BY reported_date DESC', (c['cluster_id'],)).fetchall()
            
        stats = {}
        stats['total_clusters'] = db.execute("SELECT COUNT(*) as c FROM incident_clusters").fetchone()['c']
        stats['active_clusters'] = db.execute("SELECT COUNT(*) as c FROM incident_clusters WHERE status = 'Active'").fetchone()['c']
        stats['investigating_clusters'] = db.execute("SELECT COUNT(*) as c FROM incident_clusters WHERE status = 'Investigating'").fetchone()['c']
        stats['resolved_clusters'] = db.execute("SELECT COUNT(*) as c FROM incident_clusters WHERE status = 'Resolved'").fetchone()['c']
        stats['total_correlated_incidents'] = db.execute("SELECT COUNT(*) as c FROM incidents WHERE cluster_id IS NOT NULL").fetchone()['c']
        
        return render_template('correlation.html', 
            active_page='correlation', 
            clusters=clusters,
            stats=stats
        )

    except Exception as e:
        app.logger.error(f'Error in correlation: {str(e)}')
        if request.is_json:
            return jsonify({'success': False, 'message': 'An error occurred'}), 500
        flash('An error occurred. Please try again.', 'error')
        return redirect(url_for('dashboard'))
@app.route('/correlation/<cluster_id_str>')
@login_required
def correlation_detail(cluster_id_str):
    db = get_db_connection()
    cluster = db.execute('''
        SELECT c.*, u.full_name as assigned_name 
        FROM incident_clusters c
        LEFT JOIN users u ON c.assigned_to = u.id
        WHERE c.cluster_id = ?
    ''', (cluster_id_str,)).fetchone()
    
    if not cluster:
        flash('Cluster not found', 'error')
        return redirect('/correlation')
        
    incidents = db.execute('''
        SELECT i.*, u.full_name as assigned_name 
        FROM incidents i 
        LEFT JOIN users u ON i.assigned_to = u.id 
        WHERE i.cluster_id = ? 
        ORDER BY i.reported_date ASC
    ''', (cluster_id_str,)).fetchall()
    
    alerts = db.execute('''
        SELECT * FROM alerts 
        WHERE cluster_id = ? 
        ORDER BY created_at DESC LIMIT 5
    ''', (cluster_id_str,)).fetchall()
    
    analysts = db.execute("SELECT id, full_name FROM users WHERE role IN ('Admin', 'Analyst') AND is_active = 1").fetchall()
    
    return render_template('correlation_detail.html', 
        active_page='correlation', 
        cluster=cluster, 
        incidents=incidents, 
        alerts=alerts,
        analysts=analysts
    )

@app.route('/correlation/update-status/<cluster_id_str>', methods=['POST'])
@login_required
def correlation_update_status(cluster_id_str):
    if current_user.role not in ['Admin', 'Analyst']:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
    new_status = request.form.get('new_status')
    if new_status not in ['Active', 'Investigating', 'Resolved']:
        return jsonify({'success': False, 'message': 'Invalid status'})
        
    db = get_db_connection()
    db.execute('UPDATE incident_clusters SET status = ?, last_updated = CURRENT_TIMESTAMP WHERE cluster_id = ?', (new_status, cluster_id_str))
    
    if new_status == 'Resolved':
        db.execute('''
            UPDATE incidents 
            SET status = 'Resolved', resolved_date = CURRENT_TIMESTAMP, updated_by = ?
            WHERE cluster_id = ? AND status NOT IN ('Resolved', 'Closed')
        ''', (current_user.id, cluster_id_str))
        
    db.execute('''
        INSERT INTO activity_logs (user_id, action_type, target_type, target_id, details, ip_address)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (current_user.id, 'UPDATE_INCIDENT', 'clusters', cluster_id_str, f'Cluster {cluster_id_str} status changed to {new_status}', request.remote_addr))
    
    db.commit()
    return jsonify({'success': True})

@app.route('/correlation/assign/<cluster_id_str>', methods=['POST'])
@login_required
def correlation_assign(cluster_id_str):
    if current_user.role not in ['Admin', 'Analyst']:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
    assigned_to = request.form.get('assigned_to')
    assigned_to = int(assigned_to) if assigned_to else None
    
    db = get_db_connection()
    db.execute('UPDATE incident_clusters SET assigned_to = ?, last_updated = CURRENT_TIMESTAMP WHERE cluster_id = ?', (assigned_to, cluster_id_str))
    
    assigned_name = "Unassigned"
    if assigned_to:
        u = db.execute('SELECT full_name FROM users WHERE id = ?', (assigned_to,)).fetchone()
        assigned_name = u['full_name'] if u else "Unknown"
        
    db.commit()
    return jsonify({'success': True, 'assigned_name': assigned_name})

@app.route('/correlation/add-note/<cluster_id_str>', methods=['POST'])
@login_required
def correlation_add_note(cluster_id_str):
    if current_user.role not in ['Admin', 'Analyst']:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
    note = request.form.get('note')
    if not note:
        return jsonify({'success': False, 'message': 'Note required'})
        
    db = get_db_connection()
    cluster = db.execute('SELECT notes FROM incident_clusters WHERE cluster_id = ?', (cluster_id_str,)).fetchone()
    
    now_str = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
    formatted_note = f"[{now_str}] [{current_user.full_name}]: {note}"
    
    existing = cluster['notes'] if cluster and cluster['notes'] else ""
    new_notes = existing + "\\n" + formatted_note if existing else formatted_note
    
    db.execute('UPDATE incident_clusters SET notes = ?, last_updated = CURRENT_TIMESTAMP WHERE cluster_id = ?', (new_notes, cluster_id_str))
    db.commit()
    
    return jsonify({'success': True, 'note': formatted_note})

@app.route('/api/dashboard-stats')
@login_required
def api_dashboard_stats():
    db = get_db_connection()
    c1 = db.execute("SELECT COUNT(*) as c FROM incident_clusters WHERE status = 'Active'").fetchone()['c']
    c2 = db.execute("SELECT COUNT(*) as c FROM incidents WHERE status = 'Open'").fetchone()['c']
    c3 = db.execute("SELECT COUNT(*) as c FROM incidents WHERE priority = 'Critical' AND status NOT IN ('Resolved','Closed')").fetchone()['c']
    c4 = db.execute('''
        SELECT COUNT(*) as c FROM alerts 
        WHERE is_read = 0 AND dismissed = 0 
        AND (recipient_id = ? OR recipient_role = ?)
    ''', (current_user.id, current_user.role)).fetchone()['c']
    
    c5 = db.execute("SELECT COUNT(*) as c FROM incidents WHERE similar_incident_id IS NOT NULL").fetchone()['c']
    c6 = db.execute("SELECT COUNT(*) as c FROM incidents WHERE solution_applied_from IS NOT NULL").fetchone()['c']
    
    c7 = db.execute("SELECT COUNT(*) as c FROM incidents").fetchone()['c']
    c8 = db.execute("SELECT COUNT(*) as c FROM incidents WHERE status = 'Investigating'").fetchone()['c']
    c9 = db.execute("SELECT COUNT(*) as c FROM incidents WHERE status IN ('Resolved', 'Closed')").fetchone()['c']
    
    return jsonify({
        "active_clusters": c1,
        "open_incidents": c2,
        "critical_incidents": c3,
        "unread_alerts": c4,
        "total_similarity_matches": c5,
        "solutions_applied": c6,
        "total_incidents": c7,
        "investigating_incidents": c8,
        "resolved_incidents": c9
    })

@app.route('/api/alert-count')
@login_required
def api_alert_count():
    db = get_db_connection()
    c = db.execute('''
        SELECT COUNT(*) as c FROM alerts 
        WHERE is_read = 0 AND dismissed = 0 
        AND (recipient_id = ? OR recipient_role = ?)
    ''', (current_user.id, current_user.role)).fetchone()['c']
    return jsonify({"count": c})

def check_sla_breaches():
    db = get_db_connection()
    try:
        settings = db.execute("SELECT setting_key, setting_value FROM settings").fetchall()
        settings_dict = {row['setting_key']: row['setting_value'] for row in settings}
    except Exception:
        settings_dict = {}

    critical_hrs = float(settings_dict.get('critical_sla_hours', 4))
    high_hrs = float(settings_dict.get('high_sla_hours', 24))
    medium_hrs = float(settings_dict.get('medium_sla_hours', 72))
    low_hrs = float(settings_dict.get('low_sla_hours', 168))
    
    sla_map = {
        'Critical': critical_hrs,
        'High': high_hrs,
        'Medium': medium_hrs,
        'Low': low_hrs
    }
    
    open_incidents = db.execute('''
        SELECT id, incident_id, priority, reported_date 
        FROM incidents 
        WHERE status IN ('Open', 'Investigating')
    ''').fetchall()
    
    now = datetime.utcnow()
    for inc in open_incidents:
        sl_limit = sla_map.get(inc['priority'], 24)
        rep_date = inc['reported_date']
        fmt = '%Y-%m-%d %H:%M:%S'
        try:
            d = datetime.strptime(str(rep_date).replace('T', ' ')[:19], fmt)
        except Exception:
            continue
            
        hours_open = (now - d).total_seconds() / 3600.0
        
        if hours_open > sl_limit:
            existing = db.execute('''
                SELECT id FROM alerts 
                WHERE alert_type = 'SLA_BREACH' AND incident_id = ? AND is_read = 0
            ''', (inc['id'],)).fetchone()
            
            if not existing:
                sev = 'CRITICAL' if inc['priority'] in ['Critical', 'High'] else 'WARNING'
                msg = f"SLA breach: {inc['incident_id']} ({inc['priority']}) has been open for {round(hours_open)}h — SLA limit is {sl_limit}h"
                
                db.execute('''
                    INSERT INTO alerts (alert_type, severity, message, incident_id, recipient_role, is_read, created_at)
                    VALUES ('SLA_BREACH', ?, ?, ?, 'Admin', 0, CURRENT_TIMESTAMP)
                ''', (sev, msg, inc['id']))
                db.execute('''
                    INSERT INTO alerts (alert_type, severity, message, incident_id, recipient_role, is_read, created_at)
                    VALUES ('SLA_BREACH', ?, ?, ?, 'Analyst', 0, CURRENT_TIMESTAMP)
                ''', (sev, msg, inc['id']))
    db.commit()

def create_high_priority_alert(incident_id_int, incident_id_str, priority):
    if priority not in ['Critical', 'High']: return
    db = get_db_connection()
    existing = db.execute('''
        SELECT id FROM alerts WHERE alert_type = 'HIGH_PRIORITY' AND incident_id = ?
    ''', (incident_id_int,)).fetchone()
    
    if not existing:
        sev = 'CRITICAL' if priority == 'Critical' else 'WARNING'
        msg = f"High priority incident logged: {incident_id_str} — {priority} priority requires immediate attention"
        db.execute('''
            INSERT INTO alerts (alert_type, severity, message, incident_id, recipient_role, is_read, created_at)
            VALUES ('HIGH_PRIORITY', ?, ?, ?, 'Admin', 0, CURRENT_TIMESTAMP)
        ''', (sev, msg, incident_id_int))
        db.execute('''
            INSERT INTO alerts (alert_type, severity, message, incident_id, recipient_role, is_read, created_at)
            VALUES ('HIGH_PRIORITY', ?, ?, ?, 'Analyst', 0, CURRENT_TIMESTAMP)
        ''', (sev, msg, incident_id_int))
        db.commit()

def create_assignment_alert(incident_id_int, incident_id_str, assigned_user_id, assigned_by_name):
    if not assigned_user_id: return
    db = get_db_connection()
    msg = f"You have been assigned incident {incident_id_str} by {assigned_by_name}"
    db.execute('''
        INSERT INTO alerts (alert_type, severity, message, incident_id, recipient_id, is_read, created_at)
        VALUES ('ASSIGNMENT', 'INFO', ?, ?, ?, 0, CURRENT_TIMESTAMP)
    ''', (msg, incident_id_int, assigned_user_id))
    db.commit()

@app.route('/alerts')
@login_required
def alerts():
    try:
        check_sla_breaches()
        db = get_db_connection()
        
        alert_type = request.args.get('alert_type', '')
        severity = request.args.get('severity', '')
        is_read = request.args.get('is_read', '')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        offset = (page - 1) * per_page
        
        where_clauses = ["(recipient_id = ? OR recipient_role = ?) AND dismissed = 0"]
        params = [current_user.id, current_user.role]
        
        if alert_type and alert_type != 'All Types':
            where_clauses.append("alert_type = ?")
            params.append(alert_type.replace(' ', '_').upper())
            
        if severity and severity != 'All Severities':
            where_clauses.append("severity = ?")
            params.append(severity.upper())
            
        if is_read != '':
            where_clauses.append("is_read = ?")
            params.append(int(is_read))
            
        where_sql = " WHERE " + " AND ".join(where_clauses)
        
        query = f"SELECT * FROM alerts {where_sql} ORDER BY created_at DESC LIMIT ? OFFSET ?"
        inc_params = params + [per_page, offset]
        alerts_list = db.execute(query, inc_params).fetchall()
        
        unread_count = db.execute("SELECT COUNT(*) as c FROM alerts WHERE (recipient_id = ? OR recipient_role = ?) AND dismissed = 0 AND is_read = 0", (current_user.id, current_user.role)).fetchone()['c']
        total_count = db.execute("SELECT COUNT(*) as c FROM alerts WHERE (recipient_id = ? OR recipient_role = ?) AND dismissed = 0", (current_user.id, current_user.role)).fetchone()['c']
        critical_count = db.execute("SELECT COUNT(*) as c FROM alerts WHERE (recipient_id = ? OR recipient_role = ?) AND dismissed = 0 AND is_read = 0 AND severity = 'CRITICAL'", (current_user.id, current_user.role)).fetchone()['c']
        
        return render_template('alerts.html', 
            active_page='alerts', 
            alerts=[dict(r) for r in alerts_list],
            unread_count=unread_count,
            total_count=total_count,
            critical_count=critical_count,
            page=page, per_page=per_page
        )

    except Exception as e:
        app.logger.error(f'Error in alerts: {str(e)}')
        if request.is_json:
            return jsonify({'success': False, 'message': 'An error occurred'}), 500
        flash('An error occurred. Please try again.', 'error')
        return redirect(url_for('dashboard'))
@app.route('/alerts/mark-read/<int:alert_id>', methods=['POST'])
@login_required
def alert_mark_read(alert_id):
    db = get_db_connection()
    db.execute('''
        UPDATE alerts SET is_read = 1, read_at = CURRENT_TIMESTAMP
        WHERE id = ? AND (recipient_id = ? OR recipient_role = ?)
    ''', (alert_id, current_user.id, current_user.role))
    db.commit()
    return jsonify({"success": True})

@app.route('/alerts/mark-all-read', methods=['POST'])
@login_required
def alert_mark_all_read():
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute('''
        UPDATE alerts SET is_read = 1, read_at = CURRENT_TIMESTAMP
        WHERE (recipient_id = ? OR recipient_role = ?) AND is_read = 0 AND dismissed = 0
    ''', (current_user.id, current_user.role))
    db.commit()
    return jsonify({"success": True, "count": cursor.rowcount})

@app.route('/alerts/dismiss/<int:alert_id>', methods=['POST'])
@login_required
def alert_dismiss(alert_id):
    db = get_db_connection()
    db.execute('''
        UPDATE alerts SET dismissed = 1, dismissed_at = CURRENT_TIMESTAMP
        WHERE id = ? AND (recipient_id = ? OR recipient_role = ?)
    ''', (alert_id, current_user.id, current_user.role))
    db.commit()
    return jsonify({"success": True})

@app.route('/alerts/dismiss-all-read', methods=['POST'])
@login_required
def alert_dismiss_all_read():
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute('''
        UPDATE alerts SET dismissed = 1, dismissed_at = CURRENT_TIMESTAMP
        WHERE (recipient_id = ? OR recipient_role = ?) AND is_read = 1 AND dismissed = 0
    ''', (current_user.id, current_user.role))
    db.commit()
    return jsonify({"success": True, "count": cursor.rowcount})

@app.route('/api/similarity/<incident_id_str>')
@login_required
def api_similarity(incident_id_str):
    db = get_db_connection()
    inc = db.execute('SELECT id FROM incidents WHERE incident_id = ?', (incident_id_str,)).fetchone()
    if not inc:
        return jsonify({'found': False, 'matches': []})
    res = get_cached_similarity(incident_id_str)
    return jsonify(res)

@app.route('/incidents/apply-solution/<incident_id_str>', methods=['POST'])
@login_required
def apply_solution(incident_id_str):
    if current_user.role not in ['Admin', 'Analyst']:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
    source_incident_id = request.form.get('source_incident_id')
    resolution_notes = request.form.get('resolution_notes')
    
    db = get_db_connection()
    db.execute('''
        UPDATE incidents SET
            resolution_notes = ?,
            solution_applied_from = ?,
            updated_at = CURRENT_TIMESTAMP,
            updated_by = ?
        WHERE incident_id = ?
    ''', (resolution_notes, source_incident_id, current_user.id, incident_id_str))
    
    inc = db.execute('SELECT id FROM incidents WHERE incident_id = ?', (incident_id_str,)).fetchone()
    if inc:
        db.execute('''
            INSERT INTO activity_logs (user_id, action_type, target_type, target_id, details, ip_address)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (current_user.id, 'UPDATE_INCIDENT', 'incidents', inc['id'], f'Solution applied from {source_incident_id}', request.remote_addr))
        
    db.commit()
    return jsonify({'success': True})


@app.route('/api/similarity-stats')
@login_required
def api_similarity_stats():
    db = get_db_connection()
    c1 = db.execute("SELECT COUNT(*) as c FROM incidents WHERE similar_incident_id IS NOT NULL").fetchone()['c']
    c2 = db.execute("SELECT COUNT(*) as c FROM incidents WHERE similarity_score >= 0.75").fetchone()['c']
    c3 = db.execute("SELECT COUNT(*) as c FROM incidents WHERE solution_applied_from IS NOT NULL").fetchone()['c']
    
    return jsonify({
        "total_with_similarity": c1,
        "high_confidence": c2,
        "solution_applied": c3
    })

@app.route('/similarity')
@login_required
def similarity():
    try:
        db = get_db_connection()
        
        incidents_raw = db.execute('''
            SELECT i.*, 
              si.incident_id as similar_to_id,
              si.title as similar_to_title,
              si.resolution_notes as similar_resolution,
              si.status as similar_status
            FROM incidents i
            LEFT JOIN incidents si ON i.similar_incident_id = si.incident_id
            WHERE i.similar_incident_id IS NOT NULL
            ORDER BY i.similarity_score DESC, i.reported_date DESC
        ''').fetchall()
        
        incidents_list = [dict(r) for r in incidents_raw]
        
        stats_c1 = db.execute("SELECT COUNT(*) as c FROM incidents WHERE similar_incident_id IS NOT NULL").fetchone()['c']
        stats_c2 = db.execute("SELECT COUNT(*) as c FROM incidents WHERE similarity_score >= 0.75").fetchone()['c']
        stats_c3 = db.execute("SELECT COUNT(*) as c FROM incidents WHERE solution_applied_from IS NOT NULL").fetchone()['c']
        
        avg_row = db.execute("SELECT AVG(similarity_score) as a FROM incidents WHERE similar_incident_id IS NOT NULL").fetchone()
        avg_sim = round(avg_row['a'] * 100) if avg_row and avg_row['a'] else 0
        
        return render_template('similarity.html', 
            active_page='similarity',
            incidents=incidents_list,
            total_with_similarity=stats_c1,
            high_confidence=stats_c2,
            solution_applied=stats_c3,
            avg_similarity=avg_sim
        )

    except Exception as e:
        app.logger.error(f'Error in similarity: {str(e)}')
        if request.is_json:
            return jsonify({'success': False, 'message': 'An error occurred'}), 500
        flash('An error occurred. Please try again.', 'error')
        return redirect(url_for('dashboard'))
import csv
from io import StringIO
from flask import Response

@app.route('/reports')
@login_required
def reports():
    try:
        if current_user.role not in ['Admin', 'Analyst'] or (current_user.role == 'Analyst' and not current_user.has_admin_privileges):
            flash("Access denied. You do not have permission to view reports.", "error")
            return redirect(url_for('dashboard'))
            
        db = get_db_connection()
        
        # Correlation metrics
        total_clusters_created = db.execute("SELECT COUNT(*) as c FROM incident_clusters").fetchone()['c']
        active_clusters = db.execute("SELECT COUNT(*) as c FROM incident_clusters WHERE status='Active'").fetchone()['c']
        resolved_clusters = db.execute("SELECT COUNT(*) as c FROM incident_clusters WHERE status='Resolved'").fetchone()['c']
        
        avg_cluster_size_row = db.execute("SELECT AVG(incident_count) as a FROM incident_clusters").fetchone()['a']
        avg_cluster_size = round(avg_cluster_size_row, 1) if avg_cluster_size_row else 0
        
        total_correlated_incidents = db.execute("SELECT COUNT(*) as c FROM incidents WHERE cluster_id IS NOT NULL").fetchone()['c']
        
        largest_cluster_row = db.execute("SELECT MAX(incident_count) as m FROM incident_clusters").fetchone()['m']
        largest_cluster = largest_cluster_row if largest_cluster_row else 0
        
        # Similarity metrics
        total_matches_found = db.execute("SELECT COUNT(*) as c FROM incidents WHERE similar_incident_id IS NOT NULL").fetchone()['c']
        high_confidence = db.execute("SELECT COUNT(*) as c FROM incidents WHERE similarity_score >= 0.75").fetchone()['c']
        medium_confidence = db.execute("SELECT COUNT(*) as c FROM incidents WHERE similarity_score >= 0.50 AND similarity_score < 0.75").fetchone()['c']
        solutions_applied = db.execute("SELECT COUNT(*) as c FROM incidents WHERE solution_applied_from IS NOT NULL").fetchone()['c']
        
        avg_similarity_score_row = db.execute("SELECT AVG(similarity_score) as a FROM incidents WHERE similar_incident_id IS NOT NULL").fetchone()['a']
        avg_similarity_score = round(avg_similarity_score_row, 2) if avg_similarity_score_row else 0
        
        # General incident metrics
        total_incidents = db.execute("SELECT COUNT(*) as c FROM incidents").fetchone()['c']
        open_count = db.execute("SELECT COUNT(*) as c FROM incidents WHERE status='Open'").fetchone()['c']
        investigating_count = db.execute("SELECT COUNT(*) as c FROM incidents WHERE status='Investigating'").fetchone()['c']
        resolved_count = db.execute("SELECT COUNT(*) as c FROM incidents WHERE status='Resolved'").fetchone()['c']
        closed_count = db.execute("SELECT COUNT(*) as c FROM incidents WHERE status='Closed'").fetchone()['c']
        
        avg_resolution_time_row = db.execute("SELECT AVG(resolution_time_minutes) as a FROM incidents WHERE resolution_time_minutes IS NOT NULL").fetchone()['a']
        avg_resolution_time = avg_resolution_time_row if avg_resolution_time_row else 0
        
        critical_count = db.execute("SELECT COUNT(*) as c FROM incidents WHERE priority='Critical'").fetchone()['c']
        high_count = db.execute("SELECT COUNT(*) as c FROM incidents WHERE priority='High'").fetchone()['c']
        medium_count = db.execute("SELECT COUNT(*) as c FROM incidents WHERE priority='Medium'").fetchone()['c']
        low_count = db.execute("SELECT COUNT(*) as c FROM incidents WHERE priority='Low'").fetchone()['c']
        
        # Recent activity logs
        recent_activity = db.execute('''
            SELECT al.*, u.full_name, u.role
            FROM activity_logs al
            JOIN users u ON al.user_id = u.id
            ORDER BY al.created_at DESC
            LIMIT 20
        ''').fetchall()
        
        metrics = {
            'total_clusters_created': total_clusters_created,
            'active_clusters': active_clusters,
            'resolved_clusters': resolved_clusters,
            'avg_cluster_size': avg_cluster_size,
            'total_correlated_incidents': total_correlated_incidents,
            'largest_cluster': largest_cluster,
            
            'total_matches_found': total_matches_found,
            'high_confidence': high_confidence,
            'medium_confidence': medium_confidence,
            'solutions_applied': solutions_applied,
            'avg_similarity_score': avg_similarity_score,
            
            'total_incidents': total_incidents,
            'open_count': open_count,
            'investigating_count': investigating_count,
            'resolved_count': resolved_count,
            'closed_count': closed_count,
            'avg_resolution_time': avg_resolution_time,
            'critical_count': critical_count,
            'high_count': high_count,
            'medium_count': medium_count,
            'low_count': low_count
        }
        
        return render_template('reports.html', active_page='reports', metrics=metrics, recent_activity=[dict(row) for row in recent_activity])
    except Exception as e:
        app.logger.error(f'Error in reports: {str(e)}')
        if request.is_json:
            return jsonify({'success': False, 'message': 'An error occurred'}), 500
        flash('An error occurred. Please try again.', 'error')
        return redirect(url_for('dashboard'))

@app.route('/reports/export/incidents')
@login_required
def export_incidents():
    if current_user.role not in ['Admin', 'Analyst'] or (current_user.role == 'Analyst' and not current_user.has_admin_privileges):
        flash("Access denied. You do not have permission to view reports.", "error")
        return redirect(url_for('dashboard'))
    db = get_db_connection()
    rows = db.execute("SELECT * FROM incidents ORDER BY reported_date DESC").fetchall()
    
    si = StringIO()
    cw = csv.writer(si)
    if rows:
        cw.writerow(rows[0].keys())
        cw.writerows(rows)
    return Response(si.getvalue(), mimetype="text/csv", headers={"Content-Disposition": "attachment;filename=incidents.csv"})

@app.route('/reports/export/clusters')
@login_required
def export_clusters():
    if current_user.role not in ['Admin', 'Analyst'] or (current_user.role == 'Analyst' and not current_user.has_admin_privileges):
        flash("Access denied. You do not have permission to view reports.", "error")
        return redirect(url_for('dashboard'))
    db = get_db_connection()
    rows = db.execute("SELECT * FROM incident_clusters ORDER BY created_at DESC").fetchall()
    
    si = StringIO()
    cw = csv.writer(si)
    if rows:
        cw.writerow(rows[0].keys())
        cw.writerows(rows)
    return Response(si.getvalue(), mimetype="text/csv", headers={"Content-Disposition": "attachment;filename=clusters.csv"})

@app.route('/reports/export/activity')
@login_required
def export_activity():
    if current_user.role not in ['Admin', 'Analyst'] or (current_user.role == 'Analyst' and not current_user.has_admin_privileges):
        flash("Access denied. You do not have permission to view reports.", "error")
        return redirect(url_for('dashboard'))
    db = get_db_connection()
    rows = db.execute('''
        SELECT al.*, u.full_name, u.role
        FROM activity_logs al
        JOIN users u ON al.user_id = u.id
        ORDER BY al.created_at DESC
    ''').fetchall()
    
    si = StringIO()
    cw = csv.writer(si)
    if rows:
        cw.writerow(rows[0].keys())
        cw.writerows(rows)
    return Response(si.getvalue(), mimetype="text/csv", headers={"Content-Disposition": "attachment;filename=activity_logs.csv"})

@app.route('/settings')
@login_required
def settings_page():
    try:
        if current_user.role != 'Admin':
            flash("Access denied. Settings are only accessible to Admin.", "error")
            return redirect(url_for('dashboard'))
            
        db = get_db_connection()
        settings_rows = db.execute("SELECT setting_key, setting_value FROM settings").fetchall()
        settings_dict = {}
        for row in settings_rows:
            settings_dict[row['setting_key']] = row['setting_value']
            
        system_info = {
            'total_incidents': db.execute("SELECT COUNT(*) as c FROM incidents").fetchone()['c'],
            'total_users': db.execute("SELECT COUNT(*) as c FROM users").fetchone()['c'],
            'total_clusters': db.execute("SELECT COUNT(*) as c FROM incident_clusters").fetchone()['c'],
            'total_alerts': db.execute("SELECT COUNT(*) as c FROM alerts").fetchone()['c'],
            'total_activity_logs': db.execute("SELECT COUNT(*) as c FROM activity_logs").fetchone()['c']
        }
        
        recent_incidents = db.execute("SELECT incident_id, title FROM incidents ORDER BY reported_date DESC LIMIT 20").fetchall()
        
        return render_template('settings.html', active_page='settings', 
                               settings=settings_dict, 
                               system_info=system_info,
                               recent_incidents=[dict(r) for r in recent_incidents])

    except Exception as e:
        app.logger.error(f'Error in settings_page: {str(e)}')
        if request.is_json:
            return jsonify({'success': False, 'message': 'An error occurred'}), 500
        flash('An error occurred. Please try again.', 'error')
        return redirect(url_for('dashboard'))
@app.route('/settings/algorithm', methods=['POST'])
@login_required
def settings_algorithm():
    if current_user.role != 'Admin':
        return jsonify({"success": False, "message": "Unauthorized"}), 403
        
    data = request.json
    try:
        corr_thresh = float(data.get('correlation_threshold', 0))
        corr_win = int(data.get('correlation_time_window_hours', 0))
        sim_thresh = float(data.get('similarity_threshold', 0))
        sim_limit = int(data.get('similarity_result_limit', 0))
        
        if not (0.1 <= corr_thresh <= 1.0): raise ValueError("Correlation threshold must be between 0.1 and 1.0")
        if not (1 <= corr_win <= 168): raise ValueError("Correlation time window must be 1 to 168 hours")
        if not (0.1 <= sim_thresh <= 1.0): raise ValueError("Similarity threshold must be between 0.1 and 1.0")
        if not (1 <= sim_limit <= 10): raise ValueError("Similarity result limit must be 1 to 10")
        
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)})

    db = get_db_connection()
    now_str = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    updates = {
        'correlation_threshold': str(corr_thresh),
        'correlation_time_window_hours': str(corr_win),
        'similarity_threshold': str(sim_thresh),
        'similarity_result_limit': str(sim_limit)
    }
    for k, v in updates.items():
        db.execute('''
            UPDATE settings SET setting_value=?, updated_by=?, updated_at=?
            WHERE setting_key=?
        ''', (v, current_user.id, now_str, k))
        
    db.execute('''
        INSERT INTO activity_logs (user_id, action_type, target_type, target_id, details, ip_address)
        VALUES (?, 'UPDATE_SETTINGS', 'system', 0, 'Algorithm settings updated by Admin', ?)
    ''', (current_user.id, request.remote_addr))
    db.commit()
    return jsonify({"success": True, "message": "Algorithm settings saved successfully"})

@app.route('/settings/sla', methods=['POST'])
@login_required
def settings_sla():
    if current_user.role != 'Admin':
        return jsonify({"success": False, "message": "Unauthorized"}), 403
    
    data = request.json
    try:
        c = int(data.get('critical_sla_hours', 0))
        h = int(data.get('high_sla_hours', 0))
        m = int(data.get('medium_sla_hours', 0))
        l = int(data.get('low_sla_hours', 0))
        
        if not (1 <= c <= 24): raise ValueError("Critical SLA must be 1 to 24")
        if not (1 <= h <= 168): raise ValueError("High SLA must be 1 to 168")
        if not (1 <= m <= 720): raise ValueError("Medium SLA must be 1 to 720")
        if not (1 <= l <= 2160): raise ValueError("Low SLA must be 1 to 2160")
        if not (c < h < m < l): raise ValueError("SLA hours must increase from Critical to Low priority")
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)})

    db = get_db_connection()
    now_str = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    updates = {'critical_sla_hours': str(c), 'high_sla_hours': str(h), 'medium_sla_hours': str(m), 'low_sla_hours': str(l)}
    
    for k, v in updates.items():
        db.execute('''
            UPDATE settings SET setting_value=?, updated_by=?, updated_at=?
            WHERE setting_key=?
        ''', (v, current_user.id, now_str, k))
        
    db.execute('''
        INSERT INTO activity_logs (user_id, action_type, target_type, target_id, details, ip_address)
        VALUES (?, 'UPDATE_SETTINGS', 'system', 0, 'SLA settings updated by Admin', ?)
    ''', (current_user.id, request.remote_addr))
    db.commit()
    return jsonify({"success": True})

@app.route('/settings/system', methods=['POST'])
@login_required
def settings_system():
    if current_user.role != 'Admin':
        return jsonify({"success": False, "message": "Unauthorized"}), 403
        
    data = request.json
    org = data.get('organization_name', '').strip()
    prefix = data.get('incident_id_prefix', '').strip()
    timeout = data.get('session_timeout', 60)
    date_fmt = data.get('date_format', 'DD/MM/YYYY')
    
    if not org or len(org) > 100: return jsonify({"success": False, "message": "Invalid org name"})
    import re
    if not prefix or len(prefix) > 10 or not re.match(r'^[A-Za-z\-]+$', prefix):
        return jsonify({"success": False, "message": "Invalid prefix"})
        
    try:
        timeout = int(timeout)
        if not (5 <= timeout <= 480): raise ValueError()
    except:
        return jsonify({"success": False, "message": "Invalid session timeout"})
        
    if date_fmt not in ['DD/MM/YYYY', 'MM/DD/YYYY', 'YYYY-MM-DD']:
        return jsonify({"success": False, "message": "Invalid date format"})

    db = get_db_connection()
    now_str = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    updates = {'organization_name': org, 'incident_id_prefix': prefix, 'session_timeout': str(timeout), 'date_format': date_fmt}
    
    for k, v in updates.items():
        db.execute('INSERT OR REPLACE INTO settings (setting_key, setting_value, updated_by, updated_at) VALUES (?, ?, ?, ?)',
                  (k, v, current_user.id, now_str))

    db.execute('''
        INSERT INTO activity_logs (user_id, action_type, target_type, target_id, details, ip_address)
        VALUES (?, 'UPDATE_SETTINGS', 'system', 0, 'System settings updated by Admin', ?)
    ''', (current_user.id, request.remote_addr))
    db.commit()
    return jsonify({"success": True})

@app.route('/settings/risk-weights', methods=['POST'])
@login_required
def settings_risk_weights():
    if current_user.role != 'Admin':
        return jsonify({"success": False, "message": "Unauthorized"}), 403
        
    data = request.json
    try:
        w1 = float(data.get('weight_asset_criticality', 0))
        w2 = float(data.get('weight_threat_severity', 0))
        w3 = float(data.get('weight_vulnerability_exposure', 0))
        w4 = float(data.get('weight_users_affected', 0))
        w5 = float(data.get('weight_repeat_penalty', 0))
        
        for w in [w1, w2, w3, w4, w5]:
            if not (0.0 <= w <= 1.0): raise ValueError("Weights must be between 0 and 1")
            
        total = w1 + w2 + w3 + w4 + w5
        if abs(total - 1.0) > 0.01:
            return jsonify({"success": False, "message": f"Weights must total 100%. Current total: {round(total*100)}%"})
            
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)})

    db = get_db_connection()
    now_str = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    updates = {
        'weight_asset_criticality': str(w1),
        'weight_threat_severity': str(w2),
        'weight_vulnerability_exposure': str(w3),
        'weight_users_affected': str(w4),
        'weight_repeat_penalty': str(w5)
    }
    for k, v in updates.items():
        db.execute('INSERT OR REPLACE INTO settings (setting_key, setting_value, updated_by, updated_at) VALUES (?, ?, ?, ?)',
                  (k, v, current_user.id, now_str))

    db.execute('''
        INSERT INTO activity_logs (user_id, action_type, target_type, target_id, details, ip_address)
        VALUES (?, 'UPDATE_SETTINGS', 'system', 0, 'Risk weights updated by Admin', ?)
    ''', (current_user.id, request.remote_addr))
    db.commit()
    return jsonify({"success": True})

@app.route('/settings/test-correlation')
@login_required
def settings_test_correlation():
    if current_user.role != 'Admin':
        return jsonify({"success": False, "message": "Unauthorized"}), 403
        
    incident_id_str = request.args.get('incident_id')
    db = get_db_connection()
    inc = db.execute("SELECT id FROM incidents WHERE incident_id = ?", (incident_id_str,)).fetchone()
    if not inc: return jsonify({"success": False, "message": "Incident not found"}), 404
    
    res = run_correlation(inc['id'])
    return jsonify(res)

@app.route('/settings/test-similarity')
@login_required
def settings_test_similarity():
    if current_user.role != 'Admin':
        return jsonify({"success": False, "message": "Unauthorized"}), 403
        
    incident_id_str = request.args.get('incident_id')
    db = get_db_connection()
    inc = db.execute("SELECT id FROM incidents WHERE incident_id = ?", (incident_id_str,)).fetchone()
    if not inc: return jsonify({"success": False, "message": "Incident not found"}), 404
    
    res = run_similarity(inc['id'])
    return jsonify(res)

@app.route('/settings/reset-defaults', methods=['POST'])
@login_required
def settings_reset_defaults():
    if current_user.role != 'Admin':
        return jsonify({"success": False, "message": "Unauthorized"}), 403
    
    defaults = {
        'correlation_threshold': '0.65',
        'correlation_time_window_hours': '48',
        'similarity_threshold': '0.50',
        'similarity_result_limit': '5',
        'critical_sla_hours': '4',
        'high_sla_hours': '24',
        'medium_sla_hours': '72',
        'low_sla_hours': '168',
        'organization_name': 'CyberIR',
        'incident_id_prefix': 'INC-'
    }
    
    db = get_db_connection()
    now_str = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    
    for k, v in defaults.items():
        db.execute('INSERT OR REPLACE INTO settings (setting_key, setting_value, updated_by, updated_at) VALUES (?, ?, ?, ?)',
                  (k, v, current_user.id, now_str))

    db.execute('''
        INSERT INTO activity_logs (user_id, action_type, target_type, target_id, details, ip_address)
        VALUES (?, 'UPDATE_SETTINGS', 'system', 0, 'Settings reset to defaults by Admin', ?)
    ''', (current_user.id, request.remote_addr))
    db.commit()
    return jsonify({"success": True})

@app.route('/profile')
@login_required
def profile_page():
    db = get_db_connection()
    user_row = db.execute("SELECT * FROM users WHERE id = ?", (current_user.id,)).fetchone()
    user_data = dict(user_row) if user_row else {}
    
    prefs = db.execute("SELECT * FROM user_preferences WHERE user_id = ?", (current_user.id,)).fetchone()
    if not prefs:
        db.execute('''
            INSERT INTO user_preferences 
            (user_id, email_notifications, email_critical_alerts, email_assignments, 
             email_correlation_alerts, email_daily_summary, in_app_alert_sound, 
             dark_mode, items_per_page)
            VALUES (?, 1, 1, 1, 1, 1, 1, 0, 25)
        ''', (current_user.id,))
        db.commit()
        prefs = db.execute("SELECT * FROM user_preferences WHERE user_id = ?", (current_user.id,)).fetchone()
    prefs_data = dict(prefs)
    
    stats = {
        'incidents_created': db.execute("SELECT COUNT(*) as c FROM incidents WHERE created_by = ?", (current_user.id,)).fetchone()['c'],
        'incidents_assigned': db.execute("SELECT COUNT(*) as c FROM incidents WHERE assigned_to = ?", (current_user.id,)).fetchone()['c'],
        'incidents_resolved': db.execute("SELECT COUNT(*) as c FROM incidents WHERE assigned_to = ? AND status IN ('Resolved', 'Closed')", (current_user.id,)).fetchone()['c'],
        'alerts_unread': db.execute("SELECT COUNT(*) as c FROM alerts WHERE (recipient_id = ? OR recipient_role = ?) AND is_read = 0 AND dismissed = 0", (current_user.id, current_user.role)).fetchone()['c']
    }
    
    activity = db.execute("SELECT * FROM activity_logs WHERE user_id = ? ORDER BY created_at DESC LIMIT 10", (current_user.id,)).fetchall()
    
    last_login = user_data.get('last_login', '')
    
    return render_template('profile.html', 
                           active_page='profile', 
                           user=user_data, 
                           prefs=prefs_data, 
                           stats=stats, 
                           activity=[dict(a) for a in activity],
                           last_login=last_login)

@app.route('/profile/update', methods=['POST'])
@login_required
def profile_update():
    full_name = request.json.get('full_name', '').strip()
    phone_number = request.json.get('phone_number', '').strip()
    
    if not full_name:
        return jsonify({"success": False, "message": "Full name is required"})
        
    db = get_db_connection()
    now_str = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    db.execute('UPDATE users SET full_name = ?, phone_number = ?, updated_at = ? WHERE id = ?', 
               (full_name, phone_number, now_str, current_user.id))
               
    db.execute('''
        INSERT INTO activity_logs (user_id, action_type, details, ip_address)
        VALUES (?, 'UPDATE_USER', 'Profile updated', ?)
    ''', (current_user.id, request.remote_addr))
    db.commit()
    
    current_user.full_name = full_name
    return jsonify({"success": True, "message": "Profile updated successfully", "new_name": full_name})

@app.route('/profile/change-password', methods=['POST'])
@login_required
def profile_change_password():
    data = request.json
    current_pwd = data.get('current_password', '')
    new_pwd = data.get('new_password', '')
    confirm_pwd = data.get('confirm_password', '')
    
    db = get_db_connection()
    user_row = db.execute("SELECT password_hash FROM users WHERE id = ?", (current_user.id,)).fetchone()
    
    from werkzeug.security import check_password_hash, generate_password_hash
    if not check_password_hash(user_row['password_hash'], current_pwd):
        return jsonify({"success": False, "field": "currentPassword", "message": "Current password is incorrect"})
        
    if len(new_pwd) < 8:
        return jsonify({"success": False, "field": "newPassword", "message": "Password must be at least 8 characters"})
        
    import re
    if not re.search(r'[A-Z]', new_pwd) or not re.search(r'[a-z]', new_pwd) or not re.search(r'[0-9]', new_pwd):
        return jsonify({"success": False, "field": "newPassword", "message": "Password must contain at least 1 uppercase, 1 lowercase, and 1 number"})
        
    if new_pwd != confirm_pwd:
        return jsonify({"success": False, "field": "confirmPassword", "message": "Passwords do not match"})
        
    if new_pwd == current_pwd:
        return jsonify({"success": False, "field": "newPassword", "message": "New password cannot be the same as current password"})
        
    from werkzeug.security import generate_password_hash
    db.execute('UPDATE users SET password_hash = ?, updated_at = ? WHERE id = ?', 
               (generate_password_hash(new_pwd), datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'), current_user.id))
               
    db.execute('''
        INSERT INTO activity_logs (user_id, action_type, details, ip_address)
        VALUES (?, 'UPDATE_USER', 'Password changed', ?)
    ''', (current_user.id, request.remote_addr))
    db.commit()
    
    return jsonify({"success": True, "message": "Password changed successfully"})

@app.route('/profile/update-preferences', methods=['POST'])
@login_required
def profile_update_preferences():
    data = request.json
    db = get_db_connection()
    
    # Cast to integers
    p = {
        'email_notifications': int(data.get('email_notifications', 1)),
        'email_critical_alerts': int(data.get('email_critical_alerts', 1)),
        'email_assignments': int(data.get('email_assignments', 1)),
        'email_correlation_alerts': int(data.get('email_correlation_alerts', 1)),
        'email_daily_summary': int(data.get('email_daily_summary', 1)),
        'in_app_alert_sound': int(data.get('in_app_alert_sound', 1)),
        'dark_mode': int(data.get('dark_mode', 0)),
        'items_per_page': int(data.get('items_per_page', 25))
    }
    
    row = db.execute("SELECT id FROM user_preferences WHERE user_id = ?", (current_user.id,)).fetchone()
    if row:
        db.execute('''
            UPDATE user_preferences SET 
                email_notifications=?, email_critical_alerts=?, email_assignments=?,
                email_correlation_alerts=?, email_daily_summary=?, in_app_alert_sound=?,
                dark_mode=?, items_per_page=?
            WHERE user_id=?
        ''', (p['email_notifications'], p['email_critical_alerts'], p['email_assignments'], 
              p['email_correlation_alerts'], p['email_daily_summary'], p['in_app_alert_sound'], 
              p['dark_mode'], p['items_per_page'], current_user.id))
    else:
        db.execute('''
            INSERT INTO user_preferences 
            (user_id, email_notifications, email_critical_alerts, email_assignments, 
             email_correlation_alerts, email_daily_summary, in_app_alert_sound, 
             dark_mode, items_per_page)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (current_user.id, p['email_notifications'], p['email_critical_alerts'], p['email_assignments'], 
              p['email_correlation_alerts'], p['email_daily_summary'], p['in_app_alert_sound'], 
              p['dark_mode'], p['items_per_page']))
              
    db.commit()
    return jsonify({"success": True})

@app.route('/profile/update-avatar-color', methods=['POST'])
@login_required
def profile_update_avatar_color():
    color = request.json.get('avatar_color', '#2563eb')
    import re
    if not re.match(r'^#[a-fA-F0-9]{6}$', color):
        return jsonify({"success": False, "message": "Invalid color format"})
        
    db = get_db_connection()
    try:
        db.execute('ALTER TABLE users ADD COLUMN avatar_color TEXT DEFAULT "#2563eb"')
        db.commit()
    except:
        pass # Column already exists
        
    db.execute('UPDATE users SET avatar_color = ? WHERE id = ?', (color, current_user.id))
    db.commit()
    
    current_user.avatar_color = color
    return jsonify({"success": True})

@app.route('/health')
def health_check():
    db_status = "connected"
    tables = {}
    try:
        db = get_db_connection()
        tables['users'] = db.execute('SELECT COUNT(*) as c FROM users').fetchone()['c']
        tables['incidents'] = db.execute('SELECT COUNT(*) as c FROM incidents').fetchone()['c']
        tables['clusters'] = db.execute('SELECT COUNT(*) as c FROM incident_clusters').fetchone()['c']
        tables['alerts'] = db.execute('SELECT COUNT(*) as c FROM alerts').fetchone()['c']
    except Exception as e:
        db_status = "error"
        app.logger.error(f'Database health check failed: {str(e)}')
        
    return jsonify({
        "status": "healthy",
        "app": APP_NAME,
        "version": APP_VERSION,
        "database": db_status,
        "tables": tables
    })

@app.route('/admin/system-info')
@login_required
def system_info():
    if current_user.role != 'Admin':
        return jsonify({"error": "Unauthorized"}), 403
        
    try:
        db = get_db_connection()
        total_inc = db.execute('SELECT COUNT(*) as c FROM incidents').fetchone()['c']
        total_usr = db.execute('SELECT COUNT(*) as c FROM users').fetchone()['c']
        total_clst = db.execute('SELECT COUNT(*) as c FROM incident_clusters').fetchone()['c']
        total_alrt = db.execute('SELECT COUNT(*) as c FROM alerts').fetchone()['c']
        total_logs = db.execute('SELECT COUNT(*) as c FROM activity_logs').fetchone()['c']
        
        # Get settings
        settings_rows = db.execute("SELECT setting_key, setting_value FROM settings").fetchall()
        st = {r['setting_key']: r['setting_value'] for r in settings_rows}
        
        db_size = 0
        if os.path.exists('cyberir.db'):
            db_size = os.path.getsize('cyberir.db') // 1024
            
        return jsonify({
            "database_size_kb": db_size,
            "total_incidents": total_inc,
            "total_users": total_usr,
            "total_clusters": total_clst,
            "total_alerts": total_alrt,
            "total_activity_logs": total_logs,
            "algorithms": {
                "correlation_threshold": float(st.get('correlation_threshold', 0.65)),
                "similarity_threshold": float(st.get('similarity_threshold', 0.50)),
                "correlation_window": int(st.get('correlation_window_hours', 48))
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()

if __name__ == '__main__':
    # Initialize DB if not exists
    if not os.path.exists('cyberir.db'):
        init_db(app)
        create_default_admin(app)
        print("Database initialized.")
            
    print("=" * 50)
    print("Starting CyberIR...")
    print("URL: http://localhost:5000")
    print("Admin: admin@cyberir.com")
    print("Password: Admin@1234")
    print("=" * 50)
    app.run(
        debug=True,
        host='0.0.0.0',
        port=5000,
        use_reloader=True
    )
