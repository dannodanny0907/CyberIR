# File: database.py - SQLite database connection and initialization utilities
import sqlite3
import os
from werkzeug.security import generate_password_hash
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, 'cyberir.db')

# Establish and return a row-factory configured SQLite connection
def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Create database tables and schema if they do not exist
def init_db():
    if not os.path.exists(DATABASE_PATH):
        with get_db_connection() as conn:
            with open(os.path.join(BASE_DIR, 'schema.sql'), 'r') as f:
                conn.executescript(f.read())
            conn.commit()

# Handle logic for get_next_incident_id
def get_next_incident_id():
    with get_db_connection() as conn:
        cursor = conn.execute("SELECT incident_id FROM incidents ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()
        if row:
            last_id_str = row['incident_id']
            try:
                last_num = int(last_id_str.split('-')[1])
                return f"INC-{last_num + 1:03d}"
            except Exception:
                return "INC-001"
        return "INC-001"

# Handle logic for get_next_cluster_id
def get_next_cluster_id():
    with get_db_connection() as conn:
        cursor = conn.execute("SELECT cluster_id FROM incident_clusters ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()
        if row:
            last_id_str = row['cluster_id']
            try:
                last_num = int(last_id_str.split('-')[1])
                return f"CLU-{last_num + 1:03d}"
            except Exception:
                return "CLU-001"
        return "CLU-001"

# Handle logic for create_default_admin
def create_default_admin():
    with get_db_connection() as conn:
        cursor = conn.execute("SELECT id FROM users WHERE email = 'admin@cyberir.com'")
        if not cursor.fetchone():
            password_hash = generate_password_hash("Admin@1234")
            conn.execute('''
                INSERT INTO users (full_name, email, password_hash, role, has_admin_privileges, is_active)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', ("System Administrator", "admin@cyberir.com", password_hash, "Admin", 1, 1))
            conn.commit()
