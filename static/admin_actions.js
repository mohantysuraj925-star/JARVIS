async function refreshMasterConsole() {
    try {
        const [mRes, nRes] = await Promise.all([
            fetch('/api/admin/metrics'),
            fetch('/api/admin/nodes')
        ]);

        if (mRes.ok) {
            const m = await mRes.json();
            
            // Console ke 4 box stats ko direct number update karein
            const allElements = document.querySelectorAll('div, span, h2, h3, p');
            allElements.forEach(el => {
                const label = (el.innerText || '').trim();
                const parent = el.closest('div');
                if (!parent) return;

                if (label === 'TOTAL USERS') {
                    const val = parent.querySelector('.text-2xl, .text-3xl, h2, h3, p, span:not(:first-child)');
                    if (val && val !== el) val.innerText = m.total_users;
                } else if (label === 'ACTIVE USERS') {
                    const val = parent.querySelector('.text-2xl, .text-3xl, h2, h3, p, span:not(:first-child)');
                    if (val && val !== el) val.innerText = m.active_users;
                } else if (label === 'WINDOWS DOWNLOADS') {
                    const val = parent.querySelector('.text-2xl, .text-3xl, h2, h3, p, span:not(:first-child)');
                    if (val && val !== el) val.innerText = m.win_downloads;
                } else if (label === 'ANDROID DOWNLOADS') {
                    const val = parent.querySelector('.text-2xl, .text-3xl, h2, h3, p, span:not(:first-child)');
                    if (val && val !== el) val.innerText = m.apk_downloads;
                }
            });
        }

        if (nRes.ok) {
            const nodes = await nRes.json();
            renderModularCards(nodes);
        }
    } catch(e) {}
}

function renderModularCards(nodes) {
    const container = document.getElementById('masterNodesContainer');
    if (!container) return;

    if (!nodes || nodes.length === 0) {
        container.innerHTML = `
            <div style="grid-column: 1 / -1; padding: 24px; text-align: center; border: 1px dashed rgba(0, 240, 255, 0.2); border-radius: 8px; color: #64748b; font-size: 13px;">
                No registered operator nodes found in database.
            </div>
        `;
        return;
    }

    container.innerHTML = '';
    nodes.forEach(u => {
        const isOnline = (Date.now() / 1000 - (u.last_seen || 0)) < 90;
        const statusBadge = u.is_active
            ? (isOnline ? '<span style="color:#10b981; font-weight:700; font-size:11px;">● ONLINE</span>' : '<span style="color:#00f0ff; font-weight:600; font-size:11px;">STANDBY</span>')
            : '<span style="color:#ef4444; font-weight:700; font-size:11px;">BLOCKED</span>';

        const life = u.is_unlimited
            ? '<span style="color:#a855f7; font-weight:700; font-size:13px;">UNLIMITED</span>'
            : `<span style="color:#00f0ff; font-weight:700; font-size:13px;">${u.days_remaining}</span> <span style="font-size:10px; color:#64748b;">DAYS</span>`;

        const card = document.createElement('div');
        card.style.cssText = `
            background: rgba(15, 23, 42, 0.75);
            border: 1px solid rgba(0, 240, 255, 0.2);
            border-radius: 8px;
            padding: 14px;
            display: flex;
            flex-direction: column;
            gap: 10px;
            backdrop-filter: blur(10px);
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.4);
        `;

        card.innerHTML = `
            <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid rgba(255,255,255,0.06); padding-bottom:8px;">
                <div style="display:flex; align-items:center; gap:6px;">
                    <span style="font-family:monospace; color:#64748b; font-size:11px;">#${u.id}</span>
                    <span style="font-weight:700; color:#f8fafc; font-size:14px;">${u.username}</span>
                </div>
                ${statusBadge}
            </div>

            <div style="display:grid; grid-template-columns: repeat(3, 1fr); gap:8px; background:rgba(2,6,23,0.5); padding:8px; border-radius:6px; font-size:11px;">
                <div>
                    <div style="color:#64748b; font-size:9px; text-transform:uppercase;">Allocation</div>
                    <div>${life}</div>
                </div>
                <div>
                    <div style="color:#64748b; font-size:9px; text-transform:uppercase;">Calendar</div>
                    <div style="font-family:monospace; color:#cbd5e1; font-size:10px;">${u.access_start_date || 'UNRESTRICTED'}</div>
                </div>
                <div>
                    <div style="color:#64748b; font-size:9px; text-transform:uppercase;">Daily Window</div>
                    <div style="font-family:monospace; color:#cbd5e1; font-size:10px;">${u.daily_time_start ? `${u.daily_time_start}-${u.daily_time_end}` : '24/7 WINDOW'}</div>
                </div>
            </div>

            <div style="display:flex; gap:6px; align-items:center; justify-content:flex-end; margin-top:4px;">
                <button onclick="controlAction(${u.id}, 'add_5')" style="display:flex; align-items:center; gap:3px; background:rgba(2,132,199,0.2); border:1px solid #0284c7; color:#38bdf8; padding:5px 8px; border-radius:4px; font-size:11px; font-weight:700; cursor:pointer;" title="Add 5 Days">
                    <i data-lucide="plus" style="width:12px; height:12px;"></i> 5D
                </button>
                <button onclick="controlAction(${u.id}, 'sub_5')" style="display:flex; align-items:center; gap:3px; background:rgba(234,88,12,0.2); border:1px solid #ea580c; color:#fb923c; padding:5px 8px; border-radius:4px; font-size:11px; font-weight:700; cursor:pointer;" title="Subtract 5 Days">
                    <i data-lucide="minus" style="width:12px; height:12px;"></i> 5D
                </button>
                <button onclick="controlAction(${u.id}, 'unlim')" style="display:flex; align-items:center; background:rgba(124,58,237,0.2); border:1px solid #7c3aed; color:#c084fc; padding:5px 9px; border-radius:4px; font-size:11px; font-weight:700; cursor:pointer;" title="Toggle Unlimited">
                    <i data-lucide="infinity" style="width:14px; height:14px;"></i>
                </button>
                <button onclick="openRestrictionsModal(${u.id}, '${u.access_start_date || ''}', '${u.access_end_date || ''}', '${u.daily_time_start || ''}', '${u.daily_time_end || ''}')" style="display:flex; align-items:center; background:rgba(15,118,110,0.2); border:1px solid #0f766e; color:#2dd4bf; padding:5px 8px; border-radius:4px; font-size:11px; cursor:pointer;" title="Set Date/Time Locks">
                    <i data-lucide="calendar" style="width:12px; height:12px;"></i>
                </button>
                <button onclick="controlAction(${u.id}, 'del')" style="display:flex; align-items:center; background:rgba(220,38,38,0.2); border:1px solid #dc2626; color:#f87171; padding:5px 8px; border-radius:4px; font-size:11px; cursor:pointer;" title="Terminate Node">
                    <i data-lucide="trash-2" style="width:12px; height:12px;"></i>
                </button>
            </div>
        `;
        container.appendChild(card);
    });

    if (window.lucide) lucide.createIcons();
}

