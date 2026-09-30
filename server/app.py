import os
import sqlite3
import time
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()

# 1. Static & Templates Setup
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

tpl_dir = "templates" if os.path.exists("templates") else ("server/templates" if os.path.exists("server/templates") else ".")
templates = Jinja2Templates(directory=tpl_dir)

# 2. Database Connection
DB_PATH = "portal.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
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

init_db()

# 3. Heartbeat Middleware
@app.middleware("http")
async def track_user_heartbeat(request: Request, call_next):
    uname = request.cookies.get("username")
    if uname and uname != "undefined" and uname != "Guest":
        try:
            conn = get_db_connection()
            conn.execute("UPDATE users SET last_seen = ? WHERE LOWER(TRIM(username)) = LOWER(TRIM(?))", (time.time(), uname))
            conn.commit()
            conn.close()
        except Exception:
            pass
    response = await call_next(request)
    return response

# 4. Root Route (Original UI Template)
@app.get("/")
async def root_portal(request: Request):
    uname = request.cookies.get("username")
    return templates.TemplateResponse(request=request, name="portal.html", context={"username": uname or "Guest"})

# 5. Smart Auth (Register + Login Unified - Solves "Pehle se maujud" issue)
@app.post("/api/register")
@app.post("/api/login")
async def auth_user(req: Request):
    try:
        data = await req.json()
    except Exception:
        return JSONResponse({"status": "error", "message": "Invalid JSON"}, status_code=400)

    uname = (data.get("username") or data.get("machine_id") or "").strip()
    pwd = (data.get("password") or "").strip()
    email = (data.get("email") or "").strip()

    if not uname or not pwd:
        return JSONResponse({"status": "error", "message": "Username and password required"}, status_code=400)

    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT id, password, is_active FROM users WHERE LOWER(TRIM(username)) = LOWER(TRIM(?))", (uname,))
    user = c.fetchone()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if user:
        # User already exists -> Auto verify password and login
        if str(user["password"]).strip() != pwd:
            conn.close()
            return JSONResponse({"status": "error", "message": "Galat password! Dusra password dalein ya alag username use karein."}, status_code=401)
        if not user["is_active"]:
            conn.close()
            return JSONResponse({"status": "error", "message": "Account blocked by admin."}, status_code=403)
        c.execute("UPDATE users SET last_seen = ? WHERE id = ?", (time.time(), user["id"]))
    else:
        # New registration -> Give 10 days access
        c.execute(
            "INSERT INTO users (username, password, email, created_at, days_remaining, is_active, last_seen) VALUES (?, ?, ?, ?, 10, 1, ?)",
            (uname, pwd, email, now_str, time.time())
        )

    conn.commit()
    conn.close()

    res = JSONResponse({"status": "success", "username": uname, "message": "Authorized"})
    res.set_cookie(key="username", value=uname, httponly=False, max_age=86400*30, path="/", samesite="lax")
    return res

# 6. Real-time Metrics (Pure SQL)
@app.get("/api/admin/metrics")
async def get_admin_metrics():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT key, val FROM portal_stats")
    stats = dict(c.fetchall())

    c.execute("SELECT COUNT(*) FROM users")
    tot = c.fetchone()[0]

    cutoff = time.time() - 180
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

# 7. Operator Nodes List
@app.get("/api/admin/nodes")
async def get_admin_nodes():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users ORDER BY id DESC")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

# 8. Download Tracking Route
@app.get("/get-package/{platform_name}")
async def download_package_tracker(platform_name: str, req: Request):
    ip = req.headers.get("x-forwarded-for") or (req.client.host if req.client else "127.0.0.1")
    plat = platform_name.lower()
    col = "win_downloads" if "win" in plat else "apk_downloads"
    uname = req.cookies.get("username") or "guest_client"

    t_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_db_connection()
    c = conn.cursor()
    c.execute(f"UPDATE portal_stats SET val = val + 1 WHERE key = '{col}'")
    c.execute("INSERT INTO download_logs (username, hwid, platform, timestamp) VALUES (?, ?, ?, ?)",
              (uname, f"IP-{ip}", plat, t_str))
    conn.commit()
    conn.close()

    ext = "apk" if ("apk" in plat or "android" in plat) else "zip"
    fpath = f"downloads/{plat}_installer.{ext}"
    if os.path.exists(fpath):
        return FileResponse(fpath, filename=f"jarvis_{plat}.{ext}")
    return {"status": "success", "platform": plat, "downloaded_by": uname, "logged_at": t_str}

# 9. Operator Lifecycle Management (+5D, -5D, Unlimited, Delete)
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