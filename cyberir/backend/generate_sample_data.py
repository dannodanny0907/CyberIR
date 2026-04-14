# File: generate_sample_data.py - Script to populate the database with mock cybersecurity incidents
import os
import sys

# Ensure proper working directory and python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from database import get_db_connection, init_db
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
from datetime import datetime, timedelta
import random
import math
from app import app
import sys

sys.stdout.reconfigure(encoding='utf-8')

SAMPLE_USERS = [
  {
    "full_name": "Sarah Mitchell",
    "email": "sarah.mitchell@cyberir.com",
    "password": "Analyst@1234",
    "role": "Analyst",
    "has_admin_privileges": 1,
    "phone_number": "+1 555 0101"
  },
  {
    "full_name": "James Okafor",
    "email": "james.okafor@cyberir.com",
    "password": "Analyst@1234",
    "role": "Analyst",
    "has_admin_privileges": 0,
    "phone_number": "+1 555 0102"
  },
  {
    "full_name": "Priya Sharma",
    "email": "priya.sharma@cyberir.com",
    "password": "Analyst@1234",
    "role": "Analyst",
    "has_admin_privileges": 0,
    "phone_number": "+1 555 0103"
  },
  {
    "full_name": "David Chen",
    "email": "david.chen@cyberir.com",
    "password": "Viewer@1234",
    "role": "Viewer",
    "has_admin_privileges": 0,
    "phone_number": "+1 555 0104"
  },
  {
    "full_name": "Emma Thompson",
    "email": "emma.thompson@cyberir.com",
    "password": "Viewer@1234",
    "role": "Viewer",
    "has_admin_privileges": 0,
    "phone_number": "+1 555 0105"
  }
]

