import os

# Dist aur venv chhodkar asli portal template dhoondein
real_portal = None
for root, dirs, files in os.walk("."):
    if ".venv" in root or "dist" in root or "build" in root:
        continue
    for f in files:
        if f.lower().endswith(".html"):
            real_portal = os.path.abspath(os.path.join(root, f))
            break
    if real_portal:
        break

print("Locking to Actual Portal File:", real_portal)

app_code = f"""
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import sqlite3, os, time
from datetime import datetime

app = FastAPI()

if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    if r"{real_portal}" and os.path.exists(r"{real_portal}"):
        with open(r"{real_portal}", "r", encoding="utf-8") as f:
            html = f.read()
            uname = request.cookies.get("username") or "admin123"
            return html.replace("{{{{ username }}}}", uname)
    return "<h3>Portal File Missing</h3>"

@app.get("/api/admin/metrics")
async def metrics():
    conn = sqlite3.connect("portal.db")
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS portal_stats (key TEXT PRIMARY KEY, val INTEGER DEFAULT 0)")
    c.execute("INSERT OR IGNORE INTO portal_stats VALUES ('win_downloads', 0)")
    c.execute("INSERT OR IGNORE INTO portal_stats VALUES ('apk_downloads', 0)")
    c.execute("SELECT key, val FROM portal_stats")
    stats = dict(c.fetchall())
    
    c.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT, last_seen REAL DEFAULT 0, is_active INTEGER DEFAULT 1)")
    c.execute("SELECT COUNT(*) FROM users")
    tot = c.fetchone()[0]
    
    cutoff = time.time() - 120
    c.execute("SELECT COUNT(*) FROM users WHERE last_seen > ? AND is_active = 1", (cutoff,))
    act = c.fetchone()[0]
    conn.close()
    
    w = stats.get("win_downloads", 0)
    a = stats.get("apk_downloads", 0)
    return {{
        "total_users": tot,
        "active_users": act,
        "win_downloads": w,
        "windows_downloads": w,
        "apk_downloads": a,
        "android_downloads": a
    }}

@app.get("/api/admin/nodes")
async def nodes():
    conn = sqlite3.connect("portal.db")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM users ORDER BY id DESC")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

@app.get("/get-package/{{platform_name}}")
async def track_download(platform_name: str, req: Request):
    ip = req.client.host if req.client else "127.0.0.1"
    plat = platform_name.lower()
    col = "win_downloads" if "win" in plat else "apk_downloads"
    uname = req.cookies.get("username") or "guest"
    t_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = sqlite3.connect("portal.db")
    c = conn.cursor()
    c.execute(f"UPDATE portal_stats SET val = val + 1 WHERE key = '{{col}}'")
    c.execute("CREATE TABLE IF NOT EXISTS download_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, hwid TEXT, platform TEXT, timestamp TEXT)")
    c.execute("INSERT INTO download_logs (username, hwid, platform, timestamp) VALUES (?, ?, ?, ?)",
              (uname, f"IP-{{ip}}", plat, t_str))
    conn.commit()
    conn.close()

    fpath = f"downloads/{{plat}}_installer.zip"
    if os.path.exists(fpath):
        return FileResponse(fpath, filename=f"jarvis_{{plat}}.zip")
    return {{"status": "success", "platform": plat, "downloaded": True}}
"""

with open("server/app.py", "w", encoding="utf-8") as f:
    f.write(app_code)

print("Server app.py restored to genuine portal UI!")