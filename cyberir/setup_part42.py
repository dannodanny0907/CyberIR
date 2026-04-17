import os, re

base_dir = r"c:\Users\PDM\Pictures\CYBER\cyberir"
frontend_dir = os.path.join(base_dir, "frontend")
backend_dir = os.path.join(base_dir, "backend")

# HTML snippets for edit_incident.html
impact_html = """
        <!-- Section: Impact of Incident -->
        <div class="card">
            <div class="section-header">
                💥 3. Impact of Incident
            </div>
            <div class="form-grid">
                <div>
                    <label class="form-label" for="impact_selections">Impact of Incident</label>
                    <select name="impact_selections" id="impact_selections" multiple size="5" class="multi-select-field">
                        <option value="Loss of access to services" {% if 'Loss of access to services' in (incident.impact_selections or '') %}selected{% endif %}>Loss of access to services</option>
                        <option value="Loss of productivity" {% if 'Loss of productivity' in (incident.impact_selections or '') %}selected{% endif %}>Loss of productivity</option>
                        <option value="Loss of reputation" {% if 'Loss of reputation' in (incident.impact_selections or '') %}selected{% endif %}>Loss of reputation</option>
                        <option value="Loss of revenue" {% if 'Loss of revenue' in (incident.impact_selections or '') %}selected{% endif %}>Loss of revenue</option>
                        <option value="Propagation to other networks" {% if 'Propagation to other networks' in (incident.impact_selections or '') %}selected{% endif %}>Propagation to other networks</option>
                        <option value="Unauthorized disclosure of data/information" {% if 'Unauthorized disclosure of data/information' in (incident.impact_selections or '') %}selected{% endif %}>Unauthorized disclosure of data/information</option>
                        <option value="Unauthorized modification of data/information" {% if 'Unauthorized modification of data/information' in (incident.impact_selections or '') %}selected{% endif %}>Unauthorized modification of data/information</option>
                        <option value="Unknown/Other" {% if 'Unknown/Other' in (incident.impact_selections or '') %}selected{% endif %}>Unknown/Other</option>
                    </select>
                    <div class="multi-select-hint">Hold Ctrl (Windows) or Cmd (Mac) to select multiple</div>
                    <div id="impact_other_container" class="other-input-container {% if 'Unknown/Other' in (incident.impact_selections or '') %}visible{% endif %}">
                        <label class="form-label" for="impact_other">Please specify impact</label>
                        <input type="text" id="impact_other" name="impact_other" class="form-input" placeholder="Describe the impact" value="{{ incident.impact_other or '' }}">
                    </div>
                </div>
                <div class="full-width">
                    <label class="form-label" for="impact_additional">Additional Impact Information</label>
                    <textarea id="impact_additional" name="impact_additional" class="form-input" rows="3" placeholder="Any additional information about the impact of this incident...">{{ incident.impact_additional or '' }}</textarea>
                </div>
            </div>
        </div>
"""

