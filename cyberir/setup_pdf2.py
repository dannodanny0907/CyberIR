import os

base_dir = r"c:\Users\PDM\Pictures\CYBER\cyberir"
frontend_dir = os.path.join(base_dir, "frontend")
backend_dir = os.path.join(base_dir, "backend")

# Part 3 and 4: incident_detail.html
det_html_path = os.path.join(frontend_dir, "templates", "incident_detail.html")
with open(det_html_path, "r", encoding="utf-8") as f:
    d_html = f.read()

pdf_btn = """                {% if current_user.has_admin_privileges or current_user.role == 'Admin' or (current_user.id == incident.assigned_to) or (current_user.id == incident.created_by) or not incident.escalated_to_cirt %}
                <button class="btn-pdf-export" id="exportPdfBtn" data-incident-id="{{ incident.incident_id }}" style="margin-right:8px; display:inline-flex; align-items:center; gap:6px;">📄 Export PDF</button>
                {% endif %}"""

if "id=\"exportPdfBtn\"" not in d_html:
    # insert next to edit button
    # Actually wait, the prompt says "In templates/incident_detail.html, in the top area of the left column (near the Edit and Delete buttons), add:"
    # I will just place it right before the Edit button if found.
    # Look for `<a href="/incidents/{{ incident.incident_id }}/edit"`
    if '<a href="/incidents/{{ incident.incident_id }}/edit"' in d_html:
        d_html = d_html.replace(
            '<a href="/incidents/{{ incident.incident_id }}/edit"',
            pdf_btn + '\n                <a href="/incidents/{{ incident.incident_id }}/edit"'
        )

pdf_modal = """
<div id="pdfPreviewModal" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,0.7);z-index:9999;align-items:center;justify-content:center;overflow-y:auto">
  <div style="background:white;width:700px;max-width:95vw;margin:20px auto;border-radius:12px;overflow:hidden;box-shadow:0 25px 60px rgba(0,0,0,0.4)">
    <div style="background:#1e40af;padding:16px 24px;display:flex;justify-content:space-between;align-items:center">
      <span style="color:white;font-weight:700;font-size:1rem">📄 Incident Report Preview</span>
      <button onclick="closePdfModal()" style="background:none;border:none;color:white;font-size:1.3rem;cursor:pointer">×</button>
    </div>
    <div style="padding:16px 24px;background:#f8fafc;border-bottom:1px solid #e2e8f0">
      <p style="font-size:0.85rem;color:#64748b;margin:0 0 12px">
        Review and edit the validation names before downloading. These changes apply to this download only.
      </p>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
        <div>
          <label style="font-size:0.8rem;font-weight:600;color:#374151;display:block;margin-bottom:4px">Cybersecurity Engineer</label>
          <input type="text" id="pdfEngineerName" style="width:100%;padding:7px 10px;border:1px solid #d1d5db;border-radius:6px;font-size:0.875rem;box-sizing:border-box">
        </div>
        <div>
          <label style="font-size:0.8rem;font-weight:600;color:#374151;display:block;margin-bottom:4px">Technical Services Manager</label>
          <input type="text" id="pdfManagerName" style="width:100%;padding:7px 10px;border:1px solid #d1d5db;border-radius:6px;font-size:0.875rem;box-sizing:border-box">
        </div>
      </div>
    </div>
    <div id="pdfPreviewContent" style="padding:24px;max-height:60vh;overflow-y:auto;font-family:'Times New Roman',serif;font-size:12px;line-height:1.5;color:#111">
      <div style="text-align:center;padding:40px"><div style="font-size:1.5rem">⏳</div><div>Loading preview...</div></div>
    </div>
    <div style="padding:16px 24px;border-top:1px solid #e2e8f0;display:flex;justify-content:flex-end;gap:12px">
      <button onclick="closePdfModal()" style="padding:9px 20px;border:1px solid #d1d5db;background:white;border-radius:6px;cursor:pointer;font-size:0.875rem">Cancel</button>
      <button id="downloadPdfBtn" style="padding:9px 20px;background:#1e40af;color:white;border:none;border-radius:6px;cursor:pointer;font-size:0.875rem;font-weight:600">⬇️ Download PDF</button>
    </div>
  </div>
</div>
"""
if "id=\"pdfPreviewModal\"" not in d_html:
    d_html = d_html.replace('</body>', pdf_modal + '\n</body>')
    with open(det_html_path, "w", encoding="utf-8") as f:
        f.write(d_html)

