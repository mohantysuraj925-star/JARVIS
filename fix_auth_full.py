import sqlite3
import re

# 1. DB me check & clean
conn = sqlite3.connect("portal.db")
c = conn.cursor()

# Agar Ran user corrupted/mismatched pass ke sath hai toh update karein
c.execute("SELECT id, username, password FROM users WHERE LOWER(TRIM(username)) = 'ran'")
row = c.fetchone()
if row:
    # Set known password so login works instantly
    c.execute("UPDATE users SET password = ?, is_active = 1 WHERE id = ?", ("Suraj@20257", row[0]))
    conn.commit()
    print("User 'Ran' password synchronized in DB!")
conn.close()

# 2. Fix Auth Endpoints in server/app.py
path = "server/app.py"
with open(path, "r", encoding="utf-8-sig") as f:
    text = f.read()

robust_auth = """
@app.post("/api/register")
async def register_node(req: Request):
    try:
        data = await req.json()
    except Exception:
        return JSONResponse({"status": "error", "message": "Invalid payload"}, status_code=400)
        
    uname = (data.get("username") or data.get("machine_id") or "").strip()
    email = (data.get("email") or "").strip()
    pwd = (data.get("password") or "").strip()

    if not uname or not pwd:
        return JSONResponse({"status": "error", "message": "Username and password required"}, status_code=400)

    import time
    from datetime import datetime
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE LOWER(TRIM(username)) = LOWER(?)", (uname,))
    if c.fetchone():
        conn.close()
        return JSONResponse({"status": "error", "message": "Yeh username pehle se register hai. Please sign in."}, status_code=400)

    c.execute(
        "INSERT INTO users (username, password, email, created_at, days_remaining, is_active, last_seen) VALUES (?, ?, ?, ?, 10, 1, ?)",
        (uname, pwd, email, now_str, time.time())
    )
    conn.commit()
    conn.close()

    res = JSONResponse({"status": "success", "username": uname, "message": "Registered successfully"})
    res.set_cookie(key="username", value=uname, httponly=False, max_age=86400*30, path="/", samesite="lax")
    return res

@app.post("/api/login")
async def user_login(req: Request):
    try:
        data = await req.json()
    except Exception:
        return JSONResponse({"status": "error", "message": "Invalid payload"}, status_code=400)

    uname = (data.get("username") or data.get("machine_id") or "").strip()
    pwd = (data.get("password") or "").strip()

    if not uname or not pwd:
        return JSONResponse({"status": "error", "message": "Username and password required"}, status_code=400)

    import time
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT id, password, is_active FROM users WHERE LOWER(TRIM(username)) = LOWER(?)", (uname,))
    user = c.fetchone()

    if not user:
        conn.close()
        return JSONResponse({"status": "error", "message": "User not found. Pehle register karein."}, status_code=404)

    if str(user["password"]).strip() != pwd:
        conn.close()
        return JSONResponse({"status": "error", "message": "Galat password!"}, status_code=401)

    if not user["is_active"]:
        conn.close()
        return JSONResponse({"status": "error", "message": "Account blocked by admin."}, status_code=403)

    c.execute("UPDATE users SET last_seen = ? WHERE id = ?", (time.time(), user["id"]))
    conn.commit()
    conn.close()

    res = JSONResponse({"status": "success", "username": uname, "message": "Authorized"})
    res.set_cookie(key="username", value=uname, httponly=False, max_age=86400*30, path="/", samesite="lax")
    return res
"""

# Replace registration and login APIs cleanly
if '@app.post("/api/register")' in text:
    text = re.sub(r'@app\.post\("/api/register"\)[\s\S]*?return\s+res[^\n]*', '', text)
if '@app.post("/api/login")' in text:
    text = re.sub(r'@app\.post\("/api/login"\)[\s\S]*?return\s+res[^\n]*', '', text)

pos = text.find('@app.get("/api/admin/metrics")')
if pos != -1:
    text = text[:pos] + robust_auth + "\n\n" + text[pos:]
else:
    text += "\n\n" + robust_auth

with open(path, "w", encoding="utf-8") as f:
    f.write(text)

print("Robust Login & Register APIs installed successfully!")