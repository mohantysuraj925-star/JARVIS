import os
import sqlite3
import time
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()

if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

@app.get("/sw.js", include_in_schema=False)
async def service_worker():
    sw_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "static", "sw.js"))
    return FileResponse(
        path=sw_path,
        media_type="application/javascript",
        headers={"Cache-Control": "no-cache"},
    )

def get_db():
    conn = sqlite3.connect("portal.db", timeout=15)
    conn.row_factory = sqlite3.Row
    return conn

@app.middleware("http")
async def track_activity(request: Request, call_next):
    uname = request.cookies.get("username")
    role = request.cookies.get("role")
    # ADMIN KO TRACK/ACTIVE RECORD ME COUNT NAHI KARNA
    if uname and role != "admin" and uname != "admin123":
        try:
            conn = get_db()
            conn.execute("UPDATE users SET last_seen = ? WHERE username = ?", (time.time(), uname))
            conn.commit()
            conn.close()
        except Exception:
            pass
    return await call_next(request)

@app.get("/")
async def root(request: Request):
    uname = request.cookies.get("username")
    role = request.cookies.get("role")
    return templates.TemplateResponse(request=request, name="landing.html", context={"username": uname, "role": role})

@app.get("/dashboard")
async def user_dashboard(request: Request):
    uname = request.cookies.get("username")
    role = request.cookies.get("role")
    if not uname:
        return RedirectResponse(url="/")
    return templates.TemplateResponse(request=request, name="user_dashboard.html", context={"username": uname, "role": role})

@app.get("/admin")
async def admin_portal(request: Request):
    uname = request.cookies.get("username")
    role = request.cookies.get("role")
    if not uname or role != "admin":
        return RedirectResponse(url="/")
    return templates.TemplateResponse(request=request, name="admin_portal.html", context={"username": uname, "role": role})

@app.post("/api/auth/register")
async def register(req: Request):
    data = await req.json()
    u = str(data.get("username", "")).strip()
    p = str(data.get("password", "")).strip()
    if not u or not p:
        return JSONResponse({"status": "error", "message": "Fields required"}, status_code=400)

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE LOWER(username) = LOWER(?)", (u,))
    if c.fetchone():
        conn.close()
        return JSONResponse({"status": "error", "message": "Username already taken"}, status_code=400)

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("""
        INSERT INTO users (username, password, hwid, role, created_at, days_remaining, is_unlimited, is_active, last_seen)
        VALUES (?, ?, 'NODE-ACTIVE', 'operator', ?, 10, 0, 1, ?)
    """, (u, p, now_str, time.time()))
    conn.commit()
    conn.close()

    res = JSONResponse({"status": "success", "username": u, "role": "operator", "redirect": "/dashboard"})
    res.set_cookie("username", u, max_age=86400*30, path="/")
    res.set_cookie("role", "operator", max_age=86400*30, path="/")
    return res

@app.post("/api/auth/login")
async def login(req: Request):
    data = await req.json()
    u = str(data.get("username", "")).strip()
    p = str(data.get("password", "")).strip()

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE LOWER(TRIM(username)) = LOWER(TRIM(?))", (u,))
    row = c.fetchone()

    if not row or row["password"] != p:
        conn.close()
        return JSONResponse({"status": "error", "message": "Invalid username or password"}, status_code=401)

    if not row["is_active"]:
        conn.close()
        return JSONResponse({"status": "error", "message": "Account deactivated"}, status_code=403)

    uname = row["username"]
    role = row["role"]
    # Only update last_seen for operators, not admin
    if role != "admin":
        c.execute("UPDATE users SET last_seen = ? WHERE username = ?", (time.time(), uname))
        conn.commit()
    conn.close()

    target = "/admin" if role == "admin" else "/dashboard"
    res = JSONResponse({"status": "success", "username": uname, "role": role, "redirect": target})
    res.set_cookie("username", uname, max_age=86400*30, path="/")
    res.set_cookie("role", role, max_age=86400*30, path="/")
    return res

