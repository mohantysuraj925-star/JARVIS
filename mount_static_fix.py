path = "server/app.py"
with open(path, "r", encoding="utf-8-sig") as f:
    text = f.read()

# StaticFiles import ensure karein
if "from fastapi.staticfiles import StaticFiles" not in text:
    text = "from fastapi.staticfiles import StaticFiles\n" + text

# Purani loose mount hata kar exact absolute mount lagayein
clean_mount = """
STATIC_DIR = os.path.join(BASE_DIR, "static")
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
"""

if 'app.mount("/static"' in text:
    import re
    text = re.sub(r'app\.mount\("/static"[^\)]+\)', clean_mount.strip(), text)
else:
    text = text.replace('app = FastAPI(title="JARVIS AI System Core")', 'app = FastAPI(title="JARVIS AI System Core")\n' + clean_mount)

with open(path, "w", encoding="utf-8") as f:
    f.write(text)

print("Static mount successfully updated to absolute path!")