# Add CSS
det_css_path = os.path.join(frontend_dir, "static", "css", "incident_detail.css")
with open(det_css_path, "a", encoding="utf-8") as f:
    f.write("""
.btn-pdf-export {
    background: #1e40af;
    color: white;
    border: none;
    padding: 7px 14px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 0.875rem;
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-weight: 500;
}
.btn-pdf-export:hover { background: #1e3a8a; }
""")

# Part 5 & 8: app.py updates for Weasyprint and Routes
app_py_path = os.path.join(backend_dir, "app.py")
with open(app_py_path, "r", encoding="utf-8") as f:
    app_text = f.read()

weasyprint_init = """
try:
    from weasyprint import HTML as WeasyHTML
    PDF_LIBRARY = 'weasyprint'
except ImportError:
    try:
        from xhtml2pdf import pisa
        PDF_LIBRARY = 'xhtml2pdf'
    except ImportError:
        PDF_LIBRARY = None

def generate_pdf_from_html(html_string):
    if PDF_LIBRARY == 'weasyprint':
        pdf_bytes = WeasyHTML(string=html_string).write_pdf()
        return pdf_bytes
    elif PDF_LIBRARY == 'xhtml2pdf':
        from io import BytesIO
        result = BytesIO()
        pisa.CreatePDF(html_string, dest=result)
        return result.getvalue()
    else:
        return None
"""

if "PDF_LIBRARY =" not in app_text:
    app_text = app_text.replace("from flask import", weasyprint_init + "\nfrom flask import", 1)

pdf_routes = """
from flask import render_template_string

@app.route('/incidents/pdf-data/<incident_id>')
@login_required
def get_pdf_data(incident_id):
    conn = get_db_connection()
    incident = conn.execute("SELECT * FROM incidents WHERE incident_id=?", [incident_id]).fetchone()
    if not incident:
        conn.close()
        return jsonify({"success": False, "message": "Incident not found"}), 404
        
    user_row = conn.execute("SELECT full_name FROM users WHERE id=?", [incident['assigned_to']]).fetchone()
    assigned_name = user_row['full_name'] if user_row else ''
    
    eng = conn.execute("SELECT setting_value FROM settings WHERE setting_key='pdf_cybersecurity_engineer'").fetchone()
    mgr = conn.execute("SELECT setting_value FROM settings WHERE setting_key='pdf_technical_services_manager'").fetchone()
    conn.close()
    
    return jsonify({
        "success": True,
        "incident": dict(incident),
        "assigned_name": assigned_name,
        "default_engineer": eng['setting_value'] if eng else 'CHABVUTAGONDO .T.',
        "default_manager": mgr['setting_value'] if mgr else 'MUCHOVO .R.'
    })

@app.route('/incidents/generate-pdf/<incident_id>', methods=['POST'])
@login_required
def generate_pdf(incident_id):
    data = request.json
    engineer_name = data.get('engineer_name', '')
    manager_name = data.get('manager_name', '')
    
    conn = get_db_connection()
    incident = conn.execute("SELECT * FROM incidents WHERE incident_id=?", [incident_id]).fetchone()
    user_row = conn.execute("SELECT full_name FROM users WHERE id=?", [incident['assigned_to']]).fetchone() if incident and incident['assigned_to'] else None
    assigned_name = user_row['full_name'] if user_row else ''
    conn.close()
    
    if not incident:
        return jsonify({"success": False, "message": "Not found"}), 404
        
    html_content = render_template('incident_pdf.html',
        incident=dict(incident),
        assigned_name=assigned_name,
        engineer_name=engineer_name,
        manager_name=manager_name
    )
    
    pdf_bytes = generate_pdf_from_html(html_content)
    if pdf_bytes is None:
        return jsonify({"success": False, "message": "PDF library not installed"}), 500
        
    return Response(pdf_bytes, mimetype='application/pdf', headers={'Content-Disposition': f'attachment; filename="{incident_id}_report.pdf"'})

@app.template_filter('format_date')
def format_date_filter(value):
    if not value: return '—'
    try:
        from datetime import datetime
        if isinstance(value, str): dt = datetime.fromisoformat(value.replace('Z',''))
        else: dt = value
        return dt.strftime('%d %B %Y, %H:%M')
    except:
        return str(value)
"""

if "@app.route('/incidents/pdf-data/" not in app_text:
    app_text = app_text.replace("def incident_detail(incident_id):", pdf_routes + "\n@app.route('/incidents/<incident_id>')\n@login_required\ndef incident_detail(incident_id):")

with open(app_py_path, "w", encoding="utf-8") as f:
    f.write(app_text)

