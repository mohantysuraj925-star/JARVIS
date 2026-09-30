path = "server/app.py"
with open(path, "r", encoding="utf-8-sig") as f:
    text = f.read()

# Real synchronous metrics endpoint
metrics_code = """
@app.get("/api/admin/metrics")
async def get_admin_metrics():
    conn = get_db()
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
    
    # Agar 1 active node chal raha hai, toh Total Users kam se kam Active Users ke barabar rahega
    tot = max(tot, act, 1 if act > 0 else 0)
    
    return {
        "total_users": tot,
        "active_users": act,
        "win_downloads": stats.get("win_downloads", 0),
        "apk_downloads": stats.get("apk_downloads", 0)
    }
"""

import re
text = re.sub(r'@app\.get\("/api/admin/metrics"\)[\s\S]*?return \{[\s\S]*?\}', metrics_code.strip(), text)

with open(path, "w", encoding="utf-8") as f:
    f.write(text)

print("Metrics sync logic updated!")