import os, re

base_dir = r"c:\Users\PDM\Pictures\CYBER\cyberir"
frontend_dir = os.path.join(base_dir, "frontend")
backend_dir = os.path.join(base_dir, "backend")

# HTML snippets

impact_html = """
        <!-- Section 3: Impact of Incident -->
        <div class="card">
            <div class="section-header">
                💥 3. Impact of Incident
            </div>
            <div class="form-grid">
                <div>
                    <label class="form-label" for="impact_selections">Impact of Incident</label>
                    <select name="impact_selections" id="impact_selections" multiple size="5" class="multi-select-field">
                        <option value="Loss of access to services">Loss of access to services</option>
                        <option value="Loss of productivity">Loss of productivity</option>
                        <option value="Loss of reputation">Loss of reputation</option>
                        <option value="Loss of revenue">Loss of revenue</option>
                        <option value="Propagation to other networks">Propagation to other networks</option>
                        <option value="Unauthorized disclosure of data/information">Unauthorized disclosure of data/information</option>
                        <option value="Unauthorized modification of data/information">Unauthorized modification of data/information</option>
                        <option value="Unknown/Other">Unknown/Other</option>
                    </select>
                    <div class="multi-select-hint">Hold Ctrl (Windows) or Cmd (Mac) to select multiple</div>
                    <div id="impact_other_container" class="other-input-container">
                        <label class="form-label" for="impact_other">Please specify impact</label>
                        <input type="text" id="impact_other" name="impact_other" class="form-input" placeholder="Describe the impact">
                    </div>
                </div>
                <div class="full-width">
                    <label class="form-label" for="impact_additional">Additional Impact Information</label>
                    <textarea id="impact_additional" name="impact_additional" class="form-input" rows="3" placeholder="Any additional information about the impact of this incident..."></textarea>
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
                                <option value="Confidential/Sensitive data/info">Confidential/Sensitive data/info</option>
                                <option value="Personally Identifiable Information (PII)">Personally Identifiable Information (PII)</option>
                                <option value="Non-sensitive data/info">Non-sensitive data/info</option>
                                <option value="IP/Copyrighted data/info">IP/Copyrighted data/info</option>
                                <option value="Publicly available data/info">Publicly available data/info</option>
                                <option value="Critical infrastructure">Critical infrastructure</option>
                                <option value="Financial data/info">Financial data/info</option>
                                <option value="Unknown/Other">Unknown/Other</option>
                            </select>
                            <div class="multi-select-hint">Hold Ctrl (Windows) or Cmd (Mac) to select multiple</div>
                            <div id="data_sensitivity_other_container" class="other-input-container">
                                <label class="form-label" for="data_sensitivity_other">Please specify data type</label>
                                <input type="text" id="data_sensitivity_other" name="data_sensitivity_other" class="form-input" placeholder="Describe the type of data">
                            </div>
                        </div>
                        <div class="full-width">
                            <label class="form-label" for="data_sensitivity_additional">Additional Affected Data Information</label>
                            <textarea id="data_sensitivity_additional" name="data_sensitivity_additional" class="form-input" rows="2" placeholder="Any additional information about the affected data..."></textarea>
                        </div>
                    </div>
                </div>
"""

