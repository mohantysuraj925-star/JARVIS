import pathlib, re

# Error-free selector fix across templates
invalid_syntax = 'span:contains("★")'

files = list(pathlib.Path(".").rglob("*.html")) + list(pathlib.Path(".").rglob("*.js"))
count = 0

for f in files:
    try:
        txt = f.read_text(encoding="utf-8", errors="ignore")
        if 'contains("★")' in txt or "contains('★')" in txt:
            # Replace invalid CSS selector with standard selector
            txt = re.sub(r'[, ]*span:contains\(["\']★["\']\)', '', txt)
            f.write_text(txt, encoding="utf-8")
            print(f"[FIXED JAVASCRIPT SYNTAX]: {f.name}")
            count += 1
    except Exception:
        pass

print(f"\nDone! Fixed in {count} files.")
