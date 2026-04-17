/* File: incident_detail.js - Logic for incident actions, resolution, and similarities */
document.addEventListener('DOMContentLoaded', () => {
    // 1. Assign Incident
    const showAssignBtn = document.getElementById('showAssignBtn');
    const assignForm = document.getElementById('assignForm');
    const displayName = document.getElementById('displayAssignedName');

    if (showAssignBtn && assignForm) {
        showAssignBtn.addEventListener('click', () => {
            assignForm.style.display = 'block';
            showAssignBtn.style.display = 'none';
        });

        assignForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const id = assignForm.dataset.incidentId;
            const formData = new FormData(assignForm);
            
            try {
                const response = await fetch(`/incidents/assign/${id}`, {
                    method: 'POST',
                    body: formData
                });
                const result = await response.json();
                if (result.success) {
                    displayName.textContent = result.assigned_name;
                    displayName.style.color = 'inherit';
                    assignForm.style.display = 'none';
                    showAssignBtn.style.display = 'block';
                    window.location.reload(); 
                } else {
                    alert(result.message);
                }
            } catch (err) {
                alert('An error occurred updating assignment.');
            }
        });
    }

    // 2 & 3. Update Status and Resolve
    document.querySelectorAll('.status-form').forEach(form => {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const id = form.dataset.incidentId;
            const status = form.dataset.status;
            
            if (!confirm(`Are you sure you want to change status to ${status}?`)) return;

            const formData = new FormData();
            formData.append('new_status', status);

            try {
                const response = await fetch(`/incidents/update-status/${id}`, {
                    method: 'POST',
                    body: formData
                });
                const result = await response.json();
                if (result.success) {
                    window.location.reload();
                } else {
                    alert(result.message);
                }
            } catch (err) {
                alert('Update failed');
            }
        });
    });

    const resolveBtn = document.getElementById('markResolvedBtn');
    const resolvePanel = document.getElementById('resolvePanel');
    const resolveForm = document.getElementById('resolveForm');

    if (resolveBtn && resolvePanel && resolveForm) {
        resolveBtn.addEventListener('click', () => {
            resolvePanel.style.display = 'block';
            resolveBtn.style.display = 'none';
        });

        resolveForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const id = resolveForm.dataset.incidentId;
            const formData = new FormData(resolveForm);

            try {
                const response = await fetch(`/incidents/resolve/${id}`, {
                    method: 'POST',
                    body: formData
                });
                const result = await response.json();
                if (result.success) {
                    window.location.reload();
                } else {
                    alert(result.message);
                }
            } catch (err) {
                alert('Resolution failed');
            }
        });
    }

    // 4. Risk bar animation
    const riskFill = document.querySelector('.risk-score-fill-large');
    if (riskFill) {
        const riskScore = parseFloat(document.getElementById('riskScoreValue')?.textContent || '0') || 0;
        setTimeout(() => {
            riskFill.style.width = riskScore + '%';
        }, 300);
    }

    // 5. Time Ago Formatting
    const timeAgoElements = document.querySelectorAll('.time-ago');
    timeAgoElements.forEach(el => {
        const timestamp = el.dataset.time;
        if (!timestamp || timestamp === 'None') {
            el.textContent = 'Never';
            return;
        }
        
        // Convert to UTC Date 
        const dateStr = timestamp.replace(' ', 'T') + 'Z'; 
        const date = new Date(dateStr);
        const now = new Date();
        const diffSeconds = Math.floor((now - date) / 1000);
        
        if (diffSeconds < 60) el.textContent = 'just now';
        else if (diffSeconds < 3600) el.textContent = Math.floor(diffSeconds/60) + ' mins ago';
        else if (diffSeconds < 86400) el.textContent = Math.floor(diffSeconds/3600) + ' hrs ago';
        else if (diffSeconds < 2592000) el.textContent = Math.floor(diffSeconds/86400) + ' days ago';
        else el.textContent = date.toLocaleDateString();
    });

    // 6. Delete Logic Detail Page
    const detailDeleteBtn = document.getElementById('detailDeleteBtn');
    const deleteModalOverlay = document.getElementById('deleteModalOverlay');
    const deleteModalCancel = document.getElementById('deleteModalCancel');
    const deleteModalConfirm = document.getElementById('deleteModalConfirm');
    
    if (detailDeleteBtn && deleteModalOverlay) {
        detailDeleteBtn.addEventListener('click', () => {
            deleteModalOverlay.style.display = 'flex';
        });

        const closeDeleteModal = () => {
            deleteModalOverlay.style.display = 'none';
        };

        if (deleteModalCancel) deleteModalCancel.addEventListener('click', closeDeleteModal);
        
        window.addEventListener('click', (e) => {
            if (e.target === deleteModalOverlay) closeDeleteModal();
        });

        if (deleteModalConfirm) {
            deleteModalConfirm.addEventListener('click', async () => {
                deleteModalConfirm.textContent = 'Deleting...';
                deleteModalConfirm.disabled = true;
                if (!window.INCIDENT_ID) return;
                
                try {
                    const response = await fetch(`/incidents/delete/${window.INCIDENT_ID}`, { method: 'POST' });
                    const result = await response.json();
                    if (result.success) {
                        window.location.href = result.redirect;
                    } else {
                        alert(result.message);
                        deleteModalConfirm.textContent = 'Delete Incident';
                        deleteModalConfirm.disabled = false;
                        closeDeleteModal();
                    }
                } catch(e) {
                    alert('Delete failed');
                    deleteModalConfirm.textContent = 'Delete Incident';
                    deleteModalConfirm.disabled = false;
                    closeDeleteModal();
                }
            });
        }
    }

    // --- PHASE 4: SIMILARITY UI ---
    
    const initSimilarityPanel = async () => {
        const incidentIdDataEl = document.getElementById('incidentIdData');
        const similarityPanel = document.getElementById('similarityPanel');
        if (!incidentIdDataEl || !similarityPanel) return;

        const incidentId = incidentIdDataEl.value;
        try {
            const response = await fetch('/api/similarity/' + incidentId);
            const data = await response.json();
            renderSimilarityPanel(data, similarityPanel);
        } catch (error) {
            similarityPanel.innerHTML = '<p class="text-muted" style="text-align:center;color:#94a3b8;font-size:0.85rem;">Could not load similarity data.</p>';
        }
    };

    function formatResolutionTime(minutes) {
        if (!minutes) return null;
        if (minutes < 60) return Math.floor(minutes) + ' minutes';
        const hours = Math.floor(minutes / 60);
        const mins = Math.floor(minutes % 60);
        if (hours < 24) {
            return mins > 0 ? hours + 'h ' + mins + 'm' : hours + 'h';
        }
        const days = Math.floor(hours / 24);
        const remHours = hours % 24;
        return remHours > 0 ? days + 'd ' + remHours + 'h' : days + ' days';
    }

    const renderSimilarityPanel = (data, pnl) => {
        if (!data.found || !data.matches || data.matches.length === 0) {
            pnl.innerHTML = `
                <div style="text-align:center; padding:30px 10px;">
                    <div style="font-size:2.5rem; margin-bottom:10px; color:#cbd5e1;">🔍</div>
                    <div style="font-weight:600; font-size:0.9rem; color:var(--text-primary);">No similar incidents found</div>
                    <div style="font-size:0.8rem; color:var(--text-secondary); margin-top:4px;">No resolved incidents match this profile. This may be a new type of threat.</div>
                </div>
            `;
            return;
        }

        let html = '';
        const bestHtml = data.matches[0].score_percent >= 75 ? 
            `<div style="font-size:0.8rem; color:#166534; font-weight:600; padding-bottom:10px; margin-bottom:10px; border-bottom:1px solid #e2e8f0;">Found ${data.matches.length} similar incident(s)</div>` :
            `<div style="font-size:0.8rem; color:#1e40af; font-weight:600; padding-bottom:10px; margin-bottom:10px; border-bottom:1px solid #e2e8f0;">Found ${data.matches.length} similar incident(s)</div>`;

        html += bestHtml;

        data.matches.forEach(m => {
            let scoreColor = '#64748b';
            if (m.score_percent >= 75) scoreColor = '#16a34a';
            else if (m.score_percent >= 50) scoreColor = '#2563eb';

            html += `
                <div class="similarity-panel-card">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                        <a href="/incidents/${m.incident_id}" class="panel-incident-id">${m.incident_id}</a>
                        <span class="badge" style="background:#f1f5f9; color:#475569;">${m.incident_type}</span>
                        <div class="panel-score-badge" style="color:${scoreColor};">${m.score_percent}%</div>
                    </div>
                    
                    <div class="panel-score-bar">
                        <div style="height:100%; border-radius:2px; background:${scoreColor}; width:${m.score_percent}%;"></div>
                    </div>
                    
                    <div style="font-weight:600; font-size:0.85rem; margin-top:6px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${m.title}</div>
                    
                    <div style="margin-top:10px;">
                        <div style="font-size:0.7rem; color:var(--text-secondary); font-weight:700; text-transform:uppercase;">Why similar:</div>
                        ${m.explanations.map(e => `<div class="panel-why-similar-list">• ${e}</div>`).join('')}
                    </div>
            `;

            if (m.resolution_notes) {
                let resTruncated = m.resolution_notes.length > 80 ? m.resolution_notes.substring(0, 80) + '...' : m.resolution_notes;
                html += `
                    <div class="panel-resolution-text">
                        <span style="font-weight:700; margin-right:4px;">✅ Resolution:</span>${resTruncated}
                    </div>
                `;
            }

            if (m.resolution_time_minutes) {
                html += `
                    <div style="font-size:0.8rem; color:var(--text-secondary); margin-top:6px;">⏱ Resolved in: ${formatResolutionTime(m.resolution_time_minutes)}</div>
                `;
            }

            html += `<div class="panel-buttons">
                        <a href="/incidents/${m.incident_id}" class="btn-secondary" style="text-decoration:none; padding:4px 10px; font-size:0.8rem;">View</a>`;
            
            if (m.resolution_notes && window.IS_RESOLVED === false && (window.USER_ROLE === 'Admin' || window.USER_ROLE === 'Analyst')) {
                html += `<button type="button" class="btn-primary apply-solution-trigger" data-source-id="${m.incident_id}" data-resolution="${encodeURIComponent(m.resolution_notes)}" style="padding:4px 10px; font-size:0.8rem; background:#16a34a; border-color:#16a34a;">Apply Solution</button>`;
            }
            html += `</div></div>`;
        });

        pnl.innerHTML = html;

        // Bind modals
        document.querySelectorAll('.apply-solution-trigger').forEach(btn => {
            btn.addEventListener('click', () => {
                const sourceId = btn.dataset.sourceId;
                const resolution = decodeURIComponent(btn.dataset.resolution);
                
                document.getElementById('applySourceId').textContent = sourceId;
                document.getElementById('applySourceIdLabel').textContent = sourceId;
                document.getElementById('applySourceResolutionText').textContent = resolution;
                document.getElementById('applyResolutionNotes').value = resolution;
                
                document.getElementById('applySolutionForm').dataset.sourceId = sourceId;
                document.getElementById('applySolutionOverlay').style.display = 'flex';
            });
        });
    };

    const applyOverlay = document.getElementById('applySolutionOverlay');
    const applyCancel = document.getElementById('applySolutionCancel');
    if (applyCancel) {
        applyCancel.addEventListener('click', () => {
            applyOverlay.style.display = 'none';
        });
        window.addEventListener('click', (e) => {
            if (e.target === applyOverlay) applyOverlay.style.display = 'none';
        });
    }

    const applyForm = document.getElementById('applySolutionForm');
    if (applyForm) {
        applyForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const sourceId = applyForm.dataset.sourceId;
            const resNotes = document.getElementById('applyResolutionNotes').value;
            
            if (!sourceId || !resNotes) return;
            
            const btn = applyForm.querySelector('.apply-solution-btn-confirm');
            btn.disabled = true;
            btn.textContent = 'Applying...';
            
            const formData = new FormData();
            formData.append('source_incident_id', sourceId);
            formData.append('resolution_notes', resNotes);
            
            try {
                const response = await fetch(`/incidents/apply-solution/${window.INCIDENT_ID}`, {
                    method: 'POST',
                    body: formData
                });
                const result = await response.json();
                if (result.success) {
                    window.location.reload();
                } else {
                    alert(result.message || 'Failed to apply solution.');
                    btn.disabled = false;
                    btn.textContent = 'Apply Solution';
                }
            } catch(e) {
                alert('An error occurred.');
                btn.disabled = false;
                btn.textContent = 'Apply Solution';
            }
        });
    }

    initSimilarityPanel();
});

