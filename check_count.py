import sqlite3
import os

db_path = 'data/cold_mailer.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM leads WHERE category = 'Schools in New Delhi'")
    count = cursor.fetchone()[0]
    print(f"COUNT:{count}")
    conn.close()
else:
    print("DB_NOT_FOUND")
