import os
import re

# 1. Database table ensure karein
import sqlite3
conn = sqlite3.connect("portal_data.db")
c = conn.cursor()
c.execute("CREATE TABLE IF NOT EXISTS permissions (username TEXT PRIMARY KEY, mobile_allowed INTEGER DEFAULT 0)")
c.execute("CREATE TABLE IF NOT EXISTS global_settings (key TEXT PRIMARY KEY, value TEXT)")
c.execute("INSERT OR IGNORE INTO global_settings (key, value) VALUES ('global_mobile', '0')")
conn.commit()
conn.close()

# 2. Server me permissions check route jodna
app_file = r"server\app.py"
with open(app_file, "r", encoding="utf-8") as f:
    app_code = f.read()

backend_patch = """
@app.get("/api/admin/toggle_all_mobile")
async def toggle_all_mobile(enabled: bool):
    conn = sqlite3.connect("portal_data.db")
    c = conn.cursor()
    c.execute("INSERT INTO global_settings (key, value) VALUES ('global_mobile', ?) ON CONFLICT(key) DO UPDATE SET value=?", ('1' if enabled else '0', '1' if enabled else '0'))
    conn.commit()
    conn.close()
    return {"status": "success", "global_mobile": enabled}

@app.get("/api/admin/get_mobile_states")
async def get_mobile_states():
    conn = sqlite3.connect("portal_data.db")
    c = conn.cursor()
    c.execute("SELECT value FROM global_settings WHERE key='global_mobile'")
    grow = c.fetchone()
    c.execute("SELECT username, mobile_allowed FROM permissions")
    perms = {r[0]: bool(r[1]) for r in c.fetchall()}
    conn.close()
    return {"global_mobile": (grow[0] == '1') if grow else False, "permissions": perms}

@app.get("/api/admin/set_single_mobile")
async def set_single_mobile(username: str, allow: bool):
    conn = sqlite3.connect("portal_data.db")
    c = conn.cursor()
    c.execute("INSERT INTO permissions (username, mobile_allowed) VALUES (?, ?) ON CONFLICT(username) DO UPDATE SET mobile_allowed=?", (username, 1 if allow else 0, 1 if allow else 0))
    conn.commit()
    conn.close()
    return {"status": "success", "username": username, "allowed": allow}
"""

if "/api/admin/toggle_all_mobile" not in app_code:
    app_code += "\n" + backend_patch
    with open(app_file, "w", encoding="utf-8") as f:
        f.write(app_code)
    print("[SUCCESS] Backend APIs added to server/app.py")

# 3. Target File: templates/admin_portal.html
target = r"templates\admin_portal.html"
with open(target, "r", encoding="utf-8-sig") as f:
    html = f.read()

# Clear previous bottom box agar bacha ho
if "<!-- ================= JARVIS ADMIN MOBILE CONTROL CENTER ================= -->" in html:
    parts = html.split("<!-- ================= JARVIS ADMIN MOBILE CONTROL CENTER ================= -->")
    end_parts = parts[1].split("<!-- ================= END MOBILE CONTROL CENTER ================= -->")
    html = parts[0] + (end_parts[1] if len(end_parts) > 1 else "")

script_to_inject = """
<script>
let isAllDeactivated = true;

async function syncMobileAdminSystem() {
    try {
        const res = await fetch('/api/admin/get_mobile_states');
        const data = await res.json();
        isAllDeactivated = !data.global_mobile;

        // Header Button update
        const masterBtn = document.getElementById('globalToggleMasterBtn');
        if (masterBtn) {
            masterBtn.innerText = isAllDeactivated ? "All are Deactivate" : "All Activate";
            masterBtn.style.background = isAllDeactivated ? "#ef4444" : "#10b981";
        }

        // Table Rows check and inject checkbox
        const table = document.querySelector('table');
        if (!table) return;

        // Add Header Column if not present
        const headerRow = table.querySelector('thead tr') || table.querySelector('tr');
        if (headerRow && !document.getElementById('th_mobile_perm')) {
            const th = document.createElement('th');
            th.id = 'th_mobile_perm';
            th.innerText = 'Mobile App Access';
            th.style.padding = '10px';
            headerRow.appendChild(th);
        }

        // Add Checkbox + Submit in each row
        const rows = table.querySelectorAll('tbody tr');
        rows.forEach(tr => {
            const firstTd = tr.querySelector('td');
            if (!firstTd) return;
            const uname = firstTd.innerText.trim();
            if (!uname) return;

            let permTd = tr.querySelector('.td-mobile-perm');
            const isAllowed = data.permissions[uname] || false;

            if (!permTd) {
                permTd = document.createElement('td');
                permTd.className = 'td-mobile-perm';
                permTd.style.cssText = 'padding: 10px; text-align: center;';
                permTd.innerHTML = `
                    <label style="display:inline-flex; align-items:center; gap:8px; cursor:pointer;">
                        <input type="checkbox" id="chk_user_${uname}" ${isAllowed ? 'checked' : ''} style="transform: scale(1.3);">
                        <button onclick="submitUserAccess('${uname}')" style="background:#00d2ff; color:#050b14; font-weight:bold; border:none; padding:4px 10px; border-radius:4px; cursor:pointer;">Submit</button>
                    </label>
                `;
                tr.appendChild(permTd);
            } else {
                const chk = document.getElementById(`chk_user_${uname}`);
                if (chk && !chk.matches(':focus')) chk.checked = isAllowed;
            }
        });
    } catch(err) {}
}

async function toggleMasterGlobal() {
    await fetch(`/api/admin/toggle_all_mobile?enabled=${isAllDeactivated}`);
    syncMobileAdminSystem();
}

async function submitUserAccess(username) {
    const chk = document.getElementById(`chk_user_${username}`);
    const allow = chk ? chk.checked : false;
    await fetch(`/api/admin/set_single_mobile?username=${encodeURIComponent(username)}&allow=${allow}`);
    alert(`${username} access: ${allow ? 'Activated' : 'Deactivated'}`);
    syncMobileAdminSystem();
}

window.addEventListener('DOMContentLoaded', () => {
    // 1. Home button identify karein aur side me button lagayein
    const allLinks = Array.from(document.querySelectorAll('a, button, span'));
    const homeBtn = allLinks.find(el => el.innerText.trim().toLowerCase() === 'home');
    if (homeBtn && !document.getElementById('globalToggleMasterBtn')) {
        const btn = document.createElement('button');
        btn.id = 'globalToggleMasterBtn';
        btn.innerText = 'All are Deactivate';
        btn.style.cssText = 'background:#ef4444; color:#fff; border:none; padding:7px 15px; border-radius:6px; font-weight:bold; cursor:pointer; margin-left:12px; font-size:13px; vertical-align:middle;';
        btn.onclick = toggleMasterGlobal;
        homeBtn.insertAdjacentElement('afterend', btn);
    }

    // 2. Continuous table monitoring (nodes poll hote hi checkbox lag jaye)
    syncMobileAdminSystem();
    setInterval(syncMobileAdminSystem, 2500);
});
</script>
"""

if "syncMobileAdminSystem" not in html:
    if "</body>" in html:
        html = html.replace("</body>", f"{script_to_inject}\n</body>")
    else:
        html += script_to_inject

with open(target, "w", encoding="utf-8") as f:
    f.write(html)

print("[COMPLETE] templates/admin_portal.html successfully updated!")
