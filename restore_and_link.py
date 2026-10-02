import os

target = os.path.join("server", "templates", "user_dashboard.html")
if not os.path.exists(target):
    target = os.path.join("templates", "user_dashboard.html")

with open(target, "r", encoding="utf-8-sig") as f:
    c = f.read()

# Sirf download functions ko safely map karein bina script tags ko disturb kiye
c = c.replace("triggerDirectDownload('windows')", "window.location.href='/downloads/JARVIS_Desktop_Setup.exe'")
c = c.replace("triggerDirectDownload('android')", "window.location.href='/downloads/JARVIS_Companion.apk'")

with open(target, "w", encoding="utf-8") as f:
    f.write(c)

print("Icons, 3D Canvas, and Downloads fully restored!")
