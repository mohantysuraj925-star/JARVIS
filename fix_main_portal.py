import sqlite3
import re

# 1. Database ko real 0 baseline par set karein
conn = sqlite3.connect("jarvis.db")
c = conn.cursor()
c.execute("DROP TABLE IF EXISTS portal_stats")
c.execute("CREATE TABLE portal_stats (key TEXT PRIMARY KEY, val INTEGER DEFAULT 0)")
c.execute("INSERT INTO portal_stats VALUES ('win_downloads', 0)")
c.execute("INSERT INTO portal_stats VALUES ('apk_downloads', 0)")
c.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    created_at TEXT NOT NULL,
    days_remaining INTEGER DEFAULT 10,
    is_unlimited INTEGER DEFAULT 0,
    is_active INTEGER DEFAULT 1,
    access_start_date TEXT DEFAULT NULL,
    access_end_date TEXT DEFAULT NULL,
    daily_time_start TEXT DEFAULT NULL,
    daily_time_end TEXT DEFAULT NULL,
    last_seen REAL DEFAULT 0
)
""")
conn.commit()
conn.close()

# 2. Server application code mein real APIs ensure karein
path = "server/app.py"
with open(path, "r", encoding="utf-8-sig") as f:
    text = f.read()

# Replace hardcoded stats logic with real DB queries
api_logic = """
@app.get("/api/admin/metrics")
async def get_admin_metrics():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT key, val FROM portal_stats")
    stats = dict(c.fetchall())
    c.execute("SELECT COUNT(*) FROM users")
    tot = c.fetchone()[0]
    import time
    cutoff = time.time() - 45
    c.execute("SELECT COUNT(*) FROM users WHERE last_seen > ?", (cutoff,))
    act = c.fetchone()[0]
    conn.close()
    return {
        "total_users": tot,
        "active_users": act,
        "win_downloads": stats.get("win_downloads", 0),
        "apk_downloads": stats.get("apk_downloads", 0)
    }

@app.get("/api/admin/nodes")
async def get_admin_nodes():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT id, username, created_at, days_remaining, is_unlimited, is_active, access_start_date, access_end_date, daily_time_start, daily_time_end, last_seen FROM users ORDER BY id DESC")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

@app.post("/api/admin/modify-lifecycle")
async def modify_lifecycle(req: Request):
    data = await req.json()
    uid = data.get("user_id")
    delta = data.get("delta_days")
    unlim = data.get("is_unlimited")
    do_del = data.get("delete")
    s_date = data.get("start_date")
    e_date = data.get("end_date")
    s_time = data.get("start_time")
    e_time = data.get("end_time")

    conn = get_db_connection()
    c = conn.cursor()
    if do_del:
        c.execute("DELETE FROM users WHERE id = ?", (uid,))
    else:
        if unlim is not None:
            c.execute("UPDATE users SET is_unlimited = ?, is_active = 1 WHERE id = ?", (unlim, uid))
        if delta is not None:
            c.execute("UPDATE users SET days_remaining = MAX(0, days_remaining + ?), is_active = 1 WHERE id = ?", (delta, uid))
        if s_date is not None or e_date is not None:
            c.execute("UPDATE users SET access_start_date = ?, access_end_date = ? WHERE id = ?", (s_date, e_date, uid))
        if s_time is not None or e_time is not None:
            c.execute("UPDATE users SET daily_time_start = ?, daily_time_end = ? WHERE id = ?", (s_time, e_time, uid))
    conn.commit()
    conn.close()
    return {"status": "ok"}
"""

if "/api/admin/modify-lifecycle" not in text:
    pos = text.find('@app.get("/get-package/')
    if pos != -1:
        text = text[:pos] + api_logic + "\n" + text[pos:]

with open(path, "w", encoding="utf-8") as f:
    f.write(text)

print("Real DB and APIs locked successfully!")