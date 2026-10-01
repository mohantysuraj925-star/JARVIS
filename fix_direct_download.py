import re

path = "server/app.py"
with open(path, "r", encoding="utf-8-sig") as f:
    text = f.read()

download_handler = """
@app.get("/get-package/{platform_name}")
async def download_package_tracker(platform_name: str, req: Request):
    ip = req.headers.get("x-forwarded-for") or (req.client.host if req.client else "127.0.0.1")
    plat = platform_name.lower()
    col = "win_downloads" if "win" in plat else "apk_downloads"
    uname = req.cookies.get("username") or "guest_client"
    
    from datetime import datetime
    t_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Counter increment aur activity log
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute(f"UPDATE portal_stats SET val = val + 1 WHERE key = '{col}'")
        c.execute("INSERT INTO download_logs (username, hwid, platform, timestamp) VALUES (?, ?, ?, ?)",
                  (uname, f"IP-{ip}", plat, t_str))
        conn.commit()
        conn.close()
    except Exception:
        pass
    
    target_zip = f"downloads/{plat}_installer.zip"
    out_name = f"JARVIS_Desktop_Setup.zip" if "win" in plat else f"JARVIS_Android_Companion.zip"
    
    if os.path.exists(target_zip):
        return FileResponse(
            path=target_zip,
            filename=out_name,
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={out_name}"}
        )
    return JSONResponse({"status": "error", "message": "Package build file missing"}, status_code=404)
"""

text = re.sub(r'@app\.get\("/get-package/\{platform_name\}"\)[\s\S]*?return[^\n]+', download_handler.strip(), text)

with open(path, "w", encoding="utf-8") as f:
    f.write(text)

print("Direct File Streaming Engine Configured!")