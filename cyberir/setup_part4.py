import os, re

base_dir = r"c:\Users\PDM\Pictures\CYBER\cyberir"
app_path = os.path.join(base_dir, "backend", "app.py")

with open(app_path, "r", encoding="utf-8") as f:
    text = f.read()

# 1. Add sanitize_input helper if missing
sanitize_fn = """def sanitize_input(val, max_len):
    if not val: return ''
    return str(val).strip()[:max_len]

"""
if "def sanitize_input" not in text:
    text = text.replace("@app.context_processor", sanitize_fn + "@app.context_processor")


# 2. Update log_incident route
log_route_marker = "title = request.form.get('title','').strip()"

log_new_code = """title = request.form.get('title','').strip()
            
            # Contact Information
            contact_full_name = sanitize_input(request.form.get('contact_full_name'), 200)
            contact_job_title = sanitize_input(request.form.get('contact_job_title'), 200)
            contact_office = sanitize_input(request.form.get('contact_office'), 200)
            contact_work_phone = sanitize_input(request.form.get('contact_work_phone'), 50)
            contact_mobile_phone = sanitize_input(request.form.get('contact_mobile_phone'), 50)
            contact_additional = sanitize_input(request.form.get('contact_additional'), 500)
            
            # Detection Method
            detection_method = sanitize_input(request.form.get('detection_method'), 100)
            detection_method_other = sanitize_input(request.form.get('detection_method_other'), 200)
            
            # Incident Type
            incident_type_list = request.form.getlist('incident_type')
            incident_type = ', '.join(incident_type_list) if incident_type_list else ''
            incident_type_other = sanitize_input(request.form.get('incident_type_other'), 200)
"""

if "# Contact Information" not in text:
    # Let's replace the first occurrence of title=... for log_incident route
    # actually replace all occurrences of `incident_type = request.form.get('incident_type','')` 
    # to avoid double replacing incident_type
    
    text = re.sub(
        r"title = request\.form\.get\('title',''\)\.strip\(\)\n\s*incident_type = request\.form\.get\('incident_type',''\)",
        log_new_code.strip() + "\n",
        text
    )

# Now update the INSERT statement in log_incident.
# Old: "INSERT INTO incidents (incident_id,title,description,incident_type,affected_asset,affected_department,users_affected,ip_address,attack_indicators,asset_criticality,threat_severity,vulnerability_exposure,is_repeat,risk_score,severity,status,assigned_to,reported_date,resolution_notes,created_by,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,'Open',?,?,?,?,datetime('now'),datetime('now'))", (incident_id,title,description,incident_type,affected_asset,affected_department,users_affected,ip_address,attack_indicators,asset_criticality,threat_severity,vulnerability_exposure,is_repeat,risk_score,severity,assigned_to,reported_date,resolution_notes,current_user.id)

insert_sql_old = '"INSERT INTO incidents (incident_id,title,description,incident_type,affected_asset,affected_department,users_affected,ip_address,attack_indicators,asset_criticality,threat_severity,vulnerability_exposure,is_repeat,risk_score,severity,status,assigned_to,reported_date,resolution_notes,created_by,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,\'Open\',?,?,?,?,datetime(\'now\'),datetime(\'now\'))"'
insert_tup_old = '(incident_id,title,description,incident_type,affected_asset,affected_department,users_affected,ip_address,attack_indicators,asset_criticality,threat_severity,vulnerability_exposure,is_repeat,risk_score,severity,assigned_to,reported_date,resolution_notes,current_user.id)'

insert_sql_new = '"INSERT INTO incidents (incident_id,title,description,incident_type,affected_asset,affected_department,users_affected,ip_address,attack_indicators,asset_criticality,threat_severity,vulnerability_exposure,is_repeat,risk_score,severity,status,assigned_to,reported_date,resolution_notes,created_by,created_at,updated_at, contact_full_name, contact_job_title, contact_office, contact_work_phone, contact_mobile_phone, contact_additional, detection_method, detection_method_other, incident_type_other) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,\'Open\',?,?,?,?,datetime(\'now\'),datetime(\'now\'), ?, ?, ?, ?, ?, ?, ?, ?, ?)"'
insert_tup_new = '(incident_id,title,description,incident_type,affected_asset,affected_department,users_affected,ip_address,attack_indicators,asset_criticality,threat_severity,vulnerability_exposure,is_repeat,risk_score,severity,assigned_to,reported_date,resolution_notes,current_user.id, contact_full_name, contact_job_title, contact_office, contact_work_phone, contact_mobile_phone, contact_additional, detection_method, detection_method_other, incident_type_other)'

text = text.replace(insert_sql_old, insert_sql_new)
text = text.replace(insert_tup_old, insert_tup_new)


# Now update the UPDATE statement in edit_incident.
update_sql_old = '"UPDATE incidents SET title=?,description=?,incident_type=?,affected_asset=?,affected_department=?,users_affected=?,ip_address=?,attack_indicators=?,asset_criticality=?,threat_severity=?,vulnerability_exposure=?,is_repeat=?,risk_score=?,severity=?,assigned_to=?,reported_date=?,updated_at=datetime(\'now\'),updated_by=? WHERE incident_id=?"'
update_tup_old = '(title,description,incident_type,affected_asset,affected_department,users_affected,ip_address,attack_indicators,asset_criticality,threat_severity,vulnerability_exposure,is_repeat,risk_score,severity,assigned_to,reported_date,current_user.id,incident_id)'

update_sql_new = '"UPDATE incidents SET title=?,description=?,incident_type=?,affected_asset=?,affected_department=?,users_affected=?,ip_address=?,attack_indicators=?,asset_criticality=?,threat_severity=?,vulnerability_exposure=?,is_repeat=?,risk_score=?,severity=?,assigned_to=?,reported_date=?,updated_at=datetime(\'now\'),updated_by=?, contact_full_name=?, contact_job_title=?, contact_office=?, contact_work_phone=?, contact_mobile_phone=?, contact_additional=?, detection_method=?, detection_method_other=?, incident_type_other=? WHERE incident_id=?"'
update_tup_new = '(title,description,incident_type,affected_asset,affected_department,users_affected,ip_address,attack_indicators,asset_criticality,threat_severity,vulnerability_exposure,is_repeat,risk_score,severity,assigned_to,reported_date,current_user.id, contact_full_name, contact_job_title, contact_office, contact_work_phone, contact_mobile_phone, contact_additional, detection_method, detection_method_other, incident_type_other, incident_id)'

text = text.replace(update_sql_old, update_sql_new)
text = text.replace(update_tup_old, update_tup_new)

with open(app_path, "w", encoding="utf-8") as f:
    f.write(text)

print("app.py updated.")
