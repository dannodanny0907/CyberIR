import os, re

base_dir = r"c:\Users\PDM\Pictures\CYBER\cyberir"
backend_dir = os.path.join(base_dir, "backend")
frontend_dir = os.path.join(base_dir, "frontend")

# 1. log_incident.html changes
log_incident_path = os.path.join(frontend_dir, "templates", "log_incident.html")
with open(log_incident_path, "r", encoding="utf-8") as f:
    html = f.read()

contact_info_html = """
        <!-- Section 0: Contact Information -->
        <div class="card">
            <div class="section-header">
                👤 1. Contact Information
            </div>
            <div class="form-grid">
                <div>
                    <label class="form-label" for="contact_full_name">Full Name <span class="text-danger">*</span></label>
                    <input type="text" id="contact_full_name" name="contact_full_name" class="form-input" placeholder="Full name of person reporting incident" required>
                </div>
                <div>
                    <label class="form-label" for="contact_job_title">Job Title</label>
                    <input type="text" id="contact_job_title" name="contact_job_title" class="form-input" placeholder="Your job title">
                </div>
                <div>
                    <label class="form-label" for="contact_office">Office</label>
                    <input type="text" id="contact_office" name="contact_office" class="form-input" placeholder="Office number or building">
                </div>
                <div>
                    <label class="form-label" for="contact_work_phone">Work Phone</label>
                    <input type="text" id="contact_work_phone" name="contact_work_phone" class="form-input" placeholder="e.g. +263 67 2127433">
                </div>
                <div>
                    <label class="form-label" for="contact_mobile_phone">Mobile Phone</label>
                    <input type="text" id="contact_mobile_phone" name="contact_mobile_phone" class="form-input" placeholder="e.g. +263 77 123 4567">
                </div>
                <div></div>
                <div class="full-width">
                    <label class="form-label" for="contact_additional">Additional Contact Information</label>
                    <textarea id="contact_additional" name="contact_additional" class="form-input" rows="2" placeholder="Email address or any other contact details"></textarea>
                </div>
            </div>
        </div>
"""

# Insert Contact info above Incident Details card
html = html.replace('        <!-- Section 1 -->\n        <div class="card">', contact_info_html + '\n        <!-- Section 1 -->\n        <div class="card">')

detection_method_html = """
                <div>
                    <label class="form-label" for="detection_method">Incident Detection Method</label>
                    <select id="detection_method" name="detection_method" class="form-input">
                        <option value="">-- Select Detection Method --</option>
                        <option value="Vulnerability Assessment">Vulnerability Assessment</option>
                        <option value="System Malfunctioning">System Malfunctioning</option>
                        <option value="User Report">User Report</option>
                        <option value="Anonymous Report">Anonymous Report</option>
                        <option value="System Report/Log">System Report/Log</option>
                        <option value="Third Party">Third Party</option>
                        <option value="Other">Other</option>
                    </select>
                    <div id="detection_method_other_container" class="other-input-container">
                        <label class="form-label" for="detection_method_other">Please specify detection method <span class="text-danger">*</span></label>
                        <input type="text" id="detection_method_other" name="detection_method_other" class="form-input" placeholder="Describe how the incident was detected">
                    </div>
                </div>
"""

# Find `type="datetime-local"` and insert detection_method after it's div wrapper.
parts = html.split('</div>\n                \n                <div class="full-width">\n                    <label class="form-label" for="description">')
if len(parts) == 2:
    html = parts[0] + '</div>\n                ' + detection_method_html + '\n                <div class="full-width">\n                    <label class="form-label" for="description">' + parts[1]


# Replace incident_type dropdown
incident_type_old = """                    <select id="incident_type" name="incident_type" class="form-input" required>
                        <option value="">-- Select Type --</option>
                        <option value="Phishing">Phishing</option>
                        <option value="Malware">Malware</option>
                        <option value="Data Breach">Data Breach</option>
                        <option value="Ransomware">Ransomware</option>
                        <option value="Unauthorized Access">Unauthorized Access</option>
                        <option value="DDoS">DDoS</option>
                        <option value="Insider Threat">Insider Threat</option>
                        <option value="Other">Other</option>
                    </select>"""

incident_type_new = """                    <select name="incident_type" id="incident_type" multiple size="5" required class="multi-select-field">
                        <option value="Account Compromise">Account Compromise</option>
                        <option value="Denial of Service">Denial of Service</option>
                        <option value="Malicious Code">Malicious Code</option>
                        <option value="Misuse of Systems">Misuse of Systems</option>
                        <option value="Reconnaissance">Reconnaissance</option>
                        <option value="Social Engineering">Social Engineering</option>
                        <option value="Technical Vulnerability">Technical Vulnerability</option>
                        <option value="Theft/Loss of Equipment or Media">Theft/Loss of Equipment or Media</option>
                        <option value="Unauthorized Access">Unauthorized Access</option>
                        <option value="Unknown/Other">Unknown/Other</option>
                    </select>
                    <div class="multi-select-hint">Hold Ctrl (Windows) or Cmd (Mac) to select multiple types</div>
                    <div id="incident_type_other_container" class="other-input-container">
                        <label class="form-label" for="incident_type_other">Please specify incident type <span class="text-danger">*</span></label>
                        <input type="text" id="incident_type_other" name="incident_type_other" class="form-input" placeholder="Describe the incident type">
                    </div>"""

html = html.replace(incident_type_old, incident_type_new)

with open(log_incident_path, "w", encoding="utf-8") as f:
    f.write(html)
    
print("log_incident.html updated.")
