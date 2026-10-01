import sqlite3
import time
from datetime import datetime

conn = sqlite3.connect("portal.db", timeout=15)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    hwid TEXT DEFAULT 'NODE-ACTIVE',
    role TEXT DEFAULT 'operator',
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

c.execute("CREATE TABLE IF NOT EXISTS portal_stats (key TEXT PRIMARY KEY, val INTEGER DEFAULT 0)")
c.execute("INSERT OR IGNORE INTO portal_stats VALUES ('win_downloads', 0)")
c.execute("INSERT OR IGNORE INTO portal_stats VALUES ('apk_downloads', 0)")

c.execute("""
CREATE TABLE IF NOT EXISTS download_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    hwid TEXT,
    platform TEXT,
    timestamp TEXT
)
""")

now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Super Admin Account
c.execute("DELETE FROM users WHERE username = 'admin123'")
c.execute("""
    INSERT INTO users (username, password, role, created_at, days_remaining, is_unlimited, is_active, last_seen)
    VALUES ('admin123', 'suraj', 'admin', ?, 9999, 1, 1, ?)
""", (now_str, time.time()))

conn.commit()
conn.close()
print("Master DB Initialized.")