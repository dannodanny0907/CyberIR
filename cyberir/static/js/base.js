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
