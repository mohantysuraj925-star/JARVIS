import re, pathlib, py_compile

ROOT = pathlib.Path(__file__).resolve().parent


class Patch:
    def __init__(self, name):
        self.path = ROOT / name
        self.name = name
        self.s = self.path.read_text(encoding="utf-8")
        self.log = []

    def rep(self, label, old, new, all_=False):
        if old in self.s:
            self.s = self.s.replace(old, new) if all_ else self.s.replace(old, new, 1)
            self.log.append("OK   " + label)
        else:
            self.log.append("MISS " + label)

    def rep_re(self, label, pat, new):
        s2, n = re.subn(pat, lambda m: new, self.s, count=1, flags=re.S)
        if n:
            self.s = s2
            self.log.append("OK   " + label)
        else:
            self.log.append("MISS " + label)

    def save(self):
        bak = self.path.with_name(self.name + ".bak")
        if not bak.exists():
            bak.write_text(self.path.read_text(encoding="utf-8"), encoding="utf-8")
        self.path.write_text(self.s, encoding="utf-8")
        print("\n".join(self.log))
        try:
            py_compile.compile(str(self.path), doraise=True)
            print(self.name + " syntax OK\n")
        except Exception as e:
            print(self.name + " SYNTAX ERROR:\n" + str(e) + "\n")


# ============================ ui.py ============================
u = Patch("ui.py")
s = u.s
blocks = list(re.finditer(r"^class SelectableBox\(QFrame\):.*?(?=^class )", s, re.S | re.M))
for m in reversed(blocks[:-1]):
    s = s[:m.start()] + s[m.end():]
u.s = s
u.log.append("OK   SelectableBox dedupe (%d removed)" % max(0, len(blocks) - 1))

u.rep_re("SetupOverlay._on_submit",
         r'        import json\n        cfg_dir = Path\("config"\).*?env_p\.write_text\(chr\(10\)\.join\(lines\), encoding="utf-8"\)',
         r'''        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        user_cfg = {
            "api_key": k,
            "operator_name": n,
            "os": self.selected_os,
            "gender": self.selected_gender,
            "is_configured": True,
        }
        (CONFIG_DIR / "user_config.json").write_text(
            json.dumps(user_cfg, indent=2), encoding="utf-8")
        (CONFIG_DIR / "user_profile.json").write_text(
            json.dumps({"gemini_api_key": k, "operator_name": n,
                        "gender": self.selected_gender}, indent=2), encoding="utf-8")
        _data = _read_full_config()
        _data["gemini_api_key"] = k
        _data["os_system"] = self.selected_os.lower()
        API_FILE.write_text(json.dumps(_data, indent=4), encoding="utf-8")
        os.environ["GEMINI_API_KEY"] = k
        env_p = BASE_DIR / ".env"
        lines = []
        if env_p.exists():
            for line in env_p.read_text(encoding="utf-8", errors="ignore").splitlines():
                if not line.startswith("GEMINI_API_KEY="):
                    lines.append(line)
        lines.append(f"GEMINI_API_KEY={k}")
        env_p.write_text("\n".join(lines), encoding="utf-8")''')

u.rep("ov.done -> setup_completed", "ov.done.connect(self._on_setup_done)",
      "ov.setup_completed.connect(self._on_setup_completed)")
u.rep("_on_setup_completed method", "    def _on_setup_done(self, key: str, os_name: str):",
      '''    def _on_setup_completed(self, cfg: dict):
        self._on_setup_done(cfg.get("api_key", ""), str(cfg.get("os", "")).lower())

    def _on_setup_done(self, key: str, os_name: str):''')
u.rep_re("_on_setup_done merge config",
         r'        os\.makedirs\(CONFIG_DIR, exist_ok=True\)\n        API_FILE\.write_text\(\n.*?\n        \)\n',
         '''        os.makedirs(CONFIG_DIR, exist_ok=True)
        _data = _read_full_config()
        _data["gemini_api_key"] = key
        _data["os_system"] = os_name
        API_FILE.write_text(json.dumps(_data, indent=4), encoding="utf-8")
''')
u.rep("setup overlay size", "ow, oh = 460, 390", "ow, oh = 480, 520", all_=True)
u.rep_re("remove first-run duplicate",
         r'        # --- FIRST-RUN SETUP TRIGGER.*?self\._setup_overlay\.raise_\(\)\n', "")
u.rep_re("CustomizeOverlay stale lines",
         r'        if hasattr\(self, "_setup_overlay"\) and self\._setup_overlay.*?on_accent_changed\(hx\)\n', "")

