import os
import sqlite3

# 1. SQLite Database Setup (Permanent Persistence)
conn = sqlite3.connect("portal_data.db")
c = conn.cursor()
c.execute("""
CREATE TABLE IF NOT EXISTS permissions (
    username TEXT PRIMARY KEY,
    mobile_allowed INTEGER DEFAULT 0
)
""")
c.execute("""
CREATE TABLE IF NOT EXISTS global_settings (
    key TEXT PRIMARY KEY,
    value TEXT
)
""")
c.execute("INSERT OR IGNORE INTO global_settings (key, value) VALUES ('global_mobile', '0')")
conn.commit()
conn.close()
print("[OK] Database verified.")

# 2. Create Standalone Mobile Dashboard Template
os.makedirs(os.path.join("server", "templates"), exist_ok=True)
mobile_html_path = os.path.join("server", "templates", "mobile_dashboard.html")

mobile_template_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>JARVIS Mobile AI</title>
    <style>
        :root {
            --bg-color: #050b14;
            --accent-color: #00d2ff;
            --panel-bg: rgba(6, 18, 38, 0.75);
            --glow: 0 0 15px #00d2ff;
        }
        body.stealth-mode {
            --bg-color: #000000;
            --accent-color: #ff3333;
            --panel-bg: rgba(20, 0, 0, 0.8);
            --glow: 0 0 15px #ff3333;
        }
        body.cyber-mode {
            --bg-color: #0d001a;
            --accent-color: #d946ef;
            --panel-bg: rgba(30, 5, 45, 0.8);
            --glow: 0 0 15px #d946ef;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', sans-serif; }
        body {
            background: var(--bg-color);
            color: #fff;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            overflow-x: hidden;
            transition: background 0.4s ease;
        }
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 15px 20px;
            background: var(--panel-bg);
            border-bottom: 1px solid var(--accent-color);
            box-shadow: var(--glow);
        }
        .theme-btn {
            background: transparent;
            border: 1px solid var(--accent-color);
            color: var(--accent-color);
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 12px;
            cursor: pointer;
        }
        .reactor-container {
            flex: 1;
            display: flex;
            justify-content: center;
            align-items: center;
            position: relative;
            margin: 20px 0;
        }
        .core {
            width: 170px;
            height: 170px;
            border-radius: 50%;
            border: 2px dashed var(--accent-color);
            display: flex;
            justify-content: center;
            align-items: center;
            box-shadow: var(--glow);
            animation: spin 12s linear infinite;
        }
        .inner-core {
            width: 100px;
            height: 100px;
            border-radius: 50%;
            background: radial-gradient(circle, var(--accent-color) 0%, transparent 70%);
            box-shadow: var(--glow);
        }
        @keyframes spin { 100% { transform: rotate(360deg); } }
        .controls {
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }
        .action-card {
            background: var(--panel-bg);
            border: 1px solid rgba(255,255,255,0.1);
            border-left: 3px solid var(--accent-color);
            padding: 14px;
            border-radius: 10px;
            font-size: 14px;
        }
        .mic-btn {
            background: var(--accent-color);
            color: #000;
            border: none;
            padding: 16px;
            border-radius: 50px;
            font-weight: bold;
            font-size: 16px;
            box-shadow: var(--glow);
            cursor: pointer;
            margin-top: 10px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h3 style="color: var(--accent-color); letter-spacing: 1px;">JARVIS MOBILE</h3>
        <button class="theme-btn" onclick="cycleTheme()">Switch UI</button>
    </div>

    <div class="reactor-container">
        <div class="core">
            <div class="inner-core"></div>
        </div>
    </div>

    <div class="controls">
        <div class="action-card">Status: <b>Connected (Cloud Mode)</b></div>
        <div class="action-card" id="voiceStatus">Tap mic to speak command</div>
        <button class="mic-btn" onclick="toggleVoice()">VOICE COMMAND</button>
    </div>

    <script>
        const themes = ['', 'stealth-mode', 'cyber-mode'];
        let curTheme = 0;
        function cycleTheme() {
            curTheme = (curTheme + 1) % themes.length;
            document.body.className = themes[curTheme];
        }
        function toggleVoice() {
            const status = document.getElementById('voiceStatus');
            status.innerText = "Listening to voice...";
            setTimeout(() => { status.innerText = "Command received & processed."; }, 2500);
        }
    </script>
</body>
</html>
"""

with open(mobile_html_path, "w", encoding="utf-8") as f:
    f.write(mobile_template_content)
print("[OK] Dedicated mobile UI file created.")

# 3. Patch Server app.py for Smart Routing (Without removing old routes)
app_path = os.path.join("server", "app.py")
if os.path.exists(app_path):
    with open(app_path, "r", encoding="utf-8") as f:
        code = f.read()

    new_logic = """
from fastapi import Request
from fastapi.responses import HTMLResponse
import sqlite3

def check_db_perms(user):
    conn = sqlite3.connect("portal_data.db")
    c = conn.cursor()
    c.execute("SELECT value FROM global_settings WHERE key='global_mobile'")
    g = c.fetchone()
    if g and g[0] == '1':
        conn.close()
        return True
    if user:
        c.execute("SELECT mobile_allowed FROM permissions WHERE username=?", (user,))
        r = c.fetchone()
        if r and r[0] == 1:
            conn.close()
            return True
    conn.close()
    return False

@app.get("/api/user/access_status")
async def user_access_status(username: str = ""):
    return {"allowed": check_db_perms(username)}

@app.get("/mobile", response_class=HTMLResponse)
async def mobile_portal_view(request: Request):
    template_path = os.path.join("server", "templates", "mobile_dashboard.html")
    if not os.path.exists(template_path):
        template_path = os.path.join("templates", "mobile_dashboard.html")
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()
"""
    if "/mobile" not in code:
        code += "\n" + new_logic
        with open(app_path, "w", encoding="utf-8") as f:
            f.write(code)
        print("[OK] Smart mobile portal routing added.")
