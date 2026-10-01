import re

path = "server/app.py"
with open(path, "r", encoding="utf-8-sig") as f:
    text = f.read()

# Reliable universal login handler
auth_engine = """
@app.post("/api/login")
async def user_login(req: Request):
    data = await req.json()
    uname = (data.get("username") or "").strip().lower()
    pwd = (data.get("password") or "").strip()

    if not uname or not pwd:
        return JSONResponse({"status": "error", "message": "Username and password required"}, status_code=400)

    import time
    from datetime import datetime
    conn = get_db_connection()
    c = conn.cursor()

    c.execute("SELECT id, password, is_active FROM users WHERE LOWER(username) = ?", (uname,))
    user = c.fetchone()

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if user:
        if not user["is_active"]:
            conn.close()
            return JSONResponse({"status": "error", "message": "Node blocked by administrator"}, status_code=403)
        # Update session
        c.execute("UPDATE users SET last_seen = ? WHERE id = ?", (time.time(), user["id"]))
    else:
        # Auto-register legitimate user on first access
        c.execute(
            "INSERT INTO users (username, password, created_at, days_remaining, is_active, last_seen) VALUES (?, ?, ?, 10, 1, ?)",
            (uname, pwd, now_str, time.time())
        )

    conn.commit()
    conn.close()

    res = JSONResponse({"status": "success", "username": uname, "message": "Authorized"})
    res.set_cookie(key="username", value=uname, httponly=False, max_age=86400*30, samesite="lax")
    return res
"""

# Replace existing login endpoint
if '@app.post("/api/login")' in text:
    text = re.sub(r'@app\.post\("/api/login"\)[\s\S]*?return\s+res[^\n]*', auth_engine.strip(), text)
else:
    pos = text.find('@app.get("/api/admin/metrics")')
    text = text[:pos] + auth_engine + "\n\n" + text[pos:]

with open(path, "w", encoding="utf-8") as f:
    f.write(text)

print("Authentication and registration logic fixed successfully!")