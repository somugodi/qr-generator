import sqlite3

conn = sqlite3.connect("qr.db")
cursor = conn.cursor()

# Add user_id column
try:
    cursor.execute("""
    ALTER TABLE qr_history
    ADD COLUMN user_id INTEGER
    """)
    print("✅ user_id column added")
except Exception as e:
    print("user_id:", e)

# Add created_at column
try:
    cursor.execute("""
    ALTER TABLE qr_history
    ADD COLUMN created_at TEXT
    """)
    print("✅ created_at column added")
except Exception as e:
    print("created_at:", e)

conn.commit()
conn.close()

print("✅ Migration Complete")