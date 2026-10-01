import os

# 1. Update Server Login matching logic
path_app = "server/app.py"
with open(path_app, "r", encoding="utf-8-sig") as f:
    code = f.read()

# Make sure login handles lowercase properly and sets cookies correctly
old_login = """    c.execute("SELECT * FROM users WHERE LOWER(username) = LOWER(?)", (u,))
    row = c.fetchone()"""

new_login = """    c.execute("SELECT * FROM users WHERE LOWER(TRIM(username)) = LOWER(TRIM(?))", (u,))
    row = c.fetchone()"""
if old_login in code:
    code = code.replace(old_login, new_login)

with open(path_app, "w", encoding="utf-8") as f:
    f.write(code)

# 2. Shared 3D Warp Canvas & Script (Exactly identical to landing page)
three_d_canvas = '<canvas id="cosmicCanvas3D" class="fixed inset-0 pointer-events-none z-0 w-full h-full opacity-80"></canvas>'

three_d_script = """
    <!-- Same 100% Working 3D Warp Engine as Landing Page -->
    <script>
        (function() {
            const canvas = document.getElementById('cosmicCanvas3D');
            if (!canvas) return;
            const ctx = canvas.getContext('2d');
            let w, h, cx, cy;
            function resize() { w = canvas.width = window.innerWidth; h = canvas.height = window.innerHeight; cx = w/2; cy = h/2; }
            window.addEventListener('resize', resize);
            resize();

            const stars = [];
            for (let i = 0; i < 900; i++) {
                stars.push({
                    x: (Math.random() - 0.5) * 3200,
                    y: (Math.random() - 0.5) * 3200,
                    z: Math.random() * 2000 + 1,
                    size: Math.random() * 1.8 + 0.8,
                    color: Math.random() > 0.4 ? '#c084fc' : '#f0abfc'
                });
            }

            let mouseX = 0, currentSpeed = 5.0, targetSpeed = 5.0;
            window.addEventListener('mousemove', (e) => {
                const normX = (e.clientX / w) * 2 - 1;
                mouseX = normX * 220;
                if (normX > 0.15) targetSpeed = 8.0 + (normX * 18.0);
                else if (normX < -0.15) targetSpeed = -6.0 - (Math.abs(normX) * 14.0);
                else targetSpeed = 5.0;
            });

            function render() {
                ctx.fillStyle = 'rgba(6, 2, 12, 0.42)';
                ctx.fillRect(0, 0, w, h);
                currentSpeed += (targetSpeed - currentSpeed) * 0.12;

                for (let i = 0; i < 900; i++) {
                    const s = stars[i];
                    const prevZ = s.z;
                    s.z -= currentSpeed;
                    if (s.z <= 1) { s.z = 2000; s.x = (Math.random() - 0.5) * 3200; s.y = (Math.random() - 0.5) * 3200; continue; }
                    if (s.z > 2000) { s.z = 2; continue; }

                    const k = 420 / s.z;
                    const px = s.x * k + cx - mouseX * 0.4;
                    const py = s.y * k + cy;

                    const kPrev = 420 / (prevZ + currentSpeed * 0.9);
                    const prevPx = s.x * kPrev + cx - mouseX * 0.4;
                    const prevPy = s.y * kPrev + cy;

                    if (px >= 0 && px <= w && py >= 0 && py <= h) {
                        const d = 1 - s.z / 2000;
                        ctx.strokeStyle = s.color;
                        ctx.fillStyle = s.color;
                        ctx.globalAlpha = Math.min(1, d * 1.2);
                        if (Math.abs(currentSpeed) > 6.5) {
                            ctx.lineWidth = s.size * d * 2.5;
                            ctx.beginPath();
                            ctx.moveTo(prevPx, prevPy);
                            ctx.lineTo(px, py);
                            ctx.stroke();
                        } else {
                            ctx.beginPath();
                            ctx.arc(px, py, s.size * d * 2.5, 0, Math.PI * 2);
                            ctx.fill();
                        }
                    }
                }
                ctx.globalAlpha = 1.0;
                requestAnimationFrame(render);
            }
            render();
        })();
    </script>
"""

