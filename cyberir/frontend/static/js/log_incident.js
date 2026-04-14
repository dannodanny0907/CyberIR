document.addEventListener('DOMContentLoaded', () => {
    // 1. Initial datetime
    const dateInput = document.getElementById('reported_date');
    if (dateInput && !dateInput.value) {
        const now = new Date();
        now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
        dateInput.value = now.toISOString().slice(0, 16);
    }
    
    // 2. Risk Score Calculator
    const severityInput = document.getElementById('threat_severity');
    const criticalityInput = document.getElementById('asset_criticality');
    const exposureInput = document.getElementById('vulnerability_exposure');
    const usersAffectedInput = document.getElementById('users_affected');
    const isRepeatCheck = document.getElementById('is_repeat');
    const previewBox = document.getElementById('riskPreviewBox');
    const scoreDisplay = document.getElementById('riskScoreDisplay');
    const priorityBadge = document.getElementById('priorityBadgePreview'); // Match exact case here!
    
    const calculateRisk = () => {
        const crit = parseInt(criticalityInput.value) || 0;
        const sev = parseInt(severityInput.value) || 0;
        const exp = parseInt(exposureInput.value) || 0;
        const users = parseInt(usersAffectedInput.value) || 0;
        const repeat = isRepeatCheck.checked;
        
        let usersScore = 1;
        if (users === 0) usersScore = 1;
        else if (users <= 5) usersScore = 2;
        else if (users <= 20) usersScore = 3;
        else if (users <= 100) usersScore = 4;
        else usersScore = 5;
        
        if (crit === 0 || sev === 0 || exp === 0) {
            scoreDisplay.textContent = '---';
            priorityBadge.textContent = 'Pending Data';
            priorityBadge.style.color = '#64748b';
            priorityBadge.style.backgroundColor = '#f1f5f9';
            priorityBadge.style.borderColor = '#cbd5e1';
            previewBox.style.background = 'linear-gradient(135deg, #f8fafc, #f1f5f9)';
            previewBox.style.borderColor = '#cbd5e1';
            scoreDisplay.style.color = '#94a3b8';
            return;
        }

        const rawScore = (crit * 0.3) + (sev * 0.3) + (exp * 0.15) + (usersScore * 0.2) + ((repeat ? 5 : 1) * 0.05);
        const riskScore = ((rawScore / 5) * 100).toFixed(2);
        scoreDisplay.textContent = riskScore + '%';
        
        let priority = '';
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
        
        priorityBadge.textContent = priority;
        priorityBadge.style.color = color;
        priorityBadge.style.borderColor = border;
        priorityBadge.style.backgroundColor = bg;
        previewBox.style.borderColor = border;
        previewBox.style.background = `linear-gradient(135deg, #ffffff, ${bg})`; 
        scoreDisplay.style.color = color;
    };
    
    // Attach event listeners
    [criticalityInput, severityInput, exposureInput, usersAffectedInput, isRepeatCheck].forEach(el => {
        if (el) el.addEventListener('input', calculateRisk);
    });
    calculateRisk();
    
    // 3. Validation
    const form = document.getElementById('logIncidentForm');
    const submitBtn = document.getElementById('submitBtn');
    
    if (form) {
        form.addEventListener('submit', (e) => {
            if (!validateIncidentForm()) {
                e.preventDefault();
            } else {
                if (typeof setButtonLoading === 'function') {
                    setButtonLoading(submitBtn, true, '🛡️ Logging...');
                } else {
                    submitBtn.disabled = true;
                    submitBtn.innerHTML = '🛡️ Logging incident...';
                }
            }
        });
    }

    document.querySelectorAll('input, select, textarea').forEach(field => {
        field.addEventListener('input', function() {
            this.classList.remove('field-error');
            this.style.borderColor = '';
            const err = document.getElementById(this.id + '_error');
            if (err) err.remove();
        });
    });
});

function validateIncidentForm() {
    clearAllErrors()
    let isValid = true
    let firstError = null

    // Title validation
    const title = document.getElementById('title')?.value.trim()
    if (!title) {
        showError('title', 'Incident title is required')
        if (!firstError) firstError = 'title'
        isValid = false
    } else if (title.length < 5) {
        showError('title', 'Title must be at least 5 characters')
        if (!firstError) firstError = 'title'
        isValid = false
    } else if (title.length > 200) {
        showError('title', 'Title must be under 200 characters')
        isValid = false
    }

    // Incident type validation
    const type = document.getElementById('incident_type')?.value
    if (!type) {
        showError('incident_type', 'Please select an incident type')
        if (!firstError) firstError = 'incident_type'
        isValid = false
    }

    // Affected asset validation
    const asset = document.getElementById('affected_asset')?.value.trim()
    if (!asset) {
        showError('affected_asset', 'Affected asset is required')
        if (!firstError) firstError = 'affected_asset'
        isValid = false
    }

    // Asset criticality validation
    const criticality = document.getElementById('asset_criticality')?.value
    if (!criticality || criticality === '') {
        showError('asset_criticality', 'Please rate the asset criticality')
        if (!firstError) firstError = 'asset_criticality'
        isValid = false
    }

    // Threat severity validation
    const severity = document.getElementById('threat_severity')?.value
    if (!severity || severity === '') {
        showError('threat_severity', 'Please rate the threat severity')
        if (!firstError) firstError = 'threat_severity'
        isValid = false
    }

    // Vulnerability exposure validation
    const exposure = document.getElementById('vulnerability_exposure')?.value
    if (!exposure || exposure === '') {
        showError('vulnerability_exposure', 'Please rate the vulnerability exposure')
        if (!firstError) firstError = 'vulnerability_exposure'
        isValid = false
    }

    // Users affected validation
    const usersAffected = parseInt(document.getElementById('users_affected')?.value)
    if (isNaN(usersAffected) || usersAffected < 0) {
        showError('users_affected', 'Users affected must be 0 or more')
        isValid = false
    }

    // IP address validation (optional but if filled)
    const ip = document.getElementById('ip_address')?.value.trim()
    if (ip && !isValidIP(ip)) {
        showError('ip_address', 'Please enter a valid IP address')
        isValid = false
    }

    // Scroll to first error
    if (firstError) {
        const el = document.getElementById(firstError)
        if (el) {
            el.scrollIntoView({ behavior: 'smooth', block: 'center' })
            el.focus()
        }
    }

    return isValid
}

function isValidIP(ip) {
    const ipv4 = /^(\d{1,3}\.){3}\d{1,3}$/
    const ipv6 = /^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$/
    if (ipv4.test(ip)) {
        return ip.split('.').every(part => parseInt(part) <= 255)
    }
    return ipv6.test(ip) || ip === 'localhost'
}

function showError(fieldId, message) {
    const field = document.getElementById(fieldId)
    if (!field) return
    field.classList.add('field-error')
    field.style.borderColor = '#dc2626'

    let errorEl = document.getElementById(fieldId + '_error')
    if (!errorEl) {
        errorEl = document.createElement('div')
        errorEl.id = fieldId + '_error'
        errorEl.className = 'field-error-msg'
        field.parentNode.insertBefore(errorEl, field.nextSibling)
    }
    errorEl.textContent = '⚠ ' + message
}

function clearAllErrors() {
    document.querySelectorAll('.field-error').forEach(f => {
        f.classList.remove('field-error')
        f.style.borderColor = ''
    })
    document.querySelectorAll('.field-error-msg').forEach(e => e.remove())
}
