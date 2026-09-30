import re

path = "server/app.py"
with open(path, "r", encoding="utf-8-sig") as f:
    text = f.read()

# 1. Real Tracking & Control Endpoints
features_code = """
@app.get("/get-package/{platform_name}")
async def download_package_tracker(platform_name: str, req: Request):
    ip = req.headers.get("x-forwarded-for") or (req.client.host if req.client else "127.0.0.1")
    plat = platform_name.lower()
    col = "win_downloads" if "win" in plat else "apk_downloads"
    uname = req.cookies.get("username") or "guest"
    
    from datetime import datetime
    t_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute(f"UPDATE portal_stats SET val = val + 1 WHERE key = '{col}'")
    c.execute("INSERT INTO download_logs (username, hwid, platform, timestamp) VALUES (?, ?, ?, ?)",
              (uname, f"IP-{ip}", plat, t_str))
    conn.commit()
    conn.close()
    
    import os
    from fastapi.responses import FileResponse
    ext = "apk" if "apk" in plat or "android" in plat else "zip"
    fpath = f"downloads/{plat}_installer.{ext}"
    if os.path.exists(fpath):
        return FileResponse(fpath, filename=f"jarvis_{plat}.{ext}")
    return {"status": "success", "platform": plat, "user": uname, "timestamp": t_str}

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
"""

# Agar endpoints pehle se nahi hain, toh end mein add karein
if "/get-package/{platform_name}" not in text:
    text += "\n\n" + features_code

with open(path, "w", encoding="utf-8") as f:
    f.write(text)

print("Features injected without altering UI!")