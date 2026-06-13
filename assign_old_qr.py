import sqlite3

conn = sqlite3.connect("qr.db")
cursor = conn.cursor()

cursor.execute("""
UPDATE qr_history
SET user_id = 1
WHERE user_id IS NULL
""")

conn.commit()

print("Updated rows:", cursor.rowcount)

conn.close()