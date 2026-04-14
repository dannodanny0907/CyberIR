/* File: similarity.js - Data fetching and processing for similarity views */
document.addEventListener('DOMContentLoaded', () => {

    function showToast(message, type='success') {
        const toast = document.createElement('div');
        toast.className = 'toast toast-' + type;
        toast.textContent = message;
        document.body.appendChild(toast);
        setTimeout(() => { toast.style.opacity = '0'; }, 2500);
        setTimeout(() => toast.remove(), 3000);
    }

    // ProgressBar Array Hook
    setTimeout(() => {
        document.querySelectorAll('.sim-fill').forEach(bar => {
            bar.style.width = bar.dataset.width + '%';
        });
    }, 100);

    // Apply Solution Modal Config
    const applyOverlay = document.getElementById('applySolutionOverlay');
    const applyCancel = document.getElementById('applySolutionCancel');

    if (applyCancel) {
        applyCancel.addEventListener('click', () => {
            applyOverlay.style.display = 'none';
        });
        window.addEventListener('click', (e) => {
            if (e.target === applyOverlay) applyOverlay.style.display = 'none';
        });
    }

    let currentTargetBtn = null;

    document.querySelectorAll('.apply-solution-trigger').forEach(btn => {
        btn.addEventListener('click', () => {
            currentTargetBtn = btn;
            
            const sourceId = btn.dataset.sourceId;
            const incidentId = btn.dataset.incidentId;
            const resolution = decodeURIComponent(btn.dataset.resolution);
            
            document.getElementById('applySourceId').textContent = sourceId;
            document.getElementById('applySourceIdLabel').textContent = sourceId;
            document.getElementById('applySourceResolutionText').textContent = resolution;
            document.getElementById('applyResolutionNotes').value = resolution;
            
            const form = document.getElementById('applySolutionForm');
            form.dataset.sourceId = sourceId;
            form.dataset.incidentId = incidentId;
            
            applyOverlay.style.display = 'flex';
        });
    });

    const applyForm = document.getElementById('applySolutionForm');
    if (applyForm) {
        applyForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const sourceId = applyForm.dataset.sourceId;
            const incidentId = applyForm.dataset.incidentId;
            const resNotes = document.getElementById('applyResolutionNotes').value;
            
            if (!sourceId || !resNotes || !incidentId) return;
            
            const confirmBtn = applyForm.querySelector('.apply-solution-btn-confirm');
            confirmBtn.disabled = true;
            confirmBtn.textContent = 'Applying...';
            
            const formData = new FormData();
            formData.append('source_incident_id', sourceId);
            formData.append('resolution_notes', resNotes);
            
            try {
                const response = await fetch(`/incidents/apply-solution/${incidentId}`, {
                    method: 'POST',
                    body: formData
                });
                const result = await response.json();
                
                if (result.success) {
                    showToast('Solution Applied ✓', 'success');
                    applyOverlay.style.display = 'none';
                    
                    if (currentTargetBtn) {
                        const ptr = currentTargetBtn.parentElement;
                        currentTargetBtn.remove();
                        const bdg = document.createElement('div');
                        bdg.className = 'solution-applied-badge';
                        bdg.textContent = 'Solution Applied ✓';
                        ptr.appendChild(bdg);
                    }
                } else {
                    showToast(result.message || 'Failure applying solution.', 'error');
                }
            } catch(e) {
                showToast('API Communication Failure.', 'error');
            } finally {
                confirmBtn.disabled = false;
                confirmBtn.textContent = 'Apply Solution';
            }
        });
    }

});
