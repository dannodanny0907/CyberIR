import os
from flask import Flask, redirect, url_for, render_template
from flask_login import LoginManager, current_user, login_required
from database import init_db, create_default_admin, get_db_connection
from auth import auth_bp, User

app = Flask(__name__)
app.secret_key = 'cyberir_super_secret_key'

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    user_row = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    if user_row:
        return User(
            id=user_row['id'],
            full_name=user_row['full_name'],
            email=user_row['email'],
            role=user_row['role'],
            has_admin_privileges=user_row['has_admin_privileges'],
            is_active=user_row['is_active']
        )
    return None

app.register_blueprint(auth_bp, url_prefix='')

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('auth.login'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

if __name__ == '__main__':
    with app.app_context():
        init_db()
        create_default_admin()
    app.run(port=5000, debug=True)
