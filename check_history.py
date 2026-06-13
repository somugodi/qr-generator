import sqlite3

conn = sqlite3.connect("qr.db")
cursor = conn.cursor()

cursor.execute("""
SELECT id, text, user_id
FROM qr_history
""")

for row in cursor.fetchall():
    print(row)

conn.close()