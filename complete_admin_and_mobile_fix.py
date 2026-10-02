import os
import sqlite3

# 1. Database table ensure karein
conn = sqlite3.connect("portal_data.db")
c = conn.cursor()
c.execute("""
CREATE TABLE IF NOT EXISTS permissions (
    username TEXT PRIMARY KEY,
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

# 2. Server API routes add karein app.py me
app_path = os.path.join("server", "app.py")
if os.path.exists(app_path):
    with open(app_path, "r", encoding="utf-8") as f:
        code = f.read()

    api_code = """
import sqlite3

@app.get("/api/admin/get_all_users_permissions")
async def get_all_users_permissions():
    conn = sqlite3.connect("portal_data.db")
    c = conn.cursor()
    c.execute("SELECT username, mobile_allowed FROM permissions")
    rows = c.fetchall()
    c.execute("SELECT value FROM global_settings WHERE key='global_mobile'")
    g = c.fetchone()
    conn.close()
    return {
        "global_mobile": (g[0] == '1') if g else False,
        "users": [{"username": r[0], "allowed": bool(r[1])} for r in rows]
    }

@app.get("/api/admin/set_global_mobile")
async def set_global_mobile(enabled: bool):
    conn = sqlite3.connect("portal_data.db")
    c = conn.cursor()
    c.execute("INSERT INTO global_settings (key, value) VALUES ('global_mobile', ?) ON CONFLICT(key) DO UPDATE SET value=?", ('1' if enabled else '0', '1' if enabled else '0'))
    conn.commit()
    conn.close()
    return {"status": "success", "global_mobile": enabled}

@app.get("/api/admin/toggle_user_permission")
async def toggle_user_permission(username: str, allow: bool):
    conn = sqlite3.connect("portal_data.db")
    c = conn.cursor()
    c.execute("INSERT INTO permissions (username, mobile_allowed) VALUES (?, ?) ON CONFLICT(username) DO UPDATE SET mobile_allowed=?", (username, 1 if allow else 0, 1 if allow else 0))
    conn.commit()
    conn.close()
    return {"status": "success", "username": username, "allowed": allow}

@app.get("/api/user/can_download_mobile")
async def can_download_mobile(username: str = ""):
    conn = sqlite3.connect("portal_data.db")
    c = conn.cursor()
    c.execute("SELECT value FROM global_settings WHERE key='global_mobile'")
    g = c.fetchone()
    if g and g[0] == '1':
        conn.close()
        return {"allowed": True}
    if username:
        c.execute("SELECT mobile_allowed FROM permissions WHERE username=?", (username,))
        row = c.fetchone()
        if row and row[0] == 1:
            conn.close()
            return {"allowed": True}
    conn.close()
    return {"allowed": False}
"""
    if "/api/admin/get_all_users_permissions" not in code:
        code += "\n" + api_code
        with open(app_path, "w", encoding="utf-8") as f:
            f.write(code)
        print("[OK] Backend admin permission APIs added.")

# 3. Admin Panel UI me Section Add Karein
admin_files = [os.path.join("server", "templates", "admin_dashboard.html"), os.path.join("templates", "admin_dashboard.html"), os.path.join("server", "templates", "admin.html")]
admin_target = None
for p in admin_files:
    if os.path.exists(p):
        admin_target = p
        break

admin_box_html = """
<!-- MOBILE PERMISSION MANAGEMENT PANEL -->
<div style="background: rgba(10, 25, 47, 0.9); border: 1px solid #00d2ff; padding: 20px; margin: 20px 0; border-radius: 12px; box-shadow: 0 0 15px rgba(0, 210, 255, 0.2);">
    <h3 style="color: #00d2ff; margin-bottom: 12px; font-size: 18px;">?? Mobile App Download Control Center</h3>
    
    <div style="display: flex; align-items: center; justify-content: space-between; padding: 12px; background: rgba(255,255,255,0.05); border-radius: 8px; margin-bottom: 15px;">
        <span style="color: #fff; font-size: 14px;">Sabhi Ke Liye Mobile Download Kholo (Global):</span>
        <button id="globalMobileToggleBtn" onclick="toggleGlobalMobile()" style="padding: 8px 18px; border-radius: 6px; font-weight: bold; cursor: pointer; border: none; background: #ff3344; color: #fff;">OFF (Sabke Liye Band)</button>
    </div>

    <div style="display: flex; gap: 10px; margin-bottom: 15px;">
        <input type="text" id="targetUsernameInput" placeholder="Kisi khas user ka username likho..." style="flex: 1; padding: 10px; border-radius: 6px; border: 1px solid #334155; background: #0b132b; color: #fff;">
        <button onclick="grantUserAccess(true)" style="background: #00e676; color: #000; font-weight: bold; border: none; padding: 10px 18px; border-radius: 6px; cursor: pointer;">Allow Karo</button>
        <button onclick="grantUserAccess(false)" style="background: #ff5252; color: #fff; font-weight: bold; border: none; padding: 10px 18px; border-radius: 6px; cursor: pointer;">Block Karo</button>
    </div>

    <div style="max-height: 160px; overflow-y: auto; background: rgba(0,0,0,0.3); border-radius: 6px; padding: 10px;">
        <div style="color: #8892b0; font-size: 12px; margin-bottom: 6px;">Special Allowed Users:</div>
        <ul id="allowedUsersList" style="list-style: none; padding: 0; margin: 0; color: #64ffda; font-size: 13px;">
            <li>Loading permissions...</li>
        </ul>
    </div>
</div>

<script>
let currentGlobalStatus = false;

async function loadAdminPermissions() {
    try {
        const res = await fetch('/api/admin/get_all_users_permissions');
        const data = await res.json();
        currentGlobalStatus = data.global_mobile;
        
        const gBtn = document.getElementById('globalMobileToggleBtn');
        if (currentGlobalStatus) {
            gBtn.innerText = "ON (Sabke Liye Khula Hai)";
            gBtn.style.background = "#00e676";
            gBtn.style.color = "#000";
        } else {
            gBtn.innerText = "OFF (Sirf Allowed Ko Milega)";
            gBtn.style.background = "#ff3344";
            gBtn.style.color = "#fff";
        }

        const listEl = document.getElementById('allowedUsersList');
        listEl.innerHTML = '';
        const allowedOnly = data.users.filter(u => u.allowed);
        if (allowedOnly.length === 0) {
            listEl.innerHTML = '<li style="color: #718096;">Kisi user ko alag se allow nahi kiya gaya hai.</li>';
        } else {
            allowedOnly.forEach(u => {
                listEl.innerHTML += `<li style="padding: 4px 0; border-bottom: 1px solid rgba(255,255,255,0.05); display: flex; justify-content: space-between;">
                    <span>? ${u.username}</span>
                    <a href="javascript:void(0)" onclick="removeUserAccess('${u.username}')" style="color: #ff5252; text-decoration: none; font-size: 12px;">Hatao</a>
                </li>`;
            });
        }
    } catch(err) { console.error(err); }
}

async function toggleGlobalMobile() {
    const nextState = !currentGlobalStatus;
    await fetch(`/api/admin/set_global_mobile?enabled=${nextState}`);
    loadAdminPermissions();
}

async function grantUserAccess(allow) {
    const user = document.getElementById('targetUsernameInput').value.trim();
    if (!user) return alert("Pehle username enter karo!");
    await fetch(`/api/admin/toggle_user_permission?username=${encodeURIComponent(user)}&allow=${allow}`);
    document.getElementById('targetUsernameInput').value = '';
    loadAdminPermissions();
}

async function removeUserAccess(user) {
    await fetch(`/api/admin/toggle_user_permission?username=${encodeURIComponent(user)}&allow=false`);
    loadAdminPermissions();
}

window.addEventListener('DOMContentLoaded', loadAdminPermissions);
</script>
"""

if admin_target:
    with open(admin_target, "r", encoding="utf-8-sig") as f:
        content = f.read()
    if "Mobile App Download Control Center" not in content:
        # Body ke andar ya pehle container ke andar daal do
        if "</body>" in content:
            content = content.replace("</body>", f"{admin_box_html}\n</body>")
        else:
            content += admin_box_html
        with open(admin_target, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"[OK] Admin panel UI updated at {admin_target}")

# 4. User Dashboard par Button ka Text & Coming Soon link karna
user_files = [os.path.join("server", "templates", "user_dashboard.html"), os.path.join("templates", "user_dashboard.html")]
for uf in user_files:
    if os.path.exists(uf):
        with open(uf, "r", encoding="utf-8-sig") as f:
            ucontent = f.read()
            
        guard_script = """
<script>
async function enforceLiveMobileState() {
    try {
        const username = localStorage.getItem('jarvis_user') || sessionStorage.getItem('jarvis_user') || '';
        const res = await fetch('/api/user/can_download_mobile?username=' + encodeURIComponent(username));
        const data = await res.json();
        
        // Find mobile/android button
        const all = Array.from(document.querySelectorAll('button, a'));
        const mBtn = all.find(el => {
            const txt = (el.innerText || '').toLowerCase();
            return txt.includes('android') || txt.includes('companion') || txt.includes('mobile');
        });

        if (mBtn) {
            if (!data.allowed) {
                mBtn.innerText = "Mobile App (Coming Soon)";
                mBtn.style.opacity = "0.5";
                mBtn.style.filter = "grayscale(1)";
                mBtn.onclick = function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    alert("Mobile APK testing mode me hai! Admin access milne par download shuru hoga.");
                    return false;
                };
            } else {
                mBtn.innerText = "Download Mobile 3D App";
                mBtn.style.opacity = "1";
                mBtn.style.filter = "none";
                mBtn.onclick = function() {
                    window.location.href = '/downloads/JARVIS_Companion.apk';
                };
            }
        }
    } catch(e) {}
}
window.addEventListener('DOMContentLoaded', enforceLiveMobileState);
</script>
"""
        if "enforceLiveMobileState" not in ucontent:
            ucontent = ucontent.replace("</body>", f"{guard_script}\n</body>")
            with open(uf, "w", encoding="utf-8") as f:
                f.write(ucontent)
            print(f"[OK] User dashboard safe download script attached to {uf}")

print("[DONE] Sabhi files successfully inject ho chuki hain!")
