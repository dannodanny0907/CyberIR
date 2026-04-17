import os

base_dir = r"c:\Users\PDM\Pictures\CYBER\cyberir"
frontend_dir = os.path.join(base_dir, "frontend")

# 1. Update base.html
base_html = os.path.join(frontend_dir, "templates", "base.html")
with open(base_html, "r", encoding="utf-8") as f:
    b_html = f.read()

cirt_nav = """      {% if current_user.role == 'CIRT' %}
      <div class="nav-section-label">CIRT PORTAL</div>
      <div class="nav-section-cirt">
        <a href="/cirt/incidents" class="{{ 'active' if active_page == 'cirt_incidents' else '' }}">
          <span class="icon">🚨</span> CIRT Incidents
        </a>
        <a href="/alerts" class="{{ 'active' if active_page == 'alerts' else '' }}">
          <span class="icon">🔔</span> Alerts
          {% if unread_alerts_count > 0 %}
          <span class="alert-badge" id="sidebarAlertBadge">{{ unread_alerts_count }}</span>
          {% else %}
          <span class="alert-badge" id="sidebarAlertBadge" style="display:none">0</span>
          {% endif %}
        </a>
      </div>
      {% else %}
      <div class="nav-section-label">Main</div>"""

if "{% if current_user.role == 'CIRT' %}" not in b_html:
    # We replace `<div class="nav-section-label">Main</div>`
    # up to `</nav>` closing the if-block inside it
    b_html = b_html.replace(
        '<div class="nav-section-label">Main</div>',
        cirt_nav
    )
    b_html = b_html.replace('    </nav>', '      {% endif %}\n    </nav>')

with open(base_html, "w", encoding="utf-8") as f:
    f.write(b_html)

