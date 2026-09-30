import sqlite3
import re
import os

# 1. Database Setup (Bina data delete kiye)
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

# 2. Update server/app.py with complete dynamic tracking
path = "server/app.py"
with open(path, "r", encoding="utf-8-sig") as f:
    text = f.read()

# Fix TemplateResponse signature
text = re.sub(
    r'templates\.TemplateResponse\(\s*["\']portal\.html["\']\s*,\s*\{([^}]+)\}\s*\)',
    r'templates.TemplateResponse(request=request, name="portal.html", context={\1})',
    text
)

# Dynamic metrics route (Direct SQL, no hardcoding)
metrics_fn = """
@app.get("/api/admin/metrics")
async def get_admin_metrics():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT key, val FROM portal_stats")
    stats = dict(c.fetchall())
    c.execute("SELECT COUNT(*) FROM users")
    tot = c.fetchone()[0]
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

@app.get("/api/admin/nodes")
async def get_admin_nodes():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users ORDER BY id DESC")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

@app.get("/get-package/{platform_name}")
async def download_package_tracker(platform_name: str, req: Request):
    ip = req.headers.get("x-forwarded-for") or (req.client.host if req.client else "127.0.0.1")
    plat = platform_name.lower()
    col = "win_downloads" if "win" in plat else "apk_downloads"
    uname = req.cookies.get("username") or req.query_params.get("user") or "guest"
    
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
        from fastapi.responses import FileResponse
        return FileResponse(fpath, filename=f"jarvis_{plat}.{ext}")
    return {"status": "success", "platform": plat, "user": uname, "logged_at": t_str}

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

# Replace or append
if '@app.get("/api/admin/metrics")' in text:
    text = re.sub(r'@app\.get\("/api/admin/metrics"\)[\s\S]*?return\s*\{[\s\S]*?\}', '', text)

text = re.sub(r'@app\.get\("/get-package/\{platform_name\}"\)[\s\S]*?return[^\n]+', '', text)
text = re.sub(r'@app\.post\("/api/admin/modify-lifecycle"\)[\s\S]*?return\s*\{[\s\S]*?\}', '', text)
text += "\n\n" + metrics_fn

# Bind download buttons to /get-package/
text = re.sub(r'href=["\'][^"\']*win[^"\']*\.(?:exe|zip)["\']', 'href="/get-package/windows"', text, flags=re.IGNORECASE)
text = re.sub(r'href=["\'][^"\']*android[^"\']*\.apk["\']', 'href="/get-package/android"', text, flags=re.IGNORECASE)

with open(path, "w", encoding="utf-8") as f:
    f.write(text)

print("Backend dynamic logic configured completely!")