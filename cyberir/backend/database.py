# File: database.py - SQLite database connection and initialization utilities
import sqlite3
import os
from werkzeug.security import generate_password_hash
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, 'cyberir.db')

# Establish and return a row-factory configured SQLite connection
def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn

# Create database tables and schema if they do not exist
def init_db():
    with get_db_connection() as conn:
        with open(os.path.join(BASE_DIR, 'schema.sql'), 'r') as f:
            conn.executescript(f.read())
        conn.commit()

    # Add new columns safely (for existing databases)
    new_columns = [
        "detection_method TEXT",
        "detection_method_other TEXT",
        "contact_full_name TEXT",
        "contact_job_title TEXT",
        "contact_office TEXT",
        "contact_work_phone TEXT",
        "contact_mobile_phone TEXT",
        "contact_additional TEXT",
        "impact_selections TEXT",
        "impact_other TEXT",
        "impact_additional TEXT",
        "data_sensitivity_selections TEXT",
        "data_sensitivity_other TEXT",
        "data_sensitivity_additional TEXT",
        "detected_datetime TIMESTAMP",
        "incident_occurred_datetime TIMESTAMP",
        "attack_source TEXT",
        "affected_system_ips TEXT",
        "attack_source_ips TEXT",
        "affected_system_functions TEXT",
        "affected_system_os TEXT",
        "affected_system_location TEXT",
        "affected_system_security_software TEXT",
        "affected_systems_count INTEGER DEFAULT 1",
        "third_parties_involved TEXT",
        "incident_type_other TEXT",
        "escalated_to_cirt BOOLEAN DEFAULT 0",
        "cirt_status TEXT DEFAULT 'Assigned'",
        "cirt_resolution_notes TEXT",
        "cirt_resolved_date TIMESTAMP"
    ]
    
    with get_db_connection() as conn:
        for column in new_columns:
            try:
                conn.execute(f"ALTER TABLE incidents ADD COLUMN {column}")
            except sqlite3.OperationalError:
                pass # Column already exists
        conn.commit()

    # Remove outdated CHECK constraint on incident_type by recreating the table
    _remove_incident_type_check_constraint()

    create_default_settings()
    create_default_admin()


def _remove_incident_type_check_constraint():
    """Recreate incidents table without CHECK constraint on incident_type."""
    with get_db_connection() as conn:
        row = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='incidents'"
        ).fetchone()
        if not row or 'CHECK' not in (row['sql'] or ''):
            return

        cols = [c[1] for c in conn.execute('PRAGMA table_info(incidents)').fetchall()]
        col_list = ', '.join(cols)

        conn.execute('PRAGMA foreign_keys=OFF')
        conn.execute('DROP TABLE IF EXISTS incidents_backup')
        conn.execute(f'CREATE TABLE incidents_backup AS SELECT {col_list} FROM incidents')
        conn.execute('DROP TABLE incidents')

        # Remove CHECK(...) clauses handling nested parentheses
        create_sql = row['sql']
        import re
        # Match CHECK( ... ) with balanced parens (up to 2 levels deep)
        create_sql = re.sub(
            r',?\s*CHECK\s*\((?:[^()]*|\((?:[^()]*|\([^()]*\))*\))*\)',
            '', create_sql, flags=re.IGNORECASE
        )
        conn.execute(create_sql)

        conn.execute(f'INSERT INTO incidents ({col_list}) SELECT {col_list} FROM incidents_backup')
        conn.execute('DROP TABLE incidents_backup')
        conn.execute('PRAGMA foreign_keys=ON')
        conn.commit()


def create_default_settings():
    with get_db_connection() as conn:
        settings_to_insert = [
            ('pdf_cybersecurity_engineer', 'CHABVUTAGONDO .T.', 'string'),
            ('pdf_technical_services_manager', 'MUCHOVO .R.', 'string'),
            ('pdf_footer_address', 'Chinhoyi University of Technology - ICT Department, Private Bag 7724, Chinhoyi, Zimbabwe | +263 67 2127433 | Cybersecurity Office: Ext 1175', 'string')
        ]
        for key, value, s_type in settings_to_insert:
            conn.execute('''
                INSERT OR IGNORE INTO settings (setting_key, setting_value, setting_type)
                VALUES (?, ?, ?)
            ''', (key, value, s_type))
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
