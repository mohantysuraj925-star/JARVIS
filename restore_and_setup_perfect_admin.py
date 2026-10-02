import os
import re

files_to_check = [
    os.path.join("server", "templates", "admin_portal.html"),
    os.path.join("templates", "admin_portal.html"),
    os.path.join("server", "templates", "admin.html")
]

target_file = None
for f in files_to_check:
    if os.path.exists(f):
        target_file = f
        break

if target_file:
    with open(target_file, "r", encoding="utf-8-sig") as fp:
        html = fp.read()

    # 1. Niche ka faltu block delete karein
    if "<!-- ================= JARVIS ADMIN MOBILE CONTROL CENTER ================= -->" in html:
        p1 = html.split("<!-- ================= JARVIS ADMIN MOBILE CONTROL CENTER ================= -->")[0]
        p2 = html.split("<!-- ================= END MOBILE CONTROL CENTER ================= -->")[-1]
        html = p1 + p2

    # 2. Clean Logic & Header Button injection
    clean_patch = """
<script>
let isGlobalActive = false;

async function syncAdminData() {
    try {
        const res = await fetch('/api/admin/live_control_data');
        const data = await res.json();
        isGlobalActive = data.global_mobile;

        // Header Switch Button update
        const masterBtn = document.getElementById('globalToggleMasterBtn');
        if (masterBtn) {
            masterBtn.innerText = isGlobalActive ? "All Activate (Click to OFF)" : "All are Deactivate";
            masterBtn.style.background = isGlobalActive ? "#10b981" : "#ef4444";
        }

        // Table updates
        const tbody = document.getElementById('adminUsersListBody') || document.querySelector('table tbody');
        if (tbody && data.users && data.users.length > 0) {
            tbody.innerHTML = '';
            data.users.forEach(u => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td style="padding:10px; border-bottom:1px solid #334155; font-weight:bold;">${u.username}</td>
                    <td style="padding:10px; border-bottom:1px solid #334155; color:${u.days_left > 0 ? '#38bdf8' : '#f87171'}; font-weight:bold;">${u.days_left} Days Left</td>
                    <td style="padding:10px; border-bottom:1px solid #334155; text-align:center;">
                        <input type="checkbox" id="chk_${u.username}" ${u.mobile_allowed ? 'checked' : ''} style="transform: scale(1.4); cursor:pointer;">
                    </td>
                    <td style="padding:10px; border-bottom:1px solid #334155;">
                        <button onclick="submitUserPerm('${u.username}')" style="background:#00d2ff; color:#000; font-weight:bold; border:none; padding:5px 12px; border-radius:4px; cursor:pointer;">Submit</button>
                    </td>
                `;
                tbody.appendChild(tr);
            });
        }
    } catch(e) {}
}

async function toggleMasterGlobal() {
    await fetch(`/api/admin/toggle_global_mobile?enabled=${!isGlobalActive}`);
    syncAdminData();
}

async function submitUserPerm(username) {
    const chk = document.getElementById(`chk_${username}`);
    const allow = chk ? chk.checked : false;
    await fetch(`/api/admin/set_user_mobile_access?username=${encodeURIComponent(username)}&allow=${allow}`);
    alert(`Success: ${username} access set to ${allow ? 'Active' : 'Deactivated'}`);
    syncAdminData();
}

window.addEventListener('DOMContentLoaded', () => {
    // Exact Home Button identify karke bagal me toggle lagana
    const allLinks = Array.from(document.querySelectorAll('a, button'));
    const homeBtn = allLinks.find(el => el.innerText.trim().toLowerCase() === 'home');
    
    if (homeBtn && !document.getElementById('globalToggleMasterBtn')) {
        const btn = document.createElement('button');
        btn.id = 'globalToggleMasterBtn';
        btn.innerText = 'All are Deactivate';
        btn.style.cssText = 'background:#ef4444; color:#fff; border:none; padding:8px 16px; border-radius:6px; font-weight:bold; cursor:pointer; margin-left:14px; vertical-align:middle;';
        btn.onclick = toggleMasterGlobal;
        homeBtn.parentNode.insertBefore(btn, homeBtn.nextSibling);
    }
    syncAdminData();
});
</script>
"""
    if "submitUserPerm" not in html:
        if "</body>" in html:
            html = html.replace("</body>", f"{clean_patch}\n</body>")
        else:
            html += clean_patch
        with open(target_file, "w", encoding="utf-8") as fp:
            fp.write(html)
        print(f"[SUCCESS] Cleaned and restored successfully in {target_file}")