INCIDENT_TEMPLATES = [
  {
    "type": "Phishing",
    "titles": [
      "Suspicious phishing email targeting Finance team",
      "Phishing campaign detected in HR department",
      "Executive spear-phishing attempt blocked",
      "Mass phishing emails received by Operations",
      "Credential harvesting phishing link reported"
    ],
    "descriptions": [
      "Multiple employees received emails impersonating IT support requesting password resets via a fraudulent link. Link leads to credential harvesting page mimicking company login portal.",
      "HR department received targeted phishing emails claiming to be from payroll system requesting urgent login to verify bank details. Several employees clicked the link before it was blocked.",
      "A sophisticated spear-phishing email was sent to the CEO and CFO impersonating a board member requesting urgent wire transfer authorization.",
      "Bulk phishing emails sent to operations staff containing malicious attachment disguised as a shipping invoice from known vendor.",
      "Employees reported receiving emails with spoofed sender addresses containing links to fake Microsoft 365 login pages to steal credentials."
    ],
    "assets": [
      "Email Server", "Exchange-Server-01",
      "Office365-Tenant", "Mail-Gateway",
      "Webmail-Portal"
    ],
    "departments": [
      "Finance", "HR", "Executive",
      "Operations", "Marketing"
    ],
    "indicators": [
      "phishing@evil-domain.com, 185.220.101.45",
      "fake-login.malicious.net, spoofed@company.com",
      "credential-harvest.tk, 94.102.49.190",
      "malware-attach.zip, 104.21.45.67",
      "stolen-creds.ru, 185.156.73.54"
    ],
    "resolutions": [
      "Blocked malicious domain at email gateway. Reset passwords for 3 affected accounts. Conducted phishing awareness training for department. Implemented DMARC policy.",
      "Isolated affected workstations. Performed credential reset for all recipients. Added sender domain to blocklist. Notified affected staff of compromise.",
      "No credentials were compromised — email blocked by spam filter. Added executive email addresses to enhanced monitoring. Briefed executives on spear-phishing indicators.",
      "Quarantined malicious attachment. Scanned all endpoints for malware. Updated email filtering rules. No payload executed successfully.",
      "Reset credentials for 8 affected users. Enabled MFA for all accounts in department. Blocked phishing infrastructure at firewall."
    ]
  },
  {
    "type": "Malware",
    "titles": [
      "Ransomware detected on Finance workstation",
      "Trojan horse malware found on server",
      "Spyware infection on executive laptop",
      "Cryptominer deployed on cloud instance",
      "Rootkit detected during security scan"
    ],
    "descriptions": [
      "Ransomware variant detected on Finance department workstation FIN-WS-04. File encryption process started before endpoint protection quarantined the threat. 23 files encrypted before containment.",
      "Trojan horse malware identified on application server APP-SRV-02 during routine scan. Malware was establishing outbound C2 connections to known malicious infrastructure.",
      "Commercial spyware found on CFO laptop during forensic review. Malware had been present for estimated 14 days and may have exfiltrated sensitive documents and communications.",
      "Unauthorized cryptocurrency mining software deployed on AWS EC2 instance following exploitation of exposed API credentials. Resource usage spiked 900% before detected.",
      "Advanced rootkit detected on domain controller DC-PRIMARY during threat hunting exercise. Rootkit was hiding malicious processes and had persistence mechanisms installed."
    ],
    "assets": [
      "Workstation-FIN-04", "App-Server-02",
      "Executive-Laptop-CFO", "AWS-EC2-Prod-03",
      "Domain-Controller-Primary"
    ],
    "departments": [
      "Finance", "IT", "Executive",
      "Operations", "IT"
    ],
    "indicators": [
      "ransomware.exe, 192.168.1.45, SHA256:a1b2c3d4e5f6",
      "trojan-dropper.dll, 10.0.0.55, c2.evil.net",
      "spyware-commercial.exe, exfil-server.com",
      "xmrig-miner, cryptopool.evil.org, 45.142.212.100",
      "rootkit-kernel.sys, persist-c2.darkweb.onion"
    ],
    "resolutions": [
      "Isolated workstation from network immediately. Restored 23 encrypted files from backup. Reimaged workstation. Updated endpoint protection signatures. Patched OS vulnerability used as initial access vector.",
      "Terminated malicious processes and removed malware. Blocked C2 domains at firewall. Performed full server audit. Reset all service account credentials.",
      "Wiped and reimaged CFO laptop. Reviewed potentially exfiltrated documents. Reported to legal team for assessment. Deployed EDR solution on all executive devices.",
      "Terminated compromised instance. Rotated all AWS credentials. Implemented IP allowlisting for API access. Reviewed all cloud resource usage for anomalies.",
      "Removed rootkit using specialized tools. Rebuilt domain controller from clean backup. Conducted full Active Directory audit. Reset all domain admin passwords."
    ]
  },
  {
    "type": "Unauthorized Access",
    "titles": [
      "Brute force attack on admin portal",
      "Unauthorized database access detected",
      "Privilege escalation by internal user",
      "External actor gained VPN access",
      "Compromised service account activity"
    ],
    "descriptions": [
      "Multiple failed login attempts followed by successful authentication to admin portal from foreign IP address. Approximately 2400 attempts over 45 minutes from single source.",
      "Database administrator detected unauthorized queries being run against customer database from application server account that should not have direct database access.",
      "Insider threat: junior analyst account used to access restricted executive reports and export sensitive financial data. Access outside normal working hours.",
      "VPN logs show successful authentication using legitimate employee credentials from overseas IP. Employee confirmed they did not initiate connection — credentials compromised.",
      "Service account SVCACC-BACKUP performing unusual lateral movement across network segments, accessing systems outside its normal operational scope."
    ],
    "assets": [
      "Admin-Portal", "Customer-Database-01",
      "Finance-Reports-Server", "VPN-Gateway",
      "Service-Account-SVCACC-BACKUP"
    ],
    "departments": [
      "IT", "IT", "Finance", "IT", "IT"
    ],
    "indicators": [
      "195.123.45.67, admin@company.com, brute-force-tool",
      "SELECT * FROM customers, app-server-ip: 10.0.1.55",
      "export-financial-data.csv, user: jsmith, 02:34 AM",
      "VPN-auth: emp.credentials, IP: 91.108.4.0/24 Russia",
      "SVCACC-BACKUP, lateral-movement, 10.0.2.0/24"
    ],
    "resolutions": [
      "Blocked source IP at firewall. Reset compromised admin credentials. Implemented account lockout after 10 failed attempts. Enabled geo-blocking for admin portal.",
      "Revoked database permissions from application account. Reviewed all unauthorized queries. No data exfiltration confirmed. Updated least-privilege access policy.",
      "Suspended user account pending investigation. Preserved forensic evidence. Notified HR and legal. Implemented after-hours access alerts. No external exfiltration detected.",
      "Immediately revoked compromised VPN credentials. Reset employee password and enabled MFA. Reviewed all actions taken during unauthorized session. No data accessed.",
      "Disabled service account and rotated credentials. Reviewed all systems accessed. Implemented service account privilege restrictions. Deployed PAM solution."
    ]
  },
  {
    "type": "Data Breach",
    "titles": [
      "Customer PII exposed via misconfigured S3 bucket",
      "Employee records accessed by unauthorized party",
      "Payment card data potentially compromised",
      "Source code repository exposed publicly",
      "Medical records breach via third-party vendor"
    ],
    "descriptions": [
      "AWS S3 bucket containing customer personally identifiable information was misconfigured as publicly accessible. Bucket contained 15,000 customer records including names, emails and partial address data. Exposed for estimated 3 days.",
      "HR system audit revealed that employee personal records including salary information and performance reviews were accessed by a user account that had been granted excessive permissions during a system migration 6 months prior.",
      "Point-of-sale system at retail locations may have been compromised by skimming malware installed by unknown actor. Approximately 340 payment card transactions potentially affected over a 2-week period.",
      "Internal source code repository was accidentally made publicly accessible during infrastructure migration. Repository contained API keys, database connection strings and proprietary algorithms. Exposed for approximately 6 hours.",
      "Third-party vendor providing patient management services notified us of unauthorized access to their systems which contained a subset of our patient records. 890 patient records potentially accessed."
    ],
    "assets": [
      "AWS-S3-Customer-Data", "HR-System-Database",
      "POS-System-Retail", "Git-Repository-Internal",
      "Vendor-Patient-Portal"
    ],
    "departments": [
      "IT", "HR", "Operations",
      "IT", "Operations"
    ],
    "indicators": [
      "s3-public-bucket, customer-data.csv exposed",
      "excessive-permissions, HR-user: mjohnson",
      "POS-malware, card-skimmer-v2.exe, 340 cards",
      "public-repo, API-keys-exposed, DB-credentials",
      "vendor-breach-notification, 890-records, patient-data"
    ],
    "resolutions": [
      "Immediately restricted S3 bucket permissions. Notified affected customers per GDPR requirements. Implemented S3 bucket policy audit across all buckets. Engaged legal counsel for regulatory reporting.",
      "Revoked excessive permissions. Conducted full audit of what data was accessed. No evidence of exfiltration outside organization. Implemented quarterly access reviews.",
      "Removed POS malware from all affected terminals. Notified card processor. Assisted affected customers with card replacement. Strengthened POS system security controls.",
      "Made repository private immediately. Rotated all exposed API keys and credentials. Reviewed git history for any unauthorized commits. Implemented repository access controls.",
      "Terminated vendor data sharing agreement. Notified affected patients. Filed regulatory report. Reviewed all third-party vendor security requirements."
    ]
  },
  {
    "type": "DDoS",
    "titles": [
      "DDoS attack targeting public web portal",
      "DNS amplification attack on nameservers",
      "Application layer DDoS on API gateway",
      "Volumetric attack saturating WAN link",
      "SYN flood attack on load balancer"
    ],
    "descriptions": [
      "Distributed denial of service attack targeting public customer portal. Attack generating approximately 45Gbps of UDP flood traffic from botnet of approximately 12,000 nodes. Portal unavailable for 34 minutes.",
      "DNS amplification attack using misconfigured open resolvers to generate approximately 120Gbps of traffic directed at company nameservers. DNS resolution service degraded for external users for 2 hours.",
      "Layer 7 application DDoS targeting API gateway with 850,000 requests per second. Attack designed to exhaust application server resources rather than saturate bandwidth. API response times degraded by 800%.",
      "Volumetric DDoS attack saturated primary WAN uplink with 8Gbps of mixed traffic. All internet-dependent services unavailable for duration of attack. Secondary link also partially affected.",
      "SYN flood attack targeting public-facing load balancer generating 2 million SYN packets per second. Load balancer connection table exhausted causing service disruption for 22 minutes."
    ],
    "assets": [
      "Public-Web-Portal", "DNS-Nameservers",
      "API-Gateway", "WAN-Primary-Link",
      "Load-Balancer-External"
    ],
    "departments": [
      "IT", "IT", "IT", "IT", "IT"
    ],
    "indicators": [
      "45Gbps-UDP-flood, botnet-12000-nodes, multiple-IPs",
      "DNS-amplification, 120Gbps, open-resolvers",
      "850k-req/sec, Layer-7, API-exhaustion",
      "8Gbps-volumetric, WAN-saturation, mixed-traffic",
      "2M-SYN/sec, connection-table-exhausted, LB-disruption"
    ],
    "resolutions": [
      "Activated DDoS mitigation service. Traffic scrubbed through cloud scrubbing center. Portal restored after 34 minutes. Implemented permanent DDoS protection service contract.",
      "Blocked amplification traffic at upstream provider. Disabled open resolver functionality. Implemented rate limiting on DNS responses. Deployed anycast DNS infrastructure.",
      "Implemented rate limiting and CAPTCHA challenges at API gateway. Blocked attacking IP ranges. Scaled API infrastructure horizontally. Deployed WAF with bot protection rules.",
      "Activated failover to secondary WAN link. Contacted upstream ISP for traffic filtering. Primary link restored after 47 minutes. Implemented BGP blackholing capability.",
      "Applied SYN cookie protection on load balancer. Blocked source IP ranges at upstream firewall. Service restored after 22 minutes. Increased load balancer connection table size."
    ]
  }
]

