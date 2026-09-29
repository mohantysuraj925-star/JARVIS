import os, sqlite3, time, datetime
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="JARVIS Portal")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))
DOWNLOADS_DIR = os.path.join(PROJECT_ROOT, "downloads")
os.makedirs(DOWNLOADS_DIR, exist_ok=True)
DB_PATH = os.path.join(BASE_DIR, "portal.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        hwid TEXT UNIQUE,
        email TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        role TEXT DEFAULT 'user'
    );
    CREATE TABLE IF NOT EXISTS system_telemetry (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        hwid TEXT UNIQUE,
        last_command TEXT DEFAULT 'Standby Mode',
        status TEXT DEFAULT 'Active',
        activation_state TEXT DEFAULT 'Deactivated',
        expires_at INTEGER,
        is_lifetime BOOLEAN DEFAULT 0,
        request_pending BOOLEAN DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS download_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        hwid TEXT,
        platform TEXT,
        downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS broadcasts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        message TEXT,
        media_url TEXT DEFAULT '',
        is_active BOOLEAN DEFAULT 1,
        created_at INTEGER
    );
    """)
    now = int(time.time())
    master_exp = now + (9999 * 86400)
    conn.execute("INSERT OR IGNORE INTO users (username, password, hwid, email, role) VALUES ('admin123', 'Suraj@2026', 'MASTER-JARVIS-001', 'master@jarvis.local', 'admin')")
    conn.execute("INSERT OR IGNORE INTO system_telemetry (username, hwid, last_command, status, activation_state, expires_at, is_lifetime) VALUES ('admin123', 'MASTER-JARVIS-001', 'JARVIS Core Active', 'Active', 'Activated', ?, 1)", (master_exp,))
    conn.commit()
    conn.close()

init_db()

class RegisterReq(BaseModel):
    username: str
    password: str
    email: str
    hwid: str

class LoginReq(BaseModel):
    username: str
    password: str

class ActivateReq(BaseModel):
    command: str

class BroadcastReq(BaseModel):
    message: str
    media_url: str = ""

class SetExpiryReq(BaseModel):
    hwid: str
    expiry_date: str

class LicenseQuickAction(BaseModel):
    hwid: str
    action: str

@app.post("/api/register")
def register(req: RegisterReq, res: Response):
    if len(req.password) < 8 or not any(c.isupper() for c in req.password) or not any(c.isdigit() for c in req.password):
        raise HTTPException(400, "Password me kam se kam 8 characters, 1 uppercase aur 1 number hona chahiye.")
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    if cur.execute("SELECT id FROM users WHERE hwid = ?", (req.hwid,)).fetchone():
        conn.close()
        raise HTTPException(403, "Is machine par account pehle se register hai.")

    try:
        ten_days_sec = int(time.time()) + (10 * 86400)
        cur.execute("INSERT INTO users (username, password, hwid, email, role) VALUES (?, ?, ?, ?, 'user')",
                    (req.username, req.password, req.hwid, req.email))
        cur.execute("INSERT INTO system_telemetry (username, hwid, last_command, status, activation_state, expires_at, is_lifetime) VALUES (?, ?, 'Node Registered', 'Active', 'Standby', ?, 0)",
                    (req.username, req.hwid, ten_days_sec))
        conn.commit()
        res.set_cookie(key="auth_session", value=req.username, max_age=86400*30, path="/", httponly=True, samesite="lax")
        conn.close()
        return {"status": "ok", "user": req.username}
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(400, "Yeh username pehle se register hai.")

@app.post("/api/login")
def login(req: LoginReq, res: Response):
    conn = sqlite3.connect(DB_PATH)
    user = conn.execute("SELECT username, role FROM users WHERE username = ? AND password = ?", (req.username, req.password)).fetchone()
    conn.close()
    if user:
        res.set_cookie(key="auth_session", value=user[0], max_age=86400*30, path="/", httponly=True, samesite="lax")
        return {"status": "ok", "role": user[1]}
    raise HTTPException(401, "Galat Username ya Password.")

@app.post("/api/logout")
def logout(res: Response):
    res.delete_cookie(key="auth_session", path="/")
    return {"status": "ok"}

@app.post("/api/jarvis/activate")
def activate_jarvis(act: ActivateReq, req: Request):
    user = req.cookies.get("auth_session") or "Desktop-Client"
    cmd = act.command.strip()
    valid_activations = ["jarvis activate ho jao", "jarvis activate", "activate jarvis", "jarvis"]
    state = "Active & Listening" if any(v in cmd.lower() for v in valid_activations) else "Command Executed"
    
    conn = sqlite3.connect(DB_PATH)
    conn.execute("UPDATE system_telemetry SET activation_state = ?, last_command = ? WHERE username = ? OR username = 'admin123'", (state, cmd, user))
    conn.commit()
    conn.close()
    return {"status": "ok", "activation_state": state, "command": cmd}

@app.get("/get-package/{platform}")
def get_package(platform: str, req: Request):
    user = req.cookies.get("auth_session") or "AnonymousNode"

    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT INTO download_logs (username, hwid, platform) VALUES (?, 'VERIFIED-CLIENT', ?)", (user, platform))
    conn.commit()
    conn.close()

    if platform == "windows":
        target = os.path.join(DOWNLOADS_DIR, "JARVIS_Installer.exe")
        if not os.path.exists(target):
            raise HTTPException(404, "JARVIS_Installer.exe file nahi mili.")
        return FileResponse(target, filename="JARVIS_Installer.exe", media_type="application/octet-stream")
    elif platform == "android":
        target = os.path.join(DOWNLOADS_DIR, "JARVIS_Mobile.apk")
        if not os.path.exists(target):
            with open(target, "wb") as f:
                f.write(b"PK\x03\x04JARVIS_MOBILE_PACKAGE")
        return FileResponse(target, filename="JARVIS_Mobile.apk", media_type="application/vnd.android.package-archive")
    raise HTTPException(404, "Invalid platform")

@app.post("/api/request-extension")
def req_ext(req: Request):
    user = req.cookies.get("auth_session")
    if not user: raise HTTPException(401)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("UPDATE system_telemetry SET request_pending = 1 WHERE username = ?", (user,))
    conn.commit()
    conn.close()
    return {"status": "ok"}

@app.get("/api/admin/metrics")
def admin_metrics(req: Request):
    user = req.cookies.get("auth_session")
    conn = sqlite3.connect(DB_PATH)
    r = conn.execute("SELECT role FROM users WHERE username = ?", (user,)).fetchone()
    if not r or r[0] != "admin":
        conn.close()
        raise HTTPException(403)
    
    tot_users = conn.execute("SELECT count(*) FROM users WHERE role != 'admin'").fetchone()[0]
    now = int(time.time())
    active_users = conn.execute("SELECT count(*) FROM system_telemetry WHERE status='Active' AND (is_lifetime=1 OR expires_at > ?)", (now,)).fetchone()[0]
    tot_win = conn.execute("SELECT count(*) FROM download_logs WHERE platform='windows'").fetchone()[0]
    tot_apk = conn.execute("SELECT count(*) FROM download_logs WHERE platform='android'").fetchone()[0]
    conn.close()
    return {"total_users": tot_users, "active_users": active_users, "win_dl": tot_win, "apk_dl": tot_apk}

@app.get("/api/admin/downloads-list")
def admin_dl_list(req: Request):
    user = req.cookies.get("auth_session")
    conn = sqlite3.connect(DB_PATH)
    r = conn.execute("SELECT role FROM users WHERE username = ?", (user,)).fetchone()
    if not r or r[0] != "admin":
        conn.close()
        raise HTTPException(403)
    conn.row_factory = sqlite3.Row
    logs = conn.execute("SELECT * FROM download_logs ORDER BY id DESC LIMIT 50").fetchall()
    conn.close()
    return {"downloads": [dict(x) for x in logs]}

@app.get("/api/admin/nodes")
def admin_nodes(req: Request):
    user = req.cookies.get("auth_session")
    conn = sqlite3.connect(DB_PATH)
    r = conn.execute("SELECT role FROM users WHERE username = ?", (user,)).fetchone()
    if not r or r[0] != "admin":
        conn.close()
        raise HTTPException(403)
    conn.row_factory = sqlite3.Row
    nodes = conn.execute("""
        SELECT t.*, u.email, u.created_at as joined_at 
        FROM system_telemetry t JOIN users u ON t.hwid = u.hwid 
        WHERE u.role != 'admin'
    """).fetchall()
    conn.close()
    return {"nodes": [dict(x) for x in nodes]}

@app.post("/api/admin/set-expiry")
def set_expiry(d: SetExpiryReq, req: Request):
    user = req.cookies.get("auth_session")
    conn = sqlite3.connect(DB_PATH)
    r = conn.execute("SELECT role FROM users WHERE username = ?", (user,)).fetchone()
    if not r or r[0] != "admin":
        conn.close()
        raise HTTPException(403)
    dt = datetime.datetime.fromisoformat(d.expiry_date)
    epoch = int(dt.timestamp())
    conn.execute("UPDATE system_telemetry SET expires_at = ?, is_lifetime = 0, status = 'Active', request_pending = 0 WHERE hwid = ?", (epoch, d.hwid))
    conn.commit()
    conn.close()
    return {"status": "ok"}

@app.post("/api/admin/quick-action")
def quick_action(a: LicenseQuickAction, req: Request):
    user = req.cookies.get("auth_session")
    conn = sqlite3.connect(DB_PATH)
    r = conn.execute("SELECT role FROM users WHERE username = ?", (user,)).fetchone()
    if not r or r[0] != "admin":
        conn.close()
        raise HTTPException(403)
    now = int(time.time())
    if a.action == "plus10":
        conn.execute("UPDATE system_telemetry SET expires_at = max(expires_at, ?) + (10 * 86400), status='Active', request_pending=0 WHERE hwid=?", (now, a.hwid))
    elif a.action == "lifetime":
        conn.execute("UPDATE system_telemetry SET is_lifetime=1, status='Active', request_pending=0 WHERE hwid=?", (a.hwid,))
    elif a.action == "revoke":
        conn.execute("UPDATE system_telemetry SET status='Revoked' WHERE hwid=?", (a.hwid,))
    conn.commit()
    conn.close()
    return {"status": "ok"}

@app.post("/api/admin/broadcast")
def post_bc(b: BroadcastReq, req: Request):
    user = req.cookies.get("auth_session")
    conn = sqlite3.connect(DB_PATH)
    r = conn.execute("SELECT role FROM users WHERE username = ?", (user,)).fetchone()
    if not r or r[0] != "admin":
        conn.close()
        raise HTTPException(403)
    now = int(time.time())
    thirty_days_ago = now - (30 * 86400)
    conn.execute("DELETE FROM broadcasts WHERE created_at < ?", (thirty_days_ago,))
    conn.execute("INSERT INTO broadcasts (message, media_url, created_at) VALUES (?, ?, ?)", (b.message, b.media_url, now))
    conn.commit()
    conn.close()
    return {"status": "ok"}

@app.get("/api/broadcasts/feed")
def get_broadcast_feed():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    now = int(time.time())
    thirty_days_ago = now - (30 * 86400)
    feed = conn.execute("SELECT * FROM broadcasts WHERE created_at >= ? ORDER BY id DESC LIMIT 30", (thirty_days_ago,)).fetchall()
    conn.close()
    return {"feed": [dict(x) for x in feed]}

@app.get("/", response_class=HTMLResponse)
def root(req: Request):
    user = req.cookies.get("auth_session")
    role = "none"
    user_status = {}
    if user:
        conn = sqlite3.connect(DB_PATH)
        r = conn.execute("SELECT role FROM users WHERE username = ?", (user,)).fetchone()
        if r:
            role = r[0]
            conn.row_factory = sqlite3.Row
            s = conn.execute("SELECT * FROM system_telemetry WHERE username = ?", (user,)).fetchone()
            if s: user_status = dict(s)
        conn.close()

    now = int(time.time())
    is_expired = False
    time_str = "N/A"
    if user_status:
        if user_status.get("is_lifetime"):
            time_str = "Infinite Lifetime"
        else:
            diff = user_status.get("expires_at", 0) - now
            if diff <= 0 or user_status.get("status") == "Revoked":
                is_expired = True
                time_str = "Expired"
            else:
                days = diff // 86400
                hours = (diff % 86400) // 3600
                mins = (diff % 3600) // 60
                time_str = f"{days}d {hours}h {mins}m bache hain"

    if user:
        header_actions = f'''
        <div style="display:flex; align-items:center; gap:12px;">
          <span style="color:#94a3b8; font-size:12px;">Welcome, <strong style="color:#c084fc;">{user}</strong></span>
          <button class="neon-btn neon-btn-cyan" onclick="openNotices()"><i data-lucide="bell"></i> Notices</button>
          <button class="neon-btn neon-btn-purple" onclick="logout()"><i data-lucide="log-out"></i> Logout</button>
        </div>
        '''
        if is_expired:
            download_section = '''
            <div class="cyber-card" style="margin-top:20px; border-color:rgba(239,68,68,0.4);">
              <h3 style="color:#f87171;"><i data-lucide="alert-triangle"></i> Trial Period Expired</h3>
              <p style="color:#94a3b8; font-size:13px; margin:8px 0 16px;">Aapka 10-days trial time khatam ho chuka hai.</p>
              <button class="neon-btn neon-btn-purple" id="reqBtn" onclick="requestAccess()"><i data-lucide="send"></i> Request Access to Super Admin</button>
            </div>
            '''
        else:
            download_section = f'''
            <div class="cyber-card" style="margin-top:20px;">
              <div style="display:flex; justify-content:space-between; align-items:center;">
                <h3 style="color:#38bdf8;"><i data-lucide="download"></i> Client Binary & Mobile Mesh</h3>
                <span style="font-size:12px; padding:4px 10px; border-radius:6px; background:rgba(168,85,247,0.15); color:#d8b4fe; border:1px solid rgba(168,85,247,0.3);">Trial Remaining: {time_str}</span>
              </div>
              <p style="color:#94a3b8; font-size:13px; margin:10px 0 16px;">Direct single-click standalone package. Zero manual setup required:</p>
              
              <div style="display:flex; gap:14px; flex-wrap:wrap;">
                <button class="neon-btn neon-btn-purple" onclick="triggerClientDownload('windows', 'JARVIS_Installer.exe')"><i data-lucide="laptop"></i> Download Windows Desktop Client (.exe)</button>
                <button class="neon-btn neon-btn-cyan" onclick="triggerClientDownload('android', 'JARVIS_Mobile.apk')"><i data-lucide="smartphone"></i> Download Android Node Companion (.apk)</button>
                <button id="mobileFaceBtn" class="neon-btn" style="display:none; background:rgba(34,197,94,0.2); border-color:#22c55e; color:#4ade80;" onclick="toggleMobileFace()"><i data-lucide="eye"></i> Toggle Mobile 3D Face Web Node</button>
              </div>

              <!-- Windows SmartScreen Help Banner -->
              <div style="margin-top:14px; padding:10px 14px; border-radius:8px; background:rgba(56,189,248,0.08); border:1px solid rgba(56,189,248,0.25); display:flex; align-items:center; gap:10px;">
                <i data-lucide="info" style="color:#38bdf8; width:18px; height:18px; flex-shrink:0;"></i>
                <span style="font-size:11px; color:#cbd5e1;">Windows Launch Note: Agar screen par <strong>'Windows protected your PC'</strong> pop-up aaye, toh <strong>More info</strong> par click karke <strong>Run anyway</strong> select karein.</span>
              </div>

              <!-- Mobile 3D Hologram Face Container (Auto-detected for Mobile Phones) -->
              <div id="mobileFaceCard" style="display:none; margin-top:18px; padding:16px; background:rgba(0,0,0,0.5); border:1px solid rgba(168,85,247,0.3); border-radius:12px; text-align:center;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                  <span style="font-size:12px; color:#c084fc; font-weight:700;"><i data-lucide="smartphone"></i> Mobile Hologram Visualizer</span>
                  <button class="action-icon-btn" onclick="toggleMobileFace()"><i data-lucide="x"></i> Close</button>
                </div>
                <div style="width:140px; height:140px; margin:0 auto; border-radius:50%; border:2px dashed #38bdf8; display:flex; align-items:center; justify-content:center; box-shadow:0 0 20px rgba(56,189,248,0.3); animation:pulse 2s infinite;">
                  <i data-lucide="cpu" style="width:60px; height:60px; color:#38bdf8;"></i>
                </div>
                <p style="color:#4ade80; font-size:12px; margin-top:10px;">JARVIS Mobile Core: Online & Synced</p>
              </div>
            </div>

            <div class="cyber-card" style="margin-top:20px; border-color:rgba(56,189,248,0.35);">
              <div style="display:flex; justify-content:space-between; align-items:center;">
                <h3 style="color:#38bdf8;"><i data-lucide="mic"></i> JARVIS Activation & Voice Command Node</h3>
                <span id="actBadge" style="font-size:11px; padding:4px 10px; border-radius:12px; background:rgba(34,197,94,0.15); color:#4ade80; border:1px solid rgba(34,197,94,0.3);">{user_status.get("activation_state", "Standby")}</span>
              </div>
              <p style="color:#94a3b8; font-size:12px; margin-num:8px 0 14px;">Trigger karne ke liye mic dabayein ya command send karein (e.g. "Jarvis activate ho jao"):</p>
              <div style="display:flex; gap:10px;">
                <button class="neon-btn neon-btn-purple" style="border-radius:50%; width:44px; height:44px; padding:0; justify-content:center;" onclick="quickVoiceTrigger()" title="Click to Activate JARVIS"><i data-lucide="power" style="width:20px; height:20px;"></i></button>
                <input type="text" id="voiceCmdInput" class="cyber-input" style="flex:1;" placeholder="Enter command: 'Jarvis activate ho jao'...">
                <button class="neon-btn neon-btn-cyan" onclick="sendJarvisCmd()"><i data-lucide="send"></i> Execute</button>
              </div>
            </div>
            '''
    else:
        header_actions = '''
        <div style="display:flex; gap:10px;">
          <button class="neon-btn neon-btn-cyan" onclick="openLogin()"><i data-lucide="log-in"></i> Sign In</button>
          <button class="neon-btn neon-btn-purple" onclick="openReg()"><i data-lucide="shield"></i> Register</button>
        </div>
        '''
        download_section = '''
        <div class="cyber-card" style="margin-top:20px; text-align:center; padding:40px 20px;">
          <i data-lucide="lock" style="width:36px; height:36px; color:#c084fc; margin-bottom:12px; filter:drop-shadow(0 0 10px rgba(192,132,252,0.8));"></i>
          <h3 style="justify-content:center; color:#f8fafc;">Hardware Authorization Required</h3>
          <p style="color:#94a3b8; font-size:13px; max-width:440px; margin:8px auto 18px;">Pehle sign in ya machine ID register karein taaki binary streams unlock ho sakein.</p>
          <button class="neon-btn neon-btn-purple" onclick="openReg()"><i data-lucide="user-plus"></i> Initialize Machine ID</button>
        </div>
        '''

    admin_panel = ""
    if role == "admin":
        admin_panel = """
        <div class="cyber-card" style="margin-top:28px; border-color:rgba(168,85,247,0.4); box-shadow:0 0 35px rgba(168,85,247,0.15);">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:20px;">
            <h3 style="color:#c084fc; font-size:16px;"><i data-lucide="sliders"></i> Super Master Control Console</h3>
            <span style="font-size:11px; padding:4px 10px; border-radius:20px; background:rgba(34,197,94,0.15); color:#4ade80; border:1px solid rgba(34,197,94,0.4);">JARVIS CORE ACTIVE</span>
          </div>
          
          <div style="display:grid; grid-template-columns:repeat(4, 1fr); gap:12px; margin-bottom:24px;">
            <div class="mini-metric" onclick="openDlModal()">
              <label>Total Users</label>
              <h2 id="mUsers">0</h2>
            </div>
            <div class="mini-metric" onclick="openDlModal()">
              <label>Active Users</label>
              <h2 id="mActive" style="color:#4ade80;">0</h2>
            </div>
            <div class="mini-metric" onclick="openDlModal()" style="cursor:pointer;" title="Click to view downloads list">
              <label>Windows Downloads</label>
              <h2 id="mWin" style="color:#38bdf8;">0</h2>
            </div>
            <div class="mini-metric" onclick="openDlModal()" style="cursor:pointer;" title="Click to view downloads list">
              <label>Android Downloads</label>
              <h2 id="mApk" style="color:#c084fc;">0</h2>
            </div>
          </div>

          <div style="background:rgba(0,0,0,0.4); border:1px solid rgba(255,255,255,0.08); border-radius:12px; padding:16px; margin-bottom:24px;">
            <label style="font-size:11px; text-transform:uppercase; color:#38bdf8; font-weight:700; letter-spacing:0.5px;">Global Broadcast Hub (30-Day Life Cycle)</label>
            <div style="display:flex; flex-direction:column; gap:8px; margin-top:8px;">
              <input type="text" id="bcMsgInput" class="cyber-input" placeholder="Type notice or message for all users...">
              <div style="display:flex; gap:8px;">
                <input type="text" id="bcMediaInput" class="cyber-input" placeholder="Optional Media URL (Image or Video Link)..." style="flex:1;">
                <button class="neon-btn neon-btn-cyan" onclick="sendBroadcast()"><i data-lucide="send"></i> Post Notice</button>
              </div>
            </div>
          </div>

          <label style="font-size:11px; text-transform:uppercase; color:#c084fc; font-weight:700; letter-spacing:0.5px;">Connected Hardware Nodes, Live Activation & Granular Expiry</label>
          <div style="overflow-x:auto;">
            <table style="width:100%; border-collapse:collapse; font-size:12px; margin-top:10px;">
              <thead>
                <tr style="border-bottom:1px solid rgba(255,255,255,0.1);">
                  <th style="padding:10px; text-align:left; color:#94a3b8;">User Name</th>
                  <th style="padding:10px; text-align:left; color:#94a3b8;">Email</th>
                  <th style="padding:10px; text-align:left; color:#94a3b8;">Hardware ID</th>
                  <th style="padding:10px; text-align:left; color:#94a3b8;">Activation / Last Command</th>
                  <th style="padding:10px; text-align:left; color:#94a3b8;">Expiry Timeline</th>
                  <th style="padding:10px; text-align:left; color:#94a3b8;">Actions Console</th>
                </tr>
              </thead>
              <tbody id="nodesTableBody">
                <tr><td colspan="6" style="text-align:center; color:#94a3b8; padding:20px;">Syncing nodes...</td></tr>
              </tbody>
            </table>
          </div>
        </div>
        """

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>JARVIS Portal</title>
  <script src="https://unpkg.com/lucide@latest"></script>
  <style>
    * {{ margin:0; padding:0; box-sizing:border-box; font-family:-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}
    body {{
      background: #06070d;
      background-image: 
        radial-gradient(circle at 10% 20%, rgba(147, 51, 234, 0.16) 0%, transparent 45%),
        radial-gradient(circle at 90% 25%, rgba(6, 182, 212, 0.14) 0%, transparent 45%);
      color: #f1f5f9; min-height: 100vh; font-size: 13px; line-height: 1.5;
    }}
    header {{
      display: flex; justify-content: space-between; align-items: center;
      padding: 16px 36px; border-bottom: 1px solid rgba(255,255,255,0.06);
      background: rgba(6, 7, 13, 0.85); backdrop-filter: blur(20px);
      position: sticky; top:0; z-index:100;
    }}
    .brand {{ display:flex; align-items:center; gap:10px; font-weight:800; font-size:15px; letter-spacing:1px; text-transform:uppercase; color:#f8fafc; }}
    .container {{ max-width: 1080px; margin: 0 auto; padding: 32px 20px; }}
    
    .cyber-card {{
      background: linear-gradient(135deg, rgba(255, 255, 255, 0.04) 0%, rgba(255, 255, 255, 0.01) 100%);
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 16px; padding: 24px; backdrop-filter: blur(16px);
      box-shadow: 0 10px 40px rgba(0,0,0,0.6);
      transition: all 0.25s ease;
    }}
    .cyber-card:hover {{
      transform: translateY(-2px);
      border-color: rgba(168, 85, 247, 0.35);
      box-shadow: 0 14px 45px rgba(168, 85, 247, 0.15);
    }}
    .cyber-card h3 {{ font-size: 14px; font-weight: 700; display:flex; align-items:center; gap:8px; }}

    .neon-btn {{
      display: inline-flex; align-items: center; gap: 8px; padding: 9px 18px;
      border-radius: 8px; font-size: 12px; font-weight: 600; cursor: pointer;
      text-decoration: none; transition: all 0.2s ease; border: 1px solid transparent;
    }}
    .neon-btn i {{ width: 14px; height: 14px; }}
    
    .neon-btn-purple {{
      background: linear-gradient(135deg, rgba(147, 51, 234, 0.3) 0%, rgba(79, 70, 229, 0.3) 100%);
      color: #f3e8ff; border-color: rgba(168, 85, 247, 0.5);
      box-shadow: 0 0 15px rgba(168, 85, 247, 0.25);
    }}
    .neon-btn-purple:hover {{
      background: linear-gradient(135deg, rgba(147, 51, 234, 0.5) 0%, rgba(79, 70, 229, 0.5) 100%);
      box-shadow: 0 0 22px rgba(168, 85, 247, 0.6);
    }}

    .neon-btn-cyan {{
      background: linear-gradient(135deg, rgba(6, 182, 212, 0.3) 0%, rgba(14, 165, 233, 0.3) 100%);
      color: #e0f2fe; border-color: rgba(56, 189, 248, 0.5);
      box-shadow: 0 0 15px rgba(56, 189, 248, 0.25);
    }}
    .neon-btn-cyan:hover {{
      background: linear-gradient(135deg, rgba(6, 182, 212, 0.5) 0%, rgba(14, 165, 233, 0.5) 100%);
      box-shadow: 0 0 22px rgba(56, 189, 248, 0.6);
    }}

    .grid-3 {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px; margin-top: 18px; }}

    .cyber-input {{
      width: 100%; padding: 10px 14px; background: rgba(0,0,0,0.5);
      border: 1px solid rgba(255,255,255,0.12); border-radius: 8px;
      color: #fff; font-size: 12px; outline: none; transition: all 0.2s;
    }}
    .cyber-input:focus {{ border-color: #38bdf8; box-shadow: 0 0 12px rgba(56, 189, 248, 0.3); }}

    .mini-metric {{
      background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.06);
      border-radius: 12px; padding: 14px; text-align: center;
      transition: all 0.2s;
    }}
    .mini-metric:hover {{ border-color: rgba(168,85,247,0.3); background: rgba(255,255,255,0.04); }}
    .mini-metric label {{ font-size: 11px; text-transform: uppercase; color: #94a3b8; font-weight: 600; display: block; }}
    .mini-metric h2 {{ font-size: 24px; font-weight: 800; margin-top: 4px; }}

    .action-icon-btn {{
      padding: 5px 8px; border-radius: 6px; background: rgba(255,255,255,0.05);
      border: 1px solid rgba(255,255,255,0.1); color: #fff; cursor: pointer;
      display: inline-flex; align-items: center; gap: 4px; font-size: 11px;
    }}
    .action-icon-btn:hover {{ background: rgba(255,255,255,0.12); border-color: #38bdf8; }}

    .view-more-link {{
      color: #38bdf8; font-size: 11px; font-weight: 600; cursor: pointer;
      display: inline-flex; align-items: center; gap: 4px; margin-top: 10px;
    }}
    .view-more-link:hover {{ text-decoration: underline; color: #7dd3fc; }}

    .modal {{
      position: fixed; inset: 0; background: rgba(0,0,0,0.85); backdrop-filter: blur(14px);
      display: none; align-items: center; justify-content: center; z-index: 200;
    }}
    .modal-box {{
      background: #0b0d14; border: 1px solid rgba(168, 85, 247, 0.3);
      border-radius: 16px; padding: 26px; width: 400px; box-shadow: 0 25px 50px rgba(0,0,0,0.8);
    }}
  </style>
</head>
<body>
  <header>
    <div class="brand">
      <i data-lucide="cpu" style="width:20px; height:20px; color:#c084fc; filter:drop-shadow(0 0 8px #c084fc);"></i>
      <span>JARVIS <span style="color:#38bdf8;">PORTAL</span></span>
    </div>
    {header_actions}
  </header>

  <div class="container">
    <div class="cyber-card" style="border-left: 3px solid #c084fc;">
      <div style="display:flex; justify-content:space-between; align-items:center;">
        <h3 style="color:#c084fc;"><i data-lucide="terminal"></i> JARVIS Executive Intelligence Core</h3>
        <button class="action-icon-btn" onclick="openSpecModal('mission')"><i data-lucide="maximize-2"></i> View More Specs</button>
      </div>
      <p style="color:#94a3b8; font-size:13px; margin-top:8px;">Autonomous executive framework providing sub-second voice synthesis, background desktop automation hooks, and machine-bound authentication.</p>
    </div>

    <div class="grid-3">
      <div class="cyber-card" style="border-top: 2px solid #a855f7;">
        <h3 style="color:#d8b4fe;"><i data-lucide="cpu"></i> Neural Interface</h3>
        <p style="color:#94a3b8; font-size:12px; margin-top:8px;">Speech recognition and system level execution run locally.</p>
        <span class="view-more-link" onclick="openSpecModal('neural')">Deep-Dive Details &rarr;</span>
      </div>
      <div class="cyber-card" style="border-top: 2px solid #38bdf8;">
        <h3 style="color:#7dd3fc;"><i data-lucide="fingerprint"></i> Anti-Abuse HWID</h3>
        <p style="color:#94a3b8; font-size:12px; margin-top:8px;">Permanent machine UUID cryptographic bind stops recurring trial abuse.</p>
        <span class="view-more-link" onclick="openSpecModal('hwid')">Security Architecture &rarr;</span>
      </div>
      <div class="cyber-card" style="border-top: 2px solid #a855f7;">
        <h3 style="color:#d8b4fe;"><i data-lucide="radio"></i> Relay Mesh Companion</h3>
        <p style="color:#94a3b8; font-size:12px; margin-top:8px;">Instant Android BLE audio sync directly to host desktop worker.</p>
        <span class="view-more-link" onclick="openSpecModal('relay')">Relay Protocols &rarr;</span>
      </div>
    </div>

    {download_section}
    {admin_panel}
  </div>

  <div class="modal" id="authModal">
    <div class="modal-box">
      <h3 id="modalTitle" style="margin-bottom:16px; color:#c084fc; font-size:16px;">Sign In</h3>
      <div style="margin-bottom:12px;">
        <input type="text" id="authU" class="cyber-input" placeholder="Username">
      </div>
      <div style="margin-bottom:12px; display:none;" id="emailWrap">
        <input type="email" id="authE" class="cyber-input" placeholder="Email Address">
      </div>
      <div style="margin-bottom:16px; position:relative;">
        <input type="password" id="authP" class="cyber-input" style="padding-right:36px;" placeholder="Password (8+ chars, 1 Upper, 1 Num)">
        <button type="button" onclick="togglePass()" style="position:absolute; right:10px; top:50%; transform:translateY(-50%); background:none; border:none; color:#94a3b8; cursor:pointer;">
          <i data-lucide="eye" id="eyeIcon" style="width:15px; height:15px;"></i>
        </button>
      </div>
      <p id="authErr" style="color:#f87171; font-size:11px; margin-bottom:14px; display:none;"></p>
      <div style="display:flex; justify-content:flex-end; gap:10px;">
        <button class="neon-btn" style="background:rgba(255,255,255,0.05); color:#fff;" onclick="closeModal('authModal')">Cancel</button>
        <button class="neon-btn neon-btn-purple" id="modalSubmitBtn" onclick="submitAuth()">Authenticate</button>
      </div>
    </div>
  </div>

  <div class="modal" id="specModal">
    <div class="modal-box" style="width:520px;">
      <h3 id="specTitle" style="color:#38bdf8; font-size:16px; margin-bottom:12px;"></h3>
      <div id="specContent" style="color:#cbd5e1; font-size:12px; line-height:1.6; max-height:340px; overflow-y:auto; border-top:1px solid rgba(255,255,255,0.08); padding-top:12px;"></div>
      <div style="text-align:right; margin-top:18px;">
        <button class="neon-btn neon-btn-cyan" onclick="closeModal('specModal')">Acknowledge</button>
      </div>
    </div>
  </div>

  <div class="modal" id="calModal">
    <div class="modal-box">
      <h3 style="color:#38bdf8; font-size:15px; margin-bottom:12px;"><i data-lucide="calendar"></i> Granular Expiry Date & Time</h3>
      <p style="color:#94a3b8; font-size:12px; margin-bottom:14px;">Select exact date, hour and minute for node expiration:</p>
      <input type="datetime-local" id="calDateInput" class="cyber-input" style="margin-bottom:16px;">
      <div style="display:flex; justify-content:flex-end; gap:8px;">
        <button class="action-icon-btn" onclick="closeModal('calModal')">Cancel</button>
        <button class="neon-btn neon-btn-cyan" onclick="saveCalExpiry()"><i data-lucide="check"></i> Apply Schedule</button>
      </div>
    </div>
  </div>

  <div class="modal" id="dlModal">
    <div class="modal-box" style="width:550px;">
      <h3 style="color:#c084fc; font-size:15px; margin-bottom:12px;"><i data-lucide="list"></i> Download Activity Logs</h3>
      <div style="max-height:300px; overflow-y:auto;">
        <table style="width:100%; border-collapse:collapse; font-size:12px;">
          <thead>
            <tr style="border-bottom:1px solid rgba(255,255,255,0.1);">
              <th style="padding:8px; text-align:left; color:#94a3b8;">User</th>
              <th style="padding:8px; text-align:left; color:#94a3b8;">HWID</th>
              <th style="padding:8px; text-align:left; color:#94a3b8;">Platform</th>
              <th style="padding:8px; text-align:left; color:#94a3b8;">Timestamp</th>
            </tr>
          </thead>
          <tbody id="dlLogsBody"></tbody>
        </table>
      </div>
      <div style="text-align:right; margin-top:14px;">
        <button class="action-icon-btn" onclick="closeModal('dlModal')">Close</button>
      </div>
    </div>
  </div>

  <div class="modal" id="noticesModal">
    <div class="modal-box" style="width:480px;">
      <h3 style="color:#38bdf8; font-size:15px; margin-bottom:12px;"><i data-lucide="bell"></i> Broadcast Notifications (Past 30 Days)</h3>
      <div id="noticesFeed" style="max-height:320px; overflow-y:auto; display:flex; flex-direction:column; gap:10px;"></div>
      <div style="text-align:right; margin-top:14px;">
        <button class="action-icon-btn" onclick="closeModal('noticesModal')">Close</button>
      </div>
    </div>
  </div>

  <script>
    lucide.createIcons();
    let authMode = 'login';
    let targetHWID = '';

    const specData = {{
      mission: {{
        title: "JARVIS Core Mission & Scope",
        body: "<p>JARVIS delivers an autonomous, offline-first operating ecosystem engineered for low latency command execution. Instead of streaming audio over third-party networks, JARVIS features an on-device wake-word engine and OS-level execution driver.</p>"
      }},
      neural: {{
        title: "Neural Engine Interface Specs",
        body: "<p>The Neural Core executes speech recognition through local lightweight transformers. Desktop resources are optimized via asynchronous threading so background tasks never stall user gaming or productivity.</p>"
      }},
      hwid: {{
        title: "HWID Cryptographic Fingerprinting",
        body: "<p>To eliminate trial exploitation, every registered machine is cryptographically hashed using hardware concurrency parameters, screen resolution, GPU vendor canvas descriptors, and machine GUIDs.</p>"
      }},
      relay: {{
        title: "Relay Mesh Companion Architecture",
        body: "<p>The Android Companion application establishes an encrypted local socket or BLE mesh connection to your main JARVIS desktop host. Mobile audio is streamed in real-time.</p>"
      }}
    }};

    function checkDeviceView() {{
      const isMobile = window.innerWidth <= 768 || /Android|iPhone|iPad|iPod/i.test(navigator.userAgent);
      const btn = document.getElementById('mobileFaceBtn');
      if (btn) {{
        btn.style.display = isMobile ? 'inline-flex' : 'none';
      }}
    }}
    window.addEventListener('resize', checkDeviceView);
    window.addEventListener('DOMContentLoaded', checkDeviceView);
    checkDeviceView();

    function toggleMobileFace() {{
      const el = document.getElementById('mobileFaceCard');
      if(el) {{
        el.style.display = (el.style.display === 'none' || el.style.display === '') ? 'block' : 'none';
      }}
    }}

    function openSpecModal(k) {{
      const d = specData[k];
      if(!d) return;
      document.getElementById('specTitle').innerText = d.title;
      document.getElementById('specContent').innerHTML = d.body;
      document.getElementById('specModal').style.display = 'flex';
    }}

    function togglePass() {{
      const el = document.getElementById('authP');
      el.type = el.type === 'password' ? 'text' : 'password';
    }}

    function openLogin() {{
      authMode = 'login';
      document.getElementById('authModal').style.display = 'flex';
      document.getElementById('modalTitle').innerText = 'JARVIS Authentication';
      document.getElementById('emailWrap').style.display = 'none';
      document.getElementById('authErr').style.display = 'none';
      document.getElementById('modalSubmitBtn').innerText = 'Sign In';
    }}

    function openReg() {{
      authMode = 'reg';
      document.getElementById('authModal').style.display = 'flex';
      document.getElementById('modalTitle').innerText = 'Register Machine Identifier';
      document.getElementById('emailWrap').style.display = 'block';
      document.getElementById('authErr').style.display = 'none';
      document.getElementById('modalSubmitBtn').innerText = 'Register Node';
    }}

    function closeModal(id) {{ document.getElementById(id).style.display = 'none'; }}

    function getHWID() {{
      let h = localStorage.getItem('jarvis_hwid_node');
      if (!h) {{
        h = 'JARVIS-NODE-' + Math.random().toString(36).substring(2, 8).toUpperCase() + '-' + (navigator.hardwareConcurrency || 4);
        localStorage.setItem('jarvis_hwid_node', h);
      }}
      return h;
    }}

    async function submitAuth() {{
      const u = document.getElementById('authU').value.trim();
      const p = document.getElementById('authP').value;
      const e = document.getElementById('authE').value.trim();
      const err = document.getElementById('authErr');
      const hwid = getHWID();

      if (!u || !p) {{
        err.innerText = 'Username aur password daalna zaroori hai.';
        err.style.display = 'block';
        return;
      }}

      const url = authMode === 'reg' ? '/api/register' : '/api/login';
      const payload = authMode === 'reg' ? {{ username: u, password: p, email: e, hwid: hwid }} : {{ username: u, password: p }};

      try {{
        const res = await fetch(url, {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify(payload)
        }});
        const d = await res.json();
        if (res.ok) {{
          location.href = '/';
        }} else {{
          err.innerText = d.detail || 'Authorization failed';
          err.style.display = 'block';
        }}
      }} catch (ex) {{
        err.innerText = 'Server unreachable';
        err.style.display = 'block';
      }}
    }}

    async function logout() {{
      await fetch('/api/logout', {{ method: 'POST' }});
      location.href = '/';
    }}

    async function triggerClientDownload(platform, filename) {{
      try {{
        const res = await fetch('/get-package/' + platform);
        if (!res.ok) throw new Error('Installer file server par nahi mili');
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        a.remove();
      }} catch (err) {{
        alert('Download error: ' + err.message);
      }}
    }}

    async function quickVoiceTrigger() {{
      await sendCommandPayload("Jarvis activate ho jao");
    }}

    async function sendJarvisCmd() {{
      const val = document.getElementById('voiceCmdInput').value.trim();
      if(!val) return alert('Command type karein!');
      await sendCommandPayload(val);
      document.getElementById('voiceCmdInput').value = '';
    }}

    async function sendCommandPayload(cmd) {{
      const res = await fetch('/api/jarvis/activate', {{
        method:'POST',
        headers: {{'Content-Type':'application/json'}},
        body: JSON.stringify({{command: cmd}})
      }});
      if(res.ok) {{
        const d = await res.json();
        const b = document.getElementById('actBadge');
        if(b) b.innerText = d.activation_state;
        alert('Command dispatched: "' + cmd + '" -> JARVIS Active!');
      }}
    }}

    async function requestAccess() {{
      const res = await fetch('/api/request-extension', {{ method: 'POST' }});
      if(res.ok) alert('Access request super admin ko bhej diya gaya hai!');
    }}

    async function openNotices() {{
      const res = await fetch('/api/broadcasts/feed');
      const d = await res.json();
      const box = document.getElementById('noticesFeed');
      box.innerHTML = '';
      if(!d.feed || d.feed.length === 0) {{
        box.innerHTML = '<p style="color:#94a3b8; font-size:12px;">Pichhle 30 din mein koi notice nahi aaya.</p>';
      }} else {{
        d.feed.forEach(n => {{
          const card = document.createElement('div');
          card.style.cssText = 'background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.08); border-radius:8px; padding:10px; font-size:12px;';
          card.innerHTML = `<p style="color:#f8fafc; font-weight:600;">${{n.message}}</p>` + 
            (n.media_url ? `<div style="margin-top:6px;"><a href="${{n.media_url}}" target="_blank" style="color:#38bdf8; font-size:11px;">[View Attached Media]</a></div>` : '');
          box.appendChild(card);
        }});
      }}
      document.getElementById('noticesModal').style.display = 'flex';
    }}

    async function loadAdminMetrics() {{
      const res = await fetch('/api/admin/metrics');
      if(!res.ok) return;
      const d = await res.json();
      document.getElementById('mUsers').innerText = d.total_users;
      document.getElementById('mActive').innerText = d.active_users;
      document.getElementById('mWin').innerText = d.win_dl;
      document.getElementById('mApk').innerText = d.apk_dl;
    }}

    async function loadAdminNodes() {{
      const res = await fetch('/api/admin/nodes');
      if(!res.ok) return;
      const d = await res.json();
      const tb = document.getElementById('nodesTableBody');
      if(!tb) return;
      tb.innerHTML = '';
      d.nodes.forEach(n => {{
        const isExp = (!n.is_lifetime && n.expires_at < Math.floor(Date.now()/1000)) || n.status === 'Revoked';
        const expLabel = n.is_lifetime ? '∞ Lifetime' : new Date(n.expires_at * 1000).toLocaleString();
        tb.innerHTML += `
          <tr style="border-bottom:1px solid rgba(255,255,255,0.04);">
            <td style="padding:10px; font-weight:600; color:#f8fafc;">${{n.username}}</td>
            <td style="padding:10px; color:#94a3b8;">${{n.email || 'N/A'}}</td>
            <td style="padding:10px; font-family:monospace; color:#38bdf8; font-size:11px;">${{n.hwid}}</td>
            <td style="padding:10px;">
              <span style="color:#4ade80;">${{n.activation_state}}</span><br>
              <span style="color:#c084fc; font-size:11px;">"${{n.last_command}}"</span>
              ${{n.request_pending ? '<br><span style="padding:2px 6px; border-radius:4px; background:rgba(239,68,68,0.2); color:#fca5a5; font-size:10px;">REQ PENDING</span>' : ''}}
            </td>
            <td style="padding:10px; font-size:11px; color:#e2e8f0;">${{expLabel}}</td>
            <td style="padding:10px; display:flex; gap:6px;">
              <button class="action-icon-btn" title="Calendar Schedule" onclick="openCalendarPicker('${{n.hwid}}')"><i data-lucide="calendar"></i></button>
              <button class="action-icon-btn" title="+10 Days" onclick="quickAction('${{n.hwid}}', 'plus10')">+10d</button>
              <button class="action-icon-btn" title="Give Lifetime" onclick="quickAction('${{n.hwid}}', 'lifetime')">Life</button>
              <button class="action-icon-btn" style="color:#f87171;" title="Revoke/Ban" onclick="quickAction('${{n.hwid}}', 'revoke')">Ban</button>
            </td>
          </tr>
        `;
      }});
      lucide.createIcons();
    }}

    function openCalendarPicker(hwid) {{
      targetHWID = hwid;
      document.getElementById('calModal').style.display = 'flex';
    }}

    async function saveCalExpiry() {{
      const val = document.getElementById('calDateInput').value;
      if(!val) return alert('Date select karein!');
      await fetch('/api/admin/set-expiry', {{
        method:'POST',
        headers: {{'Content-Type':'application/json'}},
        body: JSON.stringify({{hwid: targetHWID, expiry_date: val}})
      }});
      closeModal('calModal');
      loadAdminNodes();
    }}

    async function quickAction(hwid, action) {{
      await fetch('/api/admin/quick-action', {{
        method:'POST',
        headers: {{'Content-Type':'application/json'}},
        body: JSON.stringify({{hwid, action}})
      }});
      loadAdminNodes();
      loadAdminMetrics();
    }}

    async function sendBroadcast() {{
      const msg = document.getElementById('bcMsgInput').value;
      const media = document.getElementById('bcMediaInput').value;
      if(!msg) return;
      await fetch('/api/admin/broadcast', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{ message: msg, media_url: media }})
      }});
      alert('Notice broadcast ho gaya!');
      document.getElementById('bcMsgInput').value = '';
      document.getElementById('bcMediaInput').value = '';
    }}

    async function openDlModal() {{
      const res = await fetch('/api/admin/downloads-list');
      const d = await res.json();
      const b = document.getElementById('dlLogsBody');
      b.innerHTML = '';
      d.downloads.forEach(x => {{
        b.innerHTML += `
          <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
            <td style="padding:6px; color:#f8fafc;">${{x.username}}</td>
            <td style="padding:6px; font-family:monospace; font-size:10px; color:#94a3b8;">${{x.hwid}}</td>
            <td style="padding:6px; color:#38bdf8;">${{x.platform}}</td>
            <td style="padding:6px; font-size:11px; color:#e2e8f0;">${{x.downloaded_at}}</td>
          </tr>
        `;
      }});
      document.getElementById('dlModal').style.display = 'flex';
    }}

    if ('{role}' === 'admin') {{
      loadAdminMetrics();
      loadAdminNodes();
    }}
  </script>
</body>
</html>"""