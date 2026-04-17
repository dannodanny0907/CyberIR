import os, re

base_dir = r"c:\Users\PDM\Pictures\CYBER\cyberir"
frontend_dir = os.path.join(base_dir, "frontend")
backend_dir = os.path.join(base_dir, "backend")

# Part 1: Update auth.py
auth_py = os.path.join(backend_dir, "auth.py")
with open(auth_py, "r", encoding="utf-8") as f:
    auth_text = f.read()

# Update redirect logic in login route
if "return redirect(url_for('cirt_incidents'))" not in auth_text:
    old_redirect = "return redirect(url_for('dashboard'))"
    new_redirect = """if user.role == 'CIRT':
                return redirect(url_for('cirt_incidents'))
            else:
                return redirect(url_for('dashboard'))"""
    # Replace ONLY the successful login redirect inside `if user_row and check_password_hash`
    auth_text = auth_text.replace(
        "            conn2.close()\n            return redirect(url_for('dashboard'))",
        "            conn2.close()\n            " + new_redirect.replace("\n", "\n            ")
    )
    # also the redirect at the top if already authenticated
    auth_text = auth_text.replace(
        "    if current_user.is_authenticated:\n        return redirect(url_for('dashboard'))",
        "    if current_user.is_authenticated:\n        if current_user.role == 'CIRT':\n            return redirect(url_for('cirt_incidents'))\n        else:\n            return redirect(url_for('dashboard'))"
    )

with open(auth_py, "w", encoding="utf-8") as f:
    f.write(auth_text)


# Part 2: Update users.html and users management routes
users_html = os.path.join(frontend_dir, "templates", "users.html")
if os.path.exists(users_html):
    with open(users_html, "r", encoding="utf-8") as f:
        u_html = f.read()
    
    # 1. `<option value="Viewer">Viewer</option>` -> append CIRT
    if '<option value="CIRT">CIRT</option>' not in u_html:
        u_html = u_html.replace(
            '<option value="Viewer">Viewer</option>',
            '<option value="Viewer">Viewer</option>\n                            <option value="CIRT">CIRT</option>'
        )

    # 2. Add Javascript to HIDE admin privileges checkbox if role == CIRT
    # And add helper text.
    # Look for role select
    if 'id="roleDesc" class="form-help"' not in u_html:
        u_html = u_html.replace(
            '</select>\n                    </div>',
            '</select>\n                        <div id="roleDesc" class="form-help" style="font-size:0.75rem; color:var(--text-secondary); margin-top:4px;"></div>\n                    </div>'
        )

    # We need to add JS to users.html to hide checkbox
    # Find `document.getElementById('role').addEventListener` or similar. If not, append to end of file
    js_append = """
<script>
document.addEventListener('DOMContentLoaded', function() {
    const roleSelects = document.querySelectorAll('select[name="role"]');
    roleSelects.forEach(select => {
        select.addEventListener('change', function() {
            const form = this.closest('form');
            const adminCheckGroup = form.querySelector('input[name="has_admin_privileges"]').closest('.checkbox-group');
            const desc = form.querySelector('#roleDesc') || form.querySelector('.role-desc');
            
            if (this.value === 'CIRT') {
                adminCheckGroup.style.display = 'none';
                form.querySelector('input[name="has_admin_privileges"]').checked = false;
                if (desc) desc.textContent = "CIRT: Access to escalated incidents (Major/Catastrophic) only";
            } else {
                adminCheckGroup.style.display = 'flex';
                if (desc) desc.textContent = "";
            }
        });
        // trigger once
        select.dispatchEvent(new Event('change'));
    });
});
</script>
"""
    if "adminCheckGroup.style.display = 'none'" not in u_html:
        u_html = u_html + js_append

    with open(users_html, "w", encoding="utf-8") as f:
        f.write(u_html)

# Add role badge to base.css (and base.html CIRT navigation later)
base_css = os.path.join(frontend_dir, "static", "css", "base.css")
with open(base_css, "r", encoding="utf-8") as f:
    css = f.read()

if ".role-cirt" not in css:
    css += """
.role-cirt { background: #0d9488; color: white; padding: 2px 8px; border-radius: 10px; font-size: 0.75rem; font-weight: 600; }
.nav-section-cirt { background: #fef2f2; border-left: 3px solid #dc2626; margin: 8px; border-radius: 6px; padding: 4px 0; }
"""
    with open(base_css, "w", encoding="utf-8") as f:
        f.write(css)


# Part 3: Update base.html sidebar
base_html = os.path.join(frontend_dir, "templates", "base.html")
with open(base_html, "r", encoding="utf-8") as f:
    b_html = f.read()

cirt_sidebar = """
        {% if current_user.is_authenticated %}
        {% if current_user.role == 'CIRT' %}
            <div style="font-size: 0.7rem; font-weight: 700; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; margin: 15px 12px 5px 12px;">CIRT PORTAL</div>
            <ul class="nav-links nav-section-cirt">
                <li><a href="/cirt/incidents" {% if active_page == 'cirt_incidents' %}class="active"{% endif %}>🚨 CIRT Incidents</a></li>
                <li><a href="/alerts" {% if active_page == 'alerts' %}class="active"{% endif %}>🔔 Alerts {% if unread_alerts_count and unread_alerts_count > 0 %}<span class="alert-badge">{{ unread_alerts_count }}</span>{% endif %}</a></li>
            </ul>
            <div style="flex-grow: 1;"></div>
        {% else %}
"""

if "{% if current_user.role == 'CIRT' %}" not in b_html:
    # Wrap existing nav-links in else block
    b_html = b_html.replace('        <ul class="nav-links">', cirt_sidebar + '        <ul class="nav-links">')
    # find where bottom user-profile starts and close the endif
    b_html = b_html.replace('        <div class="user-profile dropdown">', '        {% endif %}\n        <div class="user-profile dropdown">')
    # wait, the base.html starts with `        {% if current_user.is_authenticated %}` or similar maybe not.
    # Wait, the prompt says "For ALl OTHER roles, the sidebar remains exactly as it is now. (Profile dropdown at bottom - still available)"
    # I already included `        {% if current_user.is_authenticated %}` in `cirt_sidebar`, I shouldn't if it's already there
    # Let me just restore base.html regex cleanly. I'll read exactly what's there first via script output.

print("done")
