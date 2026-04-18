import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend')))

from database import get_db_connection
from correlation_engine import run_correlation
from app import app
import time

def main():
    with app.app_context():
        conn = get_db_connection()
        incidents = conn.execute("SELECT id, incident_id FROM incidents").fetchall()
        conn.close()
        
        print(f"Found {len(incidents)} incidents. Running algorithms...")
        
        clusters_created = 0
        
        for inc in incidents:
            primary_id = inc['id']
            inc_str = inc['incident_id']
            print(f"Processing {inc_str}...")
            start_time = time.time()
            try:
                corr = run_correlation(primary_id)
                if corr and corr.get('clustered'):
                    clusters_created += 1
            except Exception as e:
                print(f"  Error: {e}")
            
            elapsed = time.time() - start_time
            print(f"  Done in {elapsed:.2f}s")
                
        print(f"Done! Clusters created: {clusters_created}")

if __name__ == '__main__':
    main()
