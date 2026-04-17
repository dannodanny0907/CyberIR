/* File: settings.js - Configuration form handlers and API integration */
document.addEventListener('DOMContentLoaded', () => {

    // 1. Tab switching
    const tabs = document.querySelectorAll('.settings-tab')
    const panels = document.querySelectorAll('.tab-panel')
    
    tabs.forEach(tab => {
        tab.addEventListener('click', function() {
            tabs.forEach(t => t.classList.remove('active'))
            panels.forEach(p => p.classList.remove('active'))
            this.classList.add('active')
            const panel = document.getElementById(this.dataset.panel)
            if(panel) panel.classList.add('active')
        })
    })

    // 2. Range sliders — live value update
    document.querySelectorAll('input[type=range]').forEach(slider => {
        const display = document.getElementById(slider.id + 'Display')
        slider.addEventListener('input', function() {
            if (display) {
                display.textContent = Math.round(this.value * 100) + '%'
            }
            updateThresholdIndicator(slider.id, this.value)
        })
        // Initialize exactly safely
        updateThresholdIndicator(slider.id, slider.value);
    })
    
    function updateThresholdIndicator(id, value) {
        const ind = document.getElementById(id + 'Ind')
        if (!ind) return
        const v = parseFloat(value)
        if (v < 0.4) {
            ind.className = 'threshold-ind ind-loose'
            ind.textContent = 'Very Loose'
        } else if (v < 0.65) {
            ind.className = 'threshold-ind ind-loose'
            ind.textContent = 'Loose'
        } else if (v <= 0.75) {
            ind.className = 'threshold-ind ind-recommended'
            ind.textContent = '✓ Recommended'
        } else {
            ind.className = 'threshold-ind ind-strict'
            ind.textContent = 'Strict'
        }
    }

    // Correlation time window text hook
    document.getElementById('correlation_time_window')?.addEventListener('input', function() {
        const h = parseInt(this.value) || 0;
        const helper = document.getElementById('corrTimeHelper');
        if(helper) helper.textContent = `Current: looks back ${h} hours (${(h/24).toFixed(1)} days)`;
    });

    // 3. SLA live validation
    function validateSLA() {
        const c = parseInt(document.getElementById('critical_sla').value) || 0;
        const h = parseInt(document.getElementById('high_sla').value) || 0;
        const m = parseInt(document.getElementById('medium_sla').value) || 0;
        const l = parseInt(document.getElementById('low_sla').value) || 0;
        const ind = document.getElementById('slaIndicator')
        const sBtn = document.getElementById('saveSlaBtn')
        
        document.getElementById('critSlaVal').textContent = c;
        document.getElementById('highSlaVal').textContent = h;
        document.getElementById('medSlaVal').textContent = m;
        document.getElementById('lowSlaVal').textContent = l;
        
        if (c < h && h < m && m < l) {
            ind.className = 'validation-ind valid'
            ind.textContent = '✅ SLA hierarchy is valid'
            if(sBtn) sBtn.disabled = false;
            return true
        } else {
            ind.className = 'validation-ind invalid'
            ind.textContent = '❌ Each SLA must be larger than the one above'
            if(sBtn) sBtn.disabled = true;
            return false
        }
    }
    
    ['critical_sla','high_sla','medium_sla','low_sla'].forEach(id => {
        document.getElementById(id)?.addEventListener('input', validateSLA)
    })

    // 4. Risk weights live total
    function updateWeightTotal() {
        let total = 0
        document.querySelectorAll('.weight-input').forEach(input => {
            total += parseFloat(input.value) || 0
        })
        total = Math.round(total)
        
        const display = document.getElementById('weightTotal')
        const indicator = document.getElementById('weightIndicator')
        const saveBtn = document.getElementById('saveWeightsBtn')
        
        if (display) display.textContent = total + '%'
        
        const valid = Math.abs(total - 100) < 1
        if (display) {
            display.className = valid ? 'total-display total-valid' : 'total-display total-invalid'
        }
        if (indicator) {
            indicator.textContent = valid ? '✅ Total: 100% — Valid' : '❌ Total: ' + total + '% — Must equal 100%'
            indicator.className = valid ? 'validation-ind valid' : 'validation-ind invalid'
        }
        if (saveBtn) saveBtn.disabled = !valid
        
        // Update formulas
        document.getElementById('f1').textContent = document.getElementById('weight_asset_criticality').value || 0;
        document.getElementById('f2').textContent = document.getElementById('weight_threat_severity').value || 0;
        document.getElementById('f3').textContent = document.getElementById('weight_vulnerability_exposure').value || 0;
        document.getElementById('f4').textContent = document.getElementById('weight_users_affected').value || 0;
        document.getElementById('f5').textContent = document.getElementById('weight_repeat_penalty').value || 0;
        
        updateWeightBars()
    }
    
    function updateWeightBars() {
        document.querySelectorAll('.weight-input').forEach(input => {
            const bar = document.getElementById(input.id + 'Bar')
            if (bar) {
                bar.style.width = Math.min(parseFloat(input.value)||0, 100) + '%'
            }
        })
    }
    
    document.querySelectorAll('.weight-input').forEach(inp => inp.addEventListener('input', updateWeightTotal))
    updateWeightTotal()

    // 5. Incident ID prefix live preview
    document.getElementById('incident_id_prefix')?.addEventListener('input', function() {
        const preview = document.getElementById('prefixPreview')
        if (preview) {
            preview.textContent = 'Next ID will look like: ' + (this.value || 'INC-') + '001'
        }
    })

    // 6. Save functions
    async function bindSave(btnId, endpoint, dataExtractor) {
        document.getElementById(btnId)?.addEventListener('click', async function() {
            const originalText = this.textContent;
            this.textContent = 'Saving...'
            this.disabled = true
            
            const data = dataExtractor();
            
            try {
                const r = await fetch(endpoint, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                })
                const result = await r.json()
                
                this.textContent = result.success ? '✅ Saved!' : '❌ Error'
                if (!result.success) alert(result.message)
            } catch(e) {
                this.textContent = '❌ Request Failed';
            }
            
            this.disabled = false
            setTimeout(() => { this.textContent = originalText }, 2000)
        })
    }

    bindSave('saveAlgorithmBtn', '/settings/algorithm', () => ({
        correlation_threshold: document.getElementById('correlation_threshold').value,
        correlation_time_window_hours: document.getElementById('correlation_time_window').value,
        similarity_threshold: document.getElementById('similarity_threshold').value,
        similarity_result_limit: document.getElementById('similarity_result_limit').value
    }));

    bindSave('saveSlaBtn', '/settings/sla', () => ({
        critical_sla_hours: document.getElementById('critical_sla').value,
        high_sla_hours: document.getElementById('high_sla').value,
        medium_sla_hours: document.getElementById('medium_sla').value,
        low_sla_hours: document.getElementById('low_sla').value
    }));

    bindSave('saveSystemBtn', '/settings/system', () => ({
        organization_name: document.getElementById('organization_name').value,
        incident_id_prefix: document.getElementById('incident_id_prefix').value,
        session_timeout: document.getElementById('session_timeout').value,
        date_format: document.getElementById('date_format').value
    }));

    bindSave('saveWeightsBtn', '/settings/risk-weights', () => ({
        weight_asset_criticality: parseFloat(document.getElementById('weight_asset_criticality').value) / 100.0,
        weight_threat_severity: parseFloat(document.getElementById('weight_threat_severity').value) / 100.0,
        weight_vulnerability_exposure: parseFloat(document.getElementById('weight_vulnerability_exposure').value) / 100.0,
        weight_users_affected: parseFloat(document.getElementById('weight_users_affected').value) / 100.0,
        weight_repeat_penalty: parseFloat(document.getElementById('weight_repeat_penalty').value) / 100.0
    }));

    // 8. Algorithm testing
    document.getElementById('runCorrelationTest')?.addEventListener('click', async function() {
        const incidentId = document.getElementById('testCorrelationIncident').value
        if (!incidentId) {
            alert('Please select an incident')
            return
        }
        
        this.textContent = '⏳ Running...'
        this.disabled = true
        
        try {
            const r = await fetch('/settings/test-correlation?incident_id=' + incidentId)
            const data = await r.json()
            
            const box = document.getElementById('correlationTestResults')
            box.style.display = 'block'
            
            if (data.clustered) {
                box.innerHTML = 
                    `<div class="test-result success">✅ Clustered: Yes</div>
                     <div class="test-result info">Cluster ID: ${data.cluster_id}</div>
                     <div class="test-result info">Matched Incidents: ${data.matches? data.matches.join(', ') : 'None'}</div>
                     <div class="test-result info">Action: ${data.action}</div>`
            } else {
                box.innerHTML = 
                    `<div class="test-result neutral">ℹ️ No correlations found above threshold</div>`
            }
        } catch(e) {
            alert('Failed to connect to testing service.');
        }
        
        this.textContent = 'Run Correlation Test'
        this.disabled = false
    })

    document.getElementById('runSimilarityTest')?.addEventListener('click', async function() {
        const incidentId = document.getElementById('testSimilarityIncident').value
        if (!incidentId) {
            alert('Please select an incident')
            return
        }
        
        this.textContent = '⏳ Running...'
        this.disabled = true
        
        try {
            const r = await fetch('/settings/test-similarity?incident_id=' + incidentId)
            const data = await r.json()
            
            const box = document.getElementById('similarityTestResults')
            box.style.display = 'block'
            
            if (data.found && data.matches && data.matches.length > 0) {
                let mHtml = `<div class="test-result success">✅ Matches Found: ${data.matches.length}</div>`;
                data.matches.forEach(m => {
                    mHtml += `<div class="test-result info">${m.incident_id} — ${Math.round(m.score*100)}% match</div>`;
                });
                box.innerHTML = mHtml;
            } else {
                box.innerHTML = 
                    `<div class="test-result neutral">ℹ️ No similar incidents found</div>`
            }
        } catch(e) {
            alert('Failed to connect to testing service.');
        }
        
        this.textContent = 'Run Similarity Test'
        this.disabled = false
    })

    // 9. Reset to defaults
    const resetInput = document.getElementById('resetConfirmInput')
    const resetBtn = document.getElementById('resetDefaultsBtn')
    
    resetInput?.addEventListener('input', function() {
        if (resetBtn) {
            resetBtn.disabled = this.value.toUpperCase() !== 'RESET'
        }
    })
    
    resetBtn?.addEventListener('click', async function() {
        if (!confirm('Reset ALL settings to defaults? This cannot be undone.')) return
        
        try {
            const r = await fetch('/settings/reset-defaults', {method: 'POST'})
            const d = await r.json()
            if (d.success) {
                alert('Settings reset to defaults.')
                window.location.reload()
            }
        } catch(e) {
            alert('Request failed');
        }
    })
});

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
