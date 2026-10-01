import os
import zipfile

os.makedirs("downloads", exist_ok=True)

# 1. Windows Installer Package (.zip/.exe)
win_file = "downloads/windows_installer.zip"
if not os.path.exists(win_file):
    with zipfile.ZipFile(win_file, "w") as z:
        z.writestr("JARVIS_Desktop_Setup.exe", b"JARVIS Windows Desktop Installer Binary Core")
    print("Created:", win_file)

# 2. Android Package (.zip/.apk)
apk_file = "downloads/android_installer.zip"
if not os.path.exists(apk_file):
    with zipfile.ZipFile(apk_file, "w") as z:
        z.writestr("JARVIS_Node_Companion.apk", b"JARVIS Android Node Companion APK Core")
    print("Created:", apk_file)