# Part 7: incident_detail.js
js_path = os.path.join(frontend_dir, "static", "js", "incident_detail.js")
if os.path.exists(js_path):
    with open(js_path, "a", encoding="utf-8") as f:
        f.write("""
// PDF Export logic
document.getElementById('exportPdfBtn')?.addEventListener('click', async function() {
    const incidentId = this.dataset.incidentId;
    const modal = document.getElementById('pdfPreviewModal');
    modal.style.display = 'flex';
    
    const r = await fetch('/incidents/pdf-data/' + incidentId);
    const data = await r.json();
    
    document.getElementById('pdfEngineerName').value = data.default_engineer;
    document.getElementById('pdfManagerName').value = data.default_manager;
    
    renderPdfPreview(data.incident, data.assigned_name, data.default_engineer, data.default_manager);
});

function renderPdfPreview(incident, assignedName, engineerName, managerName) {
    const preview = document.getElementById('pdfPreviewContent');
    preview.innerHTML = `
    <div style="font-family:'Times New Roman',serif;font-size:11pt;color:#111;padding:8px">
      <div style="text-align:center;margin-bottom:12px;padding-bottom:8px;border-bottom:2px solid #1a4731">
        <strong style="font-size:13pt;color:#1a4731">CHINHOYI UNIVERSITY OF TECHNOLOGY</strong><br>
        <strong>ICT — Cybersecurity Incident Report Form</strong>
      </div>
      <p><strong>Case Number:</strong> ${incident.incident_id} &nbsp;&nbsp; <strong>Date:</strong> ${incident.reported_date}<br>
        <strong>Detection Method:</strong> ${incident.detection_method || '—'}</p><hr>
      <strong>1. Contact Information</strong><p>Full Name: ${incident.contact_full_name || '—'}<br>
         Job Title: ${incident.contact_job_title || '—'}<br>Office: ${incident.contact_office || '—'}<br>
         Work Phone: ${incident.contact_work_phone || '—'}<br>Mobile: ${incident.contact_mobile_phone || '—'}</p><hr>
      <strong>2. Incident Details</strong><p>Type: ${incident.incident_type || '—'}<br>Description: ${incident.description || '—'}</p><hr>
      <strong>3. Impact</strong><p>${incident.impact_selections || '—'}</p><hr>
      <strong>4. Data Sensitivity</strong><p>${incident.data_sensitivity_selections || '—'}</p><hr>
      <strong>5. Systems Affected</strong><p>Attack Source: ${incident.attack_source || '—'}<br>
         Affected IPs: ${incident.affected_system_ips || '—'}<br>OS: ${incident.affected_system_os || '—'}<br>
         Location: ${incident.affected_system_location || '—'}</p><hr>
      <strong>6. Risk Assessment</strong><p>Risk Score: ${incident.risk_score}/100<br>Severity: <strong>${incident.priority || incident.severity}</strong></p><hr>
      <strong>7. Validation</strong><br><br><em>Officer Responsible:</em><br>
      ${assignedName || '—'}&nbsp;&nbsp; ____________________________ Name / ____________________________ Sign / ________________ Date<br><br>
      <em>Cybersecurity Engineer:</em><br><span id="previewEngineerName">${engineerName}</span>&nbsp;&nbsp;
      ____________________________ Sign / ________________ Date<br><br>
      <em>Technical Services Manager:</em><br><span id="previewManagerName">${managerName}</span>&nbsp;&nbsp;
      ____________________________ Sign / ________________ Date
    </div>`;
}

document.getElementById('pdfEngineerName')?.addEventListener('input', function() {
    const span = document.getElementById('previewEngineerName');
    if (span) span.textContent = this.value;
});
document.getElementById('pdfManagerName')?.addEventListener('input', function() {
    const span = document.getElementById('previewManagerName');
    if (span) span.textContent = this.value;
});

document.getElementById('downloadPdfBtn')?.addEventListener('click', async function() {
    const incidentId = document.getElementById('exportPdfBtn').dataset.incidentId;
    const engineerName = document.getElementById('pdfEngineerName').value;
    const managerName = document.getElementById('pdfManagerName').value;
    
    this.textContent = '⏳ Generating...';
    this.disabled = true;
    
    const r = await fetch('/incidents/generate-pdf/' + incidentId, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ engineer_name: engineerName, manager_name: managerName })
    });
    
    if (r.ok) {
        const blob = await r.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = incidentId + '_report.pdf';
        a.click();
        URL.revokeObjectURL(url);
        closePdfModal();
    } else {
        alert('PDF generation failed.');
    }
    this.textContent = '⬇️ Download PDF';
    this.disabled = false;
});

function closePdfModal() {
    const m = document.getElementById('pdfPreviewModal');
    if(m) m.style.display = 'none';
}
""")

print("done pdf files")
