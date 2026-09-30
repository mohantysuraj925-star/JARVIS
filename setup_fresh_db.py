import sqlite3
import time

conn = sqlite3.connect("jarvis.db")
c = conn.cursor()

# 1. Reset Stats to clean 0
c.execute("DROP TABLE IF EXISTS portal_stats")
c.execute("""
    CREATE TABLE portal_stats (
        key TEXT PRIMARY KEY,
        val INTEGER DEFAULT 0
    )
""")
c.execute("INSERT INTO portal_stats VALUES ('win_downloads', 0)")
c.execute("INSERT INTO portal_stats VALUES ('apk_downloads', 0)")

# 2. Reset Users table
c.execute("DROP TABLE IF EXISTS users")
c.execute("""
    CREATE TABLE users (
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

# 3. Add 1 test user taaki buttons saamne turant dikhein
c.execute("""
    INSERT INTO users (username, password, created_at, days_remaining, is_unlimited, is_active, last_seen)
    VALUES (?, ?, ?, ?, ?, ?, ?)
""", ("operator_demo", "pass123", "2026-09-30", 10, 0, 1, time.time()))

conn.commit()
conn.close()
print("Clean DB initialized with 0 stats and 1 visible operator node!")