async function controlAction(uid, act) {
    let p = { user_id: uid };
    if (act === 'add_5') p.delta_days = 5;
    if (act === 'sub_5') p.delta_days = -5;
    if (act === 'unlim') p.is_unlimited = 1;
    if (act === 'del') {
        if (!confirm('Are you sure you want to terminate this operator node?')) return;
        p.delete = true;
    }

    const res = await fetch('/api/admin/modify-lifecycle', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(p)
    });
    if (res.ok) refreshMasterConsole();
}

function openRestrictionsModal(uid, sDate, eDate, sTime, eTime) {
    let modal = document.getElementById('lifecycleRestrictionModal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'lifecycleRestrictionModal';
        modal.style.cssText = 'position:fixed; inset:0; background:rgba(2,6,23,0.85); backdrop-filter:blur(8px); display:flex; justify-content:center; align-items:center; z-index:999999;';
        modal.innerHTML = `
            <div style="background:#0b1329; border:1px solid #00f0ff; border-radius:10px; padding:22px; max-width:400px; width:90%; color:#fff; box-shadow:0 0 30px rgba(0,240,255,0.25);">
                <div style="display:flex; align-items:center; gap:8px; margin-bottom:14px; color:#00f0ff;">
                    <i data-lucide="sliders" style="width:16px; height:16px;"></i>
                    <h3 style="margin:0; font-size:15px; letter-spacing:0.5px; text-transform:uppercase;">Access Windows</h3>
                </div>
                <input type="hidden" id="rstUid">
                <div style="margin-bottom:12px;">
                    <label style="font-size:11px; color:#94a3b8; text-transform:uppercase;">Calendar Interval</label>
                    <div style="display:flex; gap:8px; margin-top:4px;">
                        <input type="date" id="rstSDate" style="flex:1; background:#040814; border:1px solid #334155; color:#fff; padding:6px; border-radius:4px; font-size:11px;">
                        <input type="date" id="rstEDate" style="flex:1; background:#040814; border:1px solid #334155; color:#fff; padding:6px; border-radius:4px; font-size:11px;">
                    </div>
                </div>
                <div style="margin-bottom:18px;">
                    <label style="font-size:11px; color:#94a3b8; text-transform:uppercase;">Daily Clock Window</label>
                    <div style="display:flex; gap:8px; margin-top:4px;">
                        <input type="time" id="rstSTime" style="flex:1; background:#040814; border:1px solid #334155; color:#fff; padding:6px; border-radius:4px; font-size:11px;">
                        <input type="time" id="rstETime" style="flex:1; background:#040814; border:1px solid #334155; color:#fff; padding:6px; border-radius:4px; font-size:11px;">
                    </div>
                </div>
                <div style="display:flex; justify-content:flex-end; gap:8px;">
                    <button onclick="document.getElementById('lifecycleRestrictionModal').style.display='none'" style="background:#1e293b; color:#94a3b8; border:none; padding:6px 12px; border-radius:4px; font-size:11px; cursor:pointer;">Dismiss</button>
                    <button onclick="saveRestrictionsModal()" style="background:#00f0ff; color:#030712; font-weight:700; border:none; padding:6px 14px; border-radius:4px; font-size:11px; cursor:pointer;">Commit</button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
        if (window.lucide) lucide.createIcons();
    }

    document.getElementById('rstUid').value = uid;
    document.getElementById('rstSDate').value = sDate;
    document.getElementById('rstEDate').value = eDate;
    document.getElementById('rstSTime').value = sTime;
    document.getElementById('rstETime').value = eTime;
    modal.style.display = 'flex';
}

async function saveRestrictionsModal() {
    const uid = document.getElementById('rstUid').value;
    const body = {
        user_id: uid,
        start_date: document.getElementById('rstSDate').value || null,
        end_date: document.getElementById('rstEDate').value || null,
        start_time: document.getElementById('rstSTime').value || null,
        end_time: document.getElementById('rstETime').value || null
    };

    const res = await fetch('/api/admin/modify-lifecycle', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(body)
    });
    if (res.ok) {
        document.getElementById('lifecycleRestrictionModal').style.display = 'none';
        refreshMasterConsole();
    }
}

// 1 second accurate telemetry polling
setInterval(refreshMasterConsole, 1000);
document.addEventListener('DOMContentLoaded', refreshMasterConsole);