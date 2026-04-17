import os

base_dir = r"c:\Users\PDM\Pictures\CYBER\cyberir"
frontend_dir = os.path.join(base_dir, "frontend")
backend_dir = os.path.join(base_dir, "backend")

# Part 2: Update settings.html
settings_html_path = os.path.join(frontend_dir, "templates", "settings.html")
with open(settings_html_path, "r", encoding="utf-8") as f:
    s_html = f.read()

pdf_tab_btn = """        {% if current_user.role == 'Admin' %}
        <button class="tab-btn" data-target="pdf-config">📄 PDF Configuration</button>
        {% endif %}"""

pdf_tab_content = """
    {% if current_user.role == 'Admin' %}
    <div class="tab-content" id="pdf-config" style="display: none;">
        <div class="card">
            <div class="card-header">
                <div class="card-title">📄 PDF Report Configuration</div>
            </div>
            <div class="card-body">
                <p style="font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 20px;">
                    Configure default names for incident report validation. Only the Administrator can change these settings.
                </p>
                <div class="form-grid">
                    <div>
                        <label class="form-label" for="pdf_cybersecurity_engineer">Default Cybersecurity Engineer Name</label>
                        <input type="text" id="pdf_cybersecurity_engineer" name="pdf_cybersecurity_engineer" class="form-input" 
                               value="{{ settings.get('pdf_cybersecurity_engineer', 'CHABVUTAGONDO .T.') }}" 
                               placeholder="Full name and initial">
                        <div style="font-size: 0.75rem; color: var(--text-secondary); margin-top: 4px;">Appears in the Validation section of all PDF reports</div>
                    </div>
                    <div>
                        <label class="form-label" for="pdf_technical_services_manager">Default Technical Services Manager Name</label>
                        <input type="text" id="pdf_technical_services_manager" name="pdf_technical_services_manager" class="form-input" 
                               value="{{ settings.get('pdf_technical_services_manager', 'MUCHOVO .R.') }}" 
                               placeholder="Full name and initial">
                        <div style="font-size: 0.75rem; color: var(--text-secondary); margin-top: 4px;">Appears in the Validation section of all PDF reports</div>
                    </div>
                </div>
                <div style="margin-top: 20px;">
                    <button class="btn-primary" id="savePdfConfigBtn">💾 Save PDF Configuration</button>
                </div>
            </div>
        </div>
    </div>
    {% endif %}
"""

if "data-target=\"pdf-config\"" not in s_html:
    # insert tab btn
    s_html = s_html.replace(
        '</nav>',
        pdf_tab_btn + '\n    </nav>'
    )
    # insert tab content at bottom of tabs wrapper
    s_html = s_html.replace(
        '</div>\n{% endblock %}',
        pdf_tab_content + '\n</div>\n{% endblock %}'
    )
    with open(settings_html_path, "w", encoding="utf-8") as f:
        f.write(s_html)

# Update settings.js
settings_js_path = os.path.join(frontend_dir, "static", "js", "settings.js")
if os.path.exists(settings_js_path):
    with open(settings_js_path, "a", encoding="utf-8") as f:
        f.write("""
document.getElementById('savePdfConfigBtn')?.addEventListener('click', async function() {
  this.textContent = 'Saving...';
  this.disabled = true;
  const data = {
    pdf_cybersecurity_engineer: document.getElementById('pdf_cybersecurity_engineer').value,
    pdf_technical_services_manager: document.getElementById('pdf_technical_services_manager').value
  };
  try {
    const r = await fetch('/settings/pdf-config', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(data)
    });
    const result = await r.json();
    this.textContent = result.success ? '✅ Saved!' : '❌ Error';
  } catch(e) {
    this.textContent = '❌ Error';
  }
  this.disabled = false;
  setTimeout(() => {
    this.textContent = '💾 Save PDF Configuration';
  }, 2500);
});
""")

# Part 5: Update app.py for settings save route
app_py = os.path.join(backend_dir, "app.py")
with open(app_py, "r", encoding="utf-8") as f:
    app_text = f.read()

pdf_route = """
@app.route('/settings/pdf-config', methods=['POST'])
@login_required
def save_pdf_config():
    if current_user.role != 'Admin':
        return jsonify({"success": False, "message": "Access denied"}), 403
    data = request.json
    engineer = data.get('pdf_cybersecurity_engineer', '')
    manager = data.get('pdf_technical_services_manager', '')
    
    conn = get_db_connection()
    # update or insert
    for k, v in [('pdf_cybersecurity_engineer', engineer), ('pdf_technical_services_manager', manager)]:
        row = conn.execute("SELECT setting_key FROM settings WHERE setting_key=?", [k]).fetchone()
        if row:
            conn.execute("UPDATE settings SET setting_value=? WHERE setting_key=?", [v, k])
        else:
            conn.execute("INSERT INTO settings (setting_key, setting_value) VALUES (?, ?)", [k, v])
            
    conn.execute("INSERT INTO activity_logs (user_id, action_type, target_type, details) VALUES (?, 'UPDATE_SETTINGS', 'Settings', 'Updated PDF Configuration')", [current_user.id])
    conn.commit()
    conn.close()
    return jsonify({"success": True})
"""
if "@app.route('/settings/pdf-config'" not in app_text:
    app_text = app_text.replace("def settings():\n", pdf_route + "\n\ndef settings():\n")

with open(app_py, "w", encoding="utf-8") as f:
    f.write(app_text)

print("done parts 2")
