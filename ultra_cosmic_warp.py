import re

path = "templates/landing.html"
with open(path, "r", encoding="utf-8-sig") as f:
    text = f.read()

cosmic_engine = """
    <!-- Ultra-Speed 3D Warp + Meteors + Shockwave Engine -->
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

        // --- ULTRA SPEED + METEORS + CLICK SHOCKWAVE ---
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

            const STAR_COUNT = 950;
            const stars = [];
            const colors = ['#f0abfc', '#d8b4fe', '#c084fc', '#e879f9', '#ffffff'];

            for (let i = 0; i < STAR_COUNT; i++) {
                stars.push({
                    x: (Math.random() - 0.5) * 3600,
                    y: (Math.random() - 0.5) * 3600,
                    z: Math.random() * 2000 + 1,
                    size: Math.random() * 1.8 + 0.9,
                    color: colors[Math.floor(Math.random() * colors.length)],
                    twinkle: Math.random() * Math.PI * 2
                });
            }

            // Shooting Stars (Meteors)
            const meteors = [];
            function spawnMeteor() {
                if (meteors.length < 3 && Math.random() < 0.035) {
                    meteors.push({
                        x: Math.random() * w,
                        y: Math.random() * (h * 0.4),
                        len: Math.random() * 90 + 80,
                        speed: Math.random() * 14 + 16,
                        opacity: 1.0
                    });
                }
            }

            // Click Shockwaves
            const shockwaves = [];
            window.addEventListener('click', (e) => {
                shockwaves.push({ x: e.clientX, y: e.clientY, r: 0, maxR: 220, alpha: 0.9 });
            });

            let mouseX = 0, mouseY = 0;
            let currentSpeed = 6.0;
            let targetSpeed = 6.0;

            window.addEventListener('mousemove', (e) => {
                const normX = (e.clientX / w) * 2 - 1;
                const normY = (e.clientY / h) * 2 - 1;
                mouseX = normX * 240;
                mouseY = normY * 240;

                if (normX > 0.15) {
                    targetSpeed = 10.0 + (normX * 24.0); // Ultra fast forward
                } else if (normX < -0.15) {
                    targetSpeed = -8.0 - (Math.abs(normX) * 18.0); // Ultra fast reverse
                } else {
                    targetSpeed = 5.5; // Steady high cruise
                }
            });

            function render() {
                ctx.fillStyle = 'rgba(7, 3, 13, 0.4)';
                ctx.fillRect(0, 0, w, h);

                currentSpeed += (targetSpeed - currentSpeed) * 0.15;
                const centerOffsetX = cx - mouseX * 0.45;
                const centerOffsetY = cy - mouseY * 0.45;

                // Render Shockwaves
                for (let i = shockwaves.length - 1; i >= 0; i--) {
                    const sw = shockwaves[i];
                    sw.r += 9;
                    sw.alpha -= 0.035;
                    if (sw.alpha <= 0 || sw.r >= sw.maxR) {
                        shockwaves.splice(i, 1);
                        continue;
                    }
                    ctx.strokeStyle = `rgba(192, 132, 252, ${sw.alpha})`;
                    ctx.lineWidth = 2.5;
                    ctx.beginPath();
                    ctx.arc(sw.x, sw.y, sw.r, 0, Math.PI * 2);
                    ctx.stroke();
                }

                // Render Stars with Warp Streaks
                for (let i = 0; i < STAR_COUNT; i++) {
                    const s = stars[i];
                    s.twinkle += 0.08;

                    const prevZ = s.z;
                    s.z -= currentSpeed;

                    if (s.z <= 1) {
                        s.z = 2000;
                        s.x = (Math.random() - 0.5) * 3600;
                        s.y = (Math.random() - 0.5) * 3600;
                        continue;
                    }
                    if (s.z > 2000) {
                        s.z = 2;
                        continue;
                    }

                    const k = 420 / s.z;
                    const px = s.x * k + centerOffsetX;
                    const py = s.y * k + centerOffsetY;

                    const kPrev = 420 / (prevZ + (currentSpeed * 0.9));
                    const prevPx = s.x * kPrev + centerOffsetX;
                    const prevPy = s.y * kPrev + centerOffsetY;

                    if (px >= 0 && px <= w && py >= 0 && py <= h) {
                        const depth = 1 - (s.z / 2000);
                        const radius = Math.max(0.8, s.size * depth * 3.2);
                        const alpha = Math.min(1, Math.max(0.2, depth * (0.85 + Math.sin(s.twinkle) * 0.15)));

                        ctx.strokeStyle = s.color;
                        ctx.fillStyle = s.color;
                        ctx.globalAlpha = alpha;

                        if (Math.abs(currentSpeed) > 7.0) {
                            ctx.lineWidth = radius * 1.1;
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

                // Render Meteors
                spawnMeteor();
                for (let i = meteors.length - 1; i >= 0; i--) {
                    const m = meteors[i];
                    m.x -= m.speed * 1.2;
                    m.y += m.speed * 0.7;
                    m.opacity -= 0.025;

                    if (m.opacity <= 0 || m.x < -100 || m.y > h + 100) {
                        meteors.splice(i, 1);
                        continue;
                    }

                    ctx.strokeStyle = `rgba(240, 171, 252, ${m.opacity})`;
                    ctx.lineWidth = 2.0;
                    ctx.beginPath();
                    ctx.moveTo(m.x, m.y);
                    ctx.lineTo(m.x + m.len, m.y - (m.len * 0.58));
                    ctx.stroke();
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

body_start = text.find("<!-- Ultra High-Speed")
if body_start == -1:
    body_start = text.find("<!-- Three-Dimensional")
if body_start == -1:
    body_start = text.find("<script>")

text = text[:body_start] + cosmic_engine

with open(path, "w", encoding="utf-8") as f:
    f.write(text)

print("Cosmic Warp Engine with Meteors & Shockwaves deployed!")