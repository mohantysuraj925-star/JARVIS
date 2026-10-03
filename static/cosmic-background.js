(() => {
    const canvas = document.getElementById('cosmicCanvas3D');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let width;
    let height;
    let centerX;
    let centerY;

    function resize() {
        width = canvas.width = window.innerWidth;
        height = canvas.height = window.innerHeight;
        centerX = width / 2;
        centerY = height / 2;
    }

    window.addEventListener('resize', resize);
    resize();

    const stars = [];
    for (let index = 0; index < 900; index += 1) {
        stars.push({
            x: (Math.random() - 0.5) * 3200,
            y: (Math.random() - 0.5) * 3200,
            z: Math.random() * 2000 + 1,
            size: Math.random() * 1.8 + 0.8,
            color: Math.random() > 0.4 ? '#c084fc' : '#f0abfc',
        });
    }

    let mouseX = 0;
    let currentSpeed = 5;
    let targetSpeed = 5;

    window.addEventListener('mousemove', (event) => {
        const normalizedX = (event.clientX / width) * 2 - 1;
        mouseX = normalizedX * 220;
        if (normalizedX > 0.15) targetSpeed = 8 + normalizedX * 18;
        else if (normalizedX < -0.15) targetSpeed = -6 - Math.abs(normalizedX) * 14;
        else targetSpeed = 5;
    });

    function render() {
        ctx.fillStyle = 'rgba(6, 2, 12, 0.42)';
        ctx.fillRect(0, 0, width, height);
        currentSpeed += (targetSpeed - currentSpeed) * 0.12;

        for (const star of stars) {
            const previousZ = star.z;
            star.z -= currentSpeed;
            if (star.z <= 1) {
                star.z = 2000;
                star.x = (Math.random() - 0.5) * 3200;
                star.y = (Math.random() - 0.5) * 3200;
                continue;
            }
            if (star.z > 2000) {
                star.z = 2;
                continue;
            }

            const scale = 420 / star.z;
            const x = star.x * scale + centerX - mouseX * 0.4;
            const y = star.y * scale + centerY;
            const previousScale = 420 / (previousZ + currentSpeed * 0.9);
            const previousX = star.x * previousScale + centerX - mouseX * 0.4;
            const previousY = star.y * previousScale + centerY;

            if (x < 0 || x > width || y < 0 || y > height) continue;
            const depth = 1 - star.z / 2000;
            ctx.strokeStyle = star.color;
            ctx.fillStyle = star.color;
            ctx.globalAlpha = Math.min(1, depth * 1.2);

            if (Math.abs(currentSpeed) > 6.5) {
                ctx.lineWidth = star.size * depth * 2.5;
                ctx.beginPath();
                ctx.moveTo(previousX, previousY);
                ctx.lineTo(x, y);
                ctx.stroke();
            } else {
                ctx.beginPath();
                ctx.arc(x, y, star.size * depth * 2.5, 0, Math.PI * 2);
                ctx.fill();
            }
        }

        ctx.globalAlpha = 1;
        window.requestAnimationFrame(render);
    }

    render();
})();
