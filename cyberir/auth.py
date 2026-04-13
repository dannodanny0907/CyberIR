from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from database import get_db_connection
from datetime import datetime
import datetime as dt

auth_bp = Blueprint('auth', __name__)

class User(UserMixin):
    def __init__(self, id, full_name, email, role, has_admin_privileges, is_active):
        self.id = id
        self.full_name = full_name
        self.email = email
        self.role = role
        self.has_admin_privileges = has_admin_privileges
        self.is_active = is_active

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        with get_db_connection() as conn:
            user_row = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()

            if user_row and check_password_hash(user_row['password_hash'], password):
                if user_row['is_active'] == 1:
                    user = User(
                        id=user_row['id'],
                        full_name=user_row['full_name'],
                        email=user_row['email'],
                        role=user_row['role'],
                        has_admin_privileges=user_row['has_admin_privileges'],
                        is_active=user_row['is_active']
                    )
                    login_user(user)

                    # Update last login
                    current_time = dt.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
                    conn.execute('UPDATE users SET last_login = ? WHERE id = ?', (current_time, user.id))
                    
                    # Log activity
                    ip_address = request.remote_addr
                    conn.execute(
                        'INSERT INTO activity_logs (user_id, action_type, details, ip_address) VALUES (?, ?, ?, ?)',
                        (user.id, 'LOGIN', 'User logged in', ip_address)
                    )
                    conn.commit()

                    return redirect(url_for('dashboard'))
                else:
                    flash('Your account has been deactivated. Contact admin.', 'error')
            else:
                flash('Invalid email or password', 'error')

    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    with get_db_connection() as conn:
        ip_address = request.remote_addr
        conn.execute(
            'INSERT INTO activity_logs (user_id, action_type, details, ip_address) VALUES (?, ?, ?, ?)',
            (current_user.id, 'LOGOUT', 'User logged out', ip_address)
        )
        conn.commit()
    
    logout_user()
    return redirect(url_for('auth.login'))
