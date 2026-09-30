import sqlite3

conn = sqlite3.connect("jarvis.db")
c = conn.cursor()

# Reset old dummy stats table to real counters
c.execute("DROP TABLE IF EXISTS portal_stats")
c.execute("""
    CREATE TABLE portal_stats (
        key TEXT PRIMARY KEY,
        val INTEGER DEFAULT 0
    )
""")
c.execute("INSERT INTO portal_stats VALUES ('win_downloads', 0)")
c.execute("INSERT INTO portal_stats VALUES ('apk_downloads', 0)")

# Users table with exact lifecycle, calendar and time constraints
c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        created_at TEXT NOT NULL,
        days_remaining INTEGER DEFAULT 10,
        is_unlimited INTEGER DEFAULT 0,
        is_active INTEGER DEFAULT 1,
        access_start_date TEXT DEFAULT NULL,
        access_end_date TEXT DEFAULT NULL,
        daily_time_start TEXT DEFAULT NULL,
        daily_time_end TEXT DEFAULT NULL,
        last_seen REAL DEFAULT 0
    )
""")

conn.commit()
conn.close()
print("Real-time zero-baseline database ready!")