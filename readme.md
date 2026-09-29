# ⚙️ JARVIS — Next-Generation Personal AI Assistant
### Developed and Maintained by Suraj (KUMAR SURAJ)

JARVIS is an ultra-fast, autonomous personal desktop assistant powered by Google Gemini Live API. Featuring real-time voice interaction, visual context streaming, system-level execution, offline persistent memory, and a custom 3D holographic avatar with live viseme lip-synchronization.

Optimized to run seamlessly on low-latency and low-bandwidth connections (down to 20 KB/s).

---

## 🚀 Complete Step-by-Step Setup & Installation Guide

Follow these exact steps to run JARVIS on any Windows, macOS, or Linux machine.

### Step 1: Download & Extract
1. Download the project repository as a ZIP archive.
2. Extract the ZIP folder to your preferred local directory (e.g., `C:\Users\YourUsername\Desktop\jarvis`).
3. Open the extracted folder in **Visual Studio Code** or your system terminal.

---

### Step 2: Set Up Virtual Environment
Creating an isolated Python environment prevents dependency version conflicts.

**On Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\python.exe setup.py
```

Use `.\.venv\Scripts\python.exe` for each command below.

**On macOS / Linux:**

```sh
python3 -m venv .venv
./.venv/bin/python setup.py
```

Use `./.venv/bin/python` for each command below.

---

## Licensing service and admin console

The desktop app now requests server authorization on startup and rechecks every
60 seconds. A device receives a 10-day trial when it first contacts the service.
Deactivation is enforced at the next successful recheck (normally within one
minute); a brief network outage gets up to two retry intervals before the app
closes. The service must remain reachable while the desktop app is running.

Run these commands from the project root in separate PowerShell windows:

```powershell
# Terminal 1 — local development license and download service
.\.venv\Scripts\python.exe -m uvicorn server.app:app --host 127.0.0.1 --port 8010

# Terminal 2 — desktop assistant
.\.venv\Scripts\python.exe main.py
```

On macOS/Linux, use `./.venv/bin/python -m uvicorn server.app:app --host
127.0.0.1 --port 8010` and `./.venv/bin/python main.py` instead.

Open `http://127.0.0.1:8010/` for the landing page and
`http://127.0.0.1:8010/admin` for the super-admin dashboard. The requested
bootstrap credentials are `admin123` / `Suraj`; before any public deployment,
set unique `JARVIS_ADMIN_USERNAME`, `JARVIS_ADMIN_PASSWORD`, and
`JARVIS_SESSION_SECRET` environment variables. Use HTTPS and set
`JARVIS_COOKIE_HTTPS_ONLY=true` behind a correctly configured TLS proxy.
Set `JARVIS_LICENSE_API_URL` to the deployed HTTPS `/api/validate` endpoint.

Downloads are served from `dist/JARVIS-Windows.zip` and `mobile/bin/JARVIS.apk`
by default. Configure `JARVIS_WINDOWS_PACKAGE` and `JARVIS_ANDROID_PACKAGE` to
the built artifacts; endpoints return HTTP 503 until the corresponding package
exists. These endpoints track downloads but do not yet provide payments or
automatically issue lifetime licenses.

The optional Android scaffold lives in `mobile/`. Build it on a configured
Linux/WSL host with Buildozer; Android SDK/NDK installation and signing are not
performed by the desktop setup script.
