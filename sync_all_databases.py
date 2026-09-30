import os
import sqlite3
import time
from datetime import datetime

# Project ke andar ki har .db file dhoondhein
db_files = []
for root, dirs, files in os.walk("."):
    if ".venv" in root:
        continue
    for f in files:
        if f.endswith(".db"):
            db_files.append(os.path.join(root, f))

now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

for db in db_files:
    try:
        conn = sqlite3.connect(db)
        c = conn.cursor()
        
        # 1. Reset Portal Stats to 0
        c.execute("DROP TABLE IF EXISTS portal_stats")
        c.execute("CREATE TABLE portal_stats (key TEXT PRIMARY KEY, val INTEGER DEFAULT 0)")
        c.execute("INSERT INTO portal_stats VALUES ('win_downloads', 0)")
        c.execute("INSERT INTO portal_stats VALUES ('apk_downloads', 0)")
        
        # 2. Reset Download Logs
        c.execute("DROP TABLE IF EXISTS download_logs")
        c.execute("""
        CREATE TABLE download_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            hwid TEXT,
            platform TEXT,
            timestamp TEXT
        )
        """)
        
        # 3. Initialize Users Table
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
        
        # Admin operator insert karein (Taaki Total Users = 1 aur Active = 1 sync rahein)
        c.execute("""
        INSERT INTO users (username, password, created_at, days_remaining, is_unlimited, is_active, last_seen)
        VALUES ('admin123', 'Suraj@2026', ?, 365, 1, 1, ?)
        """, (now_str, time.time()))
        
        conn.commit()
        conn.close()
        print(f"Cleaned and synced DB: {db}")
    except Exception as e:
        print(f"Error on {db}: {e}")