# 2. Create cirt_incidents.html
cirt_html_content = """{% extends 'base.html' %}

{% block title %}CIRT Incidents{% endblock %}
{% block page_title %}CIRT Incident Portal{% endblock %}

{% block extra_css %}
<link rel="stylesheet" href="{{ url_for('static', filename='css/incidents.css') }}">
<link rel="stylesheet" href="{{ url_for('static', filename='css/cirt_incidents.css') }}">
{% endblock %}

{% block content %}
<div class="cirt-banner">
    🚨 CIRT Portal — You are viewing incidents escalated for Cyber Security Incident Response Team action only.
</div>

<div class="dashboard-grid" style="margin-bottom: 20px;">
    <div class="metric-card">
        <div class="metric-title">Total CIRT Incidents</div>
        <div class="metric-value" style="color: #dc2626;">{{ total_cirt }}</div>
        <div class="metric-subtitle">🚨 Escalated overall</div>
    </div>
    <div class="metric-card">
        <div class="metric-title">Catastrophic</div>
        <div class="metric-value" style="color: #991b1b;">{{ catastrophic_count }}</div>
        <div class="metric-subtitle">🔴 Highest severity</div>
    </div>
    <div class="metric-card">
        <div class="metric-title">Major</div>
        <div class="metric-value" style="color: #ea580c;">{{ major_count }}</div>
        <div class="metric-subtitle">🟠 Elevated severity</div>
    </div>
    <div class="metric-card">
        <div class="metric-title">Open/Active</div>
        <div class="metric-value" style="color: #ea580c;">{{ open_cirt }}</div>
        <div class="metric-subtitle">🔍 Needs investigation</div>
    </div>
</div>

<div class="card full-height">
    <div class="card-header action-bar">
        <div class="card-title">CIRT Incidents</div>
        <div class="action-buttons">
            <a href="/cirt/incidents/export" class="btn-primary" style="text-decoration: none;">📥 Export CSV</a>
        </div>
    </div>

    <!-- Filter Bar -->
    <div class="filter-bar">
        <form id="filterForm" method="GET" action="/cirt/incidents" class="filter-grid">
            <select name="status" class="filter-select">
                <option value="All Statuses" {% if status == 'All Statuses' %}selected{% endif %}>All Statuses</option>
                <option value="Open" {% if status == 'Open' %}selected{% endif %}>Open</option>
                <option value="Investigating" {% if status == 'Investigating' %}selected{% endif %}>Investigating</option>
                <option value="Resolved" {% if status == 'Resolved' %}selected{% endif %}>Resolved</option>
                <option value="Closed" {% if status == 'Closed' %}selected{% endif %}>Closed</option>
            </select>
            <select name="severity" class="filter-select">
                <option value="All Severities" {% if severity == 'All Severities' %}selected{% endif %}>All Severities</option>
                <option value="Major" {% if severity == 'Major' %}selected{% endif %}>Major</option>
                <option value="Catastrophic" {% if severity == 'Catastrophic' %}selected{% endif %}>Catastrophic</option>
            </select>
            <div class="search-box">
                <span class="search-icon">🔍</span>
                <input type="text" id="searchInput" name="search" class="filter-search" placeholder="Search CIRT incidents..." value="{{ search }}">
            </div>
            <input type="hidden" name="sort" value="{{ sort }}">
            <input type="hidden" name="order" value="{{ order }}">
        </form>
        {% if status != 'All Statuses' or severity != 'All Severities' or search %}
        <a href="/cirt/incidents" class="btn-secondary" style="font-size: 0.75rem; text-decoration: none; display: flex; align-items: center;">Clear Filters</a>
        {% endif %}
    </div>

    <div class="table-container">
        {% if incidents %}
        <table class="data-table">
            <thead>
                <tr>
                    <th data-sort="incident_id" class="sortable">Incident ID <span class="sort-indicator {% if sort == 'incident_id' %}active{% endif %}">{{ '▼' if sort == 'incident_id' and order == 'desc' else ('▲' if sort == 'incident_id' else '▼') }}</span></th>
                    <th data-sort="title" class="sortable">Title <span class="sort-indicator {% if sort == 'title' %}active{% endif %}">{{ '▼' if sort == 'title' and order == 'desc' else ('▲' if sort == 'title' else '▼') }}</span></th>
                    <th>Type</th>
                    <th data-sort="priority" class="sortable">Severity <span class="sort-indicator {% if sort == 'priority' %}active{% endif %}">{{ '▼' if sort == 'priority' and order == 'desc' else ('▲' if sort == 'priority' else '▼') }}</span></th>
                    <th data-sort="status" class="sortable">Status <span class="sort-indicator {% if sort == 'status' %}active{% endif %}">{{ '▼' if sort == 'status' and order == 'desc' else ('▲' if sort == 'status' else '▼') }}</span></th>
                    <th data-sort="risk_score" class="sortable">Risk Score <span class="sort-indicator {% if sort == 'risk_score' %}active{% endif %}">{{ '▼' if sort == 'risk_score' and order == 'desc' else ('▲' if sort == 'risk_score' else '▼') }}</span></th>
                    <th data-sort="detected_datetime" class="sortable">Detected/Reported <span class="sort-indicator {% if sort == 'detected_datetime' %}active{% endif %}">{{ '▼' if sort == 'detected_datetime' and order == 'desc' else ('▲' if sort == 'detected_datetime' else '▼') }}</span></th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
                {% for inc in incidents %}
                <tr class="clickable-row" data-href="/incidents/{{ inc.incident_id }}" data-reported="{{ inc.reported_date }}">
                    <td class="id-cell"><a href="/incidents/{{ inc.incident_id }}" style="text-decoration:none; color:inherit;">{{ inc.incident_id }}</a></td>
                    <td class="title-cell"><div class="title-truncate" title="{{ inc.title }}">{{ inc.title[:40] + '...' if inc.title|length > 40 else inc.title }}</div></td>
                    <td>
                        {% for type in (inc.incident_type or '').split(', ') %}
                            {% if type.strip() %}
                            <span class="badge" style="background:var(--primary); color:white;">{{ type.strip() }}</span>
                            {% endif %}
                        {% endfor %}
                    </td>
                    <td><span class="badge badge-{{ inc.priority|lower }}">{{ inc.priority }}</span></td>
                    <td><span class="badge status-{{ inc.status|lower|replace(' ', '-') }}">{{ inc.status }}</span></td>
                    <td>
                        <div class="risk-score-container">
                            <span class="risk-score-text">{{ inc.risk_score }}%</span>
                            <div class="risk-score-bar">
                                {% set color = '#dc2626' if inc.priority == 'Catastrophic' else '#ea580c' %}
                                <div class="risk-score-fill" style="width: {{ inc.risk_score }}%; background: {{ color }};"></div>
                            </div>
                        </div>
                    </td>
                    <td class="date-cell">{{ inc.detected_datetime or inc.reported_date }}</td>
                    <td><a href="/incidents/{{ inc.incident_id }}" class="btn-secondary" style="padding:4px 8px; font-size:0.75rem; text-decoration:none;">View</a></td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% else %}
        <div class="empty-state">
            <div class="empty-icon">🚨</div>
            <div class="empty-title">No escalated incidents at this time</div>
            <div class="empty-subtitle">Incidents with Major or Catastrophic severity are automatically escalated to CIRT.</div>
        </div>
        {% endif %}
    </div>

    <!-- Pagination -->
    {% if total_pages > 1 %}
    <div class="pagination">
        <div class="pagination-info">Showing {{ (page-1)*per_page + 1 }} to {{ page*per_page if page*per_page < total_count else total_count }} of {{ total_count }} results</div>
        <div class="pagination-controls">
            <a href="?page={{ page-1 }}&sort={{ sort }}&order={{ order }}&status={{ status }}&severity={{ severity }}&search={{ search }}" class="btn-secondary {% if page == 1 %}disabled{% endif %}" style="text-decoration: none;">Previous</a>
            {% for p in range(1, total_pages + 1) %}
            <a href="?page={{ p }}&sort={{ sort }}&order={{ order }}&status={{ status }}&severity={{ severity }}&search={{ search }}" class="btn-secondary {% if p == page %}active{% endif %}" style="text-decoration: none;">{{ p }}</a>
            {% endfor %}
            <a href="?page={{ page+1 }}&sort={{ sort }}&order={{ order }}&status={{ status }}&severity={{ severity }}&search={{ search }}" class="btn-secondary {% if page == total_pages %}disabled{% endif %}" style="text-decoration: none;">Next</a>
        </div>
    </div>
    {% endif %}
</div>
{% endblock %}

{% block extra_js %}
<script src="{{ url_for('static', filename='js/cirt_incidents.js') }}"></script>
{% endblock %}
"""
with open(os.path.join(frontend_dir, "templates", "cirt_incidents.html"), "w", encoding="utf-8") as f:
    f.write(cirt_html_content)