// PDF Export logic
document.getElementById('exportPdfBtn')?.addEventListener('click', async function() {
    const incidentId = this.dataset.incidentId;
    const modal = document.getElementById('pdfPreviewModal');
    modal.style.display = 'flex';
    
    const r = await fetch('/incidents/pdf-data/' + incidentId);
    const data = await r.json();
    
    document.getElementById('pdfEngineerName').value = data.default_engineer;
    document.getElementById('pdfManagerName').value = data.default_manager;
    
    renderPdfPreview(data.incident, data.assigned_name, data.default_engineer, data.default_manager, data.logo_data);
});

function renderPdfPreview(incident, assignedName, engineerName, managerName, logoData) {
    const preview = document.getElementById('pdfPreviewContent');
    const logoHtml = logoData 
        ? `<img src="${logoData}" alt="CUT Logo" style="width:60px; height:auto; margin-right: 15px;">` 
        : `<div style="width:50px;height:50px;background:#1a4731;border-radius:50%;text-align:center;line-height:50px;color:white;font-weight:bold;font-size:14pt;margin-right:15px;">CUT</div>`;

    preview.innerHTML = `
    <div style="font-family:'Times New Roman',serif;font-size:11pt;color:#111;padding:8px">
      <div style="display:flex; align-items:center; justify-content:center; margin-bottom:12px; padding-bottom:8px; border-bottom:2px solid #1a4731">
        ${logoHtml}
        <div style="text-align:center;">
          <strong style="font-size:13pt;color:#1a4731">CHINHOYI UNIVERSITY OF TECHNOLOGY</strong><br>
          <strong>ICT — Cybersecurity Incident Report Form</strong>
        </div>
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
