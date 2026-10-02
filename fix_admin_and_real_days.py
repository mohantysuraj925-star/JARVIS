import os
import sqlite3
from datetime import datetime, timedelta

# 1. Database table ensure karein
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

# 2. Server routes update karein app.py me
app_path = os.path.join("server", "app.py")
if os.path.exists(app_path):
    with open(app_path, "r", encoding="utf-8") as f:
        code = f.read()

    new_api_logic = """
from datetime import datetime, timedelta
import sqlite3

def get_db_conn():
    return sqlite3.connect("portal_data.db")

@app.get("/api/admin/system_overview")
async def get_system_overview():
    conn = get_db_conn()
    c = conn.cursor()
    c.execute("SELECT key, value FROM global_settings WHERE key='global_mobile'")
    grow = c.fetchone()
    global_mob = (grow[1] == '1') if grow else False
    
    c.execute("SELECT username, created_at, trial_days, mobile_allowed FROM users")
    users_data = []
    now = datetime.utcnow()
    for row in c.fetchall():
        u_name, c_at, t_days, m_allow = row
        days_left = t_days
        if c_at:
            try:
                created_dt = datetime.fromisoformat(c_at)
                elapsed = (now - created_dt).total_seconds() / 86400.0
                days_left = max(0, int(t_days - elapsed))
            except:
                pass
        users_data.append({
            "username": u_name,
            "days_left": days_left,
            "mobile_allowed": bool(m_allow)
        })
    conn.close()
    return {"global_mobile": global_mob, "users": users_data}

@app.get("/api/user/real_subscription")
async def get_real_subscription(username: str):
    conn = get_db_conn()
    c = conn.cursor()
    c.execute("SELECT created_at, trial_days FROM users WHERE username=?", (username,))
    row = c.fetchone()
    now = datetime.utcnow()
    if not row:
        now_str = now.isoformat()
        c.execute("INSERT INTO users (username, created_at, trial_days, mobile_allowed) VALUES (?, ?, 10, 0)", (username, now_str))
        conn.commit()
        conn.close()
        return {"days_left": 10, "status": "active"}
    
    c_at, t_days = row
    if not c_at:
        c_at = now.isoformat()
        c.execute("UPDATE users SET created_at=? WHERE username=?", (c_at, username))
        conn.commit()
    
    created_dt = datetime.fromisoformat(c_at)
    elapsed_days = (now - created_dt).total_seconds() / 86400.0
    remaining = max(0, int(t_days - elapsed_days))
    conn.close()
    return {"days_left": remaining, "status": "active" if remaining > 0 else "expired"}
"""
    if "/api/admin/system_overview" not in code:
        code += "\n" + new_api_logic
        with open(app_path, "w", encoding="utf-8") as f:
            f.write(code)
        print("[OK] Real calculation and admin overview APIs added.")

# 3. Admin Panel UI me Section Add Karein
admin_candidates = [
    os.path.join("server", "templates", "admin_dashboard.html"),
    os.path.join("templates", "admin_dashboard.html"),
    os.path.join("server", "templates", "admin.html")
]