# 3. Create static/css/cirt_incidents.css
cirt_css = """
.cirt-banner {
    background: #fef2f2;
    border: 1px solid #fca5a5;
    border-radius: 8px;
    padding: 12px 18px;
    margin-bottom: 20px;
    color: #991b1b;
    font-size: 0.875rem;
    font-weight: 500;
    display: flex;
    align-items: center;
    gap: 10px;
}

.badge-catastrophic.recent {
    animation: pulse-red 2s infinite;
}
@keyframes pulse-red {
    0%, 100% { box-shadow: 0 0 0 0 rgba(220,38,38,0.4); }
    50% { box-shadow: 0 0 0 6px rgba(220,38,38,0); }
}
"""
with open(os.path.join(frontend_dir, "static", "css", "cirt_incidents.css"), "w", encoding="utf-8") as f:
    f.write(cirt_css)


# 4. Create static/js/cirt_incidents.js
cirt_js = """
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
"""
with open(os.path.join(frontend_dir, "static", "js", "cirt_incidents.js"), "w", encoding="utf-8") as f:
    f.write(cirt_js)

# 5. Add escalation indicator to incident_detail.html
det_file = os.path.join(frontend_dir, "templates", "incident_detail.html")
with open(det_file, "r", encoding="utf-8") as f:
    dhtml = f.read()

escalation_badge = """
{% if incident.escalated_to_cirt %}
<div class="escalation-badge">
    🚨 Escalated to CIRT
    <span class="escalation-sub">
        This incident has been assigned to the Cyber Security Incident Response Team
    </span>
</div>
{% endif %}
"""
if '<div class="escalation-badge">' not in dhtml:
    # Right column Incident Details card starts with:
    # `<div class="card"> <div class="section-header">Incident Details</div>`
    # Let's insert the badge right below the header
    dhtml = dhtml.replace(
        '<div class="section-header">Incident Details</div>',
        '<div class="section-header">Incident Details</div>' + escalation_badge
    )
    with open(det_file, "w", encoding="utf-8") as f:
        f.write(dhtml)

det_css_file = os.path.join(frontend_dir, "static", "css", "incident_detail.css")
with open(det_css_file, "a", encoding="utf-8") as f:
    f.write("""
.escalation-badge {
    background: #fef2f2;
    border: 1px solid #fca5a5;
    border-radius: 8px;
    padding: 10px 14px;
    color: #991b1b;
    font-weight: 600;
    font-size: 0.875rem;
    margin-bottom: 12px;
    display: flex;
    flex-direction: column;
    gap: 4px;
}
.escalation-sub {
    font-weight: 400;
    font-size: 0.78rem;
    color: #b91c1c;
}
""")

print("done")
