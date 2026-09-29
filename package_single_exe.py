import os, sys, shutil, subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOADS_DIR = os.path.join(BASE_DIR, "downloads")
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

print("[1/2] Building DIRECT SINGLE-FILE EXECUTABLE (Zero Zip / No Extraction needed)...")
folders_to_copy = ["actions", "apps", "config", "core", "dashboard", "features", "frontend", "models", "modules", "plugins"]
add_data_args = []
for folder in folders_to_copy:
    src = os.path.join(BASE_DIR, folder)
    if os.path.exists(src):
        add_data_args.extend(["--add-data", f"{src}{os.pathsep}{folder}"])

# --onefile flag se single standalone .exe banegi
cmd = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--onefile", "--windowed", "--name", "JARVIS_Installer"] + add_data_args + [os.path.join(BASE_DIR, "main.py")]
subprocess.run(cmd, check=True)

print("[2/2] Moving JARVIS_Installer.exe to downloads folder...")
built_exe = os.path.join(BASE_DIR, "dist", "JARVIS_Installer.exe")
target_exe = os.path.join(DOWNLOADS_DIR, "JARVIS_Installer.exe")

if os.path.exists(target_exe):
    os.remove(target_exe)

shutil.copy2(built_exe, target_exe)

print("\n" + "="*60)
print("[SUCCESS] Direct Single-Click Executable Tayar!")
print("Path: " + target_exe)
print("="*60)
print("Ab website se koi bhi user direct 'JARVIS_Installer.exe' download karega.")
print("Unhe koi zip kholne ki zarurat nahi hai. Bas 2 baar click karenge aur aapka 3D AI Assistant chalu!")
