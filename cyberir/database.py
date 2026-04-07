import sqlite3
from flask import g
from werkzeug.security import generate_password_hash

DATABASE = 'cyberir.db'

def get_db_connection():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

def init_db(app):
    with app.app_context():
        db = get_db_connection()
        with open('schema.sql', 'r', encoding='utf-8') as f:
            db.cursor().executescript(f.read())
        db.commit()

def get_next_incident_id():
    db = get_db_connection()
    cursor = db.cursor()
    # Get the prefix from settings if exists, else 'INC-'
    cursor.execute("SELECT setting_value FROM settings WHERE setting_key = 'incident_id_prefix'")
    row = cursor.fetchone()
    prefix = row['setting_value'] if row else 'INC-'
    
    cursor.execute("SELECT incident_id FROM incidents ORDER BY id DESC LIMIT 1")
    last_id = cursor.fetchone()
    
    if last_id:
        try:
            num = int(last_id['incident_id'].replace(prefix, ''))
            return f"{prefix}{num + 1:03d}"
        except:
            pass
    return f"{prefix}001"

def get_next_cluster_id():
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("SELECT cluster_id FROM incident_clusters ORDER BY id DESC LIMIT 1")
    last_id = cursor.fetchone()
    
    if last_id:
        try:
            num = int(last_id['cluster_id'].replace('CLU-', ''))
            return f"CLU-{num + 1:03d}"
        except:
            pass
    return "CLU-001"

def create_default_admin(app):
    with app.app_context():
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM users")
        row = cursor.fetchone()
        
        if row['count'] == 0:
            password_hash = generate_password_hash("Admin@1234")
            cursor.execute('''
                INSERT INTO users (full_name, email, password_hash, role, has_admin_privileges, is_active)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', ("System Administrator", "admin@cyberir.com", password_hash, "Admin", 1, 1))
            db.commit()
