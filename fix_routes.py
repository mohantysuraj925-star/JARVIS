import os
import re

path = "server/app.py"
with open(path, "r", encoding="utf-8-sig") as f:
    text = f.read()

# 1. Ensure root route '/' exists and serves dashboard/portal correctly
root_check = """
@app.get("/")
async def root_index(request: Request):
    uname = request.cookies.get("username")
    # Agar template engine hai toh portal render karein, nahi toh static/file serve karein
    for t_dir in ["templates", "server/templates"]:
        p = os.path.join(t_dir, "portal.html")
        if os.path.exists(p):
            if "templates" in globals() and hasattr(templates, "TemplateResponse"):
                return templates.TemplateResponse("portal.html", {"request": request, "username": uname or "Guest"})
            return FileResponse(p)
    return {"status": "online", "message": "JARVIS Portal Ready"}
"""

if '@app.get("/")' not in text:
    pos = text.find("app = FastAPI")
    eol = text.find("\n", pos)
    text = text[:eol+1] + "\n" + root_check + "\n" + text[eol+1:]

with open(path, "w", encoding="utf-8") as f:
    f.write(text)

print("Routes synced successfully!")