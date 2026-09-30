import os

code = """import os
import sqlite3
import time
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()

# Mount Static Files
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates setup (Original UI path)
templates = Jinja2Templates(directory="templates" if os.path.exists("templates") else "server/templates")

def get_db_connection():
    conn = sqlite3.connect("portal.db")
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/")
async def root_portal(request: Request):
    uname = request.cookies.get("username")
    return templates.TemplateResponse("portal.html", {"request": request, "username": uname or "Guest"})

@app.get("/api/admin/metrics")
async def get_metrics():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT key, val FROM portal_stats")
    stats = dict(c.fetchall())
    c.execute("SELECT COUNT(*) FROM users")
    tot = c.fetchone()[0]
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
async def get_nodes():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users ORDER BY id DESC")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows
"""

with open("server/app.py", "w", encoding="utf-8") as f:
    f.write(code)

print("Original server app and UI loader completely restored!")