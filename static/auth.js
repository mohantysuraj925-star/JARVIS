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
  if (!u || !p) {
    alert('Please enter username and password.');
    return;
  }

  const endpoint = (currentAuthMode === 'register') ? '/api/admin/create-user' : '/api/heartbeat';
  try {
    const res = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: u, password: p })
    });

    if (res.ok) {
      closeAuthModal();
      alert(currentAuthMode === 'register' ? 'Node Registered! 10-Day Trial Active.' : 'Handshake Verified!');
      location.reload();
    } else {
      alert('Authentication Failed');
    }
  } catch (err) {
    alert('Server Connection Error');
  }
}

document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('button, a').forEach(el => {
    const txt = (el.innerText || '').toLowerCase();
    if (txt.includes('login') || txt.includes('sign in')) {
      el.onclick = (e) => { e.preventDefault(); openAuthModal('login'); };
    }
    if (txt.includes('register') || txt.includes('sign up')) {
      el.onclick = (e) => { e.preventDefault(); openAuthModal('register'); };
    }
  });
});
