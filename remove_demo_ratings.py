import glob, re

for path in glob.glob("**/*.html", recursive=True):
    if ".venv" in path or ".git" in path or "node_modules" in path:
        continue
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        html = f.read()

    # Puraane demo/static rating breakdown ko permanently remove karna
    patterns = [
        r'<div[^>]*>[\s\S]*?5\s*★[\s\S]*?0%[\s\S]*?1\s*★[\s\S]*?0%[\s\S]*?</div>',
        r'5\s*★\s*0%[\s\S]*?1\s*★\s*0%',
        r'<div[^>]*class="[^"]*rating-breakdown[^"]*"[\s\S]*?</div>',
        r'<div[^>]*id="[^"]*ratingBreakdown[^"]*"[\s\S]*?</div>'
    ]
    
    modified = False
    for pat in patterns:
        if re.search(pat, html, re.IGNORECASE):
            html = re.sub(pat, '', html, flags=re.IGNORECASE)
            modified = True

    if modified:
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        print("Cleaned demo ratings from:", path)

print("Demo percentage breakdown removed!")