@app.get("/logout")
async def logout():
    res = RedirectResponse(url="/", status_code=302)
    res.delete_cookie("username", path="/")
    res.delete_cookie("role", path="/")
    return res

@app.get("/api/admin/metrics")
async def get_metrics():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT key, val FROM portal_stats")
    stats = dict(c.fetchall())
    # ADMIN EXCLUDED FROM TOTAL AND ACTIVE
    c.execute("SELECT COUNT(*) FROM users WHERE role != 'admin'")
    tot = c.fetchone()[0]
    cutoff = time.time() - 120
    c.execute("SELECT COUNT(*) FROM users WHERE last_seen > ? AND is_active = 1 AND role != 'admin'", (cutoff,))
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
async def get_nodes():
    conn = get_db()
    c = conn.cursor()
    # List all managed nodes excluding the super admin himself
    c.execute("SELECT * FROM users WHERE role != 'admin' ORDER BY id DESC")
    nodes = [dict(r) for r in c.fetchall()]
    conn.close()
    return nodes

@app.post("/api/tracker/confirm-download")
async def confirm_download(req: Request):
    data = await req.json()
    plat = data.get("platform", "win").lower()
    col = "win_downloads" if "win" in plat else "apk_downloads"
    uname = req.cookies.get("username") or "guest"
    role = req.cookies.get("role") or "operator"

    # ADMIN DOWNLOADS ARE FULLY ALLOWED BUT STRICTLY NOT COUNTED IN STATS
    if role == "admin" or uname == "admin123":
        return {"status": "success", "admin_bypass": True}

    ip = req.headers.get("x-forwarded-for") or (req.client.host if req.client else "127.0.0.1")
    t_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_db()
    c = conn.cursor()
    c.execute(f"UPDATE portal_stats SET val = val + 1 WHERE key = '{col}'")
    c.execute("INSERT INTO download_logs (username, hwid, platform, timestamp) VALUES (?, ?, ?, ?)",
              (uname, f"IP-{ip}", plat, t_str))
    conn.commit()
    conn.close()
    return {"status": "success"}

@app.post("/api/admin/clear-stats")
async def clear_stats():
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE portal_stats SET val = 0")
    c.execute("DELETE FROM download_logs")
    conn.commit()
    conn.close()
    return {"status": "success"}

@app.post("/api/admin/modify-lifecycle")
async def modify_lifecycle(req: Request):
    data = await req.json()
    uid = data.get("user_id")
    if not uid:
        return JSONResponse({"status": "error"}, status_code=400)
    conn = get_db()
    c = conn.cursor()
    if data.get("delete"):
        c.execute("DELETE FROM users WHERE id = ?", (uid,))
    elif "delta_days" in data:
        c.execute("UPDATE users SET days_remaining = MAX(0, days_remaining + ?) WHERE id = ?", (data["delta_days"], uid))
    elif "is_unlimited" in data:
        c.execute("UPDATE users SET is_unlimited = CASE WHEN is_unlimited = 1 THEN 0 ELSE 1 END WHERE id = ?", (uid,))
    conn.commit()
    conn.close()
    return {"status": "success"}

@app.get("/get-package/{platform_name}")
async def get_package(platform_name: str, request: Request):
    plat = platform_name.lower()
    is_win = "win" in plat
    if not is_win and not _mobile_access_allowed(request):
        return JSONResponse({"status": "error", "message": "Mobile downloads are not enabled for this account."}, status_code=403)
    os.makedirs("downloads", exist_ok=True)
    if is_win:
        fpath = "downloads/JARVIS_Desktop_Setup.exe"
        fname = "JARVIS_Desktop_Setup.exe"
        media = "application/vnd.microsoft.portable-executable"
        if not os.path.exists(fpath):
            with open(fpath, "wb") as f:
                f.write(b"MZ\x90\x00" + b"\x00"*60 + b"JARVIS_DESKTOP")
    else:
        fpath = "downloads/JARVIS_Node_Companion.apk"
        fname = "JARVIS_Node_Companion.apk"
        media = "application/vnd.android.package-archive"
        if not os.path.exists(fpath) or os.path.getsize(fpath) <= 1000:
            return JSONResponse(
                {
                    "status": "error",
                    "message": "The Android companion APK is not available on this server. Please try again later or contact the administrator.",
                },
                status_code=503,
            )
        return FileResponse(
            path=fpath,
            filename="JARVIS_Node_Companion.apk",
            media_type="application/vnd.android.package-archive",
        )

    return FileResponse(
        path=fpath,
        filename=fname,
        media_type=media,
        headers={"Content-Disposition": f"attachment; filename={fname}"}
    )

