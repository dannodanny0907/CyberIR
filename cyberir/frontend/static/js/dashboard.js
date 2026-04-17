/* File: dashboard.js - Chart generation and real-time dashboard updates */
document.addEventListener('DOMContentLoaded', () => {

    // 1. Chart Initialization
    
    // Status Pie Chart
    const statusDataRaw = document.getElementById('statusData').textContent;
    const statusData = JSON.parse(statusDataRaw);
    
    const statusColors = {
        'Open': '#dc2626',
        'Investigating': '#d97706',
        'Resolved': '#16a34a',
        'Closed': '#64748b'
    };
    
    const statusChart = new Chart(document.getElementById('statusChart'), {
        type: 'pie',
        data: {
            labels: statusData.map(d => d.status),
            datasets: [{
                data: statusData.map(d => d.count),
                backgroundColor: statusData.map(d => statusColors[d.status] || '#94a3b8'),
                borderWidth: 0
            }]
        },
        options: {
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { padding: 15, usePointStyle: true, boxWidth: 8 }
                }
            },
            onClick: (event, activeElements) => {
                if (activeElements.length > 0) {
                    const label = statusChart.data.labels[activeElements[0].index];
                    window.location.href = `/reports?status=${encodeURIComponent(label)}`;
                }
            }
        }
    });
    document.getElementById('statusChart').style.cursor = 'pointer';

    // Severity Doughnut Chart
    const priorityDataRaw = document.getElementById('priorityData').textContent;
    const priorityData = JSON.parse(priorityDataRaw);
    
    const priorityColors = {
        'Catastrophic': '#dc2626',
        'Major': '#ea580c',
        'Moderate': '#2563eb',
        'Minor': '#16a34a'
    };
    
    const priorityChart = new Chart(document.getElementById('priorityChart'), {
        type: 'doughnut',
        data: {
            labels: priorityData.map(d => d.priority),
            datasets: [{
                data: priorityData.map(d => d.count),
                backgroundColor: priorityData.map(d => priorityColors[d.priority] || '#94a3b8'),
                borderWidth: 0
            }]
        },
        options: {
            maintainAspectRatio: false,
            cutout: '62%',
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { padding: 15, usePointStyle: true, boxWidth: 8 }
                }
            },
            onClick: (event, activeElements) => {
                if (activeElements.length > 0) {
                    const label = priorityChart.data.labels[activeElements[0].index];
                    window.location.href = `/reports?priority=${encodeURIComponent(label)}`;
                }
            }
        }
    });
    document.getElementById('priorityChart').style.cursor = 'pointer';

    // Type Horizontal Bar Chart
    const typeDataRaw = document.getElementById('typeData').textContent;
    const typeData = JSON.parse(typeDataRaw);
    
    const typeChart = new Chart(document.getElementById('typeChart'), {
        type: 'bar',
        data: {
            labels: typeData.map(d => d.incident_type),
            datasets: [{
                data: typeData.map(d => d.count),
                backgroundColor: '#2563eb',
                borderRadius: 4
            }]
        },
        options: {
            indexAxis: 'y',
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: { beginAtZero: true, grid: { color: '#f1f5f9' } },
                y: { grid: { display: false }, ticks: { font: { size: 11 } } }
            },
            onClick: (event, activeElements) => {
                if (activeElements.length > 0) {
                    const label = typeChart.data.labels[activeElements[0].index];
                    window.location.href = `/reports?type=${encodeURIComponent(label)}`;
                }
            }
        }
    });
    document.getElementById('typeChart').style.cursor = 'pointer';

    // Trend Line Chart (14 Days)
    const trendDataRaw = document.getElementById('trendData').textContent;
    const trendDataDb = JSON.parse(trendDataRaw);
    
    const last14Dates = [];
    const countsDict = {};
    trendDataDb.forEach(d => countsDict[d.date] = d.count);
    
    // Generate dates
    for(let i=13; i>=0; i--) {
        const d = new Date();
        d.setDate(d.getDate() - i);
        const iso = d.toISOString().split('T')[0]; // YYYY-MM-DD
        const formatted = d.toLocaleDateString('en-US', { month: 'short', day: '2-digit' });
        last14Dates.push({ iso, formatted });
    }
    
    const finalTrendLabels = last14Dates.map(d => d.formatted);
    const finalTrendData = last14Dates.map(d => countsDict[d.iso] || 0);

    new Chart(document.getElementById('trendChart'), {
        type: 'line',
        data: {
            labels: finalTrendLabels,
            datasets: [{
                data: finalTrendData,
                borderColor: '#2563eb',
                backgroundColor: 'rgba(37,99,235,0.06)',
                borderWidth: 2,
                fill: true,
                tension: 0.4,
                pointBackgroundColor: '#2563eb',
                pointRadius: 4,
                pointHoverRadius: 6
            }]
        },
        options: {
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                y: { beginAtZero: true, stepSize: 1, grid: { color: '#f1f5f9' } },
                x: { grid: { display: false } }
            }
        }
    });

    // Resolution Time Horizontal Bar Chart
    const resDataRaw = document.getElementById('resolutionData').textContent;
    const resData = JSON.parse(resDataRaw);
    
    const resCanvas = document.getElementById('resolutionChart');
    const resNoData = document.getElementById('resolutionNoData');
    
    if (resData.length === 0) {
        resCanvas.style.display = 'none';
        resNoData.style.display = 'flex';
    } else {
        resNoData.style.display = 'none';
        resCanvas.style.display = 'block';
        
        new Chart(resCanvas, {
            type: 'bar',
            data: {
                labels: resData.map(d => d.incident_type),
                datasets: [{
                    label: 'Hours',
                    data: resData.map(d => d.avg_hours),
                    backgroundColor: '#7c3aed',
                    borderRadius: 4
                }]
            },
            options: {
                indexAxis: 'y',
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: {
                        beginAtZero: true,
                        title: { display: true, text: 'Hours', font: { size: 10 } },
                        grid: { color: '#f1f5f9' }
                    },
                    y: { grid: { display: false }, ticks: { font: { size: 11 } } }
                }
            }
        });
    }

    // 2. Row Click Navigation
    document.querySelectorAll('[data-href]').forEach(row => {
        row.style.cursor = 'pointer';
        row.addEventListener('click', () => {
            window.location.href = row.dataset.href;
        });
    });

    // 3. Animate Metric Cards on Load
    document.querySelectorAll('.metric-card').forEach((card, i) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(10px)';
        card.style.transition = `opacity 0.3s ease ${i * 0.05}s, transform 0.3s ease ${i * 0.05}s`;
        setTimeout(() => {
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, 50);
    });

    // 4. Auto-Refresh Stats
    async function refreshStats() {
        try {
            const r = await fetch('/api/dashboard-stats');
            if (r.ok) {
                const data = await r.json();
                
                const updateEl = (id, val) => {
                    const el = document.getElementById(id);
                    if (el && val !== undefined) el.textContent = val;
                };

                updateEl('stat-total', data.total_incidents);
                updateEl('stat-open', data.open_incidents);
                updateEl('stat-investigating', data.investigating_incidents);
                updateEl('stat-resolved', data.resolved_incidents);
                updateEl('stat-critical', data.critical_incidents);
                updateEl('stat-clusters', data.active_clusters);
                updateEl('stat-similarity', data.total_similarity_matches);
                
                // Show/hide correlation banner
                const banner = document.getElementById('correlationBanner');
                if (banner) {
                    if (data.active_clusters > 0) {
                        banner.style.display = 'flex';
                        const countSpan = document.getElementById('banner-cluster-count');
                        if (countSpan) countSpan.textContent = data.active_clusters;
                    } else {
                        banner.style.display = 'none';
                    }
                }
            }
        } catch(e) {
            // silent fail
        }
    }

    setInterval(refreshStats, 60000);
});
