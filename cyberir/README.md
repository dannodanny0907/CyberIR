# CyberIR — Cybersecurity Incident Management System
## With Real-Time Correlation And Knowledge Retrieval

### Project Overview
CyberIR is a cybersecurity incident management system
featuring two core algorithms:
1. Real-Time Correlation Engine — automatically groups
   related incidents into clusters
2. Historical Similarity Search — finds similar past
   incidents and suggests proven solutions

### Tech Stack
- Backend: Python 3.11+ / Flask
- Database: SQLite
- Frontend: HTML / CSS / JavaScript
- Charts: Chart.js

### Setup Instructions

1. Clone or download the project folder

2. Install dependencies:
   pip install -r requirements.txt

3. Run the application:
   python app.py

4. Open browser: http://localhost:5000

5. Login with default admin:
   Email: admin@cyberir.com
   Password: Admin@1234

### Generate Sample Data (Optional)
To populate with 40+ realistic sample incidents:
   python generate_sample_data.py

### Default Users After Sample Data
| Role    | Email                          | Password      |
|---------|--------------------------------|---------------|
| Admin   | admin@cyberir.com              | Admin@1234    |
| Analyst | sarah.mitchell@cyberir.com     | Analyst@1234  |
| Analyst | james.okafor@cyberir.com       | Analyst@1234  |
| Analyst | priya.sharma@cyberir.com       | Analyst@1234  |
| Viewer  | david.chen@cyberir.com         | Viewer@1234   |
| Viewer  | emma.thompson@cyberir.com      | Viewer@1234   |

### Project Structure
cyberir/
├── app.py                 # Main Flask application
├── auth.py                # Authentication
├── database.py            # Database functions
├── correlation_engine.py  # Algorithm 1: Correlation
├── similarity_engine.py   # Algorithm 2: Similarity
├── schema.sql             # Database schema
├── generate_sample_data.py # Sample data generator
├── requirements.txt
├── README.md
├── static/
│   ├── css/               # One CSS file per page
│   └── js/                # One JS file per page
└── templates/             # HTML templates

### Algorithm Details

#### Correlation Engine
Weights: Time(30%) + Type(25%) + Department(20%)
  + System(15%) + Indicators(10%)
Threshold: 0.65 (configurable in Settings)
Window: 48 hours (configurable)

#### Similarity Engine
Weights: System(40%) + Type(30%) + Description(20%)
  + Priority(10%)
Threshold: 0.50 (configurable)
Returns: Top 5 most similar resolved incidents

### Modules
1. Dashboard — metrics, charts, algorithm stats
2. Incidents — log, view, edit, manage incidents
3. Correlation — view and manage incident clusters
4. Similarity — view historical matches and solutions
5. Alerts — all system notifications
6. Reports — analytics and CSV exports
7. Settings — algorithm and system configuration
8. Users — user management (Admin only)
9. Profile — personal settings and preferences
