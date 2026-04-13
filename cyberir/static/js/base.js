document.addEventListener('DOMContentLoaded', () => {
    // Live clock
    const clockElement = document.getElementById('liveClock');
    if (clockElement) {
        const updateClock = () => {
            const now = new Date();
            const options = { weekday: 'long', year: 'numeric', month: 'long', day: '2-digit' };
            const dateStr = now.toLocaleDateString('en-GB', options); // e.g. Sunday, 05 April 2026
            const timeStr = now.toLocaleTimeString('en-GB', { hour12: false }); // 14:32:05
            clockElement.textContent = `${dateStr} — ${timeStr}`;
        };
        updateClock();
        setInterval(updateClock, 1000);
    }
    
    // Sidebar active link fallback
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-links a');
    let hasActive = false;
    navLinks.forEach(link => {
        if (link.classList.contains('active')) {
            hasActive = true;
        }
    });
    
    if (!hasActive) {
        navLinks.forEach(link => {
            const href = link.getAttribute('href');
            if (href && href !== '#' && href === currentPath) {
                link.classList.add('active');
            }
        });
    }

    // Auto-dismiss flash messages
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach(msg => {
        setTimeout(() => {
            msg.style.opacity = '0';
            setTimeout(() => msg.remove(), 500); // Wait for transition
        }, 4000);
    });
    // Auto-refresh sidebar badge every 30 seconds
    setInterval(async () => {
        try {
            const r = await fetch('/api/alert-count');
            const d = await r.json();
            const badge = document.getElementById('sidebarAlertBadge');
            if (badge) {
                if (d.count <= 0) {
                    badge.style.display = 'none';
                } else {
                    badge.style.display = 'inline-block';
                    badge.textContent = d.count > 99 ? '99+' : d.count;
                }
            }
        } catch(e) {}
    }, 30000);
});

// Page transition loader
document.addEventListener('DOMContentLoaded', () => {
    const loader = document.createElement('div')
    loader.id = 'pageLoader'
    loader.className = 'page-loader'
    loader.style.display = 'none'
    document.body.prepend(loader)
})

// Show loader on navigation
document.querySelectorAll('a:not([href^="#"]):not([target="_blank"]):not([href^="javascript"])')
    .forEach(link => {
        link.addEventListener('click', function(e) {
            if (this.href && !this.href.startsWith('mailto') && !this.classList.contains('no-loader')) {
                const loader = document.getElementById('pageLoader')
                if (loader) loader.style.display = 'block'
            }
        })
    })

// Button loading state helper
function setButtonLoading(btn, loading, originalText) {
    if (loading) {
        btn.dataset.originalText = btn.textContent
        btn.textContent = originalText || 'Loading...'
        btn.classList.add('btn-loading')
        btn.disabled = true
    } else {
        btn.textContent = btn.dataset.originalText || originalText
        btn.classList.remove('btn-loading')
        btn.disabled = false
    }
}

// Confirm dialogs helper
function confirmAction(message, onConfirm, dangerText) {
    const modal = document.getElementById('globalConfirmModal')
    if (!modal) {
        if (confirm(message)) onConfirm()
        return
    }
    document.getElementById('confirmMessage').textContent = message
    const btn = document.getElementById('confirmActionBtn')
    btn.textContent = dangerText || 'Confirm'
    btn.onclick = () => {
        modal.style.display = 'none'
        onConfirm()
    }
    modal.style.display = 'flex'
}

// Flash messages auto-dismiss
setTimeout(() => {
    document.querySelectorAll('.flash-message').forEach(msg => {
        msg.style.transition = 'opacity 0.5s'
        msg.style.opacity = '0'
        setTimeout(() => msg.remove(), 500)
    })
}, 4000)

// Mobile Support (Hamburger Menu & Sidebar Overlay)
document.addEventListener('DOMContentLoaded', () => {
    const sidebar = document.querySelector('.sidebar')
    const mobileBtn = document.getElementById('mobileMenuBtn')
    
    let overlay = document.createElement('div')
    overlay.className = 'sidebar-overlay'
    document.body.appendChild(overlay)

    mobileBtn?.addEventListener('click', () => {
        sidebar?.classList.toggle('open')
        overlay.classList.toggle('visible')
    })

    overlay.addEventListener('click', () => {
        sidebar?.classList.remove('open')
        overlay.classList.remove('visible')
    })
});

// Keyboard Additions
document.addEventListener('keydown', (e) => {
    if (e.altKey) {
        switch(e.key.toLowerCase()) {
            case 'd': window.location='/dashboard'; break;
            case 'i': window.location='/incidents'; break;
            case 'n':
                if (document.querySelector('[href="/incidents/log"]')) {
                    window.location='/incidents/log'
                }
                break;
            case 'a': window.location='/alerts'; break;
        }
    }
})

// Profile dropdown toggle
const profileTrigger = document.getElementById('profileTrigger')
const profileDropdown = document.getElementById('profileDropdown')
const profileChevron = document.querySelector('.profile-chevron')

profileTrigger?.addEventListener('click', function(e) {
    e.stopPropagation()
    const isOpen = profileDropdown.classList.contains('open')
    
    profileDropdown.classList.toggle('open')
    profileChevron?.classList.toggle('open')
})

document.addEventListener('click', () => {
    if (profileDropdown?.classList.contains('open')) {
        profileDropdown.classList.remove('open')
        profileChevron?.classList.remove('open')
    }
})
