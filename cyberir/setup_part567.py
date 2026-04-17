import os, re

base_dir = r"c:\Users\PDM\Pictures\CYBER\cyberir"
frontend_dir = os.path.join(base_dir, "frontend")

# Part 5: Update incident_detail.html
detail_path = os.path.join(frontend_dir, "templates", "incident_detail.html")
with open(detail_path, "r", encoding="utf-8") as f:
    d_html = f.read()

impact_card = """
        <div class="card">
            <div class="section-header">💥 Impact of Incident</div>
            <div class="incident-details-list">
                <div class="detail-row">
                    <span class="detail-label">Impact Selections</span>
                    <span class="detail-value">
                        {% if incident.impact_selections %}
                            {% for item in incident.impact_selections.split(', ') %}
                                {% if item.strip() %}
                                <span class="impact-badge">{{ item.strip() }}</span>
                                {% endif %}
                            {% endfor %}
                        {% else %}
                            <span style="color:var(--text-secondary); font-style:italic;">No impact data</span>
                        {% endif %}
                    </span>
                </div>
                {% if incident.impact_other %}
                <div class="detail-row">
                    <span class="detail-label">Impact Other</span>
                    <span class="detail-value">{{ incident.impact_other }}</span>
                </div>
                {% endif %}
                {% if incident.impact_additional %}
                <div class="detail-row">
                    <span class="detail-label">Additional Info</span>
                    <span class="detail-value">{{ incident.impact_additional }}</span>
                </div>
                {% endif %}
            </div>
        </div>
"""

systems_card = """
        <div class="card">
            <div class="section-header">🖥️ Systems Affected</div>
            <div class="incident-details-list">
                {% if incident.detected_datetime %}
                <div class="detail-row">
                    <span class="detail-label">First Detected</span>
                    <span class="detail-value">{{ incident.detected_datetime }}</span>
                </div>
                {% endif %}
                {% if incident.incident_occurred_datetime %}
                <div class="detail-row">
                    <span class="detail-label">Incident Occurred</span>
                    <span class="detail-value">{{ incident.incident_occurred_datetime }}</span>
                </div>
                {% endif %}
                {% if incident.attack_source %}
                <div class="detail-row">
                    <span class="detail-label">Attack Source</span>
                    <span class="detail-value">{{ incident.attack_source }}</span>
                </div>
                {% endif %}
                {% if incident.affected_system_ips %}
                <div class="detail-row">
                    <span class="detail-label">System IPs</span>
                    <span class="detail-value">{{ incident.affected_system_ips }}</span>
                </div>
                {% endif %}
                {% if incident.attack_source_ips %}
                <div class="detail-row">
                    <span class="detail-label">Attack Source IPs</span>
                    <span class="detail-value">{{ incident.attack_source_ips }}</span>
                </div>
                {% endif %}
                {% if incident.affected_system_functions %}
                <div class="detail-row">
                    <span class="detail-label">System Functions</span>
                    <span class="detail-value">{{ incident.affected_system_functions }}</span>
                </div>
                {% endif %}
                {% if incident.affected_system_os %}
                <div class="detail-row">
                    <span class="detail-label">Operating System</span>
                    <span class="detail-value">{{ incident.affected_system_os }}</span>
                </div>
                {% endif %}
                {% if incident.affected_system_location %}
                <div class="detail-row">
                    <span class="detail-label">Physical Location</span>
                    <span class="detail-value">{{ incident.affected_system_location }}</span>
                </div>
                {% endif %}
                {% if incident.affected_system_security_software %}
                <div class="detail-row">
                    <span class="detail-label">Security Software</span>
                    <span class="detail-value">{{ incident.affected_system_security_software }}</span>
                </div>
                {% endif %}
                {% if incident.affected_systems_count %}
                <div class="detail-row">
                    <span class="detail-label">Systems Affected Count</span>
                    <span class="detail-value">{{ incident.affected_systems_count }}</span>
                </div>
                {% endif %}
                {% if incident.third_parties_involved %}
                <div class="detail-row">
                    <span class="detail-label">Third Parties Involved</span>
                    <span class="detail-value">{{ incident.third_parties_involved }}</span>
                </div>
                {% endif %}
                {% if not (incident.detected_datetime or incident.incident_occurred_datetime or incident.attack_source or incident.affected_system_ips or incident.attack_source_ips or incident.affected_system_functions or incident.affected_system_os or incident.affected_system_location or incident.affected_system_security_software or incident.affected_systems_count or incident.third_parties_involved) %}
                <div class="detail-row">
                    <span class="detail-value" style="color:var(--text-secondary); font-style:italic;">No system records defined.</span>
                </div>
                {% endif %}
            </div>
        </div>
"""