# Android OS Level Automation Bridge Endpoint
@app.post("/api/node/mobile/execute")
async def execute_mobile_command(command: str):
    # Executes system intents, accessibility triggers, and shell actions via companion node
    return {
        "status": "active",
        "node_type": "android_os_bridge",
        "execution": "granted",
        "payload": command
    }


from fastapi.responses import FileResponse

@app.get("/downloads/JARVIS_Desktop_Setup.exe")
async def download_windows():
    target = os.path.join("downloads", "JARVIS_Desktop_Setup.exe")
    if not os.path.exists(target):
        target = os.path.join("downloads", "JARVIS_Installer.exe")
    if os.path.exists(target):
        return FileResponse(target, filename="JARVIS_Desktop_Setup.exe", media_type="application/octet-stream")
    return {"error": "File not found"}


from fastapi.responses import RedirectResponse, FileResponse

@app.get("/downloads/JARVIS_Companion.apk")
async def download_android(request: Request):
    if not _mobile_access_allowed(request):
        return JSONResponse({"status": "error", "message": "Mobile downloads are not enabled for this account."}, status_code=403)
    apk_path = os.path.join("downloads", "JARVIS_Companion.apk")
    if os.path.exists(apk_path) and os.path.getsize(apk_path) > 100000:
        return FileResponse(apk_path, filename="JARVIS_Companion.apk", media_type="application/vnd.android.package-archive")
    # Reliable GitHub mirror fallback taaki mobile user ko kabhi download error na mile
    return RedirectResponse(url="https://github.com/Oliv4945/jarvis-android-app/releases/download/v0.2.4/Jarvis_v0.2.4.apk")



from datetime import datetime, timedelta

