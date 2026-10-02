import os
import sqlite3

# 1. Database & Table setup
conn = sqlite3.connect("portal_data.db")
c = conn.cursor()
c.execute("""
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    created_at TEXT,
    trial_days INTEGER DEFAULT 10,
    mobile_allowed INTEGER DEFAULT 0
)
""")
c.execute("""
CREATE TABLE IF NOT EXISTS global_settings (
    key TEXT PRIMARY KEY,
    value TEXT
)
""")
c.execute("INSERT OR IGNORE INTO global_settings (key, value) VALUES ('global_mobile', '0')")
conn.commit()
conn.close()

# 2. Server APIs ensure karein app.py me
app_path = os.path.join("server", "app.py")
if os.path.exists(app_path):
    with open(app_path, "r", encoding="utf-8") as f:
        code = f.read()

    api_code = """
from datetime import datetime
import sqlite3

@app.get("/api/admin/live_control_data")
async def live_control_data():
    conn = sqlite3.connect("portal_data.db")
    c = conn.cursor()
    c.execute("SELECT value FROM global_settings WHERE key='global_mobile'")
    grow = c.fetchone()
    global_mob = (grow[0] == '1') if grow else False

    c.execute("SELECT username, created_at, trial_days, mobile_allowed FROM users")
    rows = c.fetchall()
    users = []
    now = datetime.utcnow()
    for u, c_at, t_days, m_allow in rows:
        d_left = t_days or 10
        if c_at:
            try:
                diff = (now - datetime.fromisoformat(c_at)).total_seconds() / 86400.0
                d_left = max(0, int((t_days or 10) - diff))
            except:
                pass
        users.append({
            "username": u,
            "days_left": d_left,
            "mobile_allowed": bool(m_allow)
        })
    conn.close()
    return {"global_mobile": global_mob, "users": users}

@app.get("/api/admin/toggle_global_mobile")
async def toggle_global_mobile(enabled: bool):
    conn = sqlite3.connect("portal_data.db")
    c = conn.cursor()
    c.execute("INSERT INTO global_settings (key, value) VALUES ('global_mobile', ?) ON CONFLICT(key) DO UPDATE SET value=?", ('1' if enabled else '0', '1' if enabled else '0'))
    conn.commit()
    conn.close()
    return {"status": "success", "global_mobile": enabled}

@app.get("/api/admin/set_user_mobile_access")
async def set_user_mobile_access(username: str, allow: bool):
    conn = sqlite3.connect("portal_data.db")
    c = conn.cursor()
    c.execute("INSERT INTO users (username, mobile_allowed, created_at) VALUES (?, ?, datetime('now')) ON CONFLICT(username) DO UPDATE SET mobile_allowed=?", (username, 1 if allow else 0, 1 if allow else 0))
    conn.commit()
    conn.close()
    return {"status": "success", "username": username, "mobile_allowed": allow}
"""
    if "/api/admin/live_control_data" not in code:
        code += "\n" + api_code
        with open(app_path, "w", encoding="utf-8") as f:
            f.write(code)
        print("[OK] app.py updated with live control APIs.")

