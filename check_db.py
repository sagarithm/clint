import sqlite3
import os

db_path = 'data/cold_mailer.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name, category, website, phone FROM leads ORDER BY id DESC LIMIT 10")
    rows = cursor.fetchall()
    for row in rows:
        print(f"Name: {row[0]} | Cat: {row[1]} | Web: {row[2]} | Phone: {row[3]}")
    conn.close()
else:
    print("DB_NOT_FOUND")
