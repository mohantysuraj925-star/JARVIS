import sqlite3
from pathlib import Path
from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, JSONResponse

router = APIRouter()
ROOT = Path(__file__).resolve().parent.parent
PORTAL_DB = ROOT / "portal_data.db"
FEEDBACK_DB = ROOT / "database.db"


def _portal():
    conn = sqlite3.connect(PORTAL_DB)
    conn.execute("CREATE TABLE IF NOT EXISTS system_config (key TEXT PRIMARY KEY, value TEXT)")
    return conn


def _mobile_active() -> bool:
    conn = _portal()
    try:
        row = conn.execute(
            "SELECT value FROM system_config WHERE key='mobile_download_active'").fetchone()
    finally:
        conn.close()
    return bool(row) and row[0].strip().lower() == "true"


@router.get("/api/system/mobile-status")
@router.get("/api/admin/mobile_status")
def mobile_status():
    try:
        a = _mobile_active()
        return {"active": a, "enabled": a, "status": "active" if a else "deactive"}
    except Exception as e:
        return {"active": False, "enabled": False, "error": str(e)}


@router.post("/api/system/mobile-toggle")
@router.post("/api/admin/toggle_all_mobile")
def mobile_toggle(payload: dict | None = None):
    try:
        if payload and "active" in payload:
            new = bool(payload["active"])
        else:
            new = not _mobile_active()
        conn = _portal()
        try:
            conn.execute(
                "INSERT OR REPLACE INTO system_config (key, value) VALUES ('mobile_download_active', ?)",
                ("true" if new else "false",))
            conn.commit()
        finally:
            conn.close()
        return {"success": True, "active": new, "enabled": new}
    except Exception as e:
        return {"success": False, "active": False, "enabled": False, "error": str(e)}


@router.post("/api/feedback")
async def save_feedback(request: Request):
    data = await request.json()
    conn = sqlite3.connect(FEEDBACK_DB)
    try:
        conn.execute("CREATE TABLE IF NOT EXISTS feedbacks (id INTEGER PRIMARY KEY AUTOINCREMENT, "
                     "username TEXT, rating INTEGER, comment TEXT, "
                     "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        conn.execute("INSERT INTO feedbacks (username, rating, comment) VALUES (?, ?, ?)",
                     (data.get("username", "Operator"), data.get("rating", 5), data.get("comment", "")))
        conn.commit()
    finally:
        conn.close()
    return {"status": "success", "message": "Feedback saved"}


@router.get("/api/feedback")
async def get_feedback(user: str = ""):
    result = {"rating": 5, "comment": "No feedback yet."}
    conn = sqlite3.connect(FEEDBACK_DB)
    try:
        if user:
            row = conn.execute("SELECT rating, comment, created_at FROM feedbacks "
                               "WHERE username=? ORDER BY id DESC LIMIT 1", (user,)).fetchone()
        else:
            row = conn.execute("SELECT rating, comment, created_at FROM feedbacks "
                               "ORDER BY id DESC LIMIT 1").fetchone()
        if row:
            result = {"rating": row[0], "comment": row[1], "date": row[2]}
    except sqlite3.OperationalError:
        pass
    finally:
        conn.close()
    return result


@router.get("/download-apk")
@router.get("/api/downloads/mobile")
async def download_apk():
    for rel in ("server/static/downloads/app-release.apk", "downloads/app-release.apk"):
        f = ROOT / rel
        if f.exists():
            return FileResponse(f, filename="GARUDA-Android.apk",
                                media_type="application/vnd.android.package-archive")
    return JSONResponse({"error": "APK not found"}, status_code=404)
