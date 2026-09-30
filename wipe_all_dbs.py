import sqlite3
import os

db_files = ["portal.db", "jarvis.db"]

for db in db_files:
    if not os.path.exists(db):
        continue
    conn = sqlite3.connect(db)
    c = conn.cursor()
    
    # 1. Reset all download counters to absolute 0
    c.execute("DROP TABLE IF EXISTS portal_stats")
    c.execute("CREATE TABLE portal_stats (key TEXT PRIMARY KEY, val INTEGER DEFAULT 0)")
    c.execute("INSERT INTO portal_stats VALUES ('win_downloads', 0)")
    c.execute("INSERT INTO portal_stats VALUES ('apk_downloads', 0)")
    
    # 2. Clear activity logs completely
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
    
    # 3. Reset users table
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
    
    # Create default admin operator so Total Users = 1 and Active Users = 1
    import time
    from datetime import datetime
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    c.execute("""
    INSERT INTO users (username, password, created_at, days_remaining, is_unlimited, is_active, last_seen)
    VALUES ('admin123', 'Suraj@2026', ?, 365, 1, 1, ?)
    """, (now_str, time.time()))

    conn.commit()
    conn.close()
    print(f"Successfully cleaned and synced: {db}")