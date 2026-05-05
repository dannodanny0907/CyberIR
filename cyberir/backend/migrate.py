import sqlite3
import os

DB_PATH = r"c:\Users\PDM\Pictures\CYBER\cyberir\backend\cyberir.db"

def migrate():
    if not os.path.exists(DB_PATH):
        print("Database not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("ALTER TABLE users ADD COLUMN avatar_color TEXT DEFAULT '#2563eb'")
        print("Successfully added avatar_color to users table.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("avatar_color already exists.")
        else:
            print(f"Error: {e}")
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    migrate()
