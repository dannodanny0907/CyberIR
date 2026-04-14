/* File: reports.js - Logic for generating and downloading reports */
document.addEventListener('DOMContentLoaded', () => {
    // Animate performance and stat bars
    setTimeout(() => {
        document.querySelectorAll('.perf-fill, .stat-fill').forEach(bar => {
            bar.style.width = bar.dataset.width + '%';
        });
    }, 200);

    // Format activity log times
    const formatTimeAgo = (dateStr) => {
        const date = new Date(dateStr + " UTC");
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        
        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins} min ago`;
        
        const diffHours = Math.floor(diffMins / 60);
        if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's': ''} ago`;
        
        const diffDays = Math.floor(diffHours / 24);
        return `${diffDays} day${diffDays > 1 ? 's': ''} ago`;
    };

    document.querySelectorAll('[data-created]').forEach(el => {
        const dateStr = el.dataset.created;
        if (dateStr) {
            const date = new Date(dateStr);
            const now = new Date();
            const diff = Math.floor((now - date) / 1000);
            let text = '';
            if (diff < 60) text = 'just now';
            else if (diff < 3600) text = Math.floor(diff/60) + 'm ago';
            else if (diff < 86400) text = Math.floor(diff/3600) + 'h ago';
            else text = Math.floor(diff/86400) + 'd ago';
            el.textContent = text;
        }
    });
});
