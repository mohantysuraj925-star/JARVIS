import os
import sqlite3
import time
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

# 1. Single Root DB Setup
db_path = os.path.abspath("portal.db")
conn = sqlite3.connect(db_path)
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

# 2. Standalone App
app = FastAPI()

if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

def get_db():
    c = sqlite3.connect(db_path)
    c.row_factory = sqlite3.Row
    return c

@app.middleware("http")
async def track_heartbeat(request: Request, call_next):
    uname = request.cookies.get("username")
    if uname:
        try:
            db = get_db()
            db.execute("UPDATE users SET last_seen = ? WHERE username = ?", (time.time(), uname))
            db.commit()
            db.close()
        except Exception:
            pass
    return await call_next(request)

@app.get("/api/admin/metrics")
async def get_metrics():
    db = get_db()
    c = db.cursor()
    c.execute("SELECT key, val FROM portal_stats")
    stats = dict(c.fetchall())
    c.execute("SELECT COUNT(*) FROM users")
    tot = c.fetchone()[0]
    cutoff = time.time() - 120
    c.execute("SELECT COUNT(*) FROM users WHERE last_seen > ? AND is_active = 1", (cutoff,))
    act = c.fetchone()[0]
    db.close()
    
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
async def get_nodes():
    db = get_db()
    c = db.cursor()
    c.execute("SELECT * FROM users ORDER BY id DESC")
    rows = [dict(r) for r in c.fetchall()]
    db.close()
    return rows

@app.get("/get-package/{platform_name}")
async def track_download(platform_name: str, req: Request):
    ip = req.client.host if req.client else "127.0.0.1"
    plat = platform_name.lower()
    col = "win_downloads" if "win" in plat else "apk_downloads"
    uname = req.cookies.get("username") or "guest"
    t_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    db = get_db()
    c = db.cursor()
    c.execute(f"UPDATE portal_stats SET val = val + 1 WHERE key = '{col}'")
    c.execute("INSERT INTO download_logs (username, hwid, platform, timestamp) VALUES (?, ?, ?, ?)",
              (uname, f"IP-{ip}", plat, t_str))
    db.commit()
    db.close()

    fpath = f"downloads/{plat}_installer.zip"
    if os.path.exists(fpath):
        return FileResponse(fpath, filename=f"jarvis_{plat}.zip")
    return {"status": "success", "platform": plat, "user": uname, "time": t_str}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)