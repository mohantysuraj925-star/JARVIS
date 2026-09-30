import os

os.makedirs("static", exist_ok=True)

# 1. auth.js
with open("static/auth.js", "w", encoding="utf-8") as f:
    f.write("""let currentAuthMode = 'login';

function openAuthModal(mode) {
  currentAuthMode = mode;
  const t = document.getElementById('authTitle');
  const b = document.getElementById('authSubmitBtn');
  if (t) t.innerText = (mode === 'register') ? 'REGISTER NEW NODE' : 'OPERATOR LOGIN';
  if (b) b.innerText = (mode === 'register') ? 'CREATE OPERATOR' : 'AUTHENTICATE';
  const m = document.getElementById('cyberAuthModal');
  if (m) m.style.display = 'flex';
}

function closeAuthModal() {
  const m = document.getElementById('cyberAuthModal');
  if (m) m.style.display = 'none';
}

async function submitAuth() {
  const u = document.getElementById('authUsername').value.trim();
  const p = document.getElementById('authPassword').value.trim();
  if (!u || !p) {
    alert('Please enter username and password.');
    return;
  }

  const endpoint = (currentAuthMode === 'register') ? '/api/admin/create-user' : '/api/heartbeat';
  try {
    const res = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: u, password: p })
    });

    if (res.ok) {
      closeAuthModal();
      alert(currentAuthMode === 'register' ? 'Node Registered! 10-Day Trial Active.' : 'Handshake Verified!');
      location.reload();
    } else {
      alert('Authentication Failed');
    }
  } catch (err) {
    alert('Server Connection Error');
  }
}

document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('button, a').forEach(el => {
    const txt = (el.innerText || '').toLowerCase();
    if (txt.includes('login') || txt.includes('sign in')) {
      el.onclick = (e) => { e.preventDefault(); openAuthModal('login'); };
    }
    if (txt.includes('register') || txt.includes('sign up')) {
      el.onclick = (e) => { e.preventDefault(); openAuthModal('register'); };
    }
  });
});
""")

