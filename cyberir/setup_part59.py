import os, re

base_dir = r"c:\Users\PDM\Pictures\CYBER\cyberir"
frontend_dir = os.path.join(base_dir, "frontend")

# 1. Update edit_incident.html
edit_incident_path = os.path.join(frontend_dir, "templates", "edit_incident.html")
with open(edit_incident_path, "r", encoding="utf-8") as f:
    edit_html = f.read()

# I will use the exact html snippets from my previous script, but fill in the `value="..."` bindings for Jinja

contact_info_html = """
        <!-- Section 0: Contact Information -->
        <div class="card">
            <div class="section-header">
                👤 1. Contact Information
            </div>
            <div class="form-grid">
                <div>
                    <label class="form-label" for="contact_full_name">Full Name <span class="text-danger">*</span></label>
                    <input type="text" id="contact_full_name" name="contact_full_name" class="form-input" placeholder="Full name of person reporting incident" value="{{ incident.contact_full_name or '' }}" required>
                </div>
                <div>
                    <label class="form-label" for="contact_job_title">Job Title</label>
                    <input type="text" id="contact_job_title" name="contact_job_title" class="form-input" placeholder="Your job title" value="{{ incident.contact_job_title or '' }}">
                </div>
                <div>
                    <label class="form-label" for="contact_office">Office</label>
                    <input type="text" id="contact_office" name="contact_office" class="form-input" placeholder="Office number or building" value="{{ incident.contact_office or '' }}">
                </div>
                <div>
                    <label class="form-label" for="contact_work_phone">Work Phone</label>
                    <input type="text" id="contact_work_phone" name="contact_work_phone" class="form-input" placeholder="e.g. +263 67 2127433" value="{{ incident.contact_work_phone or '' }}">
                </div>
                <div>
                    <label class="form-label" for="contact_mobile_phone">Mobile Phone</label>
                    <input type="text" id="contact_mobile_phone" name="contact_mobile_phone" class="form-input" placeholder="e.g. +263 77 123 4567" value="{{ incident.contact_mobile_phone or '' }}">
                </div>
                <div></div>
                <div class="full-width">
                    <label class="form-label" for="contact_additional">Additional Contact Information</label>
                    <textarea id="contact_additional" name="contact_additional" class="form-input" rows="2" placeholder="Email address or any other contact details">{{ incident.contact_additional or '' }}</textarea>
                </div>
            </div>
        </div>
"""

# Edit html doesn't have <!-- Section 1 --> properly sometimes? 
# Usually it mirrors log_incident.html exactly. Let's find `<div class="card">` that contains Incident Details.
if "👤 1. Contact Information" not in edit_html:
    edit_html = re.sub(r'(<div class="card">\s*<div class="section-header">\s*📋 Incident Details)', contact_info_html + r'\n        \1', edit_html)


detection_method_html = """
                <div>
                    <label class="form-label" for="detection_method">Incident Detection Method</label>
                    <select id="detection_method" name="detection_method" class="form-input">
                        <option value="">-- Select Detection Method --</option>
                        <option value="Vulnerability Assessment" {% if incident.detection_method == 'Vulnerability Assessment' %}selected{% endif %}>Vulnerability Assessment</option>
                        <option value="System Malfunctioning" {% if incident.detection_method == 'System Malfunctioning' %}selected{% endif %}>System Malfunctioning</option>
                        <option value="User Report" {% if incident.detection_method == 'User Report' %}selected{% endif %}>User Report</option>
                        <option value="Anonymous Report" {% if incident.detection_method == 'Anonymous Report' %}selected{% endif %}>Anonymous Report</option>
                        <option value="System Report/Log" {% if incident.detection_method == 'System Report/Log' %}selected{% endif %}>System Report/Log</option>
                        <option value="Third Party" {% if incident.detection_method == 'Third Party' %}selected{% endif %}>Third Party</option>
                        <option value="Other" {% if incident.detection_method == 'Other' %}selected{% endif %}>Other</option>
                    </select>
                    <div id="detection_method_other_container" class="other-input-container {% if incident.detection_method == 'Other' %}visible{% endif %}">
                        <label class="form-label" for="detection_method_other">Please specify detection method <span class="text-danger">*</span></label>
                        <input type="text" id="detection_method_other" name="detection_method_other" class="form-input" placeholder="Describe how the incident was detected" value="{{ incident.detection_method_other or '' }}" {% if incident.detection_method == 'Other' %}required{% endif %}>
                    </div>
                </div>
"""

