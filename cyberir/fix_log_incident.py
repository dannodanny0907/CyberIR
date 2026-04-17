import os

base_dir = r"c:\Users\PDM\Pictures\CYBER\cyberir"
frontend_dir = os.path.join(base_dir, "frontend")
js_dir = os.path.join(frontend_dir, "static", "js")

for filename in ["log_incident.js", "edit_incident.js"]:
    path = os.path.join(js_dir, filename)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 1. Update the priority string block to severity
        old_block = """        let priority = '';
        let color = '';
        let border = '';
        let bg = '';
        if (riskScore >= 75) {
            priority = 'Critical'; color = '#dc2626'; border = '#fca5a5'; bg = '#fee2e2';
        } else if (riskScore >= 50) {
            priority = 'High'; color = '#ea580c'; border = '#fdba74'; bg = '#ffedd5';
        } else if (riskScore >= 25) {
            priority = 'Medium'; color = '#2563eb'; border = '#bae6fd'; bg = '#e0f2fe';
        } else {
            priority = 'Low'; color = '#16a34a'; border = '#bbf7d0'; bg = '#dcfce7';
        }
        
        priorityBadge.textContent = priority;"""
        
        new_block = """        let severity = '';
        let color = '';
        let border = '';
        let bg = '';
        if (riskScore >= 75) {
            severity = 'Catastrophic'; color = '#dc2626'; border = '#fca5a5'; bg = '#fee2e2';
        } else if (riskScore >= 50) {
            severity = 'Major'; color = '#ea580c'; border = '#fdba74'; bg = '#ffedd5';
        } else if (riskScore >= 25) {
            severity = 'Moderate'; color = '#2563eb'; border = '#bae6fd'; bg = '#e0f2fe';
        } else {
            severity = 'Minor'; color = '#16a34a'; border = '#bbf7d0'; bg = '#dcfce7';
        }
        
        priorityBadge.textContent = severity;
        
        // escalation warning
        const warnId = 'cirt-escalation-warn';
        let warnEl = document.getElementById(warnId);
        if (severity === 'Major' || severity === 'Catastrophic') {
            if (!warnEl) {
                warnEl = document.createElement('div');
                warnEl.id = warnId;
                warnEl.style.color = '#dc2626';
                warnEl.style.marginTop = '10px';
                warnEl.style.fontWeight = 'bold';
                warnEl.style.fontSize = '0.9rem';
                warnEl.textContent = '⚠️ This incident will be escalated to CIRT';
                previewBox.appendChild(warnEl);
            }
        } else {
            if (warnEl) warnEl.remove();
        }"""
        
        if "let priority = '';" in content:
            content = content.replace(old_block, new_block)
        else:
            # If my previous python scripts messed it up by replacing Critical with Catastrophic already
            # Let's do a more robust regex or just manual replace
            content = content.replace("let priority =", "let severity =")
            content = content.replace("priority = 'Catastrophic'", "severity = 'Catastrophic'")
            content = content.replace("priority = 'Major'", "severity = 'Major'")
            content = content.replace("priority = 'Moderate'", "severity = 'Moderate'")
            content = content.replace("priority = 'Minor'", "severity = 'Minor'")
            content = content.replace("priority = 'Critical'", "severity = 'Catastrophic'")
            content = content.replace("priority = 'High'", "severity = 'Major'")
            content = content.replace("priority = 'Medium'", "severity = 'Moderate'")
            content = content.replace("priority = 'Low'", "severity = 'Minor'")
            content = content.replace("priorityBadge.textContent = priority", "priorityBadge.textContent = severity")
            
            # Just append the warning logic right after priorityBadge logic
            if "const warnId =" not in content and "priorityBadge.style.color" in content:
                content = content.replace("priorityBadge.style.color = color;", "priorityBadge.style.color = color;\n        const warnId = 'cirt-escalation-warn'; let warnEl = document.getElementById(warnId); if(severity === 'Major' || severity === 'Catastrophic'){ if(!warnEl){ warnEl = document.createElement('div'); warnEl.id = warnId; warnEl.style.color = '#dc2626'; warnEl.style.marginTop = '10px'; warnEl.style.fontWeight = 'bold'; warnEl.style.fontSize = '0.9rem'; warnEl.textContent = '⚠️ This incident will be escalated to CIRT'; previewBox.appendChild(warnEl); } } else { if(warnEl) warnEl.remove(); }")
                
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

print("done")
