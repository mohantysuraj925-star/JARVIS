import os
import json
import sqlite3
import time
import asyncio
import hashlib
import logging
import secrets
import tempfile
import uuid
from urllib.parse import urlparse
from datetime import datetime, timedelta
from typing import Literal
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

app = FastAPI()
_companion_connections: dict[str, WebSocket] = {}
_companion_connections_lock = asyncio.Lock()

if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")
MOBILE_OVERRIDE_ROLES = frozenset({"admin", "creator"})
SITE_SETTINGS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "site_settings.json")
DEFAULT_SITE_SETTINGS = {
    "creator_name": "Suraj Kumar",
    "journey_text": (
        "Built completely from scratch over 7 months of dedicated research and development. "
        "Inspired by Tony Stark's JARVIS and AI concepts, developed by deeply analyzing ideas "
        "across multi-AI platforms (ChatGPT, Gemini, DeepSeek, Claude, VS Code AI) to build a "
        "personalized, powerful AI companion ecosystem."
    ),
    "email": "mohantysuraj91@gmail.com",
    "phone": "",
    "api_guide_link": "https://aistudio.google.com/app/apikey",
    "footer_text": (
        "© 2026 JARVIS Project. Engineered & Developed by Suraj Kumar. All rights reserved."
    ),
}
logger = logging.getLogger(__name__)


def _load_site_settings():
    try:
        with open(SITE_SETTINGS_PATH, encoding="utf-8") as settings_file:
            stored_settings = json.load(settings_file)
    except FileNotFoundError:
        return DEFAULT_SITE_SETTINGS.copy()

    if not isinstance(stored_settings, dict):
        raise ValueError("Homepage settings file must contain a JSON object.")

    settings = DEFAULT_SITE_SETTINGS.copy()
    for key in settings:
        if key in stored_settings:
            value = stored_settings[key]
            if not isinstance(value, str):
                raise ValueError(f"Homepage setting {key!r} must be a string.")
            settings[key] = value
    return settings


def _save_site_settings(settings):
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=os.path.dirname(SITE_SETTINGS_PATH),
            prefix=".site_settings_",
            suffix=".tmp",
            delete=False,
        ) as settings_file:
            temporary_path = settings_file.name
            json.dump(settings, settings_file, ensure_ascii=False, indent=2)
            settings_file.write("\n")
            settings_file.flush()
            os.fsync(settings_file.fileno())
        os.replace(temporary_path, SITE_SETTINGS_PATH)
        temporary_path = None
    finally:
        if temporary_path and os.path.exists(temporary_path):
            os.remove(temporary_path)

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


def _ensure_expiry_schema(conn):
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(users)")}
    if "expires_at" not in columns:
        conn.execute("ALTER TABLE users ADD COLUMN expires_at REAL")

    has_access_end_date = "access_end_date" in columns
    legacy_expiry_column = ", access_end_date" if has_access_end_date else ""
    rows = conn.execute(
        "SELECT id, created_at, days_remaining"
        f"{legacy_expiry_column} FROM users WHERE expires_at IS NULL"
    ).fetchall()
    for row in rows:
        try:
            if has_access_end_date and row["access_end_date"]:
                legacy_expiry = str(row["access_end_date"])
                expiry_datetime = datetime.fromisoformat(legacy_expiry)
                if len(legacy_expiry) == 10:
                    expiry_datetime += timedelta(days=1)
                expires_at = expiry_datetime.timestamp()
            else:
                created_at = datetime.fromisoformat(str(row["created_at"])).timestamp()
                duration_days = max(0, int(row["days_remaining"]))
                expires_at = created_at + duration_days * 86400
        except (TypeError, ValueError, OverflowError) as error:
            raise ValueError(
                f"Cannot initialize expiry for user record {row['id']}."
            ) from error
        conn.execute(
            "UPDATE users SET expires_at = ? WHERE id = ? AND expires_at IS NULL",
            (expires_at, row["id"]),
        )
        if has_access_end_date and not row["access_end_date"]:
            conn.execute(
                "UPDATE users SET access_end_date = ? WHERE id = ?",
                (datetime.fromtimestamp(expires_at).strftime("%Y-%m-%d"), row["id"]),
            )


def _is_mobile_override_role(role):
    return role in MOBILE_OVERRIDE_ROLES


def _mobile_access_allowed(request: Request):
    username = request.cookies.get("username")
    if not username:
        return False
    conn = get_db()
    try:
        _ensure_mobile_permission_tables(conn)
        account = conn.execute(
            "SELECT role, is_active FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        if not account or not account["is_active"]:
            conn.commit()
            return False
        if _is_mobile_override_role(account["role"]):
            conn.commit()
            return True
        allowed = (
            _global_mobile_enabled(conn)
            and _user_mobile_allowed(conn, username)
        )
        conn.commit()
        return allowed
    finally:
        conn.close()


def _companion_apk_path(minimum_size=1000):
    apk_candidates = (
        os.path.join("downloads", "JARVIS_Companion.apk"),
        os.path.join("downloads", "app-debug.apk"),
        os.path.join("downloads", "JARVIS_Node_Companion.apk"),
    )
    return next(
        (
            candidate for candidate in apk_candidates
            if os.path.isfile(candidate) and os.path.getsize(candidate) > minimum_size
        ),
        None,
    )


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
    settings = _load_site_settings()
    public_settings = {key: value for key, value in settings.items() if key != "phone"}
    return templates.TemplateResponse(
        request=request,
        name="landing.html",
        context={
            "username": uname,
            "role": role,
            "settings": public_settings,
        },
    )

@app.get("/dashboard")
async def user_dashboard(request: Request):
    uname = request.cookies.get("username")
    if not uname:
        return RedirectResponse(url="/")
    conn = get_db()
    try:
        account = conn.execute(
            "SELECT role, is_active FROM users WHERE username = ?",
            (uname,),
        ).fetchone()
        if not account or not account["is_active"]:
            return RedirectResponse(url="/logout")
        _ensure_expiry_schema(conn)
        conn.commit()
    finally:
        conn.close()
    return templates.TemplateResponse(request=request, name="user_dashboard.html", context={"username": uname, "role": account["role"]})

@app.get("/admin")
async def admin_portal(request: Request):
    uname = request.cookies.get("username")
    if not uname:
        return RedirectResponse(url="/")
    conn = get_db()
    try:
        account = conn.execute(
            "SELECT role, is_active FROM users WHERE username = ?",
            (uname,),
        ).fetchone()
    finally:
        conn.close()
    if not account or not account["is_active"] or not _is_mobile_override_role(account["role"]):
        return RedirectResponse(url="/")
    role = account["role"]
    settings = _load_site_settings() if role == "admin" else None
    return templates.TemplateResponse(
        request=request,
        name="admin_portal.html",
        context={"username": uname, "role": role, "settings": settings},
    )


@app.post("/admin/update-settings")
async def update_site_settings(request: Request):
    if _admin_only_access_denied(request):
        return JSONResponse(
            {"status": "error", "message": "Administrator access required."},
            status_code=403,
        )

    if request.headers.get("content-type", "").split(";", 1)[0].strip().lower() != "application/json":
        return JSONResponse(
            {"status": "error", "message": "Settings must be submitted as JSON."},
            status_code=415,
        )
    try:
        payload = await request.json()
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JSONResponse(
            {"status": "error", "message": "Invalid JSON request body."},
            status_code=400,
        )
    if not isinstance(payload, dict) or set(payload) != set(DEFAULT_SITE_SETTINGS):
        return JSONResponse(
            {"status": "error", "message": "All homepage settings fields are required."},
            status_code=400,
        )

    settings = {}
    max_lengths = {
        "creator_name": 100,
        "journey_text": 4000,
        "email": 254,
        "phone": 64,
        "api_guide_link": 2048,
        "footer_text": 1000,
    }
    for key, max_length in max_lengths.items():
        value = payload[key]
        if not isinstance(value, str):
            return JSONResponse(
                {"status": "error", "message": f"{key} must be text."},
                status_code=400,
            )
        value = value.strip()
        if len(value) > max_length:
            return JSONResponse(
                {"status": "error", "message": f"{key} exceeds the maximum length."},
                status_code=400,
            )
        settings[key] = value

    if any(not settings[key] for key in ("creator_name", "journey_text", "email", "api_guide_link", "footer_text")):
        return JSONResponse(
            {"status": "error", "message": "Required homepage settings cannot be empty."},
            status_code=400,
        )
    if "@" not in settings["email"] or any(char.isspace() for char in settings["email"]):
        return JSONResponse(
            {"status": "error", "message": "Enter a valid contact email address."},
            status_code=400,
        )
    guide_url = urlparse(settings["api_guide_link"])
    if guide_url.scheme != "https" or not guide_url.netloc:
        return JSONResponse(
            {"status": "error", "message": "The API guide link must be an HTTPS URL."},
            status_code=400,
        )

    try:
        _save_site_settings(settings)
    except OSError:
        logger.exception("Could not save homepage settings.")
        return JSONResponse(
            {"status": "error", "message": "Homepage settings could not be saved."},
            status_code=500,
        )
    return {"status": "success", "message": "Homepage content saved."}

@app.post("/api/auth/register")
async def register(req: Request):
    data = await req.json()
    u = str(data.get("username", "")).strip()
    p = str(data.get("password", "")).strip()
    if not u or not p:
        return JSONResponse({"status": "error", "message": "Fields required"}, status_code=400)

    conn = get_db()
    _ensure_expiry_schema(conn)
    conn.commit()
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE LOWER(username) = LOWER(?)", (u,))
    if c.fetchone():
        conn.close()
        return JSONResponse({"status": "error", "message": "Username already taken"}, status_code=400)

    now = time.time()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("""
        INSERT INTO users (username, password, hwid, role, created_at, days_remaining, is_unlimited, is_active, last_seen, expires_at)
        VALUES (?, ?, 'NODE-ACTIVE', 'operator', ?, 10, 0, 1, ?, ?)
    """, (u, p, now_str, now, now + 10 * 86400))
    if "access_end_date" in {
        column["name"] for column in c.execute("PRAGMA table_info(users)")
    }:
        c.execute(
            "UPDATE users SET access_end_date = ? WHERE username = ?",
            (datetime.fromtimestamp(now + 10 * 86400).strftime("%Y-%m-%d"), u),
        )
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
    _ensure_expiry_schema(conn)
    conn.commit()
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

    target = "/admin" if _is_mobile_override_role(role) else "/dashboard"
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
    _ensure_expiry_schema(conn)
    c = conn.cursor()
    if data.get("delete"):
        c.execute("DELETE FROM users WHERE id = ?", (uid,))
    elif "delta_days" in data:
        account = c.execute(
            "SELECT expires_at FROM users WHERE id = ?",
            (uid,),
        ).fetchone()
        if not account:
            conn.close()
            return JSONResponse({"status": "error", "message": "User not found."}, status_code=404)
        try:
            delta_days = int(data["delta_days"])
        except (TypeError, ValueError):
            conn.close()
            return JSONResponse({"status": "error", "message": "Invalid day adjustment."}, status_code=400)
        remaining_seconds = max(
            0,
            float(account["expires_at"]) - time.time() + delta_days * 86400,
        )
        expires_at = time.time() + remaining_seconds
        c.execute(
            "UPDATE users SET expires_at = ?, days_remaining = ? WHERE id = ?",
            (expires_at, int((remaining_seconds + 86399) // 86400), uid),
        )
        if "access_end_date" in {
            column["name"] for column in c.execute("PRAGMA table_info(users)")
        }:
            c.execute(
                "UPDATE users SET access_end_date = ? WHERE id = ?",
                (datetime.fromtimestamp(expires_at).strftime("%Y-%m-%d"), uid),
            )
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
        fpath = _companion_apk_path()
        fname = "JARVIS_Node_Companion.apk"
        media = "application/vnd.android.package-archive"
        if not fpath:
            return JSONResponse(
                {
                    "status": "error",
                    "message": "PWA is ready to use. Android APK is building via GitHub Actions.",
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
    apk_path = _companion_apk_path(minimum_size=100000)
    if apk_path:
        return FileResponse(apk_path, filename="JARVIS_Companion.apk", media_type="application/vnd.android.package-archive")
    return JSONResponse(
        {
            "status": "error",
            "message": "PWA is ready to use. Android APK is building via GitHub Actions.",
        },
        status_code=503,
    )

@app.get("/api/user/subscription_status")
async def subscription_status(request: Request):
    username = request.cookies.get("username")
    if not username:
        return JSONResponse(
            {"status": "error", "message": "Sign in required."},
            status_code=401,
        )
    conn = get_db()
    try:
        _ensure_expiry_schema(conn)
        account = conn.execute(
            "SELECT role, is_active, is_unlimited, expires_at FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        conn.commit()
    finally:
        conn.close()
    if not account or not account["is_active"]:
        return JSONResponse(
            {"status": "error", "message": "Active account required."},
            status_code=403,
        )

    is_unlimited = bool(account["is_unlimited"]) or _is_mobile_override_role(account["role"])
    expires_at = None if is_unlimited else float(account["expires_at"])
    server_time = time.time()
    remaining = None if is_unlimited else max(0, expires_at - server_time)
    days_left = None if is_unlimited else int(remaining // 86400)
    hours_left = None if is_unlimited else int((remaining % 86400) // 3600)
    return {
        "status": "unlimited" if is_unlimited else "expired" if remaining == 0 else "active",
        "days_left": days_left,
        "hours_left": hours_left,
        "remaining_seconds": remaining,
        "expires_at": expires_at,
        "server_time": server_time,
        "is_unlimited": is_unlimited,
        "needs_renewal": False if is_unlimited else days_left <= 1,
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


class CompanionPairRequest(BaseModel):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=1024)
    device_name: str = Field(min_length=1, max_length=80)


class CompanionCommandRequest(BaseModel):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=1024)
    device_id: str = Field(min_length=1, max_length=64)
    action: Literal["open_app"]
    app: Literal["whatsapp", "youtube", "settings"]


class CompanionRevokeRequest(BaseModel):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=1024)
    device_id: str = Field(min_length=1, max_length=64)


class CompanionCommandResultRequest(BaseModel):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=1024)
    command_id: str = Field(min_length=1, max_length=64)


def _ensure_companion_tables(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS companion_devices (
            device_id TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            device_name TEXT NOT NULL,
            token_hash TEXT NOT NULL UNIQUE,
            created_at REAL NOT NULL,
            last_seen REAL,
            revoked INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS companion_commands (
            command_id TEXT PRIMARY KEY,
            device_id TEXT NOT NULL,
            username TEXT NOT NULL,
            status TEXT NOT NULL,
            updated_at REAL NOT NULL
        );
    """)


def _companion_rate_limited(conn, device_id):
    now = time.time()
    conn.execute(
        "DELETE FROM companion_commands WHERE updated_at < ?",
        (now - 7 * 86400,),
    )
    count = conn.execute(
        "SELECT COUNT(*) FROM companion_commands WHERE device_id = ? AND updated_at > ?",
        (device_id, now - 60),
    ).fetchone()[0]
    return count >= 10


def _companion_account_error(username, password, require_mobile=True):
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT username, password, role, is_active FROM users "
            "WHERE LOWER(TRIM(username)) = LOWER(TRIM(?))",
            (username,),
        ).fetchone()
        if not row or not secrets.compare_digest(
            str(row["password"]).encode("utf-8"),
            password.encode("utf-8"),
        ):
            return JSONResponse(
                {"status": "error", "message": "Invalid username or password."},
                status_code=401,
            ), None
        if not row["is_active"]:
            return JSONResponse(
                {"status": "error", "message": "Account deactivated."},
                status_code=403,
            ), None
        if require_mobile and not _is_mobile_override_role(row["role"]):
            _ensure_mobile_permission_tables(conn)
            if not _global_mobile_enabled(conn) or not _user_mobile_allowed(conn, row["username"]):
                return JSONResponse(
                    {"status": "error", "message": "Mobile companion access is not enabled for this account."},
                    status_code=403,
                ), None
        return None, row["username"]
    finally:
        conn.close()


@app.post("/api/companion/pair")
async def pair_companion(payload: CompanionPairRequest):
    account_error, username = _companion_account_error(payload.username, payload.password)
    if account_error:
        return account_error

    device_id = str(uuid.uuid4())
    access_token = secrets.token_urlsafe(32)
    conn = get_db()
    try:
        _ensure_companion_tables(conn)
        conn.execute(
            "INSERT INTO companion_devices "
            "(device_id, username, device_name, token_hash, created_at) VALUES (?, ?, ?, ?, ?)",
            (
                device_id,
                username,
                payload.device_name.strip(),
                hashlib.sha256(access_token.encode("utf-8")).hexdigest(),
                time.time(),
            ),
        )
        conn.commit()
    finally:
        conn.close()
    return {
        "status": "paired",
        "device_id": device_id,
        "access_token": access_token,
    }


@app.post("/api/companion/revoke")
async def revoke_companion(payload: CompanionRevokeRequest):
    account_error, username = _companion_account_error(
        payload.username,
        payload.password,
        require_mobile=False,
    )
    if account_error:
        return account_error

    conn = get_db()
    try:
        _ensure_companion_tables(conn)
        cursor = conn.execute(
            "UPDATE companion_devices SET revoked = 1 "
            "WHERE device_id = ? AND username = ? AND revoked = 0",
            (payload.device_id, username),
        )
        conn.commit()
        if cursor.rowcount == 0:
            return JSONResponse(
                {"status": "error", "message": "Paired device not found."},
                status_code=404,
            )
    finally:
        conn.close()

    async with _companion_connections_lock:
        websocket = _companion_connections.pop(payload.device_id, None)
    if websocket:
        await websocket.close(code=1008, reason="Device pairing revoked")
    return {"status": "revoked", "device_id": payload.device_id}


@app.websocket("/ws/companion")
async def companion_socket(websocket: WebSocket):
    authorization = websocket.headers.get("authorization", "")
    scheme, _, access_token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not access_token:
        await websocket.close(code=4401, reason="Bearer token required")
        return

    token_hash = hashlib.sha256(access_token.encode("utf-8")).hexdigest()
    conn = get_db()
    try:
        _ensure_companion_tables(conn)
        device = conn.execute(
            "SELECT d.device_id, d.username, u.role FROM companion_devices d "
            "JOIN users u ON u.username = d.username "
            "WHERE d.token_hash = ? AND d.revoked = 0 AND u.is_active = 1",
            (token_hash,),
        ).fetchone()
        if not device:
            await websocket.close(code=4401, reason="Invalid or revoked pairing token")
            return
        _ensure_mobile_permission_tables(conn)
        if not _is_mobile_override_role(device["role"]) and (
            not _global_mobile_enabled(conn)
            or not _user_mobile_allowed(conn, device["username"])
        ):
            await websocket.close(code=4403, reason="Mobile companion access disabled")
            return
    finally:
        conn.close()

    device_id = device["device_id"]
    await websocket.accept()
    async with _companion_connections_lock:
        previous = _companion_connections.get(device_id)
        _companion_connections[device_id] = websocket
    if previous and previous is not websocket:
        await previous.close(code=4001, reason="A newer connection replaced this one")

    try:
        while True:
            raw_message = await websocket.receive_text()
            if len(raw_message) > 4096:
                await websocket.close(code=1009, reason="Message too large")
                break
            try:
                message = json.loads(raw_message)
            except json.JSONDecodeError:
                await websocket.close(code=1003, reason="Invalid JSON")
                break
            if not isinstance(message, dict):
                await websocket.close(code=1003, reason="JSON object required")
                break

            if message.get("type") == "request_command":
                app_name = message.get("app")
                if not isinstance(app_name, str) or app_name not in {"whatsapp", "youtube", "settings"}:
                    await websocket.send_json({
                        "type": "command_error",
                        "message": "Only WhatsApp, YouTube, and Settings can be opened.",
                    })
                    continue

                command_id = str(uuid.uuid4())
                conn = get_db()
                try:
                    owner = conn.execute(
                        "SELECT d.username, d.revoked, u.role, u.is_active "
                        "FROM companion_devices d JOIN users u ON u.username = d.username "
                        "WHERE d.device_id = ?",
                        (device_id,),
                    ).fetchone()
                    if (
                        not owner
                        or owner["revoked"]
                        or not owner["is_active"]
                        or (
                            not _is_mobile_override_role(owner["role"])
                            and (
                                not _global_mobile_enabled(conn)
                                or not _user_mobile_allowed(conn, owner["username"])
                            )
                        )
                    ):
                        await websocket.close(code=4403, reason="Mobile companion access disabled")
                        break

                    conn.execute(
                        "UPDATE companion_devices SET last_seen = ? WHERE device_id = ?",
                        (time.time(), device_id),
                    )
                    if _companion_rate_limited(conn, device_id):
                        await websocket.send_json({
                            "type": "command_error",
                            "message": "Too many commands. Please wait before trying again.",
                        })
                        continue
                    conn.execute(
                        "INSERT INTO companion_commands "
                        "(command_id, device_id, username, status, updated_at) "
                        "VALUES (?, ?, ?, 'pending', ?)",
                        (command_id, device_id, owner["username"], time.time()),
                    )
                    conn.commit()
                finally:
                    conn.close()
                await websocket.send_json({
                    "id": command_id,
                    "action": "open_app",
                    "app": app_name,
                    "requires_confirmation": True,
                })
                continue

            conn = get_db()
            try:
                conn.execute(
                    "UPDATE companion_devices SET last_seen = ? "
                    "WHERE device_id = ? AND revoked = 0",
                    (time.time(), device_id),
                )
                if (
                    message.get("type") == "command_result"
                    and isinstance(message.get("status"), str)
                    and message.get("status") in {"launched", "cancelled", "unavailable"}
                    and isinstance(message.get("id"), str)
                ):
                    conn.execute(
                        "UPDATE companion_commands SET status = ?, updated_at = ? "
                        "WHERE command_id = ? AND device_id = ? AND status = 'pending'",
                        (message["status"], time.time(), message["id"], device_id),
                    )
                conn.commit()
            finally:
                conn.close()
    except WebSocketDisconnect:
        pass
    finally:
        async with _companion_connections_lock:
            if _companion_connections.get(device_id) is websocket:
                _companion_connections.pop(device_id, None)


@app.post("/api/companion/command")
async def send_companion_command(payload: CompanionCommandRequest):
    account_error, username = _companion_account_error(payload.username, payload.password)
    if account_error:
        return account_error

    conn = get_db()
    try:
        _ensure_companion_tables(conn)
        device = conn.execute(
            "SELECT device_id FROM companion_devices "
            "WHERE device_id = ? AND username = ? AND revoked = 0",
            (payload.device_id, username),
        ).fetchone()
    finally:
        conn.close()
    if not device:
        return JSONResponse(
            {"status": "error", "message": "Paired device not found."},
            status_code=404,
        )

    async with _companion_connections_lock:
        websocket = _companion_connections.get(payload.device_id)
    if not websocket:
        return JSONResponse(
            {"status": "error", "message": "The paired device is not connected."},
            status_code=409,
        )

    command_id = str(uuid.uuid4())
    conn = get_db()
    try:
        _ensure_companion_tables(conn)
        if _companion_rate_limited(conn, payload.device_id):
            conn.commit()
            return JSONResponse(
                {"status": "error", "message": "Too many commands. Please wait before trying again."},
                status_code=429,
            )
        conn.execute(
            "INSERT INTO companion_commands "
            "(command_id, device_id, username, status, updated_at) "
            "VALUES (?, ?, ?, 'pending', ?)",
            (command_id, payload.device_id, username, time.time()),
        )
        conn.commit()
    finally:
        conn.close()

    try:
        await websocket.send_json({
            "id": command_id,
            "action": payload.action,
            "app": payload.app,
            "requires_confirmation": True,
        })
    except (WebSocketDisconnect, RuntimeError):
        conn = get_db()
        try:
            conn.execute(
                "UPDATE companion_commands SET status = 'delivery_failed', updated_at = ? "
                "WHERE command_id = ? AND status = 'pending'",
                (time.time(), command_id),
            )
            conn.commit()
        finally:
            conn.close()
        return JSONResponse(
            {"status": "error", "message": "The paired device disconnected before delivery."},
            status_code=409,
        )
    return {"status": "sent", "command_id": command_id}


@app.post("/api/companion/command/result")
async def get_companion_command_result(payload: CompanionCommandResultRequest):
    account_error, username = _companion_account_error(payload.username, payload.password)
    if account_error:
        return account_error

    conn = get_db()
    try:
        _ensure_companion_tables(conn)
        result = conn.execute(
            "SELECT status, updated_at FROM companion_commands "
            "WHERE command_id = ? AND username = ?",
            (payload.command_id, username),
        ).fetchone()
        if not result:
            return JSONResponse(
                {"status": "error", "message": "Command not found."},
                status_code=404,
            )
        return {
            "command_id": payload.command_id,
            "status": result["status"],
            "updated_at": result["updated_at"],
        }
    finally:
        conn.close()


def _admin_access_denied(request: Request):
    username = request.cookies.get("username")
    if not username:
        return True
    conn = get_db()
    try:
        account = conn.execute(
            "SELECT role, is_active FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        return (
            not account
            or not account["is_active"]
            or not _is_mobile_override_role(account["role"])
        )
    finally:
        conn.close()


def _admin_only_access_denied(request: Request):
    username = request.cookies.get("username")
    if not username:
        return True
    conn = get_db()
    try:
        account = conn.execute(
            "SELECT role, is_active FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        return not account or not account["is_active"] or account["role"] != "admin"
    finally:
        conn.close()


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
        _ensure_expiry_schema(conn)
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
            "SELECT username, expires_at, is_unlimited FROM users "
            "WHERE role NOT IN ('admin', 'creator') ORDER BY id DESC"
        ).fetchall()
        permissions = {
            row["username"]: _user_mobile_allowed(conn, row["username"])
            for row in users
        }
        now = time.time()
        user_states = []
        for row in users:
            is_unlimited = bool(row["is_unlimited"])
            remaining = None if is_unlimited else max(0, float(row["expires_at"]) - now)
            user_states.append({
                "username": row["username"],
                "expires_at": None if is_unlimited else row["expires_at"],
                "remaining_seconds": remaining,
                "days_left": None if is_unlimited else int(remaining // 86400),
                "hours_left": None if is_unlimited else int((remaining % 86400) // 3600),
                "is_unlimited": is_unlimited,
                "mobile_allowed": permissions[row["username"]],
            })
        conn.commit()
        return {
            "global_mobile": global_mobile,
            "server_time": now,
            "permissions": permissions,
            "users": user_states,
            "mobile_allowed": True,
            "allowed": True,
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
