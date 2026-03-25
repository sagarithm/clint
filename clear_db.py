import sqlite3
import os

db_path = "data/cold_mailer.db"

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    tables = ["leads", "outreach_history", "daily_stats"]
    for table in tables:
        try:
            cursor.execute(f"DELETE FROM {table}")
            print(f"Cleared table: {table}")
        except sqlite3.OperationalError as e:
            print(f"Error clearing {table}: {e}")
            
    conn.commit()
    conn.close()
    print("Database refresh complete.")
else:
    print("Database file not found.")