# 2. admin_actions.js
with open("static/admin_actions.js", "w", encoding="utf-8") as f:
    f.write("""async function refreshAdminState() {
    try {
        const [mRes, nRes] = await Promise.all([
            fetch('/api/admin/metrics'),
            fetch('/api/admin/nodes')
        ]);

        if (mRes.ok) {
            const m = await mRes.json();
            const elTotal = document.getElementById('metric-total-users') || document.querySelector('[data-metric="total"]');
            const elActive = document.getElementById('metric-active-users') || document.querySelector('[data-metric="active"]');
            const elWin = document.getElementById('metric-win-dl') || document.querySelector('[data-metric="win"]');
            const elApk = document.getElementById('metric-apk-dl') || document.querySelector('[data-metric="apk"]');

            if (elTotal) elTotal.innerText = m.total_users ?? 0;
            if (elActive) elActive.innerText = m.active_users ?? 0;
            if (elWin) elWin.innerText = m.win_downloads ?? 0;
            if (elApk) elApk.innerText = m.apk_downloads ?? 0;
        }

        if (nRes.ok) {
            const nodes = await nRes.json();
            renderNodesTable(nodes);
        }
    } catch(e) {
        console.error("Sync error:", e);
    }
}

function renderNodesTable(nodes) {
    const tableBody = document.getElementById('nodesTableBody') || document.querySelector('tbody');
    if (!tableBody) return;

    tableBody.innerHTML = '';

    if (!nodes || nodes.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="7" style="text-align:center; padding:20px; color:#64748b;">No active operator nodes found.</td></tr>';
        return;
    }

    nodes.forEach(u => {
        const isOnline = (Date.now() / 1000 - (u.last_seen || 0)) < 45;
        const statusBadge = u.is_active
            ? (isOnline ? '<span style="color:#10b981; font-weight:bold;">● ONLINE</span>' : '<span style="color:#00f0ff;">STANDBY</span>')
            : '<span style="color:#ef4444; font-weight:bold;">BLOCKED</span>';

        const lifeText = u.is_unlimited 
            ? '<span style="color:#a855f7; font-weight:bold; font-size:16px;">∞ UNLIMITED</span>' 
            : `${u.days_remaining} Days`;

        const calText = (u.access_start_date && u.access_end_date)
            ? `${u.access_start_date} → ${u.access_end_date}`
            : '<span style="color:#64748b;">No Date Lock</span>';

        const timeText = (u.daily_time_start && u.daily_time_end)
            ? `${u.daily_time_start} - ${u.daily_time_end}`
            : '<span style="color:#64748b;">24/7 Access</span>';

        const tr = document.createElement('tr');
        tr.style.borderBottom = '1px solid rgba(255,255,255,0.08)';
        tr.innerHTML = `
            <td style="padding:12px 10px;">#${u.id}</td>
            <td style="padding:12px 10px; font-weight:bold; color:#00f0ff;">${u.username}</td>
            <td style="padding:12px 10px;">${statusBadge}</td>
            <td style="padding:12px 10px; font-weight:bold;">${lifeText}</td>
            <td style="padding:12px 10px; font-size:12px; font-family:monospace;">${calText}</td>
            <td style="padding:12px 10px; font-size:12px; font-family:monospace;">${timeText}</td>
            <td style="padding:12px 10px;">
                <div style="display:flex; gap:6px; flex-wrap:wrap; align-items:center;">
                    <button onclick="userAction(${u.id}, 'add_days')" style="background:#0284c7; color:#fff; border:none; padding:6px 10px; border-radius:4px; font-weight:bold; cursor:pointer;" title="Add 5 Days">+5D</button>
                    <button onclick="userAction(${u.id}, 'sub_days')" style="background:#ea580c; color:#fff; border:none; padding:6px 10px; border-radius:4px; font-weight:bold; cursor:pointer;" title="Subtract 5 Days">-5D</button>
                    <button onclick="userAction(${u.id}, 'unlimited')" style="background:#7c3aed; color:#fff; border:none; padding:6px 12px; border-radius:4px; font-weight:bold; cursor:pointer;" title="Make Unlimited">∞</button>
                    <button onclick="openLockModal(${u.id}, '${u.access_start_date || ''}', '${u.access_end_date || ''}', '${u.daily_time_start || ''}', '${u.daily_time_end || ''}')" style="background:#0f766e; color:#fff; border:none; padding:6px 10px; border-radius:4px; font-weight:bold; cursor:pointer;" title="Set Date/Time Locks">📅</button>
                    <button onclick="userAction(${u.id}, 'delete')" style="background:#dc2626; color:#fff; border:none; padding:6px 10px; border-radius:4px; font-weight:bold; cursor:pointer;" title="Delete Node">🗑️</button>
                </div>
            </td>
        `;
        tableBody.appendChild(tr);
    });
}

async function userAction(userId, action) {
    let payload = { user_id: userId };
    if (action === 'add_days') payload.delta_days = 5;
    if (action === 'sub_days') payload.delta_days = -5;
    if (action === 'unlimited') payload.is_unlimited = 1;
    if (action === 'delete') {
        if (!confirm('Are you sure you want to delete this user?')) return;
        payload.delete = true;
    }

    try {
        const res = await fetch('/api/admin/modify-lifecycle', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        if (res.ok) {
            refreshAdminState();
        } else {
            alert('Failed to execute command');
        }
    } catch(e) {
        alert('Server connection error');
    }
}

function openLockModal(id, sDate, eDate, sTime, eTime) {
    let m = document.getElementById('quickLockModal');
    if (!m) {
        m = document.createElement('div');
        m.id = 'quickLockModal';
        m.style.cssText = 'position:fixed; inset:0; background:rgba(2,6,23,0.85); backdrop-filter:blur(8px); display:flex; justify-content:center; align-items:center; z-index:999999;';
        m.innerHTML = `
            <div style="background:#0b1329; border:1px solid #00f0ff; border-radius:12px; padding:24px; max-width:420px; width:90%; color:#fff; box-shadow:0 0 30px rgba(0,240,255,0.25);">
                <h3 style="color:#00f0ff; margin-bottom:15px; font-size:18px;">Set Access Window & Time Lock</h3>
                <input type="hidden" id="modalUid">
                <div style="margin-bottom:12px;">
                    <label style="font-size:12px; color:#94a3b8;">Calendar Date Range (Start -> End)</label>
                    <div style="display:flex; gap:8px; margin-top:4px;">
                        <input type="date" id="mSDate" style="flex:1; background:#040814; border:1px solid #334155; color:#fff; padding:6px; border-radius:6px;">
                        <input type="date" id="mEDate" style="flex:1; background:#040814; border:1px solid #334155; color:#fff; padding:6px; border-radius:6px;">
                    </div>
                </div>
                <div style="margin-bottom:20px;">
                    <label style="font-size:12px; color:#94a3b8;">Daily Operational Clock (Start -> End)</label>
                    <div style="display:flex; gap:8px; margin-top:4px;">
                        <input type="time" id="mSTime" style="flex:1; background:#040814; border:1px solid #334155; color:#fff; padding:6px; border-radius:6px;">
                        <input type="time" id="mETime" style="flex:1; background:#040814; border:1px solid #334155; color:#fff; padding:6px; border-radius:6px;">
                    </div>
                </div>
                <div style="display:flex; justify-content:flex-end; gap:8px;">
                    <button onclick="document.getElementById('quickLockModal').style.display='none'" style="background:#334155; color:#fff; border:none; padding:8px 14px; border-radius:6px; cursor:pointer;">Cancel</button>
                    <button onclick="submitLocks()" style="background:#00f0ff; color:#030712; font-weight:bold; border:none; padding:8px 16px; border-radius:6px; cursor:pointer;">Save Restrictions</button>
                </div>
            </div>
        `;
        document.body.appendChild(m);
    }

    document.getElementById('modalUid').value = id;
    document.getElementById('mSDate').value = sDate;
    document.getElementById('mEDate').value = eDate;
    document.getElementById('mSTime').value = sTime;
    document.getElementById('mETime').value = eTime;
    m.style.display = 'flex';
}

async function submitLocks() {
    const uid = document.getElementById('modalUid').value;
    const payload = {
        user_id: uid,
        start_date: document.getElementById('mSDate').value || null,
        end_date: document.getElementById('mEDate').value || null,
        start_time: document.getElementById('mSTime').value || null,
        end_time: document.getElementById('mETime').value || null
    };

    const res = await fetch('/api/admin/modify-lifecycle', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    });

    if (res.ok) {
        document.getElementById('quickLockModal').style.display = 'none';
        refreshAdminState();
    } else {
        alert('Could not update date/time locks.');
    }
}

setInterval(refreshAdminState, 3500);
document.addEventListener('DOMContentLoaded', refreshAdminState);
""")

print("Clean JS files written successfully!")