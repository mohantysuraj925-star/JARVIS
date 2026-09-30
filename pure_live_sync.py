import re
import os

path = "server/app.py"
with open(path, "r", encoding="utf-8-sig") as f:
    text = f.read()

# Pure dynamic real-time tracking route
clean_endpoints = """
@app.get("/get-package/{platform_name}")
async def download_package_tracker(platform_name: str, req: Request):
    ip = req.headers.get("x-forwarded-for") or (req.client.host if req.client else "127.0.0.1")
    plat = platform_name.lower()
    col = "win_downloads" if "win" in plat else "apk_downloads"
    
    from datetime import datetime
    t_stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute(f"UPDATE portal_stats SET val = val + 1 WHERE key = '{col}'")
    c.execute("INSERT INTO download_logs (username, hwid, platform, timestamp) VALUES (?, ?, ?, ?)",
              ("guest_download", f"IP-{ip}", plat, t_stamp))
    conn.commit()
    conn.close()
    
    file_path = f"downloads/{plat}_installer.zip"
    if os.path.exists(file_path):
        return FileResponse(file_path, filename=f"jarvis_{plat}.zip")
    return {"status": "success", "platform": plat, "ip_logged": ip, "time": t_stamp}

@app.get("/api/admin/metrics")
async def get_admin_metrics():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT key, val FROM portal_stats")
    stats = dict(c.fetchall())
    
    c.execute("SELECT COUNT(*) FROM users")
    tot = c.fetchone()[0]
    
    import time
    cutoff = time.time() - 300
    c.execute("SELECT COUNT(*) FROM users WHERE last_seen > ?", (cutoff,))
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
"""

text = re.sub(r'@app\.get\("/get-package/\{platform_name\}"\)[\s\S]*?@app\.get\("/api/admin/metrics"\)[\s\S]*?return\s*\{[\s\S]*?\}', clean_endpoints.strip(), text)

# Download buttons direct file bypass na karein, tracking route par jayein
text = re.sub(r'href=["\'][^"\']*win[^"\']*\.exe["\']', 'href="/get-package/windows"', text, flags=re.IGNORECASE)
text = re.sub(r'href=["\'][^"\']*android[^"\']*\.apk["\']', 'href="/get-package/android"', text, flags=re.IGNORECASE)

with open(path, "w", encoding="utf-8") as f:
    f.write(text)

print("Dynamic real-time engine hooked cleanly!")