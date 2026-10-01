import re

path = "templates/landing.html"
with open(path, "r", encoding="utf-8-sig") as f:
    text = f.read()

# 1. Canvas tag ensure karein
if '<div id="canvas-container"' in text:
    text = re.sub(r'<div id="canvas-container"[^>]*></div>', '<canvas id="starCanvas3D" class="fixed inset-0 pointer-events-none z-0 w-full h-full"></canvas>', text)
elif '<canvas id="starCanvas"' in text:
    text = text.replace('id="starCanvas"', 'id="starCanvas3D"')

# 2. Advanced 3D Depth Star Engine
engine_code = """
    <!-- Three-Dimensional Perspective Starfield Engine -->
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
                fb.innerText = "Kripya username aur password dono bharein.";
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
                fb.innerText = data.message || "Auth error";
                fb.classList.remove('hidden');
            }
        }

        const specDetails = {
            neural: {
                title: "Neural Interface & Autonomous Pipeline",
                icon: "cpu",
                body: `<p class="font-bold text-purple-300">1. Architecture</p><p>Low-latency localized speech pipeline without external dependencies.</p>`
            },
            hwid: {
                title: "Anti-Abuse HWID Architecture",
                icon: "key",
                body: `<p class="font-bold text-purple-300">1. Hardware Protection</p><p>Cryptographic UUID bind to prevent multi-instance bypass.</p>`
            },
            sync: {
                title: "Real-time Telemetry & Mesh Relay",
                icon: "refresh-cw",
                body: `<p class="font-bold text-purple-300">1. Real-time Mesh</p><p>Encrypted telemetry between desktop host daemon and mobile node.</p>`
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

        // --- 3D PERSPECTIVE WARP STAR ENGINE ---
        (function() {
            const canvas = document.getElementById('starCanvas3D');
            const ctx = canvas.getContext('2d');
            let w, h, cx, cy;
            
            function resize() {
                w = canvas.width = window.innerWidth;
                h = canvas.height = window.innerHeight;
                cx = w / 2;
                cy = h / 2;
            }
            window.addEventListener('resize', resize);
            resize();

            const STAR_COUNT = 1000;
            const stars = [];

            for (let i = 0; i < STAR_COUNT; i++) {
                stars.push({
                    x: (Math.random() - 0.5) * 3000,
                    y: (Math.random() - 0.5) * 3000,
                    z: Math.random() * 2000 + 1,
                    size: Math.random() * 1.6 + 0.8,
                    color: Math.random() > 0.35 ? '#c084fc' : '#e9d5ff'
                });
            }

            let mouseZone = 0; // -1: Left (Zoom out), 0: Center, 1: Right (Zoom in)
            let currentSpeed = 0.8;

            window.addEventListener('mousemove', (e) => {
                const normX = (e.clientX / w) * 2 - 1;
                if (normX > 0.25) {
                    mouseZone = normX; // Zoom In trigger
                } else if (normX < -0.25) {
                    mouseZone = normX; // Zoom Out trigger
                } else {
                    mouseZone = 0; // Center neutral
                }
            });

            function render() {
                ctx.fillStyle = '#07030d';
                ctx.fillRect(0, 0, w, h);

                // Smooth speed interpolation
                let targetSpeed = 0.6;
                if (mouseZone > 0.25) {
                    targetSpeed = 4.5 * mouseZone; // Faster 3D forward fly
                } else if (mouseZone < -0.25) {
                    targetSpeed = -4.5 * Math.abs(mouseZone); // Reverse 3D warp
                }
                currentSpeed += (targetSpeed - currentSpeed) * 0.08;

                for (let i = 0; i < STAR_COUNT; i++) {
                    const s = stars[i];

                    s.z -= currentSpeed;

                    // Boundary loop
                    if (s.z <= 1) {
                        s.z = 2000;
                        s.x = (Math.random() - 0.5) * 3000;
                        s.y = (Math.random() - 0.5) * 3000;
                    }
                    if (s.z > 2000) {
                        s.z = 2;
                    }

                    // 3D Perspective Projection
                    const k = 450 / s.z;
                    const px = s.x * k + cx;
                    const py = s.y * k + cy;

                    if (px >= 0 && px <= w && py >= 0 && py <= h) {
                        const depthFactor = (1 - s.z / 2000);
                        const radius = Math.max(0.6, s.size * depthFactor * 3.0);
                        const alpha = Math.min(1, depthFactor * 1.3);

                        ctx.fillStyle = s.color;
                        ctx.globalAlpha = alpha;
                        ctx.beginPath();
                        ctx.arc(px, py, radius, 0, Math.PI * 2);
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

body_start = text.find("<!-- Instant Native Starfield Script -->")
if body_start == -1:
    body_start = text.find("<!-- Scripts -->")
if body_start == -1:
    body_start = text.find("<script>")

if body_start != -1:
    text = text[:body_start] + engine_code
else:
    text += engine_code

with open(path, "w", encoding="utf-8") as f:
    f.write(text)

print("Real 3D Perspective Warp Starfield deployed successfully!")