import os

# 1. Dummy icon ensure karein agar pehle se nahi hai
os.makedirs("static", exist_ok=True)
icon_path = os.path.join("static", "icon.png")
if not os.path.exists(icon_path):
    with open(icon_path, "wb") as f:
        f.write(b"")

# 2. Service Worker create karein
sw_code = """
self.addEventListener('install', (e) => {
    self.skipWaiting();
});
self.addEventListener('fetch', (e) => {
    e.respondWith(fetch(e.request));
});
"""
with open("static/sw.js", "w", encoding="utf-8") as f:
    f.write(sw_code.strip())

# 3. HTML templates me manifest link aur SW register karein
tags_to_insert = """
    <!-- PWA Config -->
    <link rel="manifest" href="/static/manifest.json">
    <meta name="theme-color" content="#8b5cf6">
    <meta name="mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <script>
      if ('serviceWorker' in navigator) {
        window.addEventListener('load', () => {
          navigator.serviceWorker.register('/static/sw.js').catch(()=>{});
        });
      }
    </script>
"""

for root, _, files in os.walk("."):
    for file in files:
        if file.endswith(".html"):
            fpath = os.path.join(root, file)
            try:
                with open(fpath, "r", encoding="utf-8-sig") as f:
                    content = f.read()
                if "manifest.json" not in content and "</head>" in content:
                    content = content.replace("</head>", f"{tags_to_insert}\n</head>")
                    with open(fpath, "w", encoding="utf-8") as f:
                        f.write(content)
            except Exception:
                pass

print("PWA setup complete!")