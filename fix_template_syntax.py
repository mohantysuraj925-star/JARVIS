path = "server/app.py"
with open(path, "r", encoding="utf-8-sig") as f:
    text = f.read()

# Replace template response signature to avoid TypeError in Starlette
old_call = 'templates.TemplateResponse("portal.html", {"request": request, "username": uname or "Guest"})'
new_call = 'templates.TemplateResponse(request=request, name="portal.html", context={"username": uname or "Guest"})'

if old_call in text:
    text = text.replace(old_call, new_call)
else:
    import re
    text = re.sub(
        r'templates\.TemplateResponse\(\s*["\']portal\.html["\']\s*,\s*\{[\s\S]*?\}\s*\)',
        new_call,
        text
    )

with open(path, "w", encoding="utf-8") as f:
    f.write(text)

print("TemplateResponse signature updated!")