# Handle logic for generate_users
def generate_users(conn, admin_id):
  print("Creating sample users...")
  user_ids = [admin_id]
  for u in SAMPLE_USERS:
    try:
      cursor = conn.execute(
        '''INSERT INTO users 
           (full_name, email, password_hash, role,
            has_admin_privileges, phone_number,
            is_active, created_by)
           VALUES (?,?,?,?,?,?,1,?)''',
        (u['full_name'], u['email'],
         generate_password_hash(u['password']),
         u['role'], u['has_admin_privileges'],
         u['phone_number'], admin_id))
      user_id = cursor.lastrowid
      user_ids.append(user_id)
      
      conn.execute('''INSERT OR IGNORE INTO user_preferences (user_id) VALUES (?)''', [user_id])
      print(f"  Created: {u['full_name']} ({u['role']})")
    except Exception as e:
      print(f"  Skipped {u['email']}: {e}")
      # If user already exists, fetch their ID so the array is still populated correctly
      existing_usr = conn.execute('SELECT id FROM users WHERE email=?', (u['email'],)).fetchone()
      if existing_usr:
          user_ids.append(existing_usr['id'])
          
  conn.commit()
  return user_ids

# Handle logic for generate_incidents
def generate_incidents(conn, user_ids, admin_id):
  print("Generating sample incidents...")
  
  analyst_ids = user_ids[1:4]
  incident_ids_db = []
  incident_counter = 1
  
  now = datetime.now()
  
  scenarios = [
    # PHISHING CLUSTER GROUP 1 — same day, Finance
    {"t":0,"ti":0,"d":2,"h":1,"s":"Resolved", "at":0,"ua":15,"ac":4,"ts":4,"ve":3, "ir":0},
    {"t":0,"ti":1,"d":2,"h":2,"s":"Resolved", "at":1,"ua":8,"ac":4,"ts":4,"ve":3, "ir":0},
    {"t":0,"ti":2,"d":2,"h":3,"s":"Investigating", "at":0,"ua":3,"ac":5,"ts":5,"ve":4, "ir":0},
    {"t":0,"ti":3,"d":2,"h":4,"s":"Open", "at":None,"ua":25,"ac":4,"ts":4,"ve":3, "ir":1},
    {"t":0,"ti":4,"d":2,"h":5,"s":"Open", "at":1,"ua":10,"ac":3,"ts":4,"ve":3, "ir":0},

    # MALWARE CLUSTER GROUP — same week
    {"t":1,"ti":0,"d":5,"h":2,"s":"Resolved", "at":0,"ua":1,"ac":5,"ts":5,"ve":4, "ir":0},
    {"t":1,"ti":1,"d":5,"h":8,"s":"Resolved", "at":2,"ua":0,"ac":4,"ts":4,"ve":3, "ir":0},
    {"t":1,"ti":2,"d":6,"h":1,"s":"Closed", "at":0,"ua":1,"ac":5,"ts":5,"ve":5, "ir":0},
    {"t":1,"ti":3,"d":6,"h":10,"s":"Investigating", "at":1,"ua":0,"ac":4,"ts":4,"ve":3, "ir":0},

    # UNAUTHORIZED ACCESS — spread over 2 weeks
    {"t":2,"ti":0,"d":8,"h":3,"s":"Resolved", "at":2,"ua":0,"ac":4,"ts":3,"ve":3, "ir":0},
    {"t":2,"ti":1,"d":9,"h":14,"s":"Resolved", "at":0,"ua":0,"ac":5,"ts":4,"ve":3, "ir":0},
    {"t":2,"ti":2,"d":10,"h":22,"s":"Closed", "at":2,"ua":1,"ac":3,"ts":3,"ve":2, "ir":0},
    {"t":2,"ti":3,"d":12,"h":8,"s":"Investigating", "at":1,"ua":0,"ac":4,"ts":4,"ve":4, "ir":0},
    {"t":2,"ti":4,"d":14,"h":11,"s":"Open", "at":None,"ua":0,"ac":3,"ts":3,"ve":3, "ir":1},

    # DATA BREACHES — spread over month
    {"t":3,"ti":0,"d":15,"h":9,"s":"Resolved", "at":0,"ua":15000,"ac":5,"ts":5,"ve":5, "ir":0},
    {"t":3,"ti":1,"d":18,"h":14,"s":"Resolved", "at":2,"ua":45,"ac":4,"ts":3,"ve":3, "ir":0},
    {"t":3,"ti":2,"d":20,"h":10,"s":"Closed", "at":0,"ua":340,"ac":5,"ts":4,"ve":4, "ir":0},
    {"t":3,"ti":3,"d":22,"h":16,"s":"Resolved", "at":1,"ua":5,"ac":4,"ts":4,"ve":4, "ir":0},
    {"t":3,"ti":4,"d":25,"h":8,"s":"Investigating", "at":2,"ua":890,"ac":5,"ts":4,"ve":4, "ir":0},

    # DDOS ATTACKS
    {"t":4,"ti":0,"d":3,"h":14,"s":"Resolved", "at":1,"ua":5000,"ac":5,"ts":4,"ve":3, "ir":0},
    {"t":4,"ti":1,"d":7,"h":9,"s":"Closed", "at":0,"ua":0,"ac":4,"ts":4,"ve":3, "ir":0},
    {"t":4,"ti":2,"d":11,"h":16,"s":"Resolved", "at":1,"ua":1500,"ac":4,"ts":3,"ve":3, "ir":0},
    {"t":4,"ti":3,"d":16,"h":11,"s":"Closed", "at":2,"ua":0,"ac":4,"ts":4,"ve":4, "ir":0},
    {"t":4,"ti":4,"d":30,"h":8,"s":"Resolved", "at":0,"ua":200,"ac":3,"ts":3,"ve":2, "ir":0},

    # SECOND PHISHING CLUSTER — 10 days ago
    {"t":0,"ti":0,"d":10,"h":9,"s":"Resolved", "at":2,"ua":5,"ac":3,"ts":3,"ve":3, "ir":1},
    {"t":0,"ti":1,"d":10,"h":10,"s":"Resolved", "at":0,"ua":12,"ac":4,"ts":4,"ve":3, "ir":1},
    {"t":0,"ti":2,"d":10,"h":11,"s":"Investigating", "at":1,"ua":2,"ac":4,"ts":4,"ve":4, "ir":0},
    {"t":0,"ti":3,"d":10,"h":13,"s":"Open", "at":None,"ua":8,"ac":3,"ts":3,"ve":3, "ir":0},

    # RECENT INCIDENTS — last 3 days
    {"t":0,"ti":4,"d":1,"h":2,"s":"Open", "at":0,"ua":20,"ac":4,"ts":4,"ve":3, "ir":0},
    {"t":1,"ti":4,"d":1,"h":6,"s":"Open", "at":None,"ua":0,"ac":5,"ts":5,"ve":5, "ir":0},
    {"t":2,"ti":0,"d":0,"h":5,"s":"Open", "at":1,"ua":0,"ac":4,"ts":4,"ve":3, "ir":0},
    {"t":3,"ti":2,"d":0,"h":3,"s":"Investigating", "at":2,"ua":100,"ac":5,"ts":4,"ve":4, "ir":0},
    {"t":4,"ti":0,"d":0,"h":1,"s":"Open", "at":None,"ua":2000,"ac":5,"ts":5,"ve":4, "ir":0},

    # OLDER RESOLVED — for similarity algorithm
    {"t":0,"ti":0,"d":35,"h":10,"s":"Resolved", "at":0,"ua":6,"ac":3,"ts":3,"ve":3, "ir":0},
    {"t":0,"ti":1,"d":38,"h":14,"s":"Closed", "at":1,"ua":3,"ac":4,"ts":3,"ve":2, "ir":0},
    {"t":1,"ti":0,"d":32,"h":9,"s":"Resolved", "at":2,"ua":1,"ac":4,"ts":4,"ve":3, "ir":0},
    {"t":1,"ti":1,"d":40,"h":11,"s":"Closed", "at":0,"ua":0,"ac":5,"ts":5,"ve":4, "ir":0},
    {"t":2,"ti":2,"d":28,"h":15,"s":"Resolved", "at":1,"ua":1,"ac":3,"ts":4,"ve":3, "ir":0},
    {"t":3,"ti":0,"d":44,"h":8,"s":"Closed", "at":2,"ua":500,"ac":5,"ts":5,"ve":5, "ir":0},
    {"t":4,"ti":3,"d":42,"h":12,"s":"Resolved", "at":0,"ua":0,"ac":4,"ts":4,"ve":3, "ir":0},
  ]
  
  for scenario in scenarios:
    template = INCIDENT_TEMPLATES[scenario['t']]
    idx = scenario['ti']
    
    reported_date = now - timedelta(days=scenario['d'], hours=scenario['h'])
    
    ua = scenario['ua']
    ua_score = 1 if ua==0 else 2 if ua<=5 else 3 if ua<=20 else 4 if ua<=100 else 5
    ac, ts, ve, ir = scenario['ac'], scenario['ts'], scenario['ve'], scenario['ir']
    raw = (ac*0.30 + ts*0.30 + ve*0.15 + ua_score*0.20 + (5 if ir else 1)*0.05)
    risk_score = round((raw/5)*100, 2)
    
    if risk_score >= 75: priority = "Critical"
    elif risk_score >= 50: priority = "High"
    elif risk_score >= 25: priority = "Medium"
    else: priority = "Low"
    
    assigned_to = analyst_ids[scenario['at']] if scenario['at'] is not None else None
    
    incident_id = f"INC-{str(incident_counter).zfill(3)}"
    
    investigating_started_date = None
    resolved_date = None
    resolution_time_minutes = None
    resolution_notes = None
    updated_by = None
    closed_date = None
    status = scenario['s']
    
    if status == 'Investigating':
        investigating_started_date = reported_date + timedelta(hours=random.randint(1,4))
    if status in ['Resolved', 'Closed']:
        investigating_started_date = reported_date + timedelta(hours=random.randint(1,3))
        resolved_date = reported_date + timedelta(hours=random.randint(4,48))
        resolution_time_minutes = int((resolved_date-reported_date).total_seconds()/60)
        resolution_notes = template['resolutions'][idx % len(template['resolutions'])]
        updated_by = assigned_to or admin_id
    if status == 'Closed':
        closed_date = resolved_date + timedelta(hours=random.randint(1,24))

    title = template['titles'][idx % len(template['titles'])]
    description = template['descriptions'][idx % len(template['descriptions'])]
    affected_asset = template['assets'][idx % len(template['assets'])]
    department = template['departments'][idx % len(template['departments'])]
    indicators = template['indicators'][idx % len(template['indicators'])]
    
    cursor = conn.execute('''
        INSERT INTO incidents (
            incident_id, title, description, incident_type, affected_asset, affected_department,
            attack_indicators, asset_criticality, threat_severity, vulnerability_exposure,
            users_affected, is_repeat, risk_score, priority, status, assigned_to,
            reported_date, investigating_started_date, resolved_date, closed_date,
            resolution_time_minutes, resolution_notes, created_by, updated_by
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    ''', (
        incident_id, title, description, template['type'], affected_asset, department,
        indicators, ac, ts, ve, ua, ir, risk_score, priority, status, assigned_to,
        reported_date, investigating_started_date, resolved_date, closed_date,
        resolution_time_minutes, resolution_notes, admin_id, updated_by
    ))
    lastrowid = cursor.lastrowid
    
    conn.execute(
        '''INSERT INTO activity_logs (user_id, action_type, target_type, target_id, created_at) VALUES (?,?,?,?,?)''',
        (assigned_to or admin_id, 'CREATE_INCIDENT', 'Incident', incident_id, reported_date)
    )
    
    incident_counter += 1
    incident_ids_db.append(lastrowid)
  
  conn.commit()
  print(f"  Created {len(scenarios)} incidents")
  return incident_ids_db

