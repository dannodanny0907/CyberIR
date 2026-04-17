import os

base_dir = r"c:\Users\PDM\Pictures\CYBER\cyberir"
frontend_dir = os.path.join(base_dir, "frontend")

# CSS Updates
log_css_path = os.path.join(frontend_dir, "static", "css", "log_incident.css")
with open(log_css_path, "a", encoding="utf-8") as f:
    f.write("""
/* Multi-select styling */
.multi-select-field {
    width: 100%;
    min-height: 150px;
    padding: 6px;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    font-size: 0.875rem;
    font-family: inherit;
}
.multi-select-field option {
    padding: 6px 8px;
    margin: 1px 0;
    border-radius: 3px;
}
.multi-select-field option:checked {
    background: #2563eb;
    color: white;
}
.multi-select-hint {
    font-size: 0.75rem;
    color: #64748b;
    margin-top: 4px;
}

/* Other input slide wrapper */
.other-input-container {
    margin-top: 8px;
    display: none;
}
.other-input-container.visible {
    display: block;
}
""")
print("CSS updated.")

# JS Updates
# There's log_incident.js and likely edit_incident.js
# The script will inject the event listeners to `DOMContentLoaded` block.
for file in ["log_incident.js", "edit_incident.js"]:
    js_path = os.path.join(frontend_dir, "static", "js", file)
    if os.path.exists(js_path):
        with open(js_path, "r", encoding="utf-8") as f:
            js = f.read()
        
        # Inject toggle handlers
        toggles = """
    // Detection method toggle
    document.getElementById('detection_method')?.addEventListener('change', function() {
        const otherContainer = document.getElementById('detection_method_other_container');
        if (this.value === 'Other') {
            otherContainer.classList.add('visible');
            document.getElementById('detection_method_other').required = true;
        } else {
            otherContainer.classList.remove('visible');
            document.getElementById('detection_method_other').required = false;
        }
    });

    // Incident type toggle
    document.getElementById('incident_type')?.addEventListener('change', function() {
        const selectedOptions = Array.from(this.selectedOptions).map(opt => opt.value);
        const otherContainer = document.getElementById('incident_type_other_container');
        if (selectedOptions.includes('Unknown/Other')) {
            otherContainer.classList.add('visible');
            document.getElementById('incident_type_other').required = true;
        } else {
            otherContainer.classList.remove('visible');
            document.getElementById('incident_type_other').required = false;
        }
    });
"""
        # Inject at the bottom of DOMContentLoaded
        if "// Attach event listeners" in js:
            js = js.replace("// Attach event listeners", toggles + "\n    // Attach event listeners")
        
        # Inject validation logic
        valid_logic = """
    // Multi-select incident type validation
    const incidentTypeSelect = document.getElementById('incident_type');
    if (incidentTypeSelect) {
        const selectedTypes = Array.from(incidentTypeSelect.selectedOptions).map(o => o.value);
        if (selectedTypes.length === 0) {
            showError('incident_type', 'Please select at least one incident type');
            isValid = false;
        }
    }
"""
        # Replace the existing incident type validation
        old_valid = """    // Incident type validation
    const type = document.getElementById('incident_type')?.value
    if (!type) {
        showError('incident_type', 'Please select an incident type')
        if (!firstError) firstError = 'incident_type'
        isValid = false
    }"""
        if old_valid in js:
            js = js.replace(old_valid, valid_logic)
        else:
            # Maybe the formatting is slightly different, fallback:
            # Let's insert valid_logic inside `clearAllErrors()\n    let isValid = true` underneath it
            js = js.replace('let isValid = true', 'let isValid = true\n' + valid_logic)

        with open(js_path, "w", encoding="utf-8") as f:
            f.write(js)

print("JS updated.")
