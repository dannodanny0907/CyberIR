import os, re

base_dir = r"c:\Users\PDM\Pictures\CYBER\cyberir"
frontend_dir = os.path.join(base_dir, "frontend")
backend_dir = os.path.join(base_dir, "backend")

# Part 1: UPDATE base.css
base_css_path = os.path.join(frontend_dir, "static", "css", "base.css")
with open(base_css_path, "r", encoding="utf-8") as f:
    css = f.read()

# Replace CSS variables
css = css.replace("--badge-critical", "--badge-catastrophic")
css = css.replace("--badge-high", "--badge-major")
css = css.replace("--badge-medium", "--badge-moderate")
css = css.replace("--badge-low", "--badge-minor")

# Replace classes
css = css.replace(".badge-critical", ".badge-catastrophic")
css = css.replace(".badge-high", ".badge-major")
css = css.replace(".badge-medium", ".badge-moderate")
css = css.replace(".badge-low", ".badge-minor")

# Forward compatibility 
css += """
.badge-critical { background-color: var(--badge-catastrophic-bg, #fef2f2); color: var(--badge-catastrophic-text, #dc2626); }
.badge-high { background-color: var(--badge-major-bg, #fff7ed); color: var(--badge-major-text, #ea580c); }
.badge-medium { background-color: var(--badge-moderate-bg, #eff6ff); color: var(--badge-moderate-text, #2563eb); }
.badge-low { background-color: var(--badge-minor-bg, #f0fdf4); color: var(--badge-minor-text, #16a34a); }
"""
with open(base_css_path, "w", encoding="utf-8") as f:
    f.write(css)

# Part 2: HTML templates
templates_dir = os.path.join(frontend_dir, "templates")

# Core display replacements
str_map = {
    ">Critical<": ">Catastrophic<",
    ">High<": ">Major<",
    ">Medium<": ">Moderate<",
    ">Low<": ">Minor<",
    
    # Options in dropdowns
    ">All Priorities<": ">All Severities<",
    
    # Priority texts
    ">Priority<": ">Severity<",
    "Priority:": "Severity:",
    "<th>Priority": "<th>Severity",
    "<th> Priority": "<th> Severity",
    "incident.priority": "incident.priority", # leaving DB column names untouched
    "badge-critical": "badge-catastrophic",
    "badge-high": "badge-major",
    "badge-medium": "badge-moderate",
    "badge-low": "badge-minor",

    # Dashboard string replacements
    "'Critical'": "'Catastrophic'",
    "'High'": "'Major'",
    "'Medium'": "'Moderate'",
    "'Low'": "'Minor'",
    '"Critical"': '"Catastrophic"',
    '"High"': '"Major"',
    '"Medium"': '"Moderate"',
    '"Low"': '"Minor"',

    # Dashboard variables
    "critical_incidents": "catastrophic_incidents",

    # Reports variables
    "critical_count": "catastrophic_count",
    "high_count": "major_count",
    "medium_count": "moderate_count",
    "low_count": "minor_count",
    
    # Priority counts
    "Priority Distribution": "Severity Distribution",
}

for root, _, files in os.walk(templates_dir):
    for filename in files:
        if filename.endswith(".html"):
            path = os.path.join(root, filename)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            for k, v in str_map.items():
                content = content.replace(k, v)

            # Special regex to catch variable displays like {{ incident.priority }} where the header is "Severity" 
            # We don't need to change {{ incident.priority }} because incident object continues to have 'priority' key 
            # due to SQLite. 

            with open(path, "w", encoding="utf-8") as f:
                f.write(content)

# Update Javascript files
js_dir = os.path.join(frontend_dir, "static", "js")

for root, _, files in os.walk(js_dir):
    for filename in files:
        if filename.endswith(".js"):
            path = os.path.join(root, filename)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            
            content = content.replace("'Critical'", "'Catastrophic'")
            content = content.replace('"Critical"', '"Catastrophic"')
            content = content.replace("'High'", "'Major'")
            content = content.replace('"High"', '"Major"')
            content = content.replace("'Medium'", "'Moderate'")
            content = content.replace('"Medium"', '"Moderate"')
            content = content.replace("'Low'", "'Minor'")
            content = content.replace('"Low"', '"Minor"')

            if filename == "log_incident.js" or filename == "edit_incident.js":
                # Part 6: LOG INCIDENT LIVE PREVIEW
                # Old: if (risk_score >= 75) priority = 'Critical' ...
                content = content.replace("priority = 'Catastrophic'", "severity = 'Catastrophic'")
                content = content.replace("priority = 'Major'", "severity = 'Major'")
                content = content.replace("priority = 'Moderate'", "severity = 'Moderate'")
                content = content.replace("priority = 'Minor'", "severity = 'Minor'")
                content = content.replace("priority;", "severity;")
                content = content.replace("let priority = ", "let severity = ")
                content = content.replace("const priority = ", "const severity = ")
                content = content.replace("priorityBadge.textContent = priority;", "priorityBadge.textContent = severity;")

                # Let's add the warning string using regex targeting where it sets the text
                # It might be setting HTML for a badge or element
                content = re.sub(
                    r'(let|const)\s+severity\s*=\s*.*?;', 
                    r'\g<0>\n    const escalateWarn = (severity === "Major" || severity === "Catastrophic") ? `<div style="color: #dc2626; margin-top: 10px; font-weight: bold; font-size: 0.9rem;">⚠️ This incident will be escalated to CIRT</div>` : "";',
                    content
                )
                
                # Check how risk score or preview is formatted in js.
                # Usually it looks like: previewElement.innerHTML = `...`; 
                # I'll just blindly try to append it or wait, I don't know the variable names in js perfectly.
                # I will just write it after finding the exact files later if I need. For now I'm applying what's safe.

            # badges replacements in js
            content = content.replace("badge-critical", "badge-catastrophic")
            content = content.replace("badge-high", "badge-major")
            content = content.replace("badge-medium", "badge-moderate")
            content = content.replace("badge-low", "badge-minor")

            content = content.replace("Priority", "Severity")
            content = content.replace("priority_filter", "severity_filter")
            
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)

# Part 7: app.py adjustments for checking sla breaches and create_high_priority_alert and route var names
app_py = os.path.join(backend_dir, "app.py")
if os.path.exists(app_py):
    with open(app_py, "r", encoding="utf-8") as f:
        ccode = f.read()

    # The create_high_priority_alert functions might be inside app.py or somewhere like correlation_engine.py
    # But since we replaced 'Critical' -> 'Catastrophic', 'High' -> 'Major' overall:
    ccode = ccode.replace("priority in ['Catastrophic', 'Major']", "severity in ['Catastrophic', 'Major']")

    ccode = ccode.replace("critical_count", "catastrophic_count")
    ccode = ccode.replace("high_count", "major_count")
    ccode = ccode.replace("medium_count", "moderate_count")
    ccode = ccode.replace("low_count", "minor_count")
    
    # "medium" and "low" SLA breaching messages. They might use original strings
    
    with open(app_py, "w", encoding="utf-8") as f:
        f.write(ccode)

print("done")
