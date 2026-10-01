async function refreshMasterConsole() {
    try {
        const [mRes, nRes] = await Promise.all([
            fetch('/api/admin/metrics'),
            fetch('/api/admin/nodes')
        ]);
        if (mRes.ok) {
            const m = await mRes.json();
            document.getElementById('statTotalUsers').innerText = m.total_users ?? 0;
            document.getElementById('statActiveUsers').innerText = m.active_users ?? 0;
            document.getElementById('statWinDownloads').innerText = m.windows_downloads ?? 0;
            document.getElementById('statApkDownloads').innerText = m.android_downloads ?? 0;
        }
        if (nRes.ok) {
            const nodes = await nRes.json();
            renderModularCards(nodes);
        }
    } catch(e) {}
}

async function clearAllMetricsToZero() {
    if (!confirm("Are you sure you want to reset all counts to 0?")) return;
    const res = await fetch('/api/admin/clear-stats', { method: 'POST' });
    if (res.ok) refreshMasterConsole();
}

function renderModularCards(nodes) {
    const container = document.getElementById('masterNodesContainer');
    const badge = document.getElementById('nodeCountBadge');
    if (!container) return;
    if (badge) badge.innerText = `${nodes ? nodes.length : 0} NODES`;

    if (!nodes || nodes.length === 0) {
        container.innerHTML = '<div class="p-6 text-center text-slate-500 font-mono text-xs">No active operator nodes.</div>';
        return;
    }

    container.innerHTML = '';
    nodes.forEach(u => {
        const isOnline = (Date.now()/1000 - (u.last_seen || 0)) < 120;
        const statusBadge = u.is_active
            ? (isOnline ? '<span class="text-[10px] font-mono text-emerald-400 font-bold">● ONLINE</span>' : '<span class="text-[10px] font-mono text-purple-400">STANDBY</span>')
            : '<span class="text-[10px] font-mono text-rose-500 font-bold">TERMINATED</span>';

        const life = u.is_unlimited ? 'UNLIMITED' : `${u.days_remaining} DAYS`;

        const card = document.createElement('div');
        card.className = "bg-purple-950/40 border border-purple-900/60 rounded-xl p-3 flex flex-col gap-2.5";
        card.innerHTML = `
            <div class="flex justify-between items-center border-b border-purple-900/50 pb-2">
                <span class="font-bold text-xs text-purple-200">${u.username} (#${u.id})</span>
                ${statusBadge}
            </div>
            <div class="grid grid-cols-3 gap-2 text-[10px] font-mono bg-black/40 p-2 rounded">
                <div><span class="text-purple-400/70">Allocation:</span> <span class="text-purple-200">${life}</span></div>
                <div><span class="text-purple-400/70">Role:</span> <span class="text-purple-200">${u.role}</span></div>
                <div><span class="text-purple-400/70">Registered:</span> <span class="text-purple-200">${u.created_at}</span></div>
            </div>
            <div class="flex gap-2 justify-end pt-1">
                <button onclick="controlAction(${u.id}, 'add_5')" class="bg-purple-900/40 border border-purple-700 text-purple-300 px-2 py-1 rounded text-[10px] font-mono">+5D</button>
                <button onclick="controlAction(${u.id}, 'sub_5')" class="bg-purple-900/40 border border-purple-700 text-purple-300 px-2 py-1 rounded text-[10px] font-mono">-5D</button>
                <button onclick="controlAction(${u.id}, 'unlim')" class="bg-purple-900/40 border border-purple-700 text-purple-300 px-2 py-1 rounded text-[10px] font-mono">∞</button>
                <button onclick="controlAction(${u.id}, 'del')" class="bg-rose-950/40 border border-rose-800 text-rose-400 px-2 py-1 rounded text-[10px] font-mono">Del</button>
            </div>
        `;
        container.appendChild(card);
    });
}

async function controlAction(uid, act) {
    let p = { user_id: uid };
    if (act === 'add_5') p.delta_days = 5;
    if (act === 'sub_5') p.delta_days = -5;
    if (act === 'unlim') p.is_unlimited = 1;
    if (act === 'del') {
        if (!confirm('Delete node?')) return;
        p.delete = true;
    }
    const res = await fetch('/api/admin/modify-lifecycle', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(p)
    });
    if (res.ok) refreshMasterConsole();
}

setInterval(refreshMasterConsole, 2000);
document.addEventListener('DOMContentLoaded', refreshMasterConsole);