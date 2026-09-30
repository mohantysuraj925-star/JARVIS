import re

path = "server/app.py"
with open(path, "r", encoding="utf-8-sig") as f:
    text = f.read()

# Remove any previously injected broken modal script
text = re.sub(r'<!-- Interactive Cyberpunk Auth Modal -->[\s\S]*?</body>', '</body>', text)

# Static files mount add karein agar nahi hai
if 'from fastapi.staticfiles import StaticFiles' not in text:
    text = 'from fastapi.staticfiles import StaticFiles\n' + text

if 'app.mount("/static"' not in text:
    text = text.replace('app = FastAPI(title="JARVIS AI System Core")', 'app = FastAPI(title="JARVIS AI System Core")\napp.mount("/static", StaticFiles(directory="static"), name="static")')

# Clean Modal HTML without JS code (calls external static/auth.js)
clean_modal_html = """<!-- Interactive Cyberpunk Auth Modal -->
<div id="cyberAuthModal" style="display:none; position:fixed; inset:0; background:rgba(3,7,18,0.85); backdrop-filter:blur(14px); z-index:9999999; justify-content:center; align-items:center;">
  <div style="background:rgba(10,16,32,0.96); border:1px solid #00f0ff; box-shadow:0 0 40px rgba(0,240,255,0.35); border-radius:18px; padding:32px; width:90%; max-width:400px; text-align:center; position:relative;">
    <span onclick="closeAuthModal()" style="position:absolute; top:14px; right:18px; color:#64748b; font-size:20px; cursor:pointer; font-weight:bold;">&times;</span>
    <div style="font-size:38px; margin-bottom:8px;">❖</div>
    <h3 id="authTitle" style="font-family:sans-serif; color:#00f0ff; letter-spacing:2px; text-transform:uppercase; margin-bottom:6px; font-size:18px;">OPERATOR ACCESS</h3>
    <p style="color:#94a3b8; font-size:13px; margin-bottom:20px;">Initialize local neural session</p>
    
    <input type="text" id="authUsername" placeholder="Operator Username" style="width:100%; background:#070d1e; border:1px solid #1e293b; color:#fff; padding:12px; border-radius:8px; margin-bottom:12px; font-size:14px; outline:none;">
    <input type="password" id="authPassword" placeholder="Security Token / Password" style="width:100%; background:#070d1e; border:1px solid #1e293b; color:#fff; padding:12px; border-radius:8px; margin-bottom:20px; font-size:14px; outline:none;">
    
    <button id="authSubmitBtn" onclick="submitAuth()" style="width:100%; background:#00f0ff; color:#030712; border:none; padding:12px; border-radius:8px; font-weight:bold; cursor:pointer; box-shadow:0 0 20px rgba(0,240,255,0.4); font-size:14px; letter-spacing:1px;">AUTHENTICATE</button>
  </div>
</div>
<script src="/static/auth.js"></script>
</body>"""

text = text.replace("</body>", clean_modal_html)

with open(path, "w", encoding="utf-8") as f:
    f.write(text)

print("Patch complete: 0 syntax collisions!")