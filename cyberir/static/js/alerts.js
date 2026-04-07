document.addEventListener('DOMContentLoaded', () => {

    // 1. Time ago function
    function timeAgo(dateStr) {
        const date = new Date(dateStr)
        const now = new Date()
        const seconds = Math.floor((now - date) / 1000)
        
        let offsetSeconds = seconds;
        // Basic fix if server generated time natively in string without Z/offsets vs local tz.
        // Assuming dates are generated near-now dynamically.
        
        if (seconds < 60 && seconds > -60) return 'just now'
        const minutes = Math.floor(Math.abs(seconds) / 60)
        if (minutes < 60) return minutes + 'm ago'
        const hours = Math.floor(minutes / 60)
        if (hours < 24) return hours + 'h ago'
        const days = Math.floor(hours / 24)
        if (days < 7) return days + 'd ago'
        return date.toLocaleDateString()
    }
    
    document.querySelectorAll('[data-created]').forEach(el => {
        // Only modify if it naturally parses.
        const created = el.dataset.created;
        if(created){
            // Standardize string replacing space with T for valid ISO parsing if missing
            const stdStr = created.replace(' ', 'T') + (created.includes('UTC') || created.includes('Z') ? '' : 'Z');
            el.textContent = timeAgo(stdStr);
        }
    })

    // 2. Mark single alert as read
    async function markRead(alertId, btn) {
        try {
            const r = await fetch('/alerts/mark-read/' + alertId, {method:'POST'})
            const d = await r.json()
            if (d.success) {
                const item = btn.closest('.alert-item')
                item.classList.remove('alert-unread')
                const msg = item.querySelector('.alert-message')
                if(msg) msg.classList.remove('alert-message-unread');
                btn.remove()
                updateUnreadBadge(-1)
            }
        } catch(e) { }
    }

    // 3. Mark all as read
    async function markAllRead() {
        try {
            const r = await fetch('/alerts/mark-all-read', {method:'POST'})
            const d = await r.json()
            if (d.success) {
                document.querySelectorAll('.alert-unread').forEach(item => {
                    item.classList.remove('alert-unread')
                    const msg = item.querySelector('.alert-message')
                    if(msg) msg.classList.remove('alert-message-unread');
                })
                document.querySelectorAll('.mark-read-btn').forEach(btn => btn.remove())
                setUnreadBadge(0)
                updateSidebarBadge(0)
                
                const markAllBtn = document.getElementById('markAllReadBtn');
                if(markAllBtn) {
                    markAllBtn.disabled = true;
                    markAllBtn.style.opacity = '0.5';
                    markAllBtn.style.cursor = 'not-allowed';
                }
            }
        } catch(e){}
    }

    // 4. Dismiss alert
    async function dismissAlert(alertId, btn) {
        try {
            const r = await fetch('/alerts/dismiss/' + alertId, {method:'POST'})
            const d = await r.json()
            if (d.success) {
                const item = btn.closest('.alert-item')
                
                // Track if we need to decrement total unread
                if(item.classList.contains('alert-unread')){
                    updateUnreadBadge(-1);
                }
                
                item.classList.add('alert-dismissing')
                setTimeout(() => {
                    item.remove()
                    checkEmptyState()
                }, 300)
            }
        } catch(e){}
    }

    // 5. Dismiss all read
    async function dismissAllRead() {
        if (!confirm('Clear all read alerts?')) return
        try {
            const r = await fetch('/alerts/dismiss-all-read', {method:'POST'})
            const d = await r.json()
            if (d.success) {
                document.querySelectorAll('.alert-item:not(.alert-unread)').forEach(item => {
                    item.classList.add('alert-dismissing')
                    setTimeout(() => item.remove(), 300)
                })
                setTimeout(() => {
                    checkEmptyState();
                    const btn = document.getElementById('dismissAllReadBtn');
                    if(btn) {
                        btn.disabled = true;
                        btn.style.opacity = '0.5';
                        btn.style.cursor = 'not-allowed';
                    }
                }, 400)
            }
        } catch(e){}
    }

    // 6. Update unread badge functions
    function updateUnreadBadge(delta) {
        const badge = document.getElementById('unreadBadge')
        if (!badge) return
        let currentText = badge.textContent.replace(' unread', '');
        let count = parseInt(currentText) + delta
        if (count <= 0) {
            badge.style.display = 'none'
            count = 0
            
            const markAllBtn = document.getElementById('markAllReadBtn');
            if(markAllBtn) {
                markAllBtn.disabled = true;
                markAllBtn.style.opacity = '0.5';
                markAllBtn.style.cursor = 'not-allowed';
            }
            const rb = document.querySelector('.alerts-summary-bar');
            if(rb) rb.style.display = 'none';
        } else {
            badge.textContent = count + ' unread'
        }
        updateSidebarBadge(count)
    }

    function setUnreadBadge(count) {
        const badge = document.getElementById('unreadBadge')
        if (badge) {
            if (count <= 0) {
                badge.style.display = 'none'
                const rb = document.querySelector('.alerts-summary-bar');
                if(rb) rb.style.display = 'none';
            }
            else {
                badge.style.display = 'inline-block'
                badge.textContent = count + ' unread'
            }
        }
        updateSidebarBadge(count)
    }

    // 7. Update sidebar alert badge
    function updateSidebarBadge(count) {
        const badge = document.getElementById('sidebarAlertBadge')
        if (!badge) return
        if (count <= 0) {
            badge.style.display = 'none'
        } else {
            badge.style.display = 'inline-block'
            badge.textContent = count > 99 ? '99+' : count
        }
    }

    // 8. Check empty state
    function checkEmptyState() {
        const list = document.getElementById('alertsList')
        if(!list) return;
        const items = list.querySelectorAll('.alert-item')
        const empty = document.getElementById('emptyState')
        const actFiltersItems = Array.from(items).filter(i => i.style.display !== 'none');
        
        let isEmpty = actFiltersItems.length === 0;
        
        if (empty) {
            if(isEmpty){
                empty.style.display = 'block';
                // Remove stray date headers if lists inside them are removed/hidden
                list.querySelectorAll('.date-group-header').forEach(h => h.style.display = 'none');
            } else {
                empty.style.display = 'none';
                list.querySelectorAll('.date-group-header').forEach(h => h.style.display = 'block');
            }
        }
    }

    // 9. Filter tabs (All/Unread/Read)
    document.querySelectorAll('.filter-tab').forEach(tab => {
        tab.addEventListener('click', function() {
            document.querySelectorAll('.filter-tab').forEach(t => t.classList.remove('active'))
            this.classList.add('active')
            const filter = this.dataset.filter
            filterAlerts(filter)
        })
    })

    function filterAlerts(filter) {
        document.querySelectorAll('.alert-item').forEach(item => {
            if (filter === 'unread') {
                item.style.display = item.classList.contains('alert-unread') ? '' : 'none'
            } else if (filter === 'read') {
                item.style.display = !item.classList.contains('alert-unread') ? '' : 'none'
            } else {
                item.style.display = ''
            }
        })
        checkEmptyState()
    }

    // 11. Alert type legend toggle
    document.getElementById('legendToggle')?.addEventListener('click', function() {
        const content = document.getElementById('legendContent')
        if (content) {
            content.classList.toggle('open')
            this.querySelector('.toggle-icon').textContent = content.classList.contains('open') ? '▲' : '▼'
        }
    })

    // 12. Auto-refresh unread count every 30 seconds
    setInterval(async () => {
        if(document.visibilityState === 'hidden') return;
        try {
            const r = await fetch('/api/alert-count')
            const d = await r.json()
            updateSidebarBadge(d.count)
        } catch(e) {}
    }, 30000)

    // 13. Wiring up buttons
    document.querySelectorAll('.mark-read-btn').forEach(btn => {
        btn.addEventListener('click', () => markRead(btn.dataset.alertId, btn))
    })

    document.querySelectorAll('.dismiss-btn').forEach(btn => {
        btn.addEventListener('click', () => dismissAlert(btn.dataset.alertId, btn))
    })

    document.getElementById('markAllReadBtn')?.addEventListener('click', markAllRead)
    document.getElementById('dismissAllReadBtn')?.addEventListener('click', dismissAllRead)
});
