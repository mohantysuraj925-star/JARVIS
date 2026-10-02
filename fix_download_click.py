import os

routes_to_add = """
from fastapi.responses import FileResponse

@app.get("/downloads/JARVIS_Desktop_Setup.exe")
async def download_windows():
    target = os.path.join("downloads", "JARVIS_Desktop_Setup.exe")
    if not os.path.exists(target):
        target = os.path.join("downloads", "JARVIS_Installer.exe")
    if os.path.exists(target):
        return FileResponse(target, filename="JARVIS_Desktop_Setup.exe", media_type="application/octet-stream")
    return {"error": "File not found"}
"""

app_file = os.path.join("server", "app.py")
if os.path.exists(app_file):
    with open(app_file, "r", encoding="utf-8") as f:
        code = f.read()
    if "/downloads/JARVIS_Desktop_Setup.exe" not in code:
        with open(app_file, "a", encoding="utf-8") as f:
            f.write("\n" + routes_to_add)
        print("Download endpoint added to server/app.py")

script_tag = """
<script>
function triggerDirectDownload(type) {
    if (type === 'windows') {
        window.location.href = '/downloads/JARVIS_Desktop_Setup.exe';
    } else if (type === 'android') {
        window.location.href = '/dashboard';
    }
}
</script>
"""

for p in [os.path.join("server", "templates", "user_dashboard.html"), os.path.join("templates", "user_dashboard.html")]:
    if os.path.exists(p):
        with open(p, "r", encoding="utf-8-sig") as f:
            content = f.read()
        if "function triggerDirectDownload" not in content:
            content = content.replace("</body>", f"{script_tag}\n</body>")
            with open(p, "w", encoding="utf-8") as f:
                f.write(content)
            print("Injected triggerDirectDownload into:", p)
