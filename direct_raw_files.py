import os
import re

# 1. Real standalone files folder me ensure karein
os.makedirs("downloads", exist_ok=True)

win_raw = "downloads/JARVIS_Desktop_Setup.exe"
apk_raw = "downloads/JARVIS_Node_Companion.apk"

# Windows binary header
if not os.path.exists(win_raw):
    with open(win_raw, "wb") as f:
        f.write(b"MZ\x90\x00" + b"\x00" * 60 + b"\x80\x00\x00\x00" + b"JARVIS_RAW_BINARY")

# Android dummy binary
if not os.path.exists(apk_raw):
    with open(apk_raw, "wb") as f:
        f.write(b"PK\x03\x04" + b"JARVIS_RAW_APK_DATA")

# 2. server/app.py me direct .exe aur .apk serve karne ka route
path = "server/app.py"
with open(path, "r", encoding="utf-8-sig") as f:
    text = f.read()

direct_handler = """
@app.get("/get-package/{platform_name}")
async def download_package_tracker(platform_name: str, req: Request):
    ip = req.headers.get("x-forwarded-for") or (req.client.host if req.client else "127.0.0.1")
    plat = platform_name.lower()
    is_win = "win" in plat
    col = "win_downloads" if is_win else "apk_downloads"
    uname = req.cookies.get("username") or "guest_client"
    
    from datetime import datetime
    t_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute(f"UPDATE portal_stats SET val = val + 1 WHERE key = '{col}'")
        c.execute("INSERT INTO download_logs (username, hwid, platform, timestamp) VALUES (?, ?, ?, ?)",
                  (uname, f"IP-{ip}", plat, t_str))
        conn.commit()
        conn.close()
    except Exception:
        pass

    if is_win:
        file_path = "downloads/JARVIS_Desktop_Setup.exe"
        filename = "JARVIS_Desktop_Setup.exe"
        media = "application/vnd.microsoft.portable-executable"
    else:
        file_path = "downloads/JARVIS_Node_Companion.apk"
        filename = "JARVIS_Node_Companion.apk"
        media = "application/vnd.android.package-archive"

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type=media,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
"""

text = re.sub(r'@app\.get\("/get-package/\{platform_name\}"\)[\s\S]*?return\s*FileResponse[\s\S]*?\)', direct_handler.strip(), text)

with open(path, "w", encoding="utf-8") as f:
    f.write(text)

print("Direct raw .exe and .apk download pipeline ready!")