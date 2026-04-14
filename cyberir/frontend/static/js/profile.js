/* File: profile.js - User profile update and form handling logic */
document.addEventListener('DOMContentLoaded', () => {

    // 1. Avatar color swatches
    document.querySelectorAll('.color-swatch').forEach(swatch => {
        swatch.addEventListener('click', async function() {
            const color = this.dataset.color
            
            document.querySelectorAll('.color-swatch').forEach(s => s.classList.remove('active'))
            this.classList.add('active')
            
            const avatar = document.getElementById('profileAvatar')
            if (avatar) avatar.style.background = color
            
            await fetch('/profile/update-avatar-color', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({avatar_color: color})
            })
            
            const sidebarAvatar = document.getElementById('sidebarAvatar')
            if (sidebarAvatar) {
                sidebarAvatar.style.background = color
            }
        })
    })

    // 2. Save profile
    document.getElementById('saveProfileBtn')?.addEventListener('click', async function() {
        clearFieldErrors();
        const fullName = document.getElementById('fullNameInput').value.trim()
        const phone = document.getElementById('phoneInput').value.trim()
        
        if (!fullName) {
            showFieldError('fullNameInput', 'Full name is required')
            return
        }
        
        this.textContent = 'Saving...'
        this.disabled = true
        
        try {
            const r = await fetch('/profile/update', {
                method: 'POST',
                headers: {'Content-Type':'application/json'},
                body: JSON.stringify({ full_name: fullName, phone_number: phone })
            })
            const d = await r.json()
            
            if (d.success) {
                this.textContent = '✅ Saved!'
                document.getElementById('profileName').textContent = d.new_name
                const sidebarName = document.getElementById('sidebarUserName')
                if (sidebarName) sidebarName.textContent = d.new_name
            } else {
                this.textContent = '❌ Error'
            }
        } catch(e) {
            this.textContent = '❌ Request Failed'
        }
        
        this.disabled = false
        setTimeout(() => { this.textContent = '💾 Save Profile' }, 2500)
    })

    // 3. Password strength checker
    document.getElementById('newPassword')?.addEventListener('input', function() {
        checkPasswordStrength(this.value)
        checkPasswordMatch()
    })
    
    function checkPasswordStrength(password) {
        const bar = document.getElementById('strengthBar')
        const text = document.getElementById('strengthText')
        
        let strength = 0
        let label = ''
        let color = ''
        let width = '0%'
        
        if (password.length >= 8) strength++
        if (/[A-Z]/.test(password)) strength++
        if (/[0-9]/.test(password)) strength++
        if (/[^A-Za-z0-9]/.test(password)) strength++
        
        if (password.length === 0) {
            width = '0%'; label = ''; color = ''
        } else if (password.length < 6) {
            width='25%'; label='Weak'; color='#dc2626'
        } else if (strength <= 2) {
            width='50%'; label='Fair'; color='#d97706'
        } else if (strength === 3) {
            width='75%'; label='Strong'; color='#2563eb'
        } else {
            width='100%'; label='Very Strong'; color='#16a34a'
        }
        
        if (bar) {
            bar.style.width = width
            bar.style.background = color
        }
        if (text) {
            text.textContent = label
            text.style.color = color
        }
    }

    // 4. Password match checker
    document.getElementById('confirmPassword')?.addEventListener('input', checkPasswordMatch)
    
    function checkPasswordMatch() {
        const newPwd = document.getElementById('newPassword').value
        const confirmPwd = document.getElementById('confirmPassword').value
        const indicator = document.getElementById('matchIndicator')
        
        if (!confirmPwd) {
            if (indicator) indicator.textContent = ''
            return
        }
        
        if (newPwd === confirmPwd) {
            if (indicator) {
                indicator.textContent = '✅ Passwords match'
                indicator.style.color = '#16a34a'
            }
        } else {
            if (indicator) {
                indicator.textContent = '❌ Passwords do not match'
                indicator.style.color = '#dc2626'
            }
        }
    }

    // 5. Show/hide password toggles
    document.querySelectorAll('.toggle-password').forEach(btn => {
        btn.addEventListener('click', function() {
            const input = document.getElementById(this.dataset.target)
            if (input) {
                if (input.type === 'password') {
                    input.type = 'text'
                    this.textContent = '🙈'
                } else {
                    input.type = 'password'
                    this.textContent = '👁️'
                }
            }
        })
    })

    // 6. Change password
    document.getElementById('changePasswordBtn')?.addEventListener('click', async function() {
        clearFieldErrors()
        
        const currentPwd = document.getElementById('currentPassword').value
        const newPwd = document.getElementById('newPassword').value
        const confirmPwd = document.getElementById('confirmPassword').value
        
        if (!currentPwd) { showFieldError('currentPassword', 'Enter your current password'); return; }
        if (newPwd.length < 8) { showFieldError('newPassword', 'Password must be at least 8 characters'); return; }
        if (!(/[A-Z]/.test(newPwd) && /[a-z]/.test(newPwd) && /[0-9]/.test(newPwd))) {
             showFieldError('newPassword', 'Password must contain uppercase, lowercase, and a number'); return;
        }
        if (newPwd !== confirmPwd) { showFieldError('confirmPassword', 'Passwords do not match'); return; }
        
        this.textContent = '🔒 Changing...'
        this.disabled = true
        
        try {
            const r = await fetch('/profile/change-password', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ current_password: currentPwd, new_password: newPwd, confirm_password: confirmPwd })
            })
            const d = await r.json()
            
            if (d.success) {
                this.textContent = '✅ Password Changed!'
                document.getElementById('currentPassword').value = ''
                document.getElementById('newPassword').value = ''
                document.getElementById('confirmPassword').value = ''
                document.getElementById('strengthBar').style.width = '0%'
                document.getElementById('strengthText').textContent = ''
                document.getElementById('matchIndicator').textContent = ''
            } else {
                if (d.field) showFieldError(d.field, d.message)
                this.textContent = '❌ Failed'
            }
        } catch(e){
            this.textContent = '❌ Request Failed';
        }
        
        this.disabled = false
        setTimeout(() => { this.textContent = '🔒 Change Password' }, 2500)
    })

    // 7. Field error helpers
    function showFieldError(fieldId, message) {
        const field = document.getElementById(fieldId)
        if (field) {
            field.style.borderColor = '#dc2626'
            let err = document.getElementById(fieldId + 'Error')
            if (!err) {
                err = document.createElement('div')
                err.id = fieldId + 'Error'
                err.style.cssText = 'color:#dc2626;font-size:0.78rem;margin-top:4px'
                field.parentNode.insertBefore(err, field.nextSibling)
            }
            err.textContent = message
        }
    }
    
    function clearFieldErrors() {
        document.querySelectorAll('input').forEach(f => f.style.borderColor = '')
        document.querySelectorAll('[id$="Error"]').forEach(e => e.remove())
    }

    // 8. Save notification preferences
    document.getElementById('savePrefsBtn')?.addEventListener('click', async function() {
        this.textContent = 'Saving...'
        this.disabled = true
        
        const prefs = {
            email_notifications: document.getElementById('pref_email_notifications').checked ? 1 : 0,
            email_critical_alerts: document.getElementById('pref_email_critical_alerts').checked ? 1:0,
            email_assignments: document.getElementById('pref_email_assignments').checked ? 1 : 0,
            email_correlation_alerts: document.getElementById('pref_email_correlation_alerts').checked ?1:0,
            email_daily_summary: document.getElementById('pref_email_daily_summary').checked ? 1 : 0,
            in_app_alert_sound: document.getElementById('pref_in_app_alert_sound').checked ? 1 : 0,
            dark_mode: document.getElementById('pref_dark_mode').checked ? 1 : 0,
            items_per_page: document.getElementById('pref_items_per_page').value
        }
        
        try {
            const r = await fetch('/profile/update-preferences', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(prefs)
            })
            const d = await r.json()
            this.textContent = d.success ? '✅ Saved!' : '❌ Error'
        } catch(e) {
             this.textContent = '❌ Request Failed';
        }
        
        this.disabled = false
        setTimeout(() => { this.textContent = '💾 Save Preferences' }, 2500)
    })

    // 9. Master email toggle disables sub-toggles
    document.getElementById('pref_email_notifications')?.addEventListener('change', function() {
        const emailToggles = [
            'pref_email_critical_alerts',
            'pref_email_assignments',
            'pref_email_correlation_alerts',
            'pref_email_daily_summary'
        ]
        emailToggles.forEach(id => {
            const el = document.getElementById(id)
            if (el) {
                el.disabled = !this.checked
                el.closest('.toggle-switch-container')?.classList.toggle('toggle-disabled', !this.checked)
            }
        })
    })

    // 10. Items per page auto-save
    document.getElementById('pref_items_per_page')?.addEventListener('change', async function() {
        await fetch('/profile/update-preferences', {
            method: 'POST',
            headers: {'Content-Type':'application/json'},
            body: JSON.stringify({ items_per_page: this.value })
        })
        showToast('Items per page updated')
    })
    
    // Simple dark mode stub auto-save
    document.getElementById('pref_dark_mode')?.addEventListener('change', async function() {
        await fetch('/profile/update-preferences', {
            method: 'POST',
            headers: {'Content-Type':'application/json'},
            body: JSON.stringify({ dark_mode: this.checked ? 1 : 0 })
        })
        if(this.checked) {
            showToast('Dark mode preference saved. Full dark theme coming soon.')
        } else {
            showToast('Dark mode disabled')
        }
    })

    // 11. Simple toast for profile page
    function showToast(message, type='success') {
        const toast = document.createElement('div')
        toast.style.cssText = `
            position:fixed;bottom:24px;right:24px;
            background:${type==='success'?'#166534':'#dc2626'};
            color:white;padding:12px 20px;
            border-radius:8px;font-size:0.875rem;
            z-index:9999;box-shadow:0 4px 12px rgba(0,0,0,0.3);
            transition:opacity 0.5s
        `
        toast.textContent = message
        document.body.appendChild(toast)
        setTimeout(() => toast.style.opacity='0', 2500)
        setTimeout(() => toast.remove(), 3000)
    }

    // 12. Activity time ago
    document.querySelectorAll('[data-created]').forEach(el => {
        const createdStr = el.dataset.created;
        if(createdStr){
            const stdStr = createdStr.replace(' ', 'T') + (createdStr.includes('UTC') || createdStr.includes('Z') ? '' : 'Z');
            const date = new Date(stdStr)
            const now = new Date()
            const diff = Math.floor((now - date) / 1000)
            let text = ''
            if (diff < 60 && diff > -60) text = 'just now'
            else if (diff < 3600) text = Math.floor(Math.abs(diff)/60) + 'm ago'
            else if (diff < 86400) text = Math.floor(Math.abs(diff)/3600) + 'h ago'
            else text = Math.floor(Math.abs(diff)/86400) + 'd ago'
            el.textContent = text
        }
    })
});
