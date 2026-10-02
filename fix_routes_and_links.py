import os

# 1. FastAPI endpoints inject karein (agar missing hain)
routes = """
from fastapi.responses import FileResponse

@app.get("/downloads/JARVIS_Desktop_Setup.exe")
async def download_windows():
    target = os.path.join("downloads", "JARVIS_Desktop_Setup.exe")
    if not os.path.exists(target):
        target = os.path.join("downloads", "JARVIS_Installer.exe")
    if os.path.exists(target):
        return FileResponse(target, filename="JARVIS_Desktop_Setup.exe", media_type="application/octet-stream")
    return {"error": "Windows Setup file not found"}

@app.get("/downloads/JARVIS_Companion.apk")
async def download_android():
    d_folder = "downloads"
    target = os.path.join(d_folder, "JARVIS_Companion.apk")
    if not os.path.exists(target) and os.path.exists(d_folder):
        for f in os.listdir(d_folder):
            if f.endswith(".apk"):
                target = os.path.join(d_folder, f)
                break
    if os.path.exists(target):
        return FileResponse(target, filename="JARVIS_Companion.apk", media_type="application/vnd.android.package-archive")
    return {"error": "Android APK file not found"}
"""

app_file = os.path.join("server", "app.py")
if os.path.exists(app_file):
    with open(app_file, "r", encoding="utf-8") as f:
        content = f.read()
    if "/downloads/JARVIS_Desktop_Setup.exe" not in content:
        with open(app_file, "a", encoding="utf-8") as f:
            f.write("\n" + routes)
        print("Download routes added to server/app.py")

# 2. Template me global JS function add karein (HTML canvas/icons ko bina chhede)
js_func = """
<script>
window.triggerDirectDownload = function(platform) {
    if (platform === 'windows') {
        window.location.href = '/downloads/JARVIS_Desktop_Setup.exe';
    } else if (platform === 'android') {
        window.location.href = '/downloads/JARVIS_Companion.apk';
    }
};
</script>
"""

for target in ["server/templates/user_dashboard.html", "templates/user_dashboard.html"]:
    if os.path.exists(target):
        with open(target, "r", encoding="utf-8-sig") as f:
            html = f.read()
        if "window.triggerDirectDownload" not in html:
            html = html.replace("</head>", f"{js_func}\n</head>")
            with open(target, "w", encoding="utf-8") as f:
                f.write(html)
            print(f"Hook attached safely to head in: {target}")
