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
            let isValid = true;
            let firstErrorEl = null;
            document.querySelectorAll('.error-msg').forEach(e => e.style.display = 'none');
            
            const reqFields = ['title', 'incident_type', 'affected_asset', 'asset_criticality', 'threat_severity', 'vulnerability_exposure'];
            
            reqFields.forEach(id => {
                const el = document.getElementById(id);
                if (!el.value) {
                    isValid = false;
                    const err = document.getElementById(id + 'Error');
                    if (err) err.style.display = 'block';
                    if (!firstErrorEl) firstErrorEl = el;
                }
            });
            
            if (!isValid) {
                e.preventDefault();
                firstErrorEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
                firstErrorEl.focus();
            } else {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '🛡️ Logging incident...';
                form.submit();
            }
        });
    }
});