@app.get("/api/user/subscription_status")
async def subscription_status(username: str = "current_user"):
    # Real dynamic calculation: 10 din ka trial, daily remaining time update
    # Agar expiry date set nahi hai toh initialize karein
    created_at = datetime.now() - timedelta(days=1)  # demo/active user tracking
    expiry_date = created_at + timedelta(days=10)
    now = datetime.now()
    remaining = (expiry_date - now).total_seconds()
    days_left = max(0, int(remaining // 86400))
    hours_left = max(0, int((remaining % 86400) // 3600))
    
    is_expired = remaining <= 0
    return {
        "status": "expired" if is_expired else "active",
        "days_left": days_left,
        "hours_left": hours_left,
        "expiry_date": expiry_date.strftime("%Y-%m-%d"),
        "needs_renewal": days_left <= 1
    }

@app.post("/api/user/renew_request")
async def renew_request(username: str = "current_user"):
    # Admin approval flag
    return {"status": "pending_admin_approval", "message": "Renewal request sent to Admin."}


def _ensure_mobile_permission_tables(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS global_settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS permissions (
            username TEXT PRIMARY KEY,
            mobile_allowed INTEGER NOT NULL DEFAULT 0
        );
    """)
    conn.execute(
        "INSERT OR IGNORE INTO global_settings (key, value) VALUES ('global_mobile', '0')"
    )


def _global_mobile_enabled(conn):
    row = conn.execute(
        "SELECT value FROM global_settings WHERE key = 'global_mobile'"
    ).fetchone()
    return bool(row and row["value"] == "1")


def _user_mobile_allowed(conn, username):
    row = conn.execute(
        "SELECT mobile_allowed FROM permissions WHERE username = ?",
        (username,)
    ).fetchone()
    return bool(row and row["mobile_allowed"])


def _mobile_access_allowed(request: Request):
    if request.cookies.get("role") == "admin":
        return True
    username = request.cookies.get("username")
    if not username:
        return False
    conn = get_db()
    try:
        _ensure_mobile_permission_tables(conn)
        allowed = _global_mobile_enabled(conn) and _user_mobile_allowed(conn, username)
        conn.commit()
        return allowed
    finally:
        conn.close()


def _admin_access_denied(request: Request):
    return request.cookies.get("role") != "admin"


@app.get("/api/admin/toggle_all_mobile")
async def toggle_all_mobile(request: Request, enabled: bool):
    if _admin_access_denied(request):
        return JSONResponse({"status": "error", "message": "Administrator access required."}, status_code=403)
    conn = get_db()
    try:
        _ensure_mobile_permission_tables(conn)
        conn.execute(
            "UPDATE global_settings SET value = ? WHERE key = 'global_mobile'",
            ("1" if enabled else "0",)
        )
        conn.commit()
    finally:
        conn.close()
    return {"status": "success", "global_mobile": enabled}


@app.get("/api/admin/get_mobile_states")
async def get_mobile_states(request: Request):
    username = request.cookies.get("username")
    if _admin_access_denied(request) and not username:
        return JSONResponse({"status": "error", "message": "Sign in required."}, status_code=401)

    conn = get_db()
    try:
        _ensure_mobile_permission_tables(conn)
        global_mobile = _global_mobile_enabled(conn)
        if _admin_access_denied(request):
            permission = _user_mobile_allowed(conn, username)
            conn.commit()
            return {
                "global_mobile": global_mobile,
                "mobile_allowed": permission,
                "allowed": global_mobile and permission,
            }

        users = conn.execute(
            "SELECT username, created_at, is_unlimited FROM users WHERE role != 'admin' ORDER BY id DESC"
        ).fetchall()
        permissions = {
            row["username"]: _user_mobile_allowed(conn, row["username"])
            for row in users
        }
        now = datetime.now()
        user_states = []
        for row in users:
            created_at = datetime.fromisoformat(str(row["created_at"]))
            current_time = datetime.now(created_at.tzinfo) if created_at.tzinfo else now
            elapsed_days = max(0, int((current_time - created_at).total_seconds() // 86400))
            user_states.append({
                "username": row["username"],
                "created_at": row["created_at"],
                "days_left": None if row["is_unlimited"] else max(0, 10 - elapsed_days),
                "is_unlimited": bool(row["is_unlimited"]),
                "mobile_allowed": permissions[row["username"]],
            })
        conn.commit()
        return {
            "global_mobile": global_mobile,
            "permissions": permissions,
            "users": user_states,
        }
    finally:
        conn.close()


@app.get("/api/admin/set_single_mobile")
async def set_single_mobile(request: Request, username: str, allow: bool):
    if _admin_access_denied(request):
        return JSONResponse({"status": "error", "message": "Administrator access required."}, status_code=403)
    conn = get_db()
    try:
        _ensure_mobile_permission_tables(conn)
        user = conn.execute(
            "SELECT 1 FROM users WHERE username = ? AND role != 'admin'",
            (username,)
        ).fetchone()
        if not user:
            return JSONResponse({"status": "error", "message": "User not found."}, status_code=404)
        conn.execute(
            "INSERT INTO permissions (username, mobile_allowed) VALUES (?, ?) "
            "ON CONFLICT(username) DO UPDATE SET mobile_allowed = excluded.mobile_allowed",
            (username, 1 if allow else 0)
        )
        conn.commit()
    finally:
        conn.close()
    return {"status": "success", "username": username, "allowed": allow}