u.rep("quick drawer", "    def _build_quick_drawer(self) -> QWidget:\n        pass\n",
      r'''    def _build_quick_drawer(self) -> QWidget:
        d = _HudOverlay(self.centralWidget())
        d.setObjectName("QuickDrawer")
        d.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        d.setStyleSheet(f"""
            QWidget#QuickDrawer {{
                background: rgba(8, 1, 3, 246);
                border: 1px solid {C.BORDER_B};
                border-radius: 6px;
            }}
        """)
        lay = QVBoxLayout(d)
        lay.setContentsMargins(10, 10, 10, 10)
        lay.setSpacing(5)

        def _btn(text, slot):
            b = QPushButton(text)
            b.setFixedHeight(28)
            b.setFont(QFont("Courier New", 8, QFont.Weight.Bold))
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setStyleSheet(f"""
                QPushButton {{ background: {C.PANEL2}; color: {C.TEXT_MED};
                    border: 1px solid {C.BORDER}; border-radius: 3px;
                    text-align: left; padding: 0 8px; }}
                QPushButton:hover {{ color: {C.TEXT}; border: 1px solid {C.BORDER_B}; }}
            """)
            b.clicked.connect(lambda _=False, f=slot: f())
            lay.addWidget(b)
            return b

        _btn("[SETTINGS]  CUSTOMISE", self._open_customize)
        _btn("[OPERATOR]  PROFILE", self._open_operator_profile)
        _btn("[AUDIO]  AUDIO DEVICES", self._open_audio_devices)
        _btn("[AI_CORE]  MEMORY", self._open_memory_panel)
        _btn("[EXT]  PLUGINS", self._open_plugin_manager)
        _btn("[SETTINGS]  PLUGIN SETTINGS", self._open_plugin_settings)
        _btn("◈  REMOTE ACCESS", self._open_remote)
        self._autostart_btn = _btn("◉  AUTO-START", self._toggle_autostart)
        self._brief_btn = _btn("☀  MORNING BRIEF", self._toggle_brief)
        self._wake_btn = _btn("[MIC]  WAKE WORD", self._toggle_wake_word)
        self._wake_sleep_btn = _btn("[SLEEP]  SLEEP NOW", self._tap_wake_manual)
        self._wake_sleep_btn.hide()
        self._ptt_btn = _btn("[LEVEL]  PUSH-TO-TALK", self._toggle_ptt)
        self._hud_btn = _btn("HUD", self._toggle_hud_style)
        _btn("⬇  DESKTOP SHORTCUT", self._create_desktop_shortcut)

        d.hide()
        try:
            self._refresh_hud_btn()
            self._refresh_talk_btns()
        except Exception:
            pass
        return d
''')
u.rep("drawer button icon", 'QPushButton("[SETTINGS]")', 'QPushButton("⚙")')
u.rep("position_quick_drawer double return", "            return\n            return\n", "            return\n")
u.rep_re("operator profile once", r'    def _open_operator_profile\(self\):.*?(?=    def _toggle_drawer)',
         '''    def _open_operator_profile(self):
        try:
            ProfileDialog(self).exec()
        except Exception as e:
            print(e)

''')
u.rep("title keeps BY SURAJ", "self._title_lbl.setText(display)", 'self._title_lbl.setText(f"{display}  BY SURAJ")')
u.rep("subtitle consistent", '"Just A Rather Very Intelligent System"', '"A Friendly Assistant"')

old = "if self._avatar is not None:\n                self._avatar.glance(dx, dy, hold)"
i = u.s.rfind(old)
if i >= 0:
    u.s = u.s[:i] + "self._win.hud.glance(dx, dy, hold)" + u.s[i + len(old):]
    u.log.append("OK   GARUDAUI.glance")
else:
    u.log.append("MISS GARUDAUI.glance")

u.rep("splitter sizes", "self._center_split.setSizes([max(total - 220, 120), 220])",
      "self._center_split.setSizes([max(total - 220, 120), 220, 0])")
u.rep("log err tag", '"err" in tl', 'tl.startswith("err")')
u.rep("rgba 0.95", "rgba(0, 4, 12, 0.95)", "rgba(0, 4, 12, 242)")
u.rep("rgba 0.08", "rgba(34,197,94,0.08)", "rgba(34,197,94,20)")
u.rep("rgba 0.4", "rgba(34,197,94,0.4)", "rgba(34,197,94,102)")