# 3. Inject Visual Control Box in Admin Templates
admin_box_ui = """
<!-- ================= JARVIS ADMIN MOBILE CONTROL CENTER ================= -->
<div id="adminMobileHub" style="margin: 25px auto; max-width: 950px; background: #0b132b; border: 2px solid #00d2ff; border-radius: 12px; padding: 20px; color: #fff; font-family: 'Segoe UI', sans-serif; box-shadow: 0 0 20px rgba(0,210,255,0.3);">
    <div style="display:flex; justify-content:space-between; align-items:center; border-bottom: 1px solid #1e293b; padding-bottom: 15px; margin-bottom: 15px;">
        <h3 style="margin:0; color:#00d2ff; font-size: 20px;">?? Mobile APK Access & Real Calculation Monitor</h3>
        <button id="hubGlobalBtn" onclick="toggleGlobalSwitch()" style="background:#ef4444; color:#fff; border:none; padding: 10px 18px; border-radius: 6px; font-weight:bold; cursor:pointer;">Global Download: OFF</button>
    </div>

    <div style="display:flex; gap:10px; margin-bottom: 15px;">
        <input type="text" id="targetUserInputField" placeholder="Username likho jise Allow ya Block karna hai..." style="flex:1; padding: 10px; border-radius: 6px; border: 1px solid #334155; background: #1c2541; color: #fff;">
        <button onclick="changeAccess(true)" style="background:#10b981; color:#000; border:none; padding: 10px 18px; border-radius: 6px; font-weight:bold; cursor:pointer;">Allow Download</button>
        <button onclick="changeAccess(false)" style="background:#f43f5e; color:#fff; border:none; padding: 10px 18px; border-radius: 6px; font-weight:bold; cursor:pointer;">Block (Coming Soon)</button>
    </div>

    <table style="width:100%; border-collapse:collapse; text-align:left; font-size:14px; background:#1c2541; border-radius:8px; overflow:hidden;">
        <thead>
            <tr style="background:#0d1b2a; color:#94a3b8; border-bottom: 2px solid #334155;">
                <th style="padding:12px;">User</th>
                <th style="padding:12px;">Live Trial Left</th>
                <th style="padding:12px;">Mobile Download Status</th>
                <th style="padding:12px;">Direct Action</th>
            </tr>
        </thead>
        <tbody id="hubUsersTableBody">
            <tr><td colspan="4" style="padding:12px; color:#64748b;">Loading user records...</td></tr>
        </tbody>
    </table>
</div>

<script>
let globalMobileActive = false;

async function loadHubData() {
    try {
        const res = await fetch('/api/admin/live_control_data');
        const data = await res.json();
        globalMobileActive = data.global_mobile;

        const gBtn = document.getElementById('hubGlobalBtn');
        if (globalMobileActive) {
            gBtn.innerText = "Global Download: ON (Sabko Milega)";
            gBtn.style.background = "#10b981";
            gBtn.style.color = "#000";
        } else {
            gBtn.innerText = "Global Download: OFF (Sirf Allowed Ko)";
            gBtn.style.background = "#ef4444";
            gBtn.style.color = "#fff";
        }

        const tbody = document.getElementById('hubUsersTableBody');
        tbody.innerHTML = '';
        if (!data.users || data.users.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" style="padding:12px; color:#94a3b8;">Koi user record nahi mila. Upar username enter karke add karein.</td></tr>';
            return;
        }

        data.users.forEach(u => {
            const tr = document.createElement('tr');
            tr.style.borderBottom = "1px solid rgba(255,255,255,0.05)";
            const isAllowed = globalMobileActive || u.mobile_allowed;
            tr.innerHTML = `
                <td style="padding:12px; font-weight:bold; color:#f8fafc;">${u.username}</td>
                <td style="padding:12px; color:${u.days_left > 0 ? '#38bdf8' : '#f87171'}; font-weight:bold;">${u.days_left} Days Left</td>
                <td style="padding:12px; font-weight:bold; color:${isAllowed ? '#4ade80' : '#f87171'};">
                    ${isAllowed ? '? Download Active' : '? Coming Soon (Locked)'}
                </td>
                <td style="padding:12px;">
                    <button onclick="setSingleUser('${u.username}', ${!u.mobile_allowed})" style="padding:6px 12px; border-radius:4px; font-size:12px; font-weight:bold; cursor:pointer; background:${u.mobile_allowed ? '#ef4444' : '#10b981'}; color:#fff; border:none;">
                        ${u.mobile_allowed ? 'Block Karo' : 'Allow Karo'}
                    </button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch(e) { console.error(e); }
}

async function toggleGlobalSwitch() {
    await fetch(`/api/admin/toggle_global_mobile?enabled=${!globalMobileActive}`);
    loadHubData();
}

async function changeAccess(allow) {
    const user = document.getElementById('targetUserInputField').value.trim();
    if (!user) return alert("Pehle username enter karein!");
    await fetch(`/api/admin/set_user_mobile_access?username=${encodeURIComponent(user)}&allow=${allow}`);
    document.getElementById('targetUserInputField').value = '';
    loadHubData();
}

async function setSingleUser(user, allow) {
    await fetch(`/api/admin/set_user_mobile_access?username=${encodeURIComponent(user)}&allow=${allow}`);
    loadHubData();
}

window.addEventListener('DOMContentLoaded', loadHubData);
</script>
<!-- ================= END MOBILE CONTROL CENTER ================= -->
"""

files_to_inject = [
    os.path.join("server", "templates", "admin_portal.html"),
    os.path.join("templates", "admin_portal.html"),
    os.path.join("server", "templates", "admin.html")
]

for fp in files_to_inject:
    if os.path.exists(fp):
        with open(fp, "r", encoding="utf-8-sig") as f:
            content = f.read()
        if "adminMobileHub" not in content:
            if "</body>" in content:
                content = content.replace("</body>", f"{admin_box_ui}\n</body>")
            else:
                content += admin_box_ui
            with open(fp, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"[SUCCESS] Injected directly into {fp}")

print("Injection complete!")
