# File: auth.py - Authentication and user login management system
from flask import (Blueprint, render_template,
    redirect, url_for, flash, request, session)
from flask_login import (LoginManager, login_user,
    logout_user, login_required, UserMixin,
    current_user)
from werkzeug.security import (
    check_password_hash, generate_password_hash)
from database import get_db_connection

login_manager = LoginManager()
auth = Blueprint('auth', __name__)

class User(UserMixin):
    # Handle logic for __init__
    def __init__(self, id, full_name, email,
                 role, has_admin_privileges,
                 active, avatar_color=None):
        self.id = id
        self.full_name = full_name
        self.email = email
        self.role = role
        self.has_admin_privileges = has_admin_privileges
        self._active = active
        self.avatar_color = avatar_color or '#2563eb'

    @property
    # Handle logic for is_active
    def is_active(self):
        return bool(self._active)

@auth.route('/login', methods=['GET', 'POST'])
# Handle login form submission and session setup
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        conn = get_db_connection()
        user_row = conn.execute(
            'SELECT * FROM users WHERE email=?',
            [email]).fetchone()
        conn.close()
        if user_row and check_password_hash(
                user_row['password_hash'], password):
            if not user_row['is_active']:
                flash('Your account has been '
                    'deactivated. Contact admin.',
                    'error')
                return redirect(url_for('auth.login'))
            user = User(
                id=user_row['id'],
                full_name=user_row['full_name'],
                email=user_row['email'],
                role=user_row['role'],
                has_admin_privileges=user_row[
                    'has_admin_privileges'],
                active=user_row['is_active'],
                avatar_color=user_row['avatar_color']
                    if 'avatar_color' in 
                    user_row.keys() 
                    else '#2563eb'
            )
            login_user(user)
            conn2 = get_db_connection()
            conn2.execute(
                """UPDATE users SET 
                   last_login=datetime('now')
                   WHERE id=?""", [user.id])
            conn2.execute(
                """INSERT INTO activity_logs
                   (user_id, action_type)
                   VALUES (?, 'LOGIN')""",
                [user.id])
            conn2.commit()
            conn2.close()
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password.',
                'error')
    return render_template('login.html')

@auth.route('/logout')
@login_required
# Terminate user session and clear authentication cookies
def logout():
    try:
        conn = get_db_connection()
        conn.execute(
            "INSERT INTO activity_logs (user_id, action_type) VALUES (?, 'LOGOUT')",
            [current_user.id])
        conn.commit()
        conn.close()
    except:
        pass
    logout_user()
    return redirect(url_for('auth.login'))

@login_manager.user_loader
# Flask-Login callback to reload the user object from the user ID
def load_user(user_id):
    conn = get_db_connection()
    user_row = conn.execute(
        'SELECT * FROM users WHERE id=?',
        [user_id]).fetchone()
    conn.close()
    if not user_row:
        return None
    return User(
        id=user_row['id'],
        full_name=user_row['full_name'],
        email=user_row['email'],
        role=user_row['role'],
        has_admin_privileges=user_row[
            'has_admin_privileges'],
        active=user_row['is_active'],
        avatar_color=user_row['avatar_color']
            if 'avatar_color' in user_row.keys()
            else '#2563eb'
    )
