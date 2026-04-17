import os, re

backend_dir = r"c:\Users\PDM\Pictures\CYBER\cyberir\backend"
app_path = os.path.join(backend_dir, "app.py")

with open(app_path, "r", encoding="utf-8") as f:
    code = f.read()

# 1. Replace labels
replacements = {
    "'Critical'": "'Catastrophic'",
    '"Critical"': '"Catastrophic"',
    "'High'": "'Major'",
    '"High"': '"Major"',
    "'Medium'": "'Moderate'",
    '"Medium"': '"Moderate"',
    "'Low'": "'Minor'",
    '"Low"': '"Minor"'
}

for k, v in replacements.items():
    code = code.replace(k, v)

# 2. Rename priority to severity for variable assignments safely.
# For log_incident:
code = code.replace("priority = ('Catastrophic'", "severity = ('Catastrophic'")
code = code.replace(",priority,", ",severity,")
code = code.replace(",priority)", ",severity)")
code = code.replace("priority_filter", "severity_filter")
code = code.replace("incidents_by_priority", "incidents_by_severity")
code = code.replace("request.args.get('priority'", "request.args.get('severity'")
code = code.replace("sort == 'priority'", "sort == 'severity'")
code = code.replace("d['priority']", "d['severity']")
code = code.replace("incident['priority']", "incident['severity']")


# 3. Add escalation logic to log_incident (specifically where it creates incident)

# In log_incident, the line is:
# new_id = cursor.lastrowid
# conn.execute("INSERT INTO activity_logs ...", [current_user.id,new_id,f"Created new incident {incident_id}: {title}"])

escalation_logic = """new_id = cursor.lastrowid
            conn.execute("INSERT INTO activity_logs (user_id,action_type,target_type,target_id,details) VALUES (?,'CREATE_INCIDENT','Incident',?,?)",[current_user.id,new_id,f"Created new incident {incident_id}: {title}"])
            
            if severity in ['Major', 'Catastrophic']:
                conn.execute('UPDATE incidents SET escalated_to_cirt = 1 WHERE id = ?', [new_id])
                cirt_users = conn.execute("SELECT id FROM users WHERE role = 'CIRT' AND is_active = 1").fetchall()
                for cirt_user in cirt_users:
                    conn.execute(
                        '''INSERT INTO alerts
                           (alert_type, severity, message, incident_id, recipient_id, is_read)
                           VALUES (?,?,?,?,?,0)''',
                        ('ESCALATION', 'CRITICAL', f'Incident {incident_id} has been escalated to CIRT — Severity: {severity}', new_id, cirt_user['id'])
                    )"""

code = code.replace('new_id = cursor.lastrowid\n            conn.execute("INSERT INTO activity_logs (user_id,action_type,target_type,target_id,details) VALUES (?,\'CREATE_INCIDENT\',\'Incident\',?,?)",[current_user.id,new_id,f"Created new incident {incident_id}: {title}"])', escalation_logic)

with open(app_path, "w", encoding="utf-8") as f:
    f.write(code)


# correlation_engine.py
cor_path = os.path.join(backend_dir, "correlation_engine.py")
if os.path.exists(cor_path):
    with open(cor_path, "r", encoding="utf-8") as f:
        ccode = f.read()
    for k, v in replacements.items():
        ccode = ccode.replace(k, v)
    
    # Where severity is derived from priority in clusters
    ccode = ccode.replace("d['priority']", "d['severity']")
    ccode = ccode.replace("incident['priority']", "incident['severity']")
    with open(cor_path, "w", encoding="utf-8") as f:
        f.write(ccode)

# similarity_engine.py
sim_path = os.path.join(backend_dir, "similarity_engine.py")
if os.path.exists(sim_path):
    with open(sim_path, "r", encoding="utf-8") as f:
        scode = f.read()
    for k, v in replacements.items():
        scode = scode.replace(k, v)

    scode = scode.replace("d['priority']", "d['severity']")
    scode = scode.replace("incident['priority']", "incident['severity']")
    with open(sim_path, "w", encoding="utf-8") as f:
        f.write(scode)

print("done")
