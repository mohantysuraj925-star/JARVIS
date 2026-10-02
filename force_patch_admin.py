import os

target = r"templates\admin_portal.html"
if not os.path.exists(target):
    print("File nahi mili:", target)
    exit(1)

with open(target, "r", encoding="utf-8-sig") as f:
    html = f.read()

# Header injection: Home link ke turant baad button jodna
header_btn = """
<button id="globalToggleMasterBtn" onclick="toggleMasterGlobal()" style="background:#ef4444; color:#fff; border:none; padding:6px 14px; border-radius:6px; font-weight:bold; cursor:pointer; margin-left:12px; font-size:13px;">
    All are Deactivate
</button>
"""

# Script logic seedha head/body me daalna
script_code = """
<script>
let isAllDeactivated = true;

async function syncAdminMobile() {
    try {
        const res = await fetch('/api/admin/get_mobile_states');
        const data = await res.json();
        isAllDeactivated = !data.global_mobile;

        const masterBtn = document.getElementById('globalToggleMasterBtn');
        if (masterBtn) {
            masterBtn.innerText = isAllDeactivated ? "All are Deactivate" : "All Activate";
            masterBtn.style.background = isAllDeactivated ? "#ef4444" : "#10b981";
        }

        const table = document.querySelector('table');
        if (!table) return;

        const theadRow = table.querySelector('thead tr') || table.querySelector('tr');
        if (theadRow && !document.getElementById('col_mobile_access')) {
            const th = document.createElement('th');
            th.id = 'col_mobile_access';
            th.innerText = 'Mobile App Access';
            th.style.padding = '10px';
            theadRow.appendChild(th);
        }

        const tbodyRows = table.querySelectorAll('tbody tr');
        tbodyRows.forEach(tr => {
            const firstCell = tr.querySelector('td');
            if (!firstCell) return;
            const uname = firstCell.innerText.trim();
            if (!uname) return;

            let cell = tr.querySelector('.cell-perm');
            const allowed = data.permissions && data.permissions[uname];

            if (!cell) {
                cell = document.createElement('td');
                cell.className = 'cell-perm';
                cell.style.cssText = 'padding:8px; text-align:center; white-space:nowrap;';
                cell.innerHTML = `
                    <input type="checkbox" id="chk_${uname}" ${allowed ? 'checked' : ''} style="transform:scale(1.2); margin-right:8px; cursor:pointer;">
                    <button onclick="submitUserPerm('${uname}')" style="background:#00d2ff; color:#000; border:none; padding:4px 10px; border-radius:4px; font-weight:bold; cursor:pointer;">Submit</button>
                `;
                tr.appendChild(cell);
            }
        });
    } catch(e) {}
}

async function toggleMasterGlobal() {
    await fetch(`/api/admin/toggle_all_mobile?enabled=${isAllDeactivated}`);
    syncAdminMobile();
}

async function submitUserPerm(username) {
    const chk = document.getElementById(`chk_${username}`);
    const allow = chk ? chk.checked : false;
    await fetch(`/api/admin/set_single_mobile?username=${encodeURIComponent(username)}&allow=${allow}`);
    alert(`Status updated for ${username}: ${allow ? 'Active' : 'Deactivated'}`);
    syncAdminMobile();
}

document.addEventListener('DOMContentLoaded', () => {
    syncAdminMobile();
    setInterval(syncAdminMobile, 3000);
});
</script>
"""

# Home text ke baad button lagana
if "globalToggleMasterBtn" not in html:
    # Anchor tag jisme Home ho
    import re
    match = re.search(r'(<a[^>]*>[^<]*Home[^<]*</a>)', html, re.IGNORECASE)
    if match:
        original = match.group(1)
        html = html.replace(original, original + header_btn)

if "syncAdminMobile" not in html:
    html = html.replace("</head>", f"{script_code}\n</head>")

with open(target, "w", encoding="utf-8") as f:
    f.write(html)

print("[DONE] templates/admin_portal.html directly patched!")