sens_subcard = """
                <div style="margin-top:20px; margin-bottom:5px; font-weight:600; font-size:0.95rem; border-bottom:1px solid var(--border-color); padding-bottom:5px;">Sensitivity of Affected Data/Information</div>
                <div class="detail-row" style="margin-top:10px;">
                    <span class="detail-label">Data Sensitivity</span>
                    <span class="detail-value">
                        {% if incident.data_sensitivity_selections %}
                            {% for s in incident.data_sensitivity_selections.split(', ') %}
                                {% if s.strip() %}
                                <span class="sensitivity-badge">{{ s.strip() }}</span>
                                {% endif %}
                            {% endfor %}
                        {% else %}
                            <span style="color:var(--text-secondary); font-style:italic;">Not Specified</span>
                        {% endif %}
                    </span>
                </div>
                {% if incident.data_sensitivity_other %}
                <div class="detail-row">
                    <span class="detail-label">Sensitivity Other</span>
                    <span class="detail-value">{{ incident.data_sensitivity_other }}</span>
                </div>
                {% endif %}
                {% if incident.data_sensitivity_additional %}
                <div class="detail-row">
                    <span class="detail-label">Additional Data Info</span>
                    <span class="detail-value">{{ incident.data_sensitivity_additional }}</span>
                </div>
                {% endif %}
"""

# Insert systems and impact into Left column (after Risk Assessment or Incident Overview)
# I will append them below Risk Assessment. Risk Assessment is `<div class="card">\n            <div class="section-header">⚠️ Risk Assessment</div>`
# It's inside a `<div class="column">`
if "💥 Impact of Incident" not in d_html:
    d_html = d_html.replace('        <!-- Risk Assessment -->', systems_card + '\n' + impact_card + '\n        <!-- Risk Assessment -->')

if "Sensitivity of Affected Data/Information" not in d_html:
    # Append to Affected Resources
    d_html = d_html.replace('<!-- End Affected Resources -->', sens_subcard + '\n        <!-- End Affected Resources -->')
    # If the marker doesn't exist, we find the end of Affected Resources card
    d_html = re.sub(r'(\n\s*</div>\n\s*</div>\n\s*<!-- Risk Assessment -->)', sens_subcard + r'\1', d_html)

with open(detail_path, "w", encoding="utf-8") as f:
    f.write(d_html)

# Part 6: CSS Updates
log_css_path = os.path.join(frontend_dir, "static", "css", "log_incident.css")
with open(log_css_path, "a", encoding="utf-8") as f:
    f.write("""
/* Attack source radio buttons styled as toggles */
.attack-source-group {
    display: flex;
    gap: 8px;
    margin-top: 4px;
}
.attack-source-btn {
    flex: 1;
    padding: 8px;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    text-align: center;
    cursor: pointer;
    font-size: 0.875rem;
    background: white;
    transition: all 0.15s;
}
input[type="radio"]:checked + .attack-source-btn {
    background: #2563eb;
    color: white;
    border-color: #2563eb;
}
.attack-source-radio {
    display: none;
}
""")

det_css_path = os.path.join(frontend_dir, "static", "css", "incident_detail.css")
with open(det_css_path, "a", encoding="utf-8") as f:
    f.write("""
.impact-badge {
    display: inline-block;
    background: #fff7ed;
    color: #c2410c;
    border: 1px solid #fed7aa;
    padding: 3px 10px;
    border-radius: 10px;
    font-size: 0.78rem;
    margin: 2px;
}
.sensitivity-badge {
    display: inline-block;
    background: #fef3c7;
    color: #92400e;
    border: 1px solid #fde68a;
    padding: 3px 10px;
    border-radius: 10px;
    font-size: 0.78rem;
    margin: 2px;
}
""")

# Part 7: JS Updates
for jsfile in ["log_incident.js", "edit_incident.js"]:
    js_path = os.path.join(frontend_dir, "static", "js", jsfile)
    if os.path.exists(js_path):
        with open(js_path, "r", encoding="utf-8") as f:
            js = f.read()

        logic = """
    // Impact of Incident toggle
    document.getElementById('impact_selections')?.addEventListener('change', function() {
        const selected = Array.from(this.selectedOptions).map(o => o.value);
        const container = document.getElementById('impact_other_container');
        if (selected.includes('Unknown/Other')) {
            container.classList.add('visible');
        } else {
            container.classList.remove('visible');
        }
    });

    // Data Sensitivity toggle
    document.getElementById('data_sensitivity_selections')?.addEventListener('change', function() {
        const selected = Array.from(this.selectedOptions).map(o => o.value);
        const container = document.getElementById('data_sensitivity_other_container');
        if (selected.includes('Unknown/Other')) {
            container.classList.add('visible');
        } else {
            container.classList.remove('visible');
        }
    });

    // Attack source radio buttons
    document.querySelectorAll('.attack-source-label').forEach(label => {
        label.addEventListener('click', function() {
            document.querySelectorAll('.attack-source-btn').forEach(btn => btn.style.background = '');
            this.querySelector('.attack-source-btn').style.background = '#2563eb';
            this.querySelector('.attack-source-btn').style.color = 'white';
        });
    });
"""
        if "// Impact of Incident toggle" not in js:
            js = js.replace("// Attach event listeners", logic + "\n    // Attach event listeners")

        with open(js_path, "w", encoding="utf-8") as f:
            f.write(js)

print("done")
