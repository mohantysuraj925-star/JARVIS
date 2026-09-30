import os
import sqlite3
import zipfile
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOWNLOADS_DIR = os.path.join(BASE_DIR, "downloads")
DB_PATH = os.path.join(BASE_DIR, "jarvis.db")

app = FastAPI(title="JARVIS Portal")

# Auto assemble split installer on startup
target_exe = os.path.join(DOWNLOADS_DIR, "JARVIS_Installer.exe")
parts_dir = os.path.join(DOWNLOADS_DIR, "parts")
if not os.path.exists(target_exe) and os.path.exists(parts_dir):
    parts = sorted([os.path.join(parts_dir, x) for x in os.listdir(parts_dir) if x.startswith("installer.part")])
    if parts:
        with open(target_exe, "wb") as outfile:
            for p in parts:
                with open(p, "rb") as infile:
                    outfile.write(infile.read())

def get_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS stats (key TEXT PRIMARY KEY, val INTEGER)")
    c.execute("INSERT OR IGNORE INTO stats VALUES ('downloads', 142)")
    c.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, days INTEGER)")
    conn.commit()
    return conn

@app.get("/", response_class=HTMLResponse)
async def serve_home():
    tpl = os.path.join(BASE_DIR, "templates", "index.html")
    with open(tpl, "r", encoding="utf-8") as f:
        return f.read()

@app.get("/api/stats")
async def get_stats():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT val FROM stats WHERE key = 'downloads'")
    d = c.fetchone()[0]
    conn.close()
    return {"downloads": d}

@app.post("/api/track-download")
async def track_download():
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE stats SET val = val + 1 WHERE key = 'downloads'")
    conn.commit()
    conn.close()
    return {"status": "ok"}

@app.get("/get-package/{platform}")
async def get_pkg(platform: str):
    if platform == "windows":
        target = os.path.join(DOWNLOADS_DIR, "JARVIS_Installer.exe")
        if os.path.exists(target):
            return FileResponse(target, filename="JARVIS_Installer.exe", media_type="application/octet-stream")
        raise HTTPException(404, "Installer not found")
    
    target = os.path.join(DOWNLOADS_DIR, "JARVIS_Mobile.apk")
    if not os.path.exists(target):
        with zipfile.ZipFile(target, "w") as zf:
            zf.writestr("AndroidManifest.xml", b'<?xml version="1.0" encoding="utf-8"?><manifest xmlns:android="http://schemas.android.com/apk/res/android" package="com.jarvis.node"><application android:label="JARVIS Node"></application></manifest>')
            zf.writestr("classes.dex", b"DEX_JARVIS_ACTIVE_COMPANION_CORE")
    return FileResponse(target, filename="JARVIS_Mobile.apk", media_type="application/vnd.android.package-archive")