# Handle logic for run_algorithms_on_all
def run_algorithms_on_all(incident_ids_db):
  print("Running algorithms on all incidents...")
  
  from correlation_engine import run_correlation
  from similarity_engine import run_similarity
  
  clusters_created = 0
  matches_found = 0
  
  for incident_id in incident_ids_db:
    try:
      corr = run_correlation(incident_id)
      if corr and corr.get('clustered'):
        clusters_created += 1
    except Exception as e:
      pass
    
    try:
      sim = run_similarity(incident_id)
      if sim and sim.get('found'):
        matches_found += 1
    except Exception as e:
      pass
  
  print(f"  Correlation: {clusters_created} incidents clustered")
  print(f"  Similarity: {matches_found} matches found")

# Handle logic for generate_activity_logs
def generate_activity_logs(conn, user_ids, admin_id):
  print("Generating activity logs...")
  
  actions = [
    'LOGIN', 'LOGIN', 'LOGIN',
    'UPDATE_INCIDENT', 'ASSIGN_INCIDENT',
    'RESOLVE_INCIDENT', 'UPDATE_SETTINGS'
  ]
  
  for user_id in user_ids:
    for i in range(random.randint(3, 8)):
      days_ago = random.randint(0, 30)
      action = random.choice(actions)
      created_at = datetime.now() - timedelta(
        days=days_ago, 
        hours=random.randint(0,23),
        minutes=random.randint(0,59))
      
      conn.execute(
        '''INSERT INTO activity_logs
           (user_id, action_type, target_type, created_at)
           VALUES (?,?,'System',?)''',
        (user_id, action, created_at))
  
  conn.commit()
  print("  Activity logs generated")