# ============================ main.py ============================
m = Patch("main.py")
m.rep_re("setup-ready check",
         r'def _is_garuda_setup_ready\(\):.*?return bool\(os\.getenv\("GEMINI_API_KEY", ""\)\.strip\(\)\)\n',
         '''def _is_garuda_setup_ready():
    import os, json
    from pathlib import Path
    base = Path(__file__).resolve().parent / "config"
    for fname, field in (("api_keys.json", "gemini_api_key"),
                         ("user_config.json", "api_key"),
                         ("user_profile.json", "gemini_api_key")):
        try:
            d = json.loads((base / fname).read_text(encoding="utf-8"))
            if str(d.get(field, "")).strip():
                return True
        except Exception:
            pass
    return bool(os.getenv("GEMINI_API_KEY", "").strip())
''')
m.rep_re("Popen patch", r'    class _Popen\(_OrigPopen\):.*?super\(\)\.__init__\(args, \*\*\s*kw\)\n',
         '''    class _Popen(_OrigPopen):
        def __init__(self, *args, **kw):
            kw["creationflags"] = kw.get("creationflags", 0) | _subprocess.CREATE_NO_WINDOW
            kw.pop("startupinfo", None)
            super().__init__(*args, **kw)
''')
m.rep_re("console reconfigure", r'for _stream in \("stdout", "stderr"\):.*?pass\s+# pythonw[^\n]*\n',
         '''for _stream in ("stdout", "stderr"):
    try:
        _s = getattr(_sys, _stream, None)
        if _s is not None and hasattr(_s, "reconfigure"):
            _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass  # pythonw / redirected pipes - never fatal
''')
m.rep("assistant name typo", '"JARVI    S"', '"GARUDA"')
s2, n = re.subn(r'(        self\.session\s+= None\n)',
                lambda mm: mm.group(1) + "        self.is_developer_mode = False\n", m.s, count=1)
if n:
    m.s = s2; m.log.append("OK   is_developer_mode init")
else:
    m.log.append("MISS is_developer_mode init")
m.rep("_resumed_with init",
      '        while True:\n            try:\n                print("[GARUDA] Connecting...")',
      '        _resumed_with = False\n        while True:\n            try:\n                print("[GARUDA] Connecting...")')
m.rep_re("run() gate",
         r'        cfg_p = Path\("config/user_config\.json"\).*?        except Exception:\n            return\n\n        self\._loop',
         '        if not _is_garuda_setup_ready():\n            print("[HARD GATE] Setup pending. Core engine blocked.")\n            return\n\n        self._loop')
m.rep_re("main() gatekeeper", r'    # --- HARD BLOCK GATEKEEPER ---.*?start_listening_on_boot = False\n', "")
i = m.s.find("# Feedback Storage Endpoint")
if i >= 0:
    m.s = m.s[:i].rstrip() + "\n"
    m.log.append("OK   removed FastAPI routes from main.py")
else:
    m.log.append("MISS FastAPI routes block")

# ---- spec: developer protocol, welcome, reconnect, model ----
m.rep_re("LIVE_MODEL configurable", r'LIVE_MODEL\s*= "models/gemini-3\.1-flash-live-preview"',
         '''def _cfg_live_model():
    try:
        v = json.loads(API_CONFIG_PATH.read_text(encoding="utf-8")).get("live_model", "")
        return v.strip() or "models/gemini-3.1-flash-live-preview"
    except Exception:
        return "models/gemini-3.1-flash-live-preview"

LIVE_MODEL = _cfg_live_model()''')

m.rep("dev prompt constant", "class _ReconnectSignal(Exception):", '''_DEV_PROMPT = (
    "[IDENTITY & DEVELOPER PROTOCOL]\\n"
    "If asked who you are, answer: \\"Main {name} hoon, ek advanced cyber-intelligence "
    "desktop assistant jise Suraj Kumar Mohanty ne develop kiya hai.\\"\\n"
    "If asked who your developer is, answer: \\"Mere nirmata aur developer Mr. Suraj Kumar "
    "Mohanty hain. Ve Khatiguda, Nabarangpur (Odisha) ke nivasi hain aur Gandhi Institute "
    "of Excellent Technocrats (GIET), Bhubaneswar se Computer Science Engineering ke student hain.\\"\\n"
    "If someone says they are your developer, ask for the developer verification password.\\n"
    "If they then say the password Mahadev, reply: \\"Har Har Mahadev! Password satyapit hua. "
    "Swagat hai Suraj Sir, {name} ab poori tarah aapke adheen hai. Batayein, kya nirdesh hain?\\" "
    "Any other password: \\"Access Denied. Galat password. Session normal user mode mein chal raha hai.\\"\\n\\n"
)


class _ReconnectSignal(Exception):''')
m.rep("dev prompt injected", "        parts = [time_ctx, identity_ctx]\n",
      '        parts = [time_ctx, identity_ctx, _DEV_PROMPT.replace("{name}", self._asst_name)]\n')