# Inject before description
# edit_incident usually has `<label class="form-label" for="description">Description</label>`
if 'id="detection_method"' not in edit_html:
    parts = edit_html.split('</div>\n                \n                <div class="full-width">\n                    <label class="form-label" for="description">')
    if len(parts) == 2:
        edit_html = parts[0] + '</div>\n                ' + detection_method_html + '\n                <div class="full-width">\n                    <label class="form-label" for="description">' + parts[1]


incident_type_old = """                    <select id="incident_type" name="incident_type" class="form-input" required>
                        <option value="Phishing" {% if incident.incident_type == 'Phishing' %}selected{% endif %}>Phishing</option>
                        <option value="Malware" {% if incident.incident_type == 'Malware' %}selected{% endif %}>Malware</option>
                        <option value="Data Breach" {% if incident.incident_type == 'Data Breach' %}selected{% endif %}>Data Breach</option>
                        <option value="Ransomware" {% if incident.incident_type == 'Ransomware' %}selected{% endif %}>Ransomware</option>
                        <option value="Unauthorized Access" {% if incident.incident_type == 'Unauthorized Access' %}selected{% endif %}>Unauthorized Access</option>
                        <option value="DDoS" {% if incident.incident_type == 'DDoS' %}selected{% endif %}>DDoS</option>
                        <option value="Insider Threat" {% if incident.incident_type == 'Insider Threat' %}selected{% endif %}>Insider Threat</option>
                        <option value="Other" {% if incident.incident_type == 'Other' %}selected{% endif %}>Other</option>
                    </select>"""

incident_type_new = """                    <select name="incident_type" id="incident_type" multiple size="5" required class="multi-select-field">
                        <option value="Account Compromise" {% if 'Account Compromise' in (incident.incident_type or '') %}selected{% endif %}>Account Compromise</option>
                        <option value="Denial of Service" {% if 'Denial of Service' in (incident.incident_type or '') %}selected{% endif %}>Denial of Service</option>
                        <option value="Malicious Code" {% if 'Malicious Code' in (incident.incident_type or '') %}selected{% endif %}>Malicious Code</option>
                        <option value="Misuse of Systems" {% if 'Misuse of Systems' in (incident.incident_type or '') %}selected{% endif %}>Misuse of Systems</option>
                        <option value="Reconnaissance" {% if 'Reconnaissance' in (incident.incident_type or '') %}selected{% endif %}>Reconnaissance</option>
                        <option value="Social Engineering" {% if 'Social Engineering' in (incident.incident_type or '') %}selected{% endif %}>Social Engineering</option>
                        <option value="Technical Vulnerability" {% if 'Technical Vulnerability' in (incident.incident_type or '') %}selected{% endif %}>Technical Vulnerability</option>
                        <option value="Theft/Loss of Equipment or Media" {% if 'Theft/Loss of Equipment or Media' in (incident.incident_type or '') %}selected{% endif %}>Theft/Loss of Equipment or Media</option>
                        <option value="Unauthorized Access" {% if 'Unauthorized Access' in (incident.incident_type or '') %}selected{% endif %}>Unauthorized Access</option>
                        <option value="Unknown/Other" {% if 'Unknown/Other' in (incident.incident_type or '') %}selected{% endif %}>Unknown/Other</option>
                    </select>
                    <div class="multi-select-hint">Hold Ctrl (Windows) or Cmd (Mac) to select multiple types</div>
                    <div id="incident_type_other_container" class="other-input-container {% if 'Unknown/Other' in (incident.incident_type or '') %}visible{% endif %}">
                        <label class="form-label" for="incident_type_other">Please specify incident type <span class="text-danger">*</span></label>
                        <input type="text" id="incident_type_other" name="incident_type_other" class="form-input" placeholder="Describe the incident type" value="{{ incident.incident_type_other or '' }}">
                    </div>"""

if '<select id="incident_type"' in edit_html and 'multiple' not in edit_html:
    # We will use regex to find the whole <select> block
    edit_html = re.sub(
        r'<select id="incident_type" name="incident_type" class="form-input" required>.*?</select>',
        incident_type_new,
        edit_html,
        flags=re.DOTALL
    )

