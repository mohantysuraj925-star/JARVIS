import os

path = "server/app.py"
with open(path, "r", encoding="utf-8-sig") as f:
    text = f.read()

# Direct static route handler
static_handler = """
@app.get("/static/{file_path:path}")
async def serve_static_direct(file_path: str):
    local_static = os.path.join(os.getcwd(), "static", file_path)
    if os.path.exists(local_static):
        media = "application/javascript" if file_path.endswith(".js") else "text/css"
        return FileResponse(local_static, media_type=media)
    parent_static = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "static", file_path)
    if os.path.exists(parent_static):
        media = "application/javascript" if file_path.endswith(".js") else "text/css"
        return FileResponse(parent_static, media_type=media)
    raise HTTPException(404, "File not found")
"""

if "/static/{file_path:path}" not in text:
    pos = text.find('@app.get("/api/admin/metrics")')
    if pos != -1:
        text = text[:pos] + static_handler + "\n" + text[pos:]
    else:
        text += "\n" + static_handler

with open(path, "w", encoding="utf-8") as f:
    f.write(text)

print("Direct static routing added!")