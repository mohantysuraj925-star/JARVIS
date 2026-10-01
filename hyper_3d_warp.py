import re

path = "templates/landing.html"
with open(path, "r", encoding="utf-8-sig") as f:
    text = f.read()

# Replace with High-Speed Warp Starfield Engine
advanced_engine = """
    <!-- Ultra High-Speed 3D Warp Starfield & Cosmic Dust Engine -->
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

        // --- CREATIVE 3D HIGH-SPEED WARP ENGINE ---
        (function() {
            const canvas = document.getElementById('starCanvas3D') || document.getElementById('starCanvas');
            if (!canvas) return;
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

            const STAR_COUNT = 850;
            const stars = [];
            const colors = ['#e879f9', '#c084fc', '#a855f7', '#f3e8ff', '#9333ea'];

            for (let i = 0; i < STAR_COUNT; i++) {
                stars.push({
                    x: (Math.random() - 0.5) * 3500,
                    y: (Math.random() - 0.5) * 3500,
                    z: Math.random() * 2000 + 1,
                    size: Math.random() * 1.8 + 0.8,
                    color: colors[Math.floor(Math.random() * colors.length)],
                    twinkle: Math.random() * Math.PI * 2
                });
            }

            let mouseX = 0;
            let mouseY = 0;
            let targetSpeed = 2.5;
            let currentSpeed = 2.5;

            window.addEventListener('mousemove', (e) => {
                const normX = (e.clientX / w) * 2 - 1;
                const normY = (e.clientY / h) * 2 - 1;
                mouseX = normX * 200;
                mouseY = normY * 200;

                if (normX > 0.15) {
                    targetSpeed = 4.0 + (normX * 12.0); // Fast forward warp
                } else if (normX < -0.15) {
                    targetSpeed = -3.0 - (Math.abs(normX) * 9.0); // Fast reverse warp
                } else {
                    targetSpeed = 2.5; // Steady cruise
                }
            });

            function render() {
                // Subtle trailing fade for warp streak visual
                ctx.fillStyle = 'rgba(7, 3, 13, 0.42)';
                ctx.fillRect(0, 0, w, h);

                // Speed interpolation
                currentSpeed += (targetSpeed - currentSpeed) * 0.12;

                const centerOffsetX = cx - mouseX * 0.4;
                const centerOffsetY = cy - mouseY * 0.4;

                for (let i = 0; i < STAR_COUNT; i++) {
                    const s = stars[i];
                    s.twinkle += 0.05;

                    const prevZ = s.z;
                    s.z -= currentSpeed;

                    // Bound checks
                    if (s.z <= 1) {
                        s.z = 2000;
                        s.x = (Math.random() - 0.5) * 3500;
                        s.y = (Math.random() - 0.5) * 3500;
                        continue;
                    }
                    if (s.z > 2000) {
                        s.z = 2;
                        continue;
                    }

                    // Current 3D projection
                    const k = 400 / s.z;
                    const px = s.x * k + centerOffsetX;
                    const py = s.y * k + centerOffsetY;

                    // Previous 3D projection (for warp streak effect)
                    const kPrev = 400 / (prevZ + (currentSpeed * 0.8));
                    const prevPx = s.x * kPrev + centerOffsetX;
                    const prevPy = s.y * kPrev + centerOffsetY;

                    if (px >= 0 && px <= w && py >= 0 && py <= h) {
                        const depth = 1 - (s.z / 2000);
                        const radius = Math.max(0.7, s.size * depth * 2.8);
                        const alpha = Math.min(1, Math.max(0.15, depth * (0.8 + Math.sin(s.twinkle) * 0.2)));

                        ctx.strokeStyle = s.color;
                        ctx.fillStyle = s.color;
                        ctx.globalAlpha = alpha;

                        // Agar speed fast hai toh streak draw karega
                        if (Math.abs(currentSpeed) > 4.5) {
                            ctx.lineWidth = radius * 0.8;
                            ctx.beginPath();
                            ctx.moveTo(prevPx, prevPy);
                            ctx.lineTo(px, py);
                            ctx.stroke();
                        } else {
                            ctx.beginPath();
                            ctx.arc(px, py, radius, 0, Math.PI * 2);
                            ctx.fill();
                        }
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

body_start = text.find("<!-- Three-Dimensional")
if body_start == -1:
    body_start = text.find("<!-- Instant Native")
if body_start == -1:
    body_start = text.find("<!-- Ultra High-Speed")
if body_start == -1:
    body_start = text.find("<script>")

text = text[:body_start] + advanced_engine

with open(path, "w", encoding="utf-8") as f:
    f.write(text)

print("Creative High-Speed Warp Starfield Deployed!")