import os, sys, shutil, zipfile, subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOADS_DIR = os.path.join(BASE_DIR, "downloads")
os.makedirs(DOWNLOADS_DIR, exist_ok=True)
DIST_DIR = os.path.join(BASE_DIR, "dist", "JARVIS")
BUILD_DIR = os.path.join(BASE_DIR, "build")

print("[1/3] Building Standalone JARVIS Executable (No Source Code Leaked)...")
folders_to_copy = ["actions", "apps", "config", "core", "dashboard", "features", "frontend", "models", "modules", "plugins"]
add_data_args = []
for folder in folders_to_copy:
    src = os.path.join(BASE_DIR, folder)
    if os.path.exists(src):
        add_data_args.extend(["--add-data", f"{src}{os.pathsep}{folder}"])

cmd = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--onedir", "--windowed", "--name", "JARVIS"] + add_data_args + [os.path.join(BASE_DIR, "main.py")]
subprocess.run(cmd, check=True)

print("[2/3] Adding 1-Click Auto Launcher...")
launcher_path = os.path.join(DIST_DIR, "Run_JARVIS.bat")
with open(launcher_path, "w", encoding="utf-8") as f:
    f.write("@echo off\r\nstart \"\" \"%~dp0JARVIS.exe\"\r\n")

print("[3/3] Packaging into downloads/JARVIS_Setup.zip...")
zip_target = os.path.join(DOWNLOADS_DIR, "JARVIS_Setup.zip")
if os.path.exists(zip_target):
    os.remove(zip_target)

with zipfile.ZipFile(zip_target, "w", zipfile.ZIP_DEFLATED) as zipf:
    for root, dirs, files in os.walk(DIST_DIR):
        for file in files:
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, DIST_DIR)
            zipf.write(full_path, rel_path)

print("[SUCCESS] Asli 3D JARVIS package tayar: " + zip_target)
