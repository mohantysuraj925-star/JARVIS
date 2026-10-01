import os
import re

path = "server/app.py"
with open(path, "r", encoding="utf-8-sig") as f:
    text = f.read()

# Exact directory resolution checking root templates first
fixed_template_loader = """# Dynamic template directory resolver
root_tpl = os.path.abspath("templates")
server_tpl = os.path.abspath("server/templates")

if os.path.exists(os.path.join(root_tpl, "portal.html")):
    tpl_dir = root_tpl
elif os.path.exists(os.path.join(server_tpl, "portal.html")):
    tpl_dir = server_tpl
else:
    tpl_dir = root_tpl

templates = Jinja2Templates(directory=tpl_dir)
"""

text = re.sub(
    r'tpl_dir\s*=\s*[\s\S]*?templates\s*=\s*Jinja2Templates\([^\)]*\)',
    fixed_template_loader.strip(),
    text
)

with open(path, "w", encoding="utf-8") as f:
    f.write(text)

print("Template search path fixed successfully!")