# Handle logic for main
def main():
  with app.app_context():
    print("=" * 50)
    print("CyberIR Sample Data Generator")
    print("=" * 50)
    
    conn = get_db_connection()
    
    existing = conn.execute('SELECT COUNT(*) as c FROM incidents').fetchone()['c']
    
    if existing > 0:
      print(f"\\n⚠️  Database already has {existing} incidents.")
      response = input("Clear existing data and regenerate? (yes/no): ")
      if response.lower() != 'yes':
        print("Cancelled.")
        conn.close()
        return
      
      print("Clearing existing data...")
      conn.execute('DELETE FROM incidents')
      conn.execute('DELETE FROM incident_clusters')
      conn.execute('DELETE FROM alerts')
      conn.execute('DELETE FROM activity_logs')
      conn.execute('DELETE FROM users WHERE id != 1')
      conn.execute('DELETE FROM user_preferences WHERE user_id != 1')
      conn.commit()
      print("Cleared.")
    
    admin = conn.execute('SELECT id FROM users WHERE role="Admin" LIMIT 1').fetchone()
    if not admin:
      print("No admin user found. Run app first.")
      return
    admin_id = admin['id']
    
    user_ids = generate_users(conn, admin_id)
    incident_ids = generate_incidents(conn, user_ids, admin_id)
    generate_activity_logs(conn, user_ids, admin_id)
    
    run_algorithms_on_all(incident_ids)
    
    print()
    print("=" * 50)
    print("✅ Sample data generated successfully!")
    print(f"   Users created: {len(user_ids)}")
    print(f"   Incidents created: {len(incident_ids)}")
    print()
    print("Login credentials:")
    print("  Admin: admin@cyberir.com / Admin@1234")
    print("  Analyst: sarah.mitchell@cyberir.com / Analyst@1234")
    print("  Viewer: david.chen@cyberir.com / Viewer@1234")
    print("=" * 50)

if __name__ == '__main__':
  main()
