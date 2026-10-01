import re

path = "templates/landing.html"
with open(path, "r", encoding="utf-8-sig") as f:
    text = f.read()

# 1. Canvas element ensure karein
text = re.sub(
    r'<div id="canvas-container"[^>]*></div>',
    '<canvas id="starCanvas" class="fixed inset-0 pointer-events-none z-0 w-full h-full"></canvas>',
    text
)

# 2. Pure Native Starfield Engine (Instant render, 0 CDN delay)
native_engine = """
    <!-- Instant Native Starfield Script -->
    <script>
        lucide.createIcons();

        function openAuthModal() { 
            const m = document.getElementById('authModal');
            if (m) { m.classList.remove('hidden'); m.classList.add('flex'); }
            lucide.createIcons();
        }
        function closeAuthModal() { 
            const m = document.getElementById('authModal');
            if (m) { m.classList.remove('flex'); m.classList.add('hidden'); }
        }

        async function submitAuth(type) {
            const u = document.getElementById('authUsername').value.trim();
            const p = document.getElementById('authPassword').value.trim();
            const fb = document.getElementById('authFeedback');
            fb.classList.add('hidden');

            if (!u || !p) {
                fb.innerText = "Please provide both username and password.";
                fb.classList.remove('hidden');
                return;
            }

            const res = await fetch(type === 'register' ? '/api/auth/register' : '/api/auth/login', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ username: u, password: p })
            });
            const data = await res.json();
            if (res.ok) {
                window.location.href = data.redirect;
            } else {
                fb.innerText = data.message || "Authentication error.";
                fb.classList.remove('hidden');
            }
        }

        // View More Details Modal Data & Handlers
        const specDetails = {
            neural: {
                title: "Neural Interface & Autonomous Pipeline",
                icon: "cpu",
                body: `<p class="font-bold text-purple-300">1. Architectural Foundations</p><p>Localized lightweight acoustic language pipelines eliminating cloud latency bottlenecks.</p>`
            },
            hwid: {
                title: "Anti-Abuse HWID Architecture",
                icon: "key",
                body: `<p class="font-bold text-purple-300">1. Machine UUID Cryptographic Lock</p><p>Generates cryptographic hash binding CPU and motherboard serials to prevent multi-session abuse.</p>`
            },
            sync: {
                title: "Real-time Telemetry & Mesh Relay",
                icon: "refresh-cw",
                body: `<p class="font-bold text-purple-300">1. Bi-directional WebSocket Mesh</p><p>Continuous real-time state sync between desktop host daemon and Android mobile nodes.</p>`
            }
        };

        function openDetailModal(key) {
            const data = specDetails[key];
            if (!data) return;
            document.getElementById('specModalTitle').innerText = data.title;
            document.getElementById('specModalIcon').setAttribute('data-lucide', data.icon);
            document.getElementById('specModalBody').innerHTML = data.body;
            const m = document.getElementById('specDetailModal');
            m.classList.remove('hidden');
            m.classList.add('flex');
            lucide.createIcons();
        }

        function closeDetailModal() {
            const m = document.getElementById('specDetailModal');
            m.classList.remove('flex');
            m.classList.add('hidden');
        }

        // --- PURE NATIVE INSTANT STAR ENGINE ---
        (function() {
            const canvas = document.getElementById('starCanvas');
            const ctx = canvas.getContext('2d');
            let w, h;
            
            function resize() {
                w = canvas.width = window.innerWidth;
                h = canvas.height = window.innerHeight;
            }
            window.addEventListener('resize', resize);
            resize();

            const numStars = 600;
            const stars = [];
            for (let i = 0; i < numStars; i++) {
                stars.push({
                    x: (Math.random() - 0.5) * w * 2,
                    y: (Math.random() - 0.5) * h * 2,
                    z: Math.random() * w,
                    color: Math.random() > 0.4 ? '#c084fc' : '#f3e8ff',
                    baseSize: Math.random() * 1.5 + 0.5
                });
            }

            let mouseOffset = 0;
            window.addEventListener('mousemove', (e) => {
                const normX = (e.clientX / window.innerWidth) * 2 - 1;
                mouseOffset = Math.abs(normX) > 0.2 ? normX : 0;
            });

            function render() {
                ctx.fillStyle = '#07030d';
                ctx.fillRect(0, 0, w, h);

                const speed = 1.2 + (mouseOffset * 2.5); // Right = zoom-in/speed up, Left = zoom-out

                for (let i = 0; i < numStars; i++) {
                    const s = stars[i];
                    s.z -= speed;

                    if (s.z <= 1) s.z = w;
                    if (s.z > w) s.z = 1;

                    const k = 250 / s.z;
                    const px = s.x * k + w / 2;
                    const py = s.y * k + h / 2;

                    if (px >= 0 && px <= w && py >= 0 && py <= h) {
                        const sz = Math.max(0.6, (1 - s.z / w) * s.baseSize * 2.2);
                        const alpha = Math.min(1, (1 - s.z / w) * 1.2);
                        ctx.fillStyle = s.color;
                        ctx.globalAlpha = alpha;
                        ctx.beginPath();
                        ctx.arc(px, py, sz, 0, Math.PI * 2);
                        ctx.fill();
                    }
                }
                ctx.globalAlpha = 1.0;
                requestAnimationFrame(render);
            }
            requestAnimationFrame(render);
        })();
    </script>
</body>
</html>
"""

# Script section replace
body_start = text.find("<!-- Scripts -->")
if body_start == -1:
    body_start = text.find("<script>")
if body_start != -1:
    text = text[:body_start] + native_engine
else:
    text += native_engine

with open(path, "w", encoding="utf-8") as f:
    f.write(text)

print("Instant native starfield patched successfully!")