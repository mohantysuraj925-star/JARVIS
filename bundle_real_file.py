import os
import zipfile

os.makedirs("downloads", exist_ok=True)

# Agar aapki real exe exist karti hai toh usko archive me pack karein
exe_path = "dist/jarvis.exe" if os.path.exists("dist/jarvis.exe") else None

with zipfile.ZipFile("downloads/win_installer.zip", "w") as z:
    if exe_path:
        z.write(exe_path, arcname="JARVIS_Master_Setup.exe")
        print("Packed real compiled binary from dist/jarvis.exe")
    else:
        z.writestr("JARVIS_Setup.bat", "@echo off\r\necho [JARVIS CORE] Active & Connected.\r\npause\r\n")
        print("Packed launcher batch script.")