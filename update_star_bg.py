path = "templates/landing.html"
with open(path, "r", encoding="utf-8-sig") as f:
    text = f.read()

# Replace Three.js animation script with interactive starfield
old_script_start = "// Three.js Interactive Deep Purple Scene"
new_star_engine = """// Three.js Real Stars Starfield with Directional Zoom
        const container = document.getElementById('canvas-container');
        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 2000);
        camera.position.z = 300;

        const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
        renderer.setSize(window.innerWidth, window.innerHeight);
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        container.appendChild(renderer.domElement);

        // Generate Real Floating Stars
        const starCount = 3500;
        const starGeo = new THREE.BufferGeometry();
        const positions = new Float32Array(starCount * 3);
        const colors = new Float32Array(starCount * 3);

        for (let i = 0; i < starCount * 3; i += 3) {
            positions[i] = (Math.random() - 0.5) * 1200;
            positions[i + 1] = (Math.random() - 0.5) * 1200;
            positions[i + 2] = (Math.random() - 0.5) * 1200;

            const shade = 0.7 + Math.random() * 0.3;
            colors[i] = 0.8 * shade;
            colors[i + 1] = 0.6 * shade;
            colors[i + 2] = 1.0 * shade;
        }

        starGeo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
        starGeo.setAttribute('color', new THREE.BufferAttribute(colors, 3));

        const starMat = new THREE.PointsMaterial({
            size: 1.8,
            vertexColors: true,
            transparent: true,
            opacity: 0.85
        });

        const starField = new THREE.Points(starGeo, starMat);
        scene.add(starField);

        // Mouse Tracking
        let mouseXRel = 0;
        window.addEventListener('mousemove', (e) => {
            const normX = (e.clientX / window.innerWidth) * 2 - 1;
            if (Math.abs(normX) > 0.25) {
                mouseXRel = normX;
            } else {
                mouseXRel = 0;
            }
        });

        function animate() {
            requestAnimationFrame(animate);

            starField.rotation.y += 0.0003;
            starField.rotation.x += 0.0001;

            if (mouseXRel > 0.25) {
                // Right side: Zoom in
                camera.position.z = Math.max(120, camera.position.z - (mouseXRel * 1.2));
            } else if (mouseXRel < -0.25) {
                // Left side: Zoom out
                camera.position.z = Math.min(550, camera.position.z + (Math.abs(mouseXRel) * 1.2));
            }

            renderer.render(scene, camera);
        }
        animate();

        window.addEventListener('resize', () => {
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        });
"""

if old_script_start in text:
    parts = text.split(old_script_start)
    text = parts[0] + new_star_engine + "\n    </script>\n</body>\n</html>"
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    print("Starfield background updated successfully!")
else:
    print("Script marker not found.")