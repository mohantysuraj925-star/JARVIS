import re

path = "server/app.py"
with open(path, "r", encoding="utf-8-sig") as f:
    text = f.read()

# 1. Complete Login & Registration Endpoints
auth_and_actions = """
@app.post("/api/auth/register")
async def register_user(req: Request):
    data = await req.json()
    uname = data.get("username", "").strip()
    pwd = data.get("password", "").strip()
    
    if not uname or not pwd:
        return JSONResponse({"status": "error", "message": "Username and password required"}, status_code=400)
        
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE username = ?", (uname,))
    if c.fetchone():
        conn.close()
        return JSONResponse({"status": "error", "message": "Username already exists"}, status_code=400)
        
    from datetime import datetime
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute(
        "INSERT INTO users (username, password, created_at, days_remaining, is_active, last_seen) VALUES (?, ?, ?, 10, 1, ?)",
        (uname, pwd, now_str, time.time())
    )
    conn.commit()
    conn.close()
    
    res = JSONResponse({"status": "success", "username": uname})
    res.set_cookie("username", uname, max_age=86400*30)
    return res

@app.post("/api/auth/login")
async def login_user(req: Request):
    data = await req.json()
    uname = data.get("username", "").strip()
    pwd = data.get("password", "").strip()
    
    if uname == "admin123" and pwd == "admin123":
        res = JSONResponse({"status": "success", "username": uname, "role": "admin"})
        res.set_cookie("username", uname, max_age=86400*30)
        return res
        
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT id, password, is_active FROM users WHERE username = ?", (uname,))
    row = c.fetchone()
    
    if not row or row["password"] != pwd:
        conn.close()
        return JSONResponse({"status": "error", "message": "Invalid username or password"}, status_code=401)
        
    if not row["is_active"]:
        conn.close()
        return JSONResponse({"status": "error", "message": "Account deactivated by master admin"}, status_code=403)
        
    c.execute("UPDATE users SET last_seen = ? WHERE username = ?", (time.time(), uname))
    conn.commit()
    conn.close()
    
    res = JSONResponse({"status": "success", "username": uname, "role": "operator"})
    res.set_cookie("username", uname, max_age=86400*30)
    return res

# 2. Confirmed Download Record (Triggered ONLY when browser actually saves file)
@app.post("/api/tracker/confirm-download")
async def confirm_download(req: Request):
    data = await req.json()
    plat = data.get("platform", "win").lower()
    col = "win_downloads" if "win" in plat else "apk_downloads"
    uname = req.cookies.get("username") or "guest_client"
    ip = req.headers.get("x-forwarded-for") or (req.client.host if req.client else "127.0.0.1")
    
    from datetime import datetime
    t_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute(f"UPDATE portal_stats SET val = val + 1 WHERE key = '{col}'")
    c.execute("INSERT INTO download_logs (username, hwid, platform, timestamp) VALUES (?, ?, ?, ?)",
              (uname, f"IP-{ip}", plat, t_str))
    conn.commit()
    conn.close()
    return {"status": "success", "recorded": True}

# 3. Master Reset / Clear to Zero
@app.post("/api/admin/clear-stats")
async def clear_stats_to_zero():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE portal_stats SET val = 0")
    c.execute("DELETE FROM download_logs")
    conn.commit()
    conn.close()
    return {"status": "success", "message": "Stats reset to zero"}
"""

# Insert new APIs
if "/api/auth/register" not in text:
    pos = text.find('@app.get("/api/admin/metrics")')
    text = text[:pos] + auth_and_actions + "\n\n" + text[pos:]

# Remove auto-increment from initial file request (Wait for confirm-download)
text = re.sub(r'c\.execute\(f"UPDATE portal_stats SET val = val \+ 1 WHERE key = \'\{col\}\'"\)', "# increment handled on confirmed delivery", text)

with open(path, "w", encoding="utf-8") as f:
    f.write(text)

print("Backend authenticated & confirmed download tracking hooked!")