# 3. Overwrite Admin Portal Template with 3D Canvas & Creator Downloads
admin_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>JARVIS PORTAL // MASTER CONSOLE</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/lucide@latest"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Orbitron:wght@600;700;900&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
        body {{ font-family: 'Plus Jakarta Sans', sans-serif; background-color: #06020c; color: #f3e8ff; min-height: 100vh; overflow-x: hidden; }}
        .font-cyber {{ font-family: 'Orbitron', sans-serif; }}
        .font-mono {{ font-family: 'JetBrains Mono', monospace; }}
        .glass-purple {{
            background: rgba(20, 8, 36, 0.85);
            backdrop-filter: blur(24px);
            border: 1px solid rgba(168, 85, 247, 0.35);
        }}
        .purple-btn {{
            background: linear-gradient(135deg, rgba(168, 85, 247, 0.3), rgba(126, 34, 206, 0.45));
            border: 1px solid rgba(192, 132, 252, 0.55);
            box-shadow: 0 0 15px rgba(168, 85, 247, 0.25);
            transition: all 0.2s ease;
        }}
        .purple-btn:hover {{
            border-color: #c084fc;
            box-shadow: 0 0 25px rgba(168, 85, 247, 0.6);
            transform: translateY(-2px);
        }}
    </style>
</head>
<body class="p-3 sm:p-5 md:p-8 flex flex-col gap-6 max-w-7xl mx-auto relative min-h-screen">
    {three_d_canvas}

    <header class="relative z-10 glass-purple rounded-2xl p-4 px-6 flex justify-between items-center gap-3">
        <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-xl bg-purple-500/15 border border-purple-500/40 flex items-center justify-center text-purple-300">
                <i data-lucide="shield" class="w-6 h-6"></i>
            </div>
            <div>
                <h1 class="font-cyber font-bold text-lg text-purple-200">JARVIS PORTAL</h1>
                <p class="text-[10px] font-mono text-purple-400">SUPER MASTER CONTROL // AUTHORIZED</p>
            </div>
        </div>

        <div class="flex items-center gap-3 font-mono">
            <a href="/" class="purple-btn px-4 py-2 rounded-xl text-xs font-bold text-purple-100 flex items-center gap-2">
                <i data-lucide="home" class="w-4 h-4 text-purple-300"></i>
                <span>← Home Page</span>
            </a>
            <div class="hidden sm:block text-right">
                <span class="text-[9px] text-purple-400 block">CREATOR ADMIN</span>
                <span class="text-xs font-bold text-purple-200">{{{{ username }}}}</span>
            </div>
            <a href="/logout" class="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs font-semibold hover:bg-rose-500/20">
                <i data-lucide="log-out" class="w-4 h-4"></i>
            </a>
        </div>
    </header>

    <main class="relative z-10 flex flex-col gap-6">
        <!-- Creator Package Download Section -->
        <section class="glass-purple rounded-2xl p-5 flex flex-col gap-4">
            <div class="flex justify-between items-center border-b border-purple-900/60 pb-3">
                <h3 class="font-cyber text-sm font-bold text-purple-200 flex items-center gap-2">
                    <i data-lucide="download" class="w-4 h-4 text-purple-400"></i> Creator Build Downloads (Admin Excluded from Counts)
                </h3>
                <span class="text-[10px] font-mono text-emerald-400">UNRESTRICTED ACCESS</span>
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <a href="/get-package/windows" class="purple-btn p-4 rounded-xl flex items-center justify-between group">
                    <div class="flex items-center gap-3.5">
                        <div class="w-10 h-10 rounded-lg bg-purple-950 border border-purple-500/50 flex items-center justify-center text-purple-300">
                            <svg class="w-5 h-5 fill-current" viewBox="0 0 24 24"><path d="M0 3.449L9.75 2.1v9.451H0m10.949-9.602L24 0v11.4H10.949M0 12.6h9.75v9.451L0 20.699M10.949 12.6H24V24l-12.051-1.899"/></svg>
                        </div>
                        <div>
                            <span class="text-xs font-bold text-purple-100 block">Download Windows Client</span>
                            <span class="text-[10px] font-mono text-purple-400 font-semibold">.EXE STANDALONE</span>
                        </div>
                    </div>
                    <i data-lucide="download" class="w-4 h-4 text-purple-400"></i>
                </a>

                <a href="/get-package/android" class="purple-btn p-4 rounded-xl flex items-center justify-between group">
                    <div class="flex items-center gap-3.5">
                        <div class="w-10 h-10 rounded-lg bg-purple-950 border border-purple-500/50 flex items-center justify-center text-purple-300">
                            <svg class="w-5 h-5 fill-none stroke-current stroke-2 stroke-linecap-round stroke-linejoin-round" viewBox="0 0 24 24"><rect width="14" height="20" x="5" y="2" rx="2" ry="2"/><path d="M12 18h.01"/></svg>
                        </div>
                        <div>
                            <span class="text-xs font-bold text-purple-100 block">Download Android Node</span>
                            <span class="text-[10px] font-mono text-purple-400 font-semibold">.APK COMPANION</span>
                        </div>
                    </div>
                    <i data-lucide="download" class="w-4 h-4 text-purple-400"></i>
                </a>
            </div>
        </section>

        <!-- Master Telemetry & Nodes -->
        <section class="glass-purple rounded-2xl p-5 flex flex-col gap-4">
            <div class="flex justify-between items-center border-b border-purple-900/60 pb-3">
                <div class="flex items-center gap-2">
                    <i data-lucide="sliders" class="w-5 h-5 text-purple-400"></i>
                    <h2 class="font-cyber font-bold text-sm tracking-wide text-purple-200">Live Operator Telemetry</h2>
                </div>
                <div class="flex items-center gap-2">
                    <button onclick="refreshMasterConsole()" class="flex items-center gap-1 bg-purple-900/40 border border-purple-600 text-purple-300 px-3 py-1 rounded-lg text-xs font-mono hover:bg-purple-900/60">
                        <i data-lucide="refresh-cw" class="w-3 h-3"></i> Refresh Data
                    </button>
                    <button onclick="clearAllMetricsToZero()" class="flex items-center gap-1 bg-rose-950/40 border border-rose-600 text-rose-400 px-3 py-1 rounded-lg text-xs font-mono hover:bg-rose-900/40">
                        <i data-lucide="rotate-ccw" class="w-3 h-3"></i> Reset Counts
                    </button>
                </div>
            </div>

            <div class="grid grid-cols-2 md:grid-cols-4 gap-3 font-mono">
                <div class="bg-purple-950/40 border border-purple-900/60 p-4 rounded-xl">
                    <span class="text-[10px] tracking-wider text-purple-400/80 block mb-1">TOTAL OPERATORS</span>
                    <h3 id="statTotalUsers" class="text-2xl font-bold text-purple-100">0</h3>
                </div>
                <div class="bg-purple-950/40 border border-purple-900/60 p-4 rounded-xl">
                    <span class="text-[10px] tracking-wider text-emerald-400 block mb-1">ACTIVE OPERATORS</span>
                    <h3 id="statActiveUsers" class="text-2xl font-bold text-emerald-400">0</h3>
                </div>
                <div class="bg-purple-950/40 border border-purple-900/60 p-4 rounded-xl">
                    <span class="text-[10px] tracking-wider text-purple-300 block mb-1">WINDOWS DOWNLOADS</span>
                    <h3 id="statWinDownloads" class="text-2xl font-bold text-purple-200">0</h3>
                </div>
                <div class="bg-purple-950/40 border border-purple-900/60 p-4 rounded-xl">
                    <span class="text-[10px] tracking-wider text-fuchsia-400 block mb-1">ANDROID DOWNLOADS</span>
                    <h3 id="statApkDownloads" class="text-2xl font-bold text-fuchsia-300">0</h3>
                </div>
            </div>

            <div class="flex flex-col gap-3 mt-2">
                <div class="flex justify-between items-center">
                    <span class="text-xs font-mono font-bold text-purple-300 uppercase tracking-wider flex items-center gap-1.5">
                        <i data-lucide="network" class="w-4 h-4 text-purple-400"></i> Managed Operator Nodes
                    </span>
                    <span id="nodeCountBadge" class="text-[10px] font-mono px-2 py-0.5 rounded bg-purple-900/40 border border-purple-700 text-purple-300">0 NODES</span>
                </div>
                <div id="masterNodesContainer" class="flex flex-col gap-3 max-h-[460px] overflow-y-auto pr-1"></div>
            </div>
        </section>
    </main>

    <script src="/static/admin_actions.js"></script>
    <script>lucide.createIcons();</script>
    {three_d_script}
</body>
</html>
"""

# 4. Overwrite User Dashboard Template with Exact 3D Canvas
user_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>JARVIS PORTAL // OPERATOR CONSOLE</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/lucide@latest"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Orbitron:wght@600;700;900&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
        body {{ font-family: 'Plus Jakarta Sans', sans-serif; background-color: #06020c; color: #f3e8ff; min-height: 100vh; overflow-x: hidden; }}
        .font-cyber {{ font-family: 'Orbitron', sans-serif; }}
        .font-mono {{ font-family: 'JetBrains Mono', monospace; }}
        .glass-purple {{
            background: rgba(20, 8, 36, 0.85);
            backdrop-filter: blur(24px);
            border: 1px solid rgba(168, 85, 247, 0.35);
        }}
        .purple-btn {{
            background: linear-gradient(135deg, rgba(168, 85, 247, 0.3), rgba(126, 34, 206, 0.45));
            border: 1px solid rgba(192, 132, 252, 0.55);
            box-shadow: 0 0 20px rgba(168, 85, 247, 0.3);
            transition: all 0.25s ease;
        }}
        .purple-btn:hover {{
            border-color: #c084fc;
            box-shadow: 0 0 35px rgba(168, 85, 247, 0.7);
            transform: translateY(-2px);
        }}
    </style>
</head>
<body class="p-3 sm:p-5 md:p-8 flex flex-col gap-6 max-w-5xl mx-auto min-h-screen relative">
    {three_d_canvas}

    <header class="relative z-10 glass-purple rounded-2xl p-4 px-6 flex justify-between items-center gap-3">
        <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-xl bg-purple-500/15 border border-purple-500/50 flex items-center justify-center text-purple-300">
                <i data-lucide="shield" class="w-6 h-6"></i>
            </div>
            <div>
                <h1 class="font-cyber font-bold text-lg text-purple-200">JARVIS PORTAL</h1>
                <p class="text-[10px] font-mono text-purple-400">OPERATOR CONSOLE // RUNTIME</p>
            </div>
        </div>

        <div class="flex items-center gap-3 font-mono">
            <a href="/" class="purple-btn px-4 py-2 rounded-xl text-xs font-bold text-purple-100 flex items-center gap-2">
                <i data-lucide="home" class="w-4 h-4 text-purple-300"></i>
                <span>← Home Page</span>
            </a>
            <div class="hidden sm:block text-right">
                <span class="text-[9px] text-purple-400 block">OPERATOR</span>
                <span class="text-xs font-bold text-purple-200">{{{{ username }}}}</span>
            </div>
            <a href="/logout" class="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs font-semibold hover:bg-rose-500/20">
                <i data-lucide="log-out" class="w-4 h-4"></i>
            </a>
        </div>
    </header>

    <main class="relative z-10 flex flex-col gap-6">
        <section class="glass-purple rounded-2xl p-6 flex flex-col gap-3">
            <div class="flex justify-between items-center">
                <span class="text-xs font-mono text-emerald-400 flex items-center gap-2 font-bold">
                    <span class="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-ping"></span> NODE ACTIVE
                </span>
                <span class="px-3 py-1 rounded text-[11px] font-mono bg-purple-900/40 border border-purple-500 text-purple-200 font-bold">
                    10 DAYS ACCESS
                </span>
            </div>
            <h2 class="font-cyber text-xl font-bold text-purple-100 flex items-center gap-2.5 mt-1">
                <i data-lucide="terminal" class="w-5 h-5 text-purple-400"></i> Operator Session: {{{{ username }}}}
            </h2>
            <p class="text-xs text-purple-300/80 leading-relaxed">
                Aapka authenticated environment setup hai. Background me full 3D cosmic warp render ho raha hai. Niche diye builds download karke machine link karein:
            </p>
        </section>

        <section class="glass-purple rounded-2xl p-6 flex flex-col gap-4">
            <div class="flex justify-between items-center border-b border-purple-900/60 pb-3">
                <h3 class="font-cyber text-sm font-bold text-purple-200">Verified Platform Distributions</h3>
                <span class="text-[10px] font-mono text-purple-400">CONFIRMED SAVE</span>
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-1">
                <button onclick="promptDownload('windows', '/get-package/windows', 'JARVIS_Desktop_Setup.exe')" 
                        class="purple-btn p-4 rounded-xl flex items-center justify-between group text-left w-full">
                    <div class="flex items-center gap-3.5">
                        <div class="w-10 h-10 rounded-lg bg-purple-950 border border-purple-500/50 flex items-center justify-center text-purple-300">
                            <svg class="w-5 h-5 fill-current" viewBox="0 0 24 24"><path d="M0 3.449L9.75 2.1v9.451H0m10.949-9.602L24 0v11.4H10.949M0 12.6h9.75v9.451L0 20.699M10.949 12.6H24V24l-12.051-1.899"/></svg>
                        </div>
                        <div>
                            <span class="text-xs font-bold text-purple-100 block">Windows Client</span>
                            <span class="text-[10px] font-mono text-purple-400 font-semibold">.EXE STANDALONE</span>
                        </div>
                    </div>
                    <i data-lucide="download" class="w-4 h-4 text-purple-400"></i>
                </button>

                <button onclick="promptDownload('android', '/get-package/android', 'JARVIS_Node_Companion.apk')" 
                        class="purple-btn p-4 rounded-xl flex items-center justify-between group text-left w-full">
                    <div class="flex items-center gap-3.5">
                        <div class="w-10 h-10 rounded-lg bg-purple-950 border border-purple-500/50 flex items-center justify-center text-purple-300">
                            <svg class="w-5 h-5 fill-none stroke-current stroke-2 stroke-linecap-round stroke-linejoin-round" viewBox="0 0 24 24"><rect width="14" height="20" x="5" y="2" rx="2" ry="2"/><path d="M12 18h.01"/></svg>
                        </div>
                        <div>
                            <span class="text-xs font-bold text-purple-100 block">Android Node</span>
                            <span class="text-[10px] font-mono text-purple-400 font-semibold">.APK COMPANION</span>
                        </div>
                    </div>
                    <i data-lucide="download" class="w-4 h-4 text-purple-400"></i>
                </button>
            </div>
        </section>
    </main>

    <!-- Modal -->
    <div id="downloadModal" class="fixed inset-0 bg-black/85 backdrop-blur-md hidden justify-center items-center z-[99999] p-4">
        <div class="glass-purple rounded-2xl p-6 max-w-sm w-full font-mono flex flex-col gap-4 border border-purple-500/50 shadow-2xl text-center">
            <div class="w-12 h-12 rounded-xl bg-purple-500/10 border border-purple-500/40 mx-auto flex items-center justify-center text-purple-300">
                <i data-lucide="download" class="w-6 h-6"></i>
            </div>
            <div>
                <h3 id="modalTitle" class="font-cyber font-bold text-sm text-purple-100">Confirm Download</h3>
                <p class="text-xs text-purple-300/70 mt-1">Start confirmed delivery stream to your machine?</p>
            </div>
            <div class="grid grid-cols-2 gap-3 pt-2">
                <button onclick="closeDownloadModal()" class="bg-purple-950/70 border border-purple-800 text-purple-300 py-2.5 rounded-xl text-xs font-bold">Cancel</button>
                <button id="modalConfirmBtn" class="purple-btn py-2.5 rounded-xl text-xs font-bold text-purple-100">Download</button>
            </div>
        </div>
    </div>

    <script>
        lucide.createIcons();
        let pendingDl = null;
        function promptDownload(platform, url, filename) {{
            pendingDl = {{ platform, url, filename }};
            document.getElementById('modalTitle').innerText = platform === 'windows' ? 'Download Windows Setup (.exe)?' : 'Download Android Node (.apk)?';
            document.getElementById('downloadModal').classList.remove('hidden');
            document.getElementById('downloadModal').classList.add('flex');
            lucide.createIcons();

            document.getElementById('modalConfirmBtn').onclick = async () => {{
                closeDownloadModal();
                const a = document.createElement('a');
                a.href = url;
                a.download = filename;
                document.body.appendChild(a);
                a.click();
                a.remove();

                await fetch('/api/tracker/confirm-download', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{ platform: platform }})
                }});
            }};
        }}
        function closeDownloadModal() {{
            document.getElementById('downloadModal').classList.remove('flex');
            document.getElementById('downloadModal').classList.add('hidden');
            pendingDl = null;
        }}
    </script>
    {three_d_script}
</body>
</html>
"""

# Write to both template directories
for target in ["templates", "server/templates"]:
    with open(f"{target}/admin_portal.html", "w", encoding="utf-8") as f:
        f.write(admin_html)
    with open(f"{target}/user_dashboard.html", "w", encoding="utf-8") as f:
        f.write(user_html)

print("SUCCESS: 3D Warp + Creator Downloads + Login Sync Patched!")