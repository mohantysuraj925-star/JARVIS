import re

path = "server/app.py"
with open(path, "r", encoding="utf-8-sig") as f:
    text = f.read()

# Ensure static script is linked without breaking UI
if '/static/admin_actions.js' not in text:
    text = text.replace("</body>", '<script src="/static/admin_actions.js"></script>\n</body>')

# Ensure Modify Lifecycle Endpoint handles deletion and updates correctly
lifecycle_api = """
@app.post("/api/admin/modify-lifecycle")
async def modify_lifecycle(req: Request):
    data = await req.json()
    uid = data.get("user_id")
    delta_days = data.get("delta_days")
    is_unlimited = data.get("is_unlimited")
    do_delete = data.get("delete")
    start_date = data.get("start_date")
    end_date = data.get("end_date")
    start_time = data.get("start_time")
    end_time = data.get("end_time")

    conn = get_db_connection()
    c = conn.cursor()
    if do_delete:
        c.execute("DELETE FROM users WHERE id = ?", (uid,))
    else:
        if is_unlimited is not None:
            c.execute("UPDATE users SET is_unlimited = ?, is_active = 1 WHERE id = ?", (is_unlimited, uid))
        if delta_days is not None:
            c.execute("UPDATE users SET days_remaining = MAX(0, days_remaining + ?), is_active = 1 WHERE id = ?", (delta_days, uid))
        if start_date is not None or end_date is not None:
            c.execute("UPDATE users SET access_start_date = ?, access_end_date = ? WHERE id = ?", (start_date, end_date, uid))
        if start_time is not None or end_time is not None:
            c.execute("UPDATE users SET daily_time_start = ?, daily_time_end = ? WHERE id = ?", (start_time, end_time, uid))
    conn.commit()
    conn.close()
    return {"status": "ok"}
"""

if '/api/admin/modify-lifecycle' not in text:
    pos = text.find('@app.get("/get-package/')
    if pos != -1:
        text = text[:pos] + lifecycle_api + "\n" + text[pos:]
else:
    # Update existing implementation with delete support
    text = re.sub(r'@app\.post\("/api/admin/modify-lifecycle"\)[\s\S]*?return \{"status": "updated"\}', lifecycle_api.strip(), text)

with open(path, "w", encoding="utf-8") as f:
    f.write(text)

print("Backend & Admin bindings successfully patched!")