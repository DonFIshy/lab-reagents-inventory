# db_setup.py
import sqlite3

# יצירת מסד נתונים חדש לריאגנטים
conn = sqlite3.connect("reagents.db")
c = conn.cursor()

# טבלת ריאגנטים
c.execute("""
CREATE TABLE IF NOT EXISTS reagents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    supplier TEXT,
    catalog_number TEXT,
    cas_number TEXT,
    internal_id TEXT,
    batch_number TEXT,
    date_received TEXT,
    expiry_date TEXT,
    expiry_note TEXT,
    quantity INTEGER,
    opening_date TEXT,
    location TEXT
)
""")

conn.commit()
conn.close()
print("✅ reagents.db created with 'reagents' table.")
