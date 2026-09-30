import re

path = "server/app.py"
with open(path, "r", encoding="utf-8-sig") as f:
    text = f.read()

# 1. Glowing Cyberpunk Login/Register Modal UI + Dynamic Action Handlers
cyber_modal = """
<!-- Interactive Cyberpunk Auth Modal -->
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

<script>
let currentAuthMode = 'login';
function openAuthModal(mode) {
  currentAuthMode = mode;
  const t = document.getElementById('authTitle');
  const b = document.getElementById('authSubmitBtn');
  if (t) t.innerText = (mode === 'register') ? 'REGISTER NEW NODE' : 'OPERATOR LOGIN';
  if (b) b.innerText = (mode === 'register') ? 'CREATE OPERATOR' : 'AUTHENTICATE';
  const m = document.getElementById('cyberAuthModal');
  if (m) m.style.display = 'flex';
}

function closeAuthModal() {
  const m = document.getElementById('cyberAuthModal');
  if (m) m.style.display = 'none';
}

async function submitAuth() {
  const u = document.getElementById('authUsername').value.trim();
  const p = document.getElementById('authPassword').value.trim();
  if(!u || !p) { alert('Please provide username and password.'); return; }

  const endpoint = (currentAuthMode === 'register') ? '/api/admin/create-user' : '/api/heartbeat';
  const res = await fetch(endpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username: u, password: p })
  });

  if (res.ok) {
    closeAuthModal();
    alert(currentAuthMode === 'register' ? 'Node Registered Successfully (10-Day Trial Provisioned)!' : 'Handshake Verified!');
    location.reload();
  } else {
    alert('Authentication Failed');
  }
}

// Intercept existing login/register triggers cleanly
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('button, a').forEach(el => {
    const txt = (el.innerText || '').toLowerCase();
    if(txt.includes('login') || txt.includes('sign in')) {
      el.onclick = (e) => { e.preventDefault(); openAuthModal('login'); };
    }
    if(txt.includes('register') || txt.includes('sign up')) {
      el.onclick = (e) => { e.preventDefault(); openAuthModal('register'); };
    }
  });
});
</script>
"""

if 'id="cyberAuthModal"' not in text:
    text = text.replace("</body>", cyber_modal + "\n</body>")

with open(path, "w", encoding="utf-8") as f:
    f.write(text)

print("Cyberpunk Auth Modal & Real Click Actions Injected!")