m.rep_re("verify_developer_access",
         r'    def verify_developer_access\(self, query: str\) -> str:.*?(?=    def speak\(self, text: str\):)',
         '''    def verify_developer_access(self, query: str):
        raw = query or ""
        q = raw.lower()
        if "mahadev" in q or "महादेव" in raw:
            self.is_developer_mode = True
            self._dev_await = False
            self.ui.write_log("SYS: [DEV MODE: UNLOCKED]")
            return ("Har Har Mahadev! Password satyapit hua. Swagat hai Suraj Sir, "
                    f"{self._asst_name} ab poori tarah aapke adheen hai. Batayein, kya nirdesh hain?")
        if any(w in q for w in ("i am your developer", "main tumhara developer",
                                "mai tumhara developer", "main developer hoon",
                                "mai developer hoon", "mai tumhara creator")):
            self._dev_await = True
            return ("Pranam Sir! Suraksha protocol ke tahat, kripya apna "
                    "developer verification password batayein.")
        if getattr(self, "_dev_await", False):
            self._dev_await = False
            return "Access Denied. Galat password. Session normal user mode mein chal raha hai."
        if any(w in q for w in ("who is your developer", "who is developer", "developer kaun",
                                "developer kon", "who made you", "kisne banaya", "kon banaya")):
            return ("Mere nirmata aur developer Mr. Suraj Kumar Mohanty hain. Ve Khatiguda, "
                    "Nabarangpur (Odisha) ke nivasi hain aur Gandhi Institute of Excellent "
                    "Technocrats (GIET), Bhubaneswar se Computer Science Engineering ke student hain.")
        if any(w in q for w in ("who are you", "tum kaun ho", "aap kaun ho")):
            return (f"Main {self._asst_name} hoon, ek advanced cyber-intelligence desktop "
                    "assistant jise Suraj Kumar Mohanty ne develop kiya hai.")
        if "user mode" in q:
            self.is_developer_mode = False
            return "User mode active."
        return None

    def _dev_note_voice(self, text: str):
        t = (text or "").lower()
        if "mahadev" in t or "महादेव" in (text or ""):
            self.is_developer_mode = True
            self.ui.write_log("SYS: [DEV MODE: UNLOCKED]")

''')

m.rep("hook typed commands",
      "    def _on_text_command(self, text: str):\n        if not self._loop or not self.session:\n            return\n",
      '''    def _on_text_command(self, text: str):
        if not self._loop or not self.session:
            return
        _dev = self.verify_developer_access(text)
        if _dev:
            asyncio.run_coroutine_threadsafe(
                self.session.send_client_content(
                    turns={"role": "user", "parts": [{"text":
                        "Say exactly this, word for word, and nothing else: " + _dev}]},
                    turn_complete=True),
                self._loop)
            return
''')
m.rep("hook voice transcript", '                                self._last_out_logged = ""   # new exchange\n',
      '                                self._last_out_logged = ""   # new exchange\n'
      '                                self._dev_note_voice(full_in)\n')

m.rep("welcome method", "    # ── main loop", '''    async def _send_first_welcome(self) -> None:
        cfg_p = BASE_DIR / "config" / "user_config.json"
        try:
            d = json.loads(cfg_p.read_text(encoding="utf-8"))
        except Exception:
            return
        if d.get("welcomed") or not d.get("gender"):
            return
        d["welcomed"] = True
        try:
            cfg_p.write_text(json.dumps(d, indent=2), encoding="utf-8")
        except Exception:
            return
        word = "Ma'am" if str(d["gender"]).lower() == "female" else "Sir"
        await asyncio.sleep(1.0)
        if self.session and self._awake:
            await self.session.send_client_content(
                turns={"role": "user", "parts": [{"text": f"Say exactly: Welcome {word}"}]},
                turn_complete=True)

    # ── main loop''')
m.rep("welcome task", '                    print("[GARUDA] Connected.")\n',
      '                    print("[GARUDA] Connected.")\n'
      '                    tg.create_task(self._send_first_welcome())\n')

