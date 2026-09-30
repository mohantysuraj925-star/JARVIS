path = "server/app.py"
with open(path, "r", encoding="utf-8-sig") as f:
    text = f.read()

nodes_endpoint = """
@app.get("/api/admin/nodes")
async def get_admin_nodes():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT id, username, created_at, days_remaining, is_unlimited, is_active, access_start_date, access_end_date, daily_time_start, daily_time_end, last_seen FROM users ORDER BY id DESC")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows
"""

if "/api/admin/nodes" not in text:
    pos = text.find('@app.get("/api/admin/metrics")')
    if pos != -1:
        text = text[:pos] + nodes_endpoint + "\n" + text[pos:]
    else:
        text += "\n" + nodes_endpoint

with open(path, "w", encoding="utf-8") as f:
    f.write(text)

print("Nodes API endpoint verified!")