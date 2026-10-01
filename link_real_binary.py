import os
import shutil

os.makedirs("downloads", exist_ok=True)

# 200MB wali real exe file dhoondein
target_exe = None
max_size = 0

for root, dirs, files in os.walk("."):
    if ".venv" in root:
        continue
    for f in files:
        if f.lower().endswith(".exe"):
            fp = os.path.join(root, f)
            try:
                sz = os.path.getsize(fp)
                if sz > max_size and "downloads" not in root:
                    max_size = sz
                    target_exe = fp
            except Exception:
                pass

if target_exe and max_size > 10 * 1024 * 1024:  # > 10MB
    dest = "downloads/JARVIS_Desktop_Setup.exe"
    shutil.copy2(target_exe, dest)
    print(f"SUCCESS: Copied real build ({max_size // (1024*1024)} MB) from {target_exe} to {dest}")
else:
    print("Real EXE path check karein ya direct downloads/ folder me copy karein.")