admin_html_snippet = """
<!-- MOBILE & DYNAMIC SUBSCRIPTION CONTROL PANEL -->
<div id="jarvisMobileAdminSection" style="margin: 25px auto; max-width: 900px; background: rgba(13, 20, 36, 0.95); border: 2px solid #00d2ff; border-radius: 12px; padding: 22px; box-shadow: 0 0 25px rgba(0,210,255,0.25); color: #fff; font-family: sans-serif;">
    <div style="display:flex; justify-content:space-between; align-items:center; border-bottom: 1px solid #1e293b; padding-bottom: 12px; margin-bottom: 18px;">
        <h2 style="margin:0; color:#00d2ff; font-size: 20px;">?? Mobile Access & Real Trial Monitor</h2>
        <button id="adminGlobalMobileBtn" onclick="toggleGlobalAccess()" style="background:#ef4444; color:#fff; border:none; padding: 8px 16px; border-radius: 6px; font-weight:bold; cursor:pointer;">Global Mobile: OFF</button>
    </div>

    <div style="display:flex; gap:10px; margin-bottom: 18px;">
        <input type="text" id="targetUserInput" placeholder="Enter username to toggle..." style="flex:1; padding: 10px; border-radius: 6px; border: 1px solid #334155; background: #0b132b; color: #fff;">
        <button onclick="setUserAccess(true)" style="background:#10b981; color:#000; border:none; padding: 10px 18px; border-radius: 6px; font-weight:bold; cursor:pointer;">Allow Mobile</button>
        <button onclick="setUserAccess(false)" style="background:#f43f5e; color:#fff; border:none; padding: 10px 18px; border-radius: 6px; font-weight:bold; cursor:pointer;">Block Mobile</button>
    </div>

    <div style="overflow-x:auto;">
        <table style="width:100%; border-collapse:collapse; text-align:left; font-size:14px;">
            <thead>
                <tr style="border-bottom: 1px solid #334155; color: #94a3b8;">
                    <th style="padding:10px;">Username</th>
                    <th style="padding:10px;">Trial Left (Real Calculation)</th>
                    <th style="padding:10px;">Mobile Download</th>
                    <th style="padding:10px;">Action</th>
                </tr>
            </thead>
            <tbody id="userOverviewTableBody">
                <tr><td colspan="4" style="padding:10px; color:#64748b;">Loading active users...</td></tr>
            </tbody>
        </table>
    </div>
</div>

<script>
let isGlobalMobileOn = false;

async function refreshAdminOverview() {
    try {
        const res = await fetch('/api/admin/system_overview');
        const data = await res.json();
        isGlobalMobileOn = data.global_mobile;
        
        const gBtn = document.getElementById('adminGlobalMobileBtn');
        if (isGlobalMobileOn) {
            gBtn.innerText = "Global Mobile: ON (Sabke Liye Active)";
            gBtn.style.background = "#10b981";
            gBtn.style.color = "#000";
        } else {
            gBtn.innerText = "Global Mobile: OFF (Controlled)";
            gBtn.style.background = "#ef4444";
            gBtn.style.color = "#fff";
        }

        const tbody = document.getElementById('userOverviewTableBody');
        tbody.innerHTML = '';
        if (!data.users || data.users.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" style="padding:10px; color:#64748b;">Abhi tak koi registered user record nahi mila.</td></tr>';
            return;
        }

        data.users.forEach(u => {
            const tr = document.createElement('tr');
            tr.style.borderBottom = "1px solid rgba(255,255,255,0.05)";
            tr.innerHTML = `
                <td style="padding:10px; font-weight:bold; color:#f8fafc;">${u.username}</td>
                <td style="padding:10px; color:${u.days_left > 0 ? '#38bdf8' : '#f87171'}; font-weight:bold;">${u.days_left} Days Left</td>
                <td style="padding:10px; color:${(isGlobalMobileOn || u.mobile_allowed) ? '#4ade80' : '#f87171'};">
                    ${(isGlobalMobileOn || u.mobile_allowed) ? '? Allowed' : '? Coming Soon (Locked)'}
                </td>
                <td style="padding:10px;">
                    <button onclick="quickToggle('${u.username}', ${!u.mobile_allowed})" style="padding:4px 10px; border-radius:4px; font-size:12px; cursor:pointer; background:${u.mobile_allowed ? '#ef4444' : '#10b981'}; color:#fff; border:none;">
                        ${u.mobile_allowed ? 'Block' : 'Allow'}
                    </button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch(e) { console.error(e); }
}

async function toggleGlobalAccess() {
    await fetch(`/api/admin/set_global_mobile?enabled=${!isGlobalMobileOn}`);
    refreshAdminOverview();
}

async function setUserAccess(allow) {
    const input = document.getElementById('targetUserInput');
    const user = input.value.trim();
    if (!user) return alert("Pehle username likho!");
    await fetch(`/api/admin/toggle_user_permission?username=${encodeURIComponent(user)}&allow=${allow}`);
    input.value = '';
    refreshAdminOverview();
}

async function quickToggle(user, allow) {
    await fetch(`/api/admin/toggle_user_permission?username=${encodeURIComponent(user)}&allow=${allow}`);
    refreshAdminOverview();
}

window.addEventListener('DOMContentLoaded', refreshAdminOverview);
</script>
"""

for target in admin_candidates:
    if os.path.exists(target):
        with open(target, "r", encoding="utf-8-sig") as f:
            content = f.read()
        if "jarvisMobileAdminSection" not in content:
            if "</body>" in content:
                content = content.replace("</body>", f"{admin_html_snippet}\n</body>")
            else:
                content += admin_html_snippet
            with open(target, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"[OK] Injected dynamic admin control box into {target}")

# 4. User Dashboard Dynamic Calculation Patch
user_candidates = [
    os.path.join("server", "templates", "user_dashboard.html"),
    os.path.join("templates", "user_dashboard.html")
]

user_patch_script = """
<script>
async function syncRealTrialData() {
    try {
        const u = localStorage.getItem('jarvis_user') || sessionStorage.getItem('jarvis_user') || 'default_user';
        const res = await fetch('/api/user/real_subscription?username=' + encodeURIComponent(u));
        const data = await res.json();
        
        // Find subscription / trial elements and update dynamically
        const allNodes = document.querySelectorAll('*');
        for (let el of allNodes) {
            if (el.children.length === 0 && (el.innerText.includes('Days Left') || el.innerText.includes('10 Days') || el.innerText.includes('Trial'))) {
                el.innerText = data.days_left + " Days Left (Active)";
                break;
            }
        }
    } catch(e) {}
}
window.addEventListener('DOMContentLoaded', syncRealTrialData);
</script>
"""

for target in user_candidates:
    if os.path.exists(target):
        with open(target, "r", encoding="utf-8-sig") as f:
            ucontent = f.read()
        if "syncRealTrialData" not in ucontent:
            ucontent = ucontent.replace("</body>", f"{user_patch_script}\n</body>")
            with open(target, "w", encoding="utf-8") as f:
                f.write(ucontent)
            print(f"[OK] Dynamic subscription updater injected into {target}")

print("[FINISHED] Setup complete.")