for a, b in (('"TimeoutError"', '"timeouterror"'), ('"CancelledError"', '"cancellederror"'),
             ('"ConnectionRefusedError"', '"connectionrefusederror"'), ('"OSError"', '"oserror"')):
    m.rep("lowercase " + a, a, b)
m.rep("add 1236 / winerror 121", '"1006",\n', '"1006", "1236", "winerror 121",\n')

# ============================ Jarvis -> Garuda ============================
for obj in (u, m):
    for old_n, new_n in (("J.A.R.V.I.S", "GARUDA"), ("JARVIS", "GARUDA"), ("Jarvis", "Garuda")):
        obj.s = obj.s.replace(old_n, new_n)
    obj.log.append("OK   Jarvis -> Garuda")

u.save()
m.save()

# ============================ server/portal_routes.py ============================
ROUTES = '''import sqlite3
from pathlib import Path
from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, JSONResponse

router = APIRouter()
ROOT = Path(__file__).resolve().parent.parent
PORTAL_DB = ROOT / "portal_data.db"
FEEDBACK_DB = ROOT / "database.db"


def _portal():
    conn = sqlite3.connect(PORTAL_DB)
    conn.execute("CREATE TABLE IF NOT EXISTS system_config (key TEXT PRIMARY KEY, value TEXT)")
    return conn


def _mobile_active() -> bool:
    conn = _portal()
    try:
        row = conn.execute(
            "SELECT value FROM system_config WHERE key='mobile_download_active'").fetchone()
    finally:
        conn.close()
    return bool(row) and row[0].strip().lower() == "true"


@router.get("/api/system/mobile-status")
@router.get("/api/admin/mobile_status")
def mobile_status():
    try:
        a = _mobile_active()
        return {"active": a, "enabled": a, "status": "active" if a else "deactive"}
    except Exception as e:
        return {"active": False, "enabled": False, "error": str(e)}


@router.post("/api/system/mobile-toggle")
@router.post("/api/admin/toggle_all_mobile")
def mobile_toggle(payload: dict | None = None):
    try:
        if payload and "active" in payload:
            new = bool(payload["active"])
        else:
            new = not _mobile_active()
        conn = _portal()
        try:
            conn.execute(
                "INSERT OR REPLACE INTO system_config (key, value) VALUES ('mobile_download_active', ?)",
                ("true" if new else "false",))
            conn.commit()
        finally:
            conn.close()
        return {"success": True, "active": new, "enabled": new}
    except Exception as e:
        return {"success": False, "active": False, "enabled": False, "error": str(e)}


@router.post("/api/feedback")
async def save_feedback(request: Request):
    data = await request.json()
    conn = sqlite3.connect(FEEDBACK_DB)
    try:
        conn.execute("CREATE TABLE IF NOT EXISTS feedbacks (id INTEGER PRIMARY KEY AUTOINCREMENT, "
                     "username TEXT, rating INTEGER, comment TEXT, "
                     "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        conn.execute("INSERT INTO feedbacks (username, rating, comment) VALUES (?, ?, ?)",
                     (data.get("username", "Operator"), data.get("rating", 5), data.get("comment", "")))
        conn.commit()
    finally:
        conn.close()
    return {"status": "success", "message": "Feedback saved"}


@router.get("/api/feedback")
async def get_feedback(user: str = ""):
    result = {"rating": 5, "comment": "No feedback yet."}
    conn = sqlite3.connect(FEEDBACK_DB)
    try:
        if user:
            row = conn.execute("SELECT rating, comment, created_at FROM feedbacks "
                               "WHERE username=? ORDER BY id DESC LIMIT 1", (user,)).fetchone()
        else:
            row = conn.execute("SELECT rating, comment, created_at FROM feedbacks "
                               "ORDER BY id DESC LIMIT 1").fetchone()
        if row:
            result = {"rating": row[0], "comment": row[1], "date": row[2]}
    except sqlite3.OperationalError:
        pass
    finally:
        conn.close()
    return result


@router.get("/download-apk")
@router.get("/api/downloads/mobile")
async def download_apk():
    for rel in ("server/static/downloads/app-release.apk", "downloads/app-release.apk"):
        f = ROOT / rel
        if f.exists():
            return FileResponse(f, filename="GARUDA-Android.apk",
                                media_type="application/vnd.android.package-archive")
    return JSONResponse({"error": "APK not found"}, status_code=404)
'''
(ROOT / "server").mkdir(exist_ok=True)
(ROOT / "server" / "portal_routes.py").write_text(ROUTES, encoding="utf-8")
print("OK   server/portal_routes.py written")
print("\nDone. Ab: python main.py")
