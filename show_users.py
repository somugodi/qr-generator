import sqlite3

conn = sqlite3.connect("qr.db")
cursor = conn.cursor()

cursor.execute("SELECT id, username FROM users")

for row in cursor.fetchall():
    print(row)

conn.close()