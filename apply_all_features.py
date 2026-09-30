import sqlite3
import os
import re

# 1. Database table & missing columns ensure karein
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

# 2. server/app.py me routes inject karein
path = "server/app.py"
with open(path, "r", encoding="utf-8-sig") as f:
    text = f.read()

features = """
@app.get("/get-package/{platform_name}")
async def download_package_tracker(platform_name: str, req: Request):
    ip = req.headers.get("x-forwarded-for") or (req.client.host if req.client else "127.0.0.1")
    plat = platform_name.lower()
    col = "win_downloads" if "win" in plat else "apk_downloads"
    uname = req.cookies.get("username") or "guest"
    
    from datetime import datetime
    t_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute(f"UPDATE portal_stats SET val = val + 1 WHERE key = '{col}'")
    c.execute("INSERT INTO download_logs (username, hwid, platform, timestamp) VALUES (?, ?, ?, ?)",
              (uname, f"IP-{ip}", plat, t_str))
    conn.commit()
    conn.close()
    
    ext = "apk" if "apk" in plat or "android" in plat else "zip"
    fpath = f"downloads/{plat}_installer.{ext}"
    if os.path.exists(fpath):
        return FileResponse(fpath, filename=f"jarvis_{plat}.{ext}")
    return {"status": "success", "platform": plat, "user": uname, "timestamp": t_str}

@app.post("/api/admin/modify-lifecycle")
async def modify_operator_lifecycle(req: Request):
    data = await req.json()
    uid = data.get("user_id")
    delta = data.get("delta_days", 0)
    unlim = data.get("is_unlimited")
    delete = data.get("delete", False)
    
    conn = get_db_connection()
    c = conn.cursor()
    if delete:
        c.execute("DELETE FROM users WHERE id = ?", (uid,))
    elif unlim is not None:
        c.execute("UPDATE users SET is_unlimited = 1 WHERE id = ?", (uid,))
    elif delta != 0:
        c.execute("UPDATE users SET days_remaining = MAX(0, days_remaining + ?), is_unlimited = 0 WHERE id = ?", (delta, uid))
    conn.commit()
    conn.close()
    return {"status": "ok"}
"""

if "/get-package/{platform_name}" not in text:
    text += "\n\n" + features

with open(path, "w", encoding="utf-8") as f:
    f.write(text)

print("Features mapped to server successfully!")