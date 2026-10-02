import os
import re

# File search
target_files = [
    os.path.join("server", "templates", "admin_portal.html"),
    os.path.join("templates", "admin_portal.html")
]

target_path = None
for p in target_files:
    if os.path.exists(p):
        target_path = p
        break

if not target_path:
    print("[ERROR] admin_portal.html nahi mili.")
    exit(1)

with open(target_path, "r", encoding="utf-8-sig") as f:
    content = f.read()

# 1. Clear any previously appended junk at bottom
if "<!-- ================= JARVIS ADMIN MOBILE CONTROL CENTER ================= -->" in content:
    content = content.split("<!-- ================= JARVIS ADMIN MOBILE CONTROL CENTER ================= -->")[0] + "</body></html>"

# 2. Inject Master Button right next to 'Home' in DOM
script_logic = """
<script>
let isGlobalDeactivated = true;

async function syncAdminData() {
    try {
        const res = await fetch('/api/admin/live_control_data');
        const data = await res.json();
        isGlobalDeactivated = !data.global_mobile;

        const masterBtn = document.getElementById('globalToggleMasterBtn');
        if (masterBtn) {
            masterBtn.innerText = isGlobalDeactivated ? "All are Deactivate" : "All Activate";
            masterBtn.style.background = isGlobalDeactivated ? "#ef4444" : "#10b981";
        }

        const tbody = document.querySelector('table tbody');
        if (tbody && data.users && data.users.length > 0) {
            tbody.innerHTML = '';
            data.users.forEach(u => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td style="padding:10px; border-bottom:1px solid #334155; font-weight:600;">${u.username}</td>
                    <td style="padding:10px; border-bottom:1px solid #334155; color:${u.days_left > 0 ? '#38bdf8' : '#f87171'}; font-weight:bold;">${u.days_left} Days Left</td>
                    <td style="padding:10px; border-bottom:1px solid #334155; text-align:center;">
                        <input type="checkbox" id="chk_${u.username}" ${u.mobile_allowed ? 'checked' : ''} style="transform: scale(1.3); cursor:pointer;">
                    </td>
                    <td style="padding:10px; border-bottom:1px solid #334155; text-align:center;">
                        <button onclick="submitUserPerm('${u.username}')" style="background:#00d2ff; color:#050b14; font-weight:bold; border:none; padding:6px 14px; border-radius:4px; cursor:pointer;">Submit</button>
                    </td>
                `;
                tbody.appendChild(tr);
            });
        }
    } catch(e) {}
}

async function toggleMasterGlobal() {
    await fetch(`/api/admin/toggle_global_mobile?enabled=${isGlobalDeactivated}`);
    syncAdminData();
}

async function submitUserPerm(username) {
    const chk = document.getElementById(`chk_${username}`);
    const allow = chk ? chk.checked : false;
    await fetch(`/api/admin/set_user_mobile_access?username=${encodeURIComponent(username)}&allow=${allow}`);
    alert(`Updated: ${username} mobile access set to ${allow ? 'Active' : 'Deactivated'}`);
    syncAdminData();
}

window.addEventListener('DOMContentLoaded', () => {
    // Locate Home element and attach button
    const links = Array.from(document.querySelectorAll('a, button, span'));
    const homeEl = links.find(el => el.textContent.trim().toLowerCase() === 'home');
    if (homeEl && !document.getElementById('globalToggleMasterBtn')) {
        const btn = document.createElement('button');
        btn.id = 'globalToggleMasterBtn';
        btn.innerText = 'All are Deactivate';
        btn.style.cssText = 'background:#ef4444; color:#fff; border:none; padding:7px 14px; border-radius:6px; font-weight:bold; cursor:pointer; margin-left:12px; font-size:13px; vertical-align:middle;';
        btn.onclick = toggleMasterGlobal;
        homeEl.insertAdjacentElement('afterend', btn);
    }
    syncAdminData();
});
</script>
"""

# Append script cleanly before </body>
if "submitUserPerm" not in content:
    if "</body>" in content:
        content = content.replace("</body>", f"{script_logic}\n</body>")
    else:
        content += script_logic

with open(target_path, "w", encoding="utf-8") as f:
    f.write(content)

print(f"[SUCCESS] Clean integration applied to {target_path}")