with open(edit_incident_path, "w", encoding="utf-8") as f:
    f.write(edit_html)


# 2. Update incident_detail.html
detail_path = os.path.join(frontend_dir, "templates", "incident_detail.html")
with open(detail_path, "r", encoding="utf-8") as f:
    d_html = f.read()

# "Detection Method: {{ incident.detection_method }} (show incident.detection_method_other if method is 'Other')"
det_method_str = """
            <div class="detail-row">
                <span class="detail-label">Detection Method</span>
                <span class="detail-value">
                    {{ incident.detection_method or 'Not Specified' }}
                    {% if incident.detection_method == 'Other' %}
                        ({{ incident.detection_method_other }})
                    {% endif %}
                </span>
            </div>
"""
if "Detection Method" not in d_html:
    d_html = d_html.replace(
        '<span class="detail-label">Date Reported</span>',
        det_method_str + '\n            <div class="detail-row"><span class="detail-label">Date Reported</span>'
    )

# "Incident Type now may be comma-separated — display each type as a separate badge:"
type_old = """<span class="detail-value">{{ incident.incident_type }}</span>"""
type_new = """<span class="detail-value">
                    {% for itype in (incident.incident_type or '').split(', ') %}
                        {% if itype.strip() %}
                            <span class="badge" style="background:var(--primary); color:white; font-size:0.75rem;">{{ itype.strip() }}</span>
                        {% endif %}
                    {% else %}
                        Not Specified
                    {% endfor %}
                    {% if 'Unknown/Other' in (incident.incident_type or '') and incident.incident_type_other %}
                        ({{ incident.incident_type_other }})
                    {% endif %}
                </span>"""
d_html = re.sub(r'<span class="detail-value">\s*\{\{\s*incident\.incident_type\s*\}\}\s*</span>', type_new, d_html)

# Add "Contact Information" card to the right column
contact_card = """
        <div class="card">
            <div class="section-header">👤 Contact Information</div>
            <div class="incident-details-list">
                {% if incident.contact_full_name %}
                <div class="detail-row">
                    <span class="detail-label">Full Name</span>
                    <span class="detail-value">{{ incident.contact_full_name }}</span>
                </div>
                {% endif %}
                {% if incident.contact_job_title %}
                <div class="detail-row">
                    <span class="detail-label">Job Title</span>
                    <span class="detail-value">{{ incident.contact_job_title }}</span>
                </div>
                {% endif %}
                {% if incident.contact_office %}
                <div class="detail-row">
                    <span class="detail-label">Office</span>
                    <span class="detail-value">{{ incident.contact_office }}</span>
                </div>
                {% endif %}
                {% if incident.contact_work_phone %}
                <div class="detail-row">
                    <span class="detail-label">Work Phone</span>
                    <span class="detail-value"><a href="tel:{{ incident.contact_work_phone }}">{{ incident.contact_work_phone }}</a></span>
                </div>
                {% endif %}
                {% if incident.contact_mobile_phone %}
                <div class="detail-row">
                    <span class="detail-label">Mobile Phone</span>
                    <span class="detail-value"><a href="tel:{{ incident.contact_mobile_phone }}">{{ incident.contact_mobile_phone }}</a></span>
                </div>
                {% endif %}
                {% if incident.contact_additional %}
                <div class="detail-row">
                    <span class="detail-label">Additional Info</span>
                    <span class="detail-value">{{ incident.contact_additional }}</span>
                </div>
                {% endif %}
                {% if not incident.contact_full_name %}
                <div class="detail-row">
                    <span class="detail-value" style="color:var(--text-secondary); font-style:italic;">No contact information recorded.</span>
                </div>
                {% endif %}
            </div>
        </div>
"""
if "👤 Contact Information" not in d_html:
    # Right column usually starts with `<div class="card"> <div class="section-header">Incident Details</div>`
    # Let's append our contact_card right before `<div class="card">` that contains Incident Details or just above it.
    d_html = re.sub(r'(<div class="card">\s*<div class="section-header">Incident Details</div>)', contact_card + r'\n        \1', d_html)

with open(detail_path, "w", encoding="utf-8") as f:
    f.write(d_html)

print("done html")