data_sensitivity_html = """
                <div class="full-width" style="margin-top: 15px;">
                    <div style="font-size: 1rem; font-weight: 600; color: var(--text-dark); margin-bottom: 10px; border-bottom: 1px solid var(--border-color); padding-bottom: 5px;">
                        4. Sensitivity of Affected Data/Information
                    </div>
                    <div class="form-grid">
                        <div>
                            <label class="form-label" for="data_sensitivity_selections">Type of Sensitive Data Affected</label>
                            <select name="data_sensitivity_selections" id="data_sensitivity_selections" multiple size="5" class="multi-select-field">
                                <option value="Confidential/Sensitive data/info" {% if 'Confidential/Sensitive data/info' in (incident.data_sensitivity_selections or '') %}selected{% endif %}>Confidential/Sensitive data/info</option>
                                <option value="Personally Identifiable Information (PII)" {% if 'Personally Identifiable Information (PII)' in (incident.data_sensitivity_selections or '') %}selected{% endif %}>Personally Identifiable Information (PII)</option>
                                <option value="Non-sensitive data/info" {% if 'Non-sensitive data/info' in (incident.data_sensitivity_selections or '') %}selected{% endif %}>Non-sensitive data/info</option>
                                <option value="IP/Copyrighted data/info" {% if 'IP/Copyrighted data/info' in (incident.data_sensitivity_selections or '') %}selected{% endif %}>IP/Copyrighted data/info</option>
                                <option value="Publicly available data/info" {% if 'Publicly available data/info' in (incident.data_sensitivity_selections or '') %}selected{% endif %}>Publicly available data/info</option>
                                <option value="Critical infrastructure" {% if 'Critical infrastructure' in (incident.data_sensitivity_selections or '') %}selected{% endif %}>Critical infrastructure</option>
                                <option value="Financial data/info" {% if 'Financial data/info' in (incident.data_sensitivity_selections or '') %}selected{% endif %}>Financial data/info</option>
                                <option value="Unknown/Other" {% if 'Unknown/Other' in (incident.data_sensitivity_selections or '') %}selected{% endif %}>Unknown/Other</option>
                            </select>
                            <div class="multi-select-hint">Hold Ctrl (Windows) or Cmd (Mac) to select multiple</div>
                            <div id="data_sensitivity_other_container" class="other-input-container {% if 'Unknown/Other' in (incident.data_sensitivity_selections or '') %}visible{% endif %}">
                                <label class="form-label" for="data_sensitivity_other">Please specify data type</label>
                                <input type="text" id="data_sensitivity_other" name="data_sensitivity_other" class="form-input" placeholder="Describe the type of data" value="{{ incident.data_sensitivity_other or '' }}">
                            </div>
                        </div>
                        <div class="full-width">
                            <label class="form-label" for="data_sensitivity_additional">Additional Affected Data Information</label>
                            <textarea id="data_sensitivity_additional" name="data_sensitivity_additional" class="form-input" rows="2" placeholder="Any additional information about the affected data...">{{ incident.data_sensitivity_additional or '' }}</textarea>
                        </div>
                    </div>
                </div>
"""

systems_affected_html = """
        <!-- Section: Systems Affected by Incident -->
        <div class="card">
            <div class="section-header">
                🖥️ 5. Systems Affected by Incident
            </div>
            <div class="form-grid">
                <div>
                    <label class="form-label" for="detected_datetime">Date/Time First Detected</label>
                    <input type="datetime-local" id="detected_datetime" name="detected_datetime" class="form-input" value="{{ incident.detected_datetime or '' }}">
                </div>
                <div>
                    <label class="form-label" for="incident_occurred_datetime">Date/Time Incident Occurred (estimate if unknown)</label>
                    <input type="datetime-local" id="incident_occurred_datetime" name="incident_occurred_datetime" class="form-input" value="{{ incident.incident_occurred_datetime or '' }}">
                </div>
                
                <div class="full-width">
                    <label class="form-label">Attack Source</label>
                    <div class="attack-source-group">
                        <label class="attack-source-label">
                            <input type="radio" name="attack_source" value="Internal" class="attack-source-radio" {% if incident.attack_source == 'Internal' %}checked{% endif %}>
                            <div class="attack-source-btn" {% if incident.attack_source == 'Internal' %}style="background: var(--primary); color: white; border-color: var(--primary);"{% endif %}>Internal</div>
                        </label>
                        <label class="attack-source-label">
                            <input type="radio" name="attack_source" value="External" class="attack-source-radio" {% if incident.attack_source == 'External' %}checked{% endif %}>
                            <div class="attack-source-btn" {% if incident.attack_source == 'External' %}style="background: var(--primary); color: white; border-color: var(--primary);"{% endif %}>External</div>
                        </label>
                        <label class="attack-source-label">
                            <input type="radio" name="attack_source" value="Both" class="attack-source-radio" {% if incident.attack_source == 'Both' %}checked{% endif %}>
                            <div class="attack-source-btn" {% if incident.attack_source == 'Both' %}style="background: var(--primary); color: white; border-color: var(--primary);"{% endif %}>Both</div>
                        </label>
                    </div>
                </div>

                <div class="full-width">
                    <label class="form-label" for="affected_system_ips">IP Address/es of Affected System/s</label>
                    <input type="text" id="affected_system_ips" name="affected_system_ips" class="form-input" placeholder="e.g. 192.168.1.10, 192.168.1.11" value="{{ incident.affected_system_ips or '' }}">
                    <div class="multi-select-hint">Comma-separated if multiple</div>
                </div>
                
                <div class="full-width">
                    <label class="form-label" for="attack_source_ips">Attack Sources IP Address/es</label>
                    <input type="text" id="attack_source_ips" name="attack_source_ips" class="form-input" placeholder="e.g. 185.220.101.45" value="{{ incident.attack_source_ips or '' }}">
                    <div class="multi-select-hint">Comma-separated if multiple</div>
                </div>

                <div>
                    <label class="form-label" for="affected_system_functions">Functions of Affected System/s</label>
                    <input type="text" id="affected_system_functions" name="affected_system_functions" class="form-input" placeholder="e.g. Web server, Database, Email server" value="{{ incident.affected_system_functions or '' }}">
                </div>
                <div>
                    <label class="form-label" for="affected_system_os">OS of Affected System/s</label>
                    <input type="text" id="affected_system_os" name="affected_system_os" class="form-input" placeholder="e.g. Ubuntu 22.04, Windows Server 2019" value="{{ incident.affected_system_os or '' }}">
                </div>

                <div>
                    <label class="form-label" for="affected_system_location">Physical Location of Affected System</label>
                    <input type="text" id="affected_system_location" name="affected_system_location" class="form-input" placeholder="e.g. Data Center, ICT Building Room 105" value="{{ incident.affected_system_location or '' }}">
                </div>
                <div>
                    <label class="form-label" for="affected_system_security_software">Security Software Loaded on Affected System</label>
                    <input type="text" id="affected_system_security_software" name="affected_system_security_software" class="form-input" placeholder="e.g. CrowdStrike Falcon, McAfee" value="{{ incident.affected_system_security_software or '' }}">
                </div>

                <div>
                    <label class="form-label" for="affected_systems_count">Estimated Quantity of Systems Affected</label>
                    <input type="number" id="affected_systems_count" name="affected_systems_count" class="form-input" min="1" placeholder="Number of systems" value="{{ incident.affected_systems_count or '' }}">
                </div>
                <div>
                    <label class="form-label" for="third_parties_involved">Third Parties Involved or Affected</label>
                    <input type="text" id="third_parties_involved" name="third_parties_involved" class="form-input" placeholder="e.g. Cloud provider, vendor name" value="{{ incident.third_parties_involved or '' }}">
                </div>
            </div>
        </div>
"""

# Modify edit_incident.html
edit_file = os.path.join(frontend_dir, "templates", "edit_incident.html")
if os.path.exists(edit_file):
    with open(edit_file, "r", encoding="utf-8") as f:
        html = f.read()

    # 1. Insert impact_html AFTER Incident Details card
    # Same logic as log_incident.html script
    html = html.replace('        <!-- Section 2 -->\n        <div class="card">\n            <div class="section-header">\n                🖥️ Affected Resources', impact_html + '\n        <!-- Section 2 -->\n        <div class="card">\n            <div class="section-header">\n                🖥️ Affected Resources')

    # 2. Insert data_sensitivity_html INSIDE Affected Resources
    html = html.replace('</textarea>\n                </div>\n            </div>\n        </div>', '</textarea>\n                </div>\n' + data_sensitivity_html + '            </div>\n        </div>')

    # 3. Insert systems_affected_html AFTER Affected Resources and BEFORE Risk Assessment
    html = html.replace('        <!-- Section 3 -->\n        <div class="card">\n            <div class="section-header">\n                ⚠️ Risk Assessment', systems_affected_html + '\n        <!-- Section 3 -->\n        <div class="card">\n            <div class="section-header">\n                ⚠️ Risk Assessment')

    with open(edit_file, "w", encoding="utf-8") as f:
        f.write(html)
    print("edit_html updated")

# Modify app.py
app_py = os.path.join(backend_dir, "app.py")
with open(app_py, "r", encoding="utf-8") as f:
    app_text = f.read()

app_new_fields = """            # Impact of Incident
            impact_list = request.form.getlist('impact_selections')
            impact_selections = ', '.join(impact_list) if impact_list else None
            impact_other = sanitize_input(request.form.get('impact_other'), 200)
            impact_additional = sanitize_input(request.form.get('impact_additional'), 1000)

            # Data Sensitivity
            sensitivity_list = request.form.getlist('data_sensitivity_selections')
            data_sensitivity_selections = ', '.join(sensitivity_list) if sensitivity_list else None
            data_sensitivity_other = sanitize_input(request.form.get('data_sensitivity_other'), 200)
            data_sensitivity_additional = sanitize_input(request.form.get('data_sensitivity_additional'), 1000)

            # Systems Affected
            detected_datetime = request.form.get('detected_datetime') or None
            incident_occurred_datetime = request.form.get('incident_occurred_datetime') or None
            attack_source = sanitize_input(request.form.get('attack_source'), 20)
            affected_system_ips = sanitize_input(request.form.get('affected_system_ips'), 500)
            attack_source_ips = sanitize_input(request.form.get('attack_source_ips'), 500)
            affected_system_functions = sanitize_input(request.form.get('affected_system_functions'), 500)
            affected_system_os = sanitize_input(request.form.get('affected_system_os'), 500)
            affected_system_location = sanitize_input(request.form.get('affected_system_location'), 500)
            affected_system_security_software = sanitize_input(request.form.get('affected_system_security_software'), 500)
            affected_systems_count_val = request.form.get('affected_systems_count')
            affected_systems_count = int(affected_systems_count_val) if affected_systems_count_val and affected_systems_count_val.isdigit() else None
            third_parties_involved = sanitize_input(request.form.get('third_parties_involved'), 500)
"""

if "# Impact of Incident" not in app_text:
    app_text = app_text.replace(
        "            incident_type_other = sanitize_input(request.form.get('incident_type_other'), 200)\n",
        "            incident_type_other = sanitize_input(request.form.get('incident_type_other'), 200)\n\n" + app_new_fields
    )

insert_sql_old = '"INSERT INTO incidents (incident_id,title,description,incident_type,affected_asset,affected_department,users_affected,ip_address,attack_indicators,asset_criticality,threat_severity,vulnerability_exposure,is_repeat,risk_score,severity,status,assigned_to,reported_date,resolution_notes,created_by,created_at,updated_at, contact_full_name, contact_job_title, contact_office, contact_work_phone, contact_mobile_phone, contact_additional, detection_method, detection_method_other, incident_type_other) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,\'Open\',?,?,?,?,datetime(\'now\'),datetime(\'now\'), ?, ?, ?, ?, ?, ?, ?, ?, ?)"'
insert_tup_old = '(incident_id,title,description,incident_type,affected_asset,affected_department,users_affected,ip_address,attack_indicators,asset_criticality,threat_severity,vulnerability_exposure,is_repeat,risk_score,severity,assigned_to,reported_date,resolution_notes,current_user.id, contact_full_name, contact_job_title, contact_office, contact_work_phone, contact_mobile_phone, contact_additional, detection_method, detection_method_other, incident_type_other)'

insert_sql_new = '"INSERT INTO incidents (incident_id,title,description,incident_type,affected_asset,affected_department,users_affected,ip_address,attack_indicators,asset_criticality,threat_severity,vulnerability_exposure,is_repeat,risk_score,severity,status,assigned_to,reported_date,resolution_notes,created_by,created_at,updated_at, contact_full_name, contact_job_title, contact_office, contact_work_phone, contact_mobile_phone, contact_additional, detection_method, detection_method_other, incident_type_other, impact_selections, impact_other, impact_additional, data_sensitivity_selections, data_sensitivity_other, data_sensitivity_additional, detected_datetime, incident_occurred_datetime, attack_source, affected_system_ips, attack_source_ips, affected_system_functions, affected_system_os, affected_system_location, affected_system_security_software, affected_systems_count, third_parties_involved) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,\'Open\',?,?,?,?,datetime(\'now\'),datetime(\'now\'), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"'
insert_tup_new = '(incident_id,title,description,incident_type,affected_asset,affected_department,users_affected,ip_address,attack_indicators,asset_criticality,threat_severity,vulnerability_exposure,is_repeat,risk_score,severity,assigned_to,reported_date,resolution_notes,current_user.id, contact_full_name, contact_job_title, contact_office, contact_work_phone, contact_mobile_phone, contact_additional, detection_method, detection_method_other, incident_type_other, impact_selections, impact_other, impact_additional, data_sensitivity_selections, data_sensitivity_other, data_sensitivity_additional, detected_datetime, incident_occurred_datetime, attack_source, affected_system_ips, attack_source_ips, affected_system_functions, affected_system_os, affected_system_location, affected_system_security_software, affected_systems_count, third_parties_involved)'
app_text = app_text.replace(insert_sql_old, insert_sql_new).replace(insert_tup_old, insert_tup_new)

update_sql_old = '"UPDATE incidents SET title=?,description=?,incident_type=?,affected_asset=?,affected_department=?,users_affected=?,ip_address=?,attack_indicators=?,asset_criticality=?,threat_severity=?,vulnerability_exposure=?,is_repeat=?,risk_score=?,severity=?,assigned_to=?,reported_date=?,updated_at=datetime(\'now\'),updated_by=?, contact_full_name=?, contact_job_title=?, contact_office=?, contact_work_phone=?, contact_mobile_phone=?, contact_additional=?, detection_method=?, detection_method_other=?, incident_type_other=? WHERE incident_id=?"'
update_tup_old = '(title,description,incident_type,affected_asset,affected_department,users_affected,ip_address,attack_indicators,asset_criticality,threat_severity,vulnerability_exposure,is_repeat,risk_score,severity,assigned_to,reported_date,current_user.id, contact_full_name, contact_job_title, contact_office, contact_work_phone, contact_mobile_phone, contact_additional, detection_method, detection_method_other, incident_type_other, incident_id)'

update_sql_new = '"UPDATE incidents SET title=?,description=?,incident_type=?,affected_asset=?,affected_department=?,users_affected=?,ip_address=?,attack_indicators=?,asset_criticality=?,threat_severity=?,vulnerability_exposure=?,is_repeat=?,risk_score=?,severity=?,assigned_to=?,reported_date=?,updated_at=datetime(\'now\'),updated_by=?, contact_full_name=?, contact_job_title=?, contact_office=?, contact_work_phone=?, contact_mobile_phone=?, contact_additional=?, detection_method=?, detection_method_other=?, incident_type_other=?, impact_selections=?, impact_other=?, impact_additional=?, data_sensitivity_selections=?, data_sensitivity_other=?, data_sensitivity_additional=?, detected_datetime=?, incident_occurred_datetime=?, attack_source=?, affected_system_ips=?, attack_source_ips=?, affected_system_functions=?, affected_system_os=?, affected_system_location=?, affected_system_security_software=?, affected_systems_count=?, third_parties_involved=? WHERE incident_id=?"'
update_tup_new = '(title,description,incident_type,affected_asset,affected_department,users_affected,ip_address,attack_indicators,asset_criticality,threat_severity,vulnerability_exposure,is_repeat,risk_score,severity,assigned_to,reported_date,current_user.id, contact_full_name, contact_job_title, contact_office, contact_work_phone, contact_mobile_phone, contact_additional, detection_method, detection_method_other, incident_type_other, impact_selections, impact_other, impact_additional, data_sensitivity_selections, data_sensitivity_other, data_sensitivity_additional, detected_datetime, incident_occurred_datetime, attack_source, affected_system_ips, attack_source_ips, affected_system_functions, affected_system_os, affected_system_location, affected_system_security_software, affected_systems_count, third_parties_involved, incident_id)'
app_text = app_text.replace(update_sql_old, update_sql_new).replace(update_tup_old, update_tup_new)

with open(app_py, "w", encoding="utf-8") as f:
    f.write(app_text)

print("app update done")
