import os
import sys

# Add backend directory to path so internal imports work
BACKEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend')
sys.path.insert(0, BACKEND_DIR)

from backend.app import app
from backend.database import init_db, create_default_admin

if __name__ == '__main__':
    init_db()
    create_default_admin()
    print("="*50)
    print("Starting CyberIR...")
    print("URL: http://localhost:5000")
    print("Admin: admin@cyberir.com / Admin@1234")
    print("="*50)
    app.run(debug=True, host='0.0.0.0', port=5000)
