document.addEventListener('DOMContentLoaded', () => {
    const filterForm = document.getElementById('filterForm');
    const searchInput = document.getElementById('searchInput');
    const hiddenSearch = document.getElementById('hiddenSearch');
    const hiddenSort = document.getElementById('hiddenSort');
    const hiddenOrder = document.getElementById('hiddenOrder');
    const hiddenPage = document.getElementById('hiddenPage');
    const hiddenPerPage = document.getElementById('hiddenPerPage');
    const clearBtn = document.getElementById('clearFiltersBtn');
    
    // 1. Search Debounce
    let debounceTimer;
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => {
                hiddenSearch.value = e.target.value;
                hiddenPage.value = '1';
                filterForm.submit();
            }, 400);
        });
    }

    // 2. Filter Auto-submit
    document.querySelectorAll('.filter-select').forEach(select => {
        select.addEventListener('change', () => {
            hiddenPage.value = '1';
            filterForm.submit();
        });
    });

    // 3. Sort Columns
    document.querySelectorAll('.sortable').forEach(th => {
        th.addEventListener('click', () => {
            const sortField = th.dataset.sort;
            if (hiddenSort.value === sortField) {
                hiddenOrder.value = hiddenOrder.value === 'asc' ? 'desc' : 'asc';
            } else {
                hiddenSort.value = sortField;
                hiddenOrder.value = 'desc';
            }
            hiddenPage.value = '1';
            filterForm.submit();
        });
    });

    // 4. Clear Filters
    if (clearBtn) {
        clearBtn.addEventListener('click', () => {
            window.location.href = '/incidents';
        });
    }

    // 5. Pagination
    document.querySelectorAll('.page-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            if (btn.classList.contains('active')) return;
            if (btn.dataset.page) {
                hiddenPage.value = btn.dataset.page;
                filterForm.submit();
            }
        });
    });

    const perPageSelect = document.getElementById('perPageSelect');
    if (perPageSelect) {
        perPageSelect.addEventListener('change', (e) => {
            hiddenPerPage.value = e.target.value;
            hiddenPage.value = '1';
            filterForm.submit();
        });
    }

    // 6. Delete Incident from table
    const deleteModalOverlay = document.getElementById('deleteModalOverlay');
    const deleteModalCancel = document.getElementById('deleteModalCancel');
    const deleteModalConfirm = document.getElementById('deleteModalConfirm');
    const deleteIncidentName = document.getElementById('deleteIncidentName');
    
    let deleteTargetId = null;
    let deleteTargetRow = null;

    document.querySelectorAll('.table-delete-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            deleteTargetId = e.target.dataset.incidentId;
            deleteIncidentName.textContent = deleteTargetId + ': ' + e.target.dataset.incidentTitle;
            deleteTargetRow = e.target.closest('tr');
            if (deleteModalOverlay) deleteModalOverlay.style.display = 'flex';
        });
    });

    const closeDeleteModal = () => {
        if (deleteModalOverlay) deleteModalOverlay.style.display = 'none';
        deleteTargetId = null;
        deleteTargetRow = null;
    };

    if (deleteModalCancel) deleteModalCancel.addEventListener('click', closeDeleteModal);
    
    window.addEventListener('click', (e) => {
        if (e.target === deleteModalOverlay) closeDeleteModal();
    });

    if (deleteModalConfirm) {
        deleteModalConfirm.addEventListener('click', async () => {
            if (!deleteTargetId) return;
            
            try {
                const response = await fetch(`/incidents/delete/${deleteTargetId}`, { method: 'POST' });
                const result = await response.json();
                
                if (result.success) {
                    if (deleteTargetRow) {
                        deleteTargetRow.style.opacity = '0';
                        setTimeout(() => {
                            deleteTargetRow.remove();
                            // Update pagination visually
                            const pagT = document.getElementById('pagTotalItem');
                            const pagEnd = document.getElementById('pagEndItem');
                            if (pagT && pagEnd) {
                                pagT.textContent = Math.max(0, parseInt(pagT.textContent) - 1);
                                pagEnd.textContent = Math.max(0, parseInt(pagEnd.textContent) - 1);
                            }
                        }, 300);
                    }
                    closeDeleteModal();
                } else {
                    alert(result.message);
                    closeDeleteModal();
                }
            } catch (err) {
                alert('Deletion failed');
                closeDeleteModal();
            }
        });
    }

});
