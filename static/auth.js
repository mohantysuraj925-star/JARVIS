async function performAuth(event) {
    if (event) event.preventDefault();
    const uInput = document.querySelector('input[type="text"], input[name="username"], #username');
    const pInput = document.querySelector('input[type="password"], input[name="password"], #password');

    if (!uInput || !pInput) return;

    const username = uInput.value.trim();
    const password = pInput.value.trim();

    if (!username || !password) {
        alert("Please enter both username and password");
        return;
    }

    try {
        const res = await fetch("/api/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, password })
        });

        const data = await res.json();
        if (res.ok && data.status === "success") {
            document.cookie = `username=${encodeURIComponent(username)}; path=/; max-age=2592000; SameSite=Lax`;
            window.location.reload();
        } else {
            alert(data.message || "Login failed");
        }
    } catch (e) {
        alert("Server connection failed. Try again.");
    }
}