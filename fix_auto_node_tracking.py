import re

path = "server/app.py"
with open(path, "r", encoding="utf-8-sig") as f:
    text = f.read()

enhanced_tracker = """@app.get("/get-package/{platform_name}")
async def download_package_tracker(platform_name: str, req: Request):
    ip = req.headers.get("x-forwarded-for") or (req.client.host if req.client else "127.0.0.1")
    ip_clean = ip.split(",")[0].strip()
    plat = platform_name.lower()
    col = "win_downloads" if "win" in plat else "apk_downloads"
    uname = req.cookies.get("username")
    
    t_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    curr_ts = time.time()
    
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute(f"UPDATE portal_stats SET val = val + 1 WHERE key = '{col}'")
    
    node_name = uname if uname and uname != "undefined" else f"Node-{ip_clean.replace('.', '-')[-7:]}"
    
    c.execute("SELECT id FROM users WHERE username = ?", (node_name,))
    row = c.fetchone()
    if not row:
        q = "INSERT INTO users (username, password, hwid, email, role, created_at, days_remaining, is_unlimited, is_active, last_seen) VALUES (?, 'guest123', ?, ?, 'operator', ?, 10, 0, 1, ?)"
        c.execute(q, (node_name, f"HWID-{ip_clean}", f"{node_name}@client.mesh", t_str, curr_ts))
    else:
        c.execute("UPDATE users SET last_seen = ?, is_active = 1 WHERE id = ?", (curr_ts, row["id"]))
        
    c.execute("INSERT INTO download_logs (username, hwid, platform, timestamp) VALUES (?, ?, ?, ?)",
              (node_name, f"IP-{ip_clean}", plat, t_str))
              
    conn.commit()
    conn.close()
    
    file_path = f"downloads/{plat}_installer.zip"
    if os.path.exists(file_path):
        return FileResponse(file_path, filename=f"jarvis_{plat}.zip")
    return {"status": "success", "node_registered": node_name, "platform": plat, "time": t_str}"""

text = re.sub(r'@app\.get\("/get-package/\{platform_name\}"\)[\s\S]*?return\s*\{[\s\S]*?\}', enhanced_tracker.strip(), text)

with open(path, "w", encoding="utf-8") as f:
    f.write(text)

print("Dynamic auto-node generator hooked successfully!")