import sqlite3
import os

db_path = 'data/cold_mailer.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name, audit_summary FROM leads WHERE audit_summary IS NOT NULL ORDER BY id DESC LIMIT 5")
    rows = cursor.fetchall()
    for row in rows:
        print(f"Name: {row[0]}")
        print(f"Audit: {row[1][:200]}...")
        print("-" * 20)
    conn.close()
else:
    print("DB_NOT_FOUND")
