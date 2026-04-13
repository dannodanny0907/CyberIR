CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    phone_number TEXT,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('Admin', 'Analyst', 'Viewer')),
    has_admin_privileges BOOLEAN DEFAULT 0,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    created_by INTEGER REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS incidents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    incident_id TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    incident_type TEXT NOT NULL CHECK(incident_type IN ('Phishing','Malware','Data Breach','Ransomware','Unauthorized Access','DDoS','Insider Threat','Other')),
    affected_asset TEXT NOT NULL,
    affected_department TEXT,
    users_affected INTEGER DEFAULT 0,
    asset_criticality INTEGER CHECK(asset_criticality BETWEEN 1 AND 5),
    threat_severity INTEGER CHECK(threat_severity BETWEEN 1 AND 5),
    vulnerability_exposure INTEGER CHECK(vulnerability_exposure BETWEEN 1 AND 5),
    is_repeat BOOLEAN DEFAULT 0,
    risk_score REAL,
    priority TEXT CHECK(priority IN ('Critical','High','Medium','Low')),
    status TEXT DEFAULT 'Open' CHECK(status IN ('Open','Investigating','Resolved','Closed')),
    assigned_to INTEGER REFERENCES users(id),
    cluster_id TEXT,
    correlation_score REAL,
    similar_incident_id TEXT,
    similarity_score REAL,
    solution_applied_from TEXT,
    attack_indicators TEXT,
    ip_address TEXT,
    reported_date TIMESTAMP NOT NULL,
    investigating_started_date TIMESTAMP,
    resolved_date TIMESTAMP,
    closed_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolution_notes TEXT,
    resolution_time_minutes INTEGER,
    created_by INTEGER NOT NULL REFERENCES users(id),
    updated_by INTEGER REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS incident_clusters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cluster_id TEXT UNIQUE NOT NULL,
    cluster_name TEXT,
    incident_count INTEGER DEFAULT 0,
    primary_type TEXT,
    first_detected TIMESTAMP NOT NULL,
    last_updated TIMESTAMP,
    status TEXT DEFAULT 'Active' CHECK(status IN ('Active','Investigating','Resolved')),
    severity TEXT CHECK(severity IN ('Critical','High','Medium','Low')),
    assigned_to INTEGER REFERENCES users(id),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_type TEXT NOT NULL CHECK(alert_type IN ('HIGH_PRIORITY','CORRELATION','SIMILARITY','SLA_BREACH','ASSIGNMENT','ESCALATION','SYSTEM')),
    severity TEXT NOT NULL CHECK(severity IN ('CRITICAL','WARNING','INFO')),
    message TEXT NOT NULL,
    incident_id INTEGER REFERENCES incidents(id),
    cluster_id TEXT,
    recipient_id INTEGER REFERENCES users(id),
    recipient_role TEXT,
    is_read BOOLEAN DEFAULT 0,
    read_at TIMESTAMP,
    dismissed BOOLEAN DEFAULT 0,
    dismissed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS activity_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    action_type TEXT NOT NULL CHECK(action_type IN ('LOGIN','LOGOUT','CREATE_INCIDENT','UPDATE_INCIDENT','DELETE_INCIDENT','ASSIGN_INCIDENT','RESOLVE_INCIDENT','CREATE_USER','UPDATE_USER','DELETE_USER','UPDATE_SETTINGS')),
    target_type TEXT,
    target_id INTEGER,
    details TEXT,
    ip_address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    setting_key TEXT UNIQUE NOT NULL,
    setting_value TEXT NOT NULL,
    setting_type TEXT CHECK(setting_type IN ('string','integer','float','boolean')),
    updated_by INTEGER REFERENCES users(id),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT OR IGNORE INTO settings (setting_key, setting_value, setting_type) VALUES
('correlation_threshold','0.65','float'),
('correlation_time_window_hours','48','integer'),
('similarity_threshold','0.50','float'),
('similarity_result_limit','5','integer'),
('critical_sla_hours','4','integer'),
('high_sla_hours','24','integer'),
('medium_sla_hours','72','integer'),
('low_sla_hours','168','integer'),
('organization_name','CyberIR','string'),
('incident_id_prefix','INC-','string');

CREATE TABLE IF NOT EXISTS knowledge_base (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    incident_type TEXT,
    content TEXT NOT NULL,
    tags TEXT,
    source_incident_id TEXT,
    created_by INTEGER NOT NULL REFERENCES users(id),
    views INTEGER DEFAULT 0,
    helpful_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_preferences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE NOT NULL REFERENCES users(id),
    email_notifications BOOLEAN DEFAULT 1,
    email_critical_alerts BOOLEAN DEFAULT 1,
    email_assignments BOOLEAN DEFAULT 1,
    email_correlation_alerts BOOLEAN DEFAULT 1,
    email_daily_summary BOOLEAN DEFAULT 0,
    in_app_alert_sound BOOLEAN DEFAULT 1,
    dark_mode BOOLEAN DEFAULT 0,
    items_per_page INTEGER DEFAULT 25,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_incidents_status ON incidents(status);
CREATE INDEX IF NOT EXISTS idx_incidents_priority ON incidents(priority);
CREATE INDEX IF NOT EXISTS idx_incidents_cluster ON incidents(cluster_id);
CREATE INDEX IF NOT EXISTS idx_incidents_assigned ON incidents(assigned_to);
CREATE INDEX IF NOT EXISTS idx_incidents_reported_date ON incidents(reported_date);
CREATE INDEX IF NOT EXISTS idx_incidents_type ON incidents(incident_type);
CREATE INDEX IF NOT EXISTS idx_alerts_recipient ON alerts(recipient_id);
CREATE INDEX IF NOT EXISTS idx_alerts_unread ON alerts(is_read);
CREATE INDEX IF NOT EXISTS idx_activity_user ON activity_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_activity_date ON activity_logs(created_at);
