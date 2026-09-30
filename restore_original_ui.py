import os
import re

path = "server/app.py"
with open(path, "r", encoding="utf-8-sig") as f:
    text = f.read()

# Exact template rendering matching your templates/portal.html
ui_route = """
@app.get("/")
async def root_index(request: Request):
    uname = request.cookies.get("username")
    return templates.TemplateResponse("portal.html", {"request": request, "username": uname or "Guest"})
"""

text = re.sub(r'@app\.get\("/"\)[\s\S]*?return\s*\{[\s\S]*?\}', ui_route.strip(), text)

with open(path, "w", encoding="utf-8") as f:
    f.write(text)

print("Original Portal HTML Route Restored!")