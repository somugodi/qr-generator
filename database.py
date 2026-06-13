import sqlite3

conn = sqlite3.connect("qr.db")

cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS qr_history(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT,
    image TEXT
)
""")

conn.commit()
conn.close()

print("QR Database Created")