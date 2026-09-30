import re

path = "server/app.py"
with open(path, "r", encoding="utf-8-sig") as f:
    text = f.read()

# Real download logging & increment engine
tracking_logic = """
@app.get("/get-package/{platform_name}")
async def download_package_tracker(platform_name: str, req: Request):
    client_ip = req.client.host if req.client else "unknown"
    plat = platform_name.lower()
    
    conn = get_db_connection()
    c = conn.cursor()
    
    # 1. Real download counter increment
    if "win" in plat:
        c.execute("UPDATE portal_stats SET val = val + 1 WHERE key = 'win_downloads'")
    elif "apk" in plat or "android" in plat:
        c.execute("UPDATE portal_stats SET val = val + 1 WHERE key = 'apk_downloads'")
        
    # 2. Real Download Activity Log entry
    from datetime import datetime
    now_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute(
        "INSERT INTO download_logs (username, hwid, platform, timestamp) VALUES (?, ?, ?, ?)",
        ("guest_client", f"IP-{client_ip}", plat, now_time)
    )
    conn.commit()
    conn.close()
    
    # Serve real package file
    file_path = f"downloads/{plat}_installer.zip"
    if os.path.exists(file_path):
        return FileResponse(file_path, filename=f"jarvis_{plat}.zip")
    return {"status": "success", "message": f"{platform_name} build recorded", "timestamp": now_time}
"""

# Replace old download handler
if '@app.get("/get-package/{platform_name}")' in text:
    text = re.sub(r'@app\.get\("/get-package/\{platform_name\}"\)[\s\S]*?return[^\n]+', tracking_logic.strip(), text)
else:
    pos = text.find('@app.get("/api/admin/metrics")')
    text = text[:pos] + tracking_logic + "\n\n" + text[pos:]

# Pure zero-baseline, strictly dynamic metrics (no fake fallback)
pure_metrics = """
@app.get("/api/admin/metrics")
async def get_admin_metrics():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT key, val FROM portal_stats")
    stats = dict(c.fetchall())
    
    c.execute("SELECT COUNT(*) FROM users")
    tot = c.fetchone()[0]
    
    import time
    cutoff = time.time() - 90
    c.execute("SELECT COUNT(*) FROM users WHERE last_seen > ?", (cutoff,))
    act = c.fetchone()[0]
    conn.close()
    
    return {
        "total_users": tot,
        "active_users": act,
        "win_downloads": stats.get("win_downloads", 0),
        "apk_downloads": stats.get("apk_downloads", 0)
    }
"""

text = re.sub(r'@app\.get\("/api/admin/metrics"\)[\s\S]*?return\s*\{[\s\S]*?\}', pure_metrics.strip(), text)

with open(path, "w", encoding="utf-8") as f:
    f.write(text)

print("Real Dynamic Download Tracking Hooked Permanently!")