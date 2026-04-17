
document.addEventListener('DOMContentLoaded', () => {
    // Submit form on filter change
    const filterForm = document.getElementById('filterForm');
    document.querySelectorAll('.filter-select').forEach(select => {
        select.addEventListener('change', () => filterForm.submit());
    });
    
    // Sort logic
    document.querySelectorAll('th.sortable').forEach(th => {
        th.addEventListener('click', () => {
            const sort = th.dataset.sort;
            const currentSort = document.querySelector('input[name="sort"]').value;
            const currentOrder = document.querySelector('input[name="order"]').value;
            
            document.querySelector('input[name="sort"]').value = sort;
            
            if (currentSort === sort) {
                document.querySelector('input[name="order"]').value = currentOrder === 'asc' ? 'desc' : 'asc';
            } else {
                document.querySelector('input[name="order"]').value = 'asc';
            }
            filterForm.submit();
        });
    });

    // Row clicks
    document.querySelectorAll('.clickable-row').forEach(row => {
        row.addEventListener('click', function(e) {
            if (e.target.tagName.toLowerCase() !== 'a' && !e.target.closest('a')) {
                window.location.href = this.dataset.href;
            }
        });
    });
    
    // Debounce search
    let searchTimeout;
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', () => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                filterForm.submit();
            }, 400);
        });
    }

    // Mark recent
    document.querySelectorAll('[data-reported]').forEach(row => {
        const reportedDateStr = row.dataset.reported;
        if (!reportedDateStr || reportedDateStr === 'None') return;
        
        try {
            const reported = new Date(reportedDateStr + 'Z'); // approximate parsing for UTC
            const localReported = new Date(reportedDateStr); // fallback local parsing
            const validDate = isNaN(reported.getTime()) ? localReported : reported;
            
            if (!isNaN(validDate.getTime())) {
                const twoHoursAgo = new Date(Date.now() - 2*60*60*1000);
                if (validDate > twoHoursAgo) {
                    const badge = row.querySelector('.badge-catastrophic');
                    if (badge) badge.classList.add('recent');
                }
            }
        } catch(e) {}
    });
});
