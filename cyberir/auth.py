from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from database import get_db_connection
from datetime import datetime

auth = Blueprint('auth', __name__)

class User(UserMixin):
    def __init__(self, id, full_name, email, role, has_admin_privileges, active, avatar_color):
        self.id = id
        self.full_name = full_name
        self.email = email
        self.role = role
        self.has_admin_privileges = has_admin_privileges
        self._active = active
        self.avatar_color = avatar_color

    @property
    def is_active(self):
        return bool(self._active)

def get_user_from_db(user_id):
    db = get_db_connection()
    user_row = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    if user_row:
        return User(
            id=user_row['id'],
            full_name=user_row['full_name'],
            email=user_row['email'],
            role=user_row['role'],
            has_admin_privileges=user_row['has_admin_privileges'],
            active=user_row['is_active'],
            avatar_color=user_row['avatar_color'] if 'avatar_color' in user_row.keys() and user_row['avatar_color'] else '#2563eb'
        )
    return None

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        db = get_db_connection()
        user_row = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        
        if user_row and check_password_hash(user_row['password_hash'], password):
            if not user_row['is_active']:
                flash('Your account has been deactivated. Contact admin.')
                return redirect(url_for('auth.login'))
                
            user = get_user_from_db(user_row['id'])
            login_user(user)
            
            # Update last_login timestamp and log action
            now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            ip_address = request.remote_addr
            
            db.execute('UPDATE users SET last_login = ? WHERE id = ?', (now, user.id))
            db.execute('''
                INSERT INTO activity_logs (user_id, action_type, details, ip_address)
                VALUES (?, ?, ?, ?)
            ''', (user.id, 'LOGIN', 'User logged in', ip_address))
            db.commit()
            
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password')
            
    return render_template('login.html')

@auth.route('/logout')
@login_required
def logout():
    db = get_db_connection()
    ip_address = request.remote_addr
    
    db.execute('''
        INSERT INTO activity_logs (user_id, action_type, details, ip_address)
        VALUES (?, ?, ?, ?)
    ''', (current_user.id, 'LOGOUT', 'User logged out', ip_address))
    db.commit()
    
    logout_user()
    return redirect(url_for('auth.login'))
