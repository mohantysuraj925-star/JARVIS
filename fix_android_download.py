import os

routes_to_add = """
@app.get("/downloads/JARVIS_Companion.apk")
async def download_android():
    # Check for any APK file in downloads folder
    d_folder = "downloads"
    target = os.path.join(d_folder, "JARVIS_Companion.apk")
    if not os.path.exists(target):
        # Fallback to any .apk file found
        for f in os.listdir(d_folder) if os.path.exists(d_folder) else []:
            if f.endswith(".apk"):
                target = os.path.join(d_folder, f)
                break
    if os.path.exists(target):
        return FileResponse(target, filename="JARVIS_Companion.apk", media_type="application/vnd.android.package-archive")
    return {"error": "APK not found in downloads folder"}
"""

app_file = os.path.join("server", "app.py")
if os.path.exists(app_file):
    with open(app_file, "r", encoding="utf-8") as f:
        code = f.read()
    if "/downloads/JARVIS_Companion.apk" not in code:
        with open(app_file, "a", encoding="utf-8") as f:
            f.write("\n" + routes_to_add)
        print("Android APK route attached to server/app.py")

script_tag = """
<script>
function triggerDirectDownload(type) {
    if (type === 'windows') {
        window.location.href = '/downloads/JARVIS_Desktop_Setup.exe';
    } else if (type === 'android') {
        window.location.href = '/downloads/JARVIS_Companion.apk';
    }
}
</script>
"""

for p in [os.path.join("server", "templates", "user_dashboard.html"), os.path.join("templates", "user_dashboard.html")]:
    if os.path.exists(p):
        with open(p, "r", encoding="utf-8-sig") as f:
            c = f.read()
        import re
        c = re.sub(r'<script>[\s\S]*?function triggerDirectDownload[\s\S]*?</script>', script_tag, c)
        with open(p, "w", encoding="utf-8") as f:
            f.write(c)
        print("Updated script tag in:", p)
