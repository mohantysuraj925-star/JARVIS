import os
import sqlite3
import re

# 1. Database table ensure karein (Bina purana data delete kiye)
conn = sqlite3.connect("portal.db")
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

# 2. Server backend routing ko exact logic par bind karein
path = "server/app.py"
with open(path, "r", encoding="utf-8-sig") as f:
    text = f.read()

# Exact dynamic logic
backend_code = """
@app.get("/api/admin/metrics")
async def get_admin_metrics():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT key, val FROM portal_stats")
    stats = dict(c.fetchall())
    
    # Real user count (jitne log register/login kiye)
    c.execute("SELECT COUNT(*) FROM users")
    tot = c.fetchone()[0]
    
    # Active users (pichhle 2 minute me active)
    import time
    cutoff = time.time() - 120
    c.execute("SELECT COUNT(*) FROM users WHERE last_seen > ? AND is_active = 1", (cutoff,))
    act = c.fetchone()[0]
    conn.close()
    
    w = stats.get("win_downloads", 0)
    a = stats.get("apk_downloads", 0)
    
    return {
        "total_users": tot,
        "active_users": act,
        "win_downloads": w,
        "windows_downloads": w,
        "apk_downloads": a,
        "android_downloads": a
    }

@app.get("/get-package/{platform_name}")
async def download_package_tracker(platform_name: str, req: Request):
    client_ip = req.client.host if req.client else "unknown"
    plat = platform_name.lower()
    col = "win_downloads" if "win" in plat else "apk_downloads"
    uname = req.cookies.get("username") or "guest_client"
    
    from datetime import datetime
    now_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    conn = get_db_connection()
    c = conn.cursor()
    
    # Increment exact download
    c.execute(f"UPDATE portal_stats SET val = val + 1 WHERE key = '{col}'")
    
    # Log the action
    c.execute("INSERT INTO download_logs (username, hwid, platform, timestamp) VALUES (?, ?, ?, ?)",
              (uname, f"IP-{client_ip}", plat, now_time))
    conn.commit()
    conn.close()
    
    file_path = f"downloads/{plat}_installer.zip"
    if os.path.exists(file_path):
        return FileResponse(file_path, filename=f"jarvis_{plat}.zip")
    return {"status": "success", "platform": plat, "downloaded_by": uname}
"""

text = re.sub(r'@app\.get\("/api/admin/metrics"\)[\s\S]*?@app\.get\("/get-package/\{platform_name\}"\)[\s\S]*?return[^\n]+', backend_code.strip(), text)

# Download buttons binding
text = re.sub(r'href=["\'][^"\']*win[^"\']*\.exe["\']', 'href="/get-package/windows"', text, flags=re.IGNORECASE)
text = re.sub(r'href=["\'][^"\']*android[^"\']*\.apk["\']', 'href="/get-package/android"', text, flags=re.IGNORECASE)

with open(path, "w", encoding="utf-8") as f:
    f.write(text)

print("Exact production lifecycle and tracking engine hooked successfully!")