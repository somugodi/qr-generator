import sqlite3

conn = sqlite3.connect("qr.db")
cursor = conn.cursor()

cursor.execute("PRAGMA table_info(qr_history)")
print(cursor.fetchall())

conn.close()