systems_affected_html = """
        <!-- Section 5: Systems Affected by Incident -->
        <div class="card">
            <div class="section-header">
                🖥️ 5. Systems Affected by Incident
            </div>
            <div class="form-grid">
                <div>
                    <label class="form-label" for="detected_datetime">Date/Time First Detected</label>
                    <input type="datetime-local" id="detected_datetime" name="detected_datetime" class="form-input">
                </div>
                <div>
                    <label class="form-label" for="incident_occurred_datetime">Date/Time Incident Occurred (estimate if unknown)</label>
                    <input type="datetime-local" id="incident_occurred_datetime" name="incident_occurred_datetime" class="form-input">
                </div>
                
                <div class="full-width">
                    <label class="form-label">Attack Source</label>
                    <div class="attack-source-group">
                        <label class="attack-source-label">
                            <input type="radio" name="attack_source" value="Internal" class="attack-source-radio">
                            <div class="attack-source-btn">Internal</div>
                        </label>
                        <label class="attack-source-label">
                            <input type="radio" name="attack_source" value="External" class="attack-source-radio">
                            <div class="attack-source-btn">External</div>
                        </label>
                        <label class="attack-source-label">
                            <input type="radio" name="attack_source" value="Both" class="attack-source-radio">
                            <div class="attack-source-btn">Both</div>
                        </label>
                    </div>
                </div>

                <div class="full-width">
                    <label class="form-label" for="affected_system_ips">IP Address/es of Affected System/s</label>
                    <input type="text" id="affected_system_ips" name="affected_system_ips" class="form-input" placeholder="e.g. 192.168.1.10, 192.168.1.11">
                    <div class="multi-select-hint">Comma-separated if multiple</div>
                </div>
                
                <div class="full-width">
                    <label class="form-label" for="attack_source_ips">Attack Sources IP Address/es</label>
                    <input type="text" id="attack_source_ips" name="attack_source_ips" class="form-input" placeholder="e.g. 185.220.101.45">
                    <div class="multi-select-hint">Comma-separated if multiple</div>
                </div>

                <div>
                    <label class="form-label" for="affected_system_functions">Functions of Affected System/s</label>
                    <input type="text" id="affected_system_functions" name="affected_system_functions" class="form-input" placeholder="e.g. Web server, Database, Email server">
                </div>
                <div>
                    <label class="form-label" for="affected_system_os">OS of Affected System/s</label>
                    <input type="text" id="affected_system_os" name="affected_system_os" class="form-input" placeholder="e.g. Ubuntu 22.04, Windows Server 2019">
                </div>

                <div>
                    <label class="form-label" for="affected_system_location">Physical Location of Affected System</label>
                    <input type="text" id="affected_system_location" name="affected_system_location" class="form-input" placeholder="e.g. Data Center, ICT Building Room 105">
                </div>
                <div>
                    <label class="form-label" for="affected_system_security_software">Security Software Loaded on Affected System</label>
                    <input type="text" id="affected_system_security_software" name="affected_system_security_software" class="form-input" placeholder="e.g. CrowdStrike Falcon, McAfee">
                </div>

                <div>
                    <label class="form-label" for="affected_systems_count">Estimated Quantity of Systems Affected</label>
                    <input type="number" id="affected_systems_count" name="affected_systems_count" class="form-input" min="1" placeholder="Number of systems">
                </div>
                <div>
                    <label class="form-label" for="third_parties_involved">Third Parties Involved or Affected</label>
                    <input type="text" id="third_parties_involved" name="third_parties_involved" class="form-input" placeholder="e.g. Cloud provider, vendor name">
                </div>
            </div>
        </div>
"""

# Modify log_incident.html
log_file = os.path.join(frontend_dir, "templates", "log_incident.html")
with open(log_file, "r", encoding="utf-8") as f:
    html = f.read()

# 1. Insert impact_html AFTER Incident Details card (which ends right after description, or right before Affected Resources)
# Locate Affected Resources card: `        <!-- Section 2 -->\n        <div class="card">\n            <div class="section-header">\n                🖥️ Affected Resources`
html = html.replace('        <!-- Section 2 -->\n        <div class="card">\n            <div class="section-header">\n                🖥️ Affected Resources', impact_html + '\n        <!-- Section 2 -->\n        <div class="card">\n            <div class="section-header">\n                🖥️ Affected Resources')

# 2. Insert data_sensitivity_html INSIDE Affected Resources
# Look for where `attack_indicators` ends.
html = html.replace('</textarea>\n                </div>\n            </div>\n        </div>', '</textarea>\n                </div>\n' + data_sensitivity_html + '            </div>\n        </div>')

# 3. Insert systems_affected_html AFTER Affected Resources and BEFORE Risk Assessment
# Risk assessment usually starts with `        <!-- Section 3 -->` or something with `⚠️ Risk Assessment`
html = html.replace('        <!-- Section 3 -->\n        <div class="card">\n            <div class="section-header">\n                ⚠️ Risk Assessment', systems_affected_html + '\n        <!-- Section 3 -->\n        <div class="card">\n            <div class="section-header">\n                ⚠️ Risk Assessment')

with open(log_file, "w", encoding="utf-8") as f:
    f.write(html)
    
print("log_html updated")
