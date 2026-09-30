import os
import sqlite3
import re

# 1. Sabhi DBs me tables ensure karein bina data wipe kiye
db_files = ["portal.db", "jarvis.db", "server/portal.db"]
for db in db_files:
    os.makedirs(os.path.dirname(db) if os.path.dirname(db) else ".", exist_ok=True)
    conn = sqlite3.connect(db)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        hwid TEXT DEFAULT 'CLIENT-NODE',
        email TEXT DEFAULT '',
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
    conn.commit()
    conn.close()

# 2. Server application code mein Registration & Download synchronization fix karein
path = "server/app.py"
with open(path, "r", encoding="utf-8-sig") as f:
    text = f.read()

# Unified DB connection jo hamesha ek hi file use kare
db_unifier = """
def get_db_connection():
    conn = sqlite3.connect("portal.db")
    conn.row_factory = sqlite3.Row
    return conn
get_db = get_db_connection
"""

if "def get_db_connection():" in text:
    text = re.sub(r'def get_db_connection\(\):[\s\S]*?return conn', db_unifier.strip(), text)

# Download route jo registered user ya guest dono ko track kare aur count badhaye
download_tracker = """
@app.get("/get-package/{platform_name}")
async def download_package_tracker(platform_name: str, req: Request):
    client_ip = req.client.host if req.client else "unknown"
    plat = platform_name.lower()
    
    # Check if user is logged in via cookie/session
    uname = req.cookies.get("username") or req.query_params.get("user") or "operator_client"
    
    conn = get_db_connection()
    c = conn.cursor()
    
    # 1. Update counter
    if "win" in plat:
        c.execute("UPDATE portal_stats SET val = val + 1 WHERE key = 'win_downloads'")
    elif "apk" in plat or "android" in plat:
        c.execute("UPDATE portal_stats SET val = val + 1 WHERE key = 'apk_downloads'")
        
    # 2. Log download
    from datetime import datetime
    now_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute(
        "INSERT INTO download_logs (username, hwid, platform, timestamp) VALUES (?, ?, ?, ?)",
        (uname, f"IP-{client_ip}", plat, now_time)
    )
    
    # 3. Agar user table me nahi hai toh auto-register as operator
    c.execute("SELECT id FROM users WHERE username = ?", (uname,))
    if not c.fetchone() and uname != "operator_client":
        c.execute(
            "INSERT INTO users (username, password, created_at, last_seen) VALUES (?, 'pass123', ?, ?)",
            (uname, now_time, time.time())
        )
    
    conn.commit()
    conn.close()
    
    file_path = f"downloads/{plat}_installer.zip"
    if os.path.exists(file_path):
        return FileResponse(file_path, filename=f"jarvis_{plat}.zip")
    return {"status": "success", "platform": plat, "recorded_for": uname}
"""

text = re.sub(r'@app\.get\("/get-package/\{platform_name\}"\)[\s\S]*?return[^\n]+', download_tracker.strip(), text)

with open(path, "w", encoding="utf-8") as f:
    f.write(text)

print("Synchronization locked to single database (portal.db) successfully!")