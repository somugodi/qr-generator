import sqlite3

conn = sqlite3.connect("qr.db")
cursor = conn.cursor()

cursor.execute("PRAGMA table_info(users)")
print(cursor.fetchall())

conn.close()