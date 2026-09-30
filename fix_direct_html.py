import os

# templates dhoondo
html_path = None
for root, dirs, files in os.walk("."):
    if "portal.html" in files:
        html_path = os.path.join(root, "portal.html")
        break

print("Found portal.html at:", html_path)

code = f"""
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import sqlite3, os, time

app = FastAPI()

if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def home():
    with open(r"{html_path}", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/api/admin/metrics")
async def metrics():
    conn = sqlite3.connect("portal.db")
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
    return {{"total_users": tot, "active_users": act, "win_downloads": w, "windows_downloads": w, "apk_downloads": a, "android_downloads": a}}

@app.get("/api/admin/nodes")
async def nodes():
    conn = sqlite3.connect("portal.db")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM users ORDER BY id DESC")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows
"""

with open("server/app.py", "w", encoding="utf-8") as f:
    f.write(code)

print("Updated server/app.py with absolute template loading.")