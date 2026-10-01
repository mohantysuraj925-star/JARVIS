import os

# 1. Static directory ensure karein
os.makedirs("static", exist_ok=True)

# 2. Valid Web Manifest create karein
manifest_content = """{
  "name": "JARVIS Assistant",
  "short_name": "JARVIS",
  "start_url": "/dashboard",
  "scope": "/",
  "display": "standalone",
  "background_color": "#0d0a1a",
  "theme_color": "#8b5cf6",
  "icons": [
    {
      "src": "/static/icon.png",
      "sizes": "192x192",
      "type": "image/png"
    }
  ]
}"""

with open("static/manifest.json", "w", encoding="utf-8") as f:
    f.write(manifest_content.strip())

# 3. 192x192 PNG Icon ensure karein (1x1 valid byte fallback)
icon_path = os.path.join("static", "icon.png")
if not os.path.exists(icon_path) or os.path.getsize(icon_path) == 0:
    png_header = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
    with open(icon_path, "wb") as f:
        f.write(png_header)

# 4. Service Worker create karein
sw_content = """self.addEventListener('install', (event) => {
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    event.waitUntil(clients.claim());
});

self.addEventListener('fetch', (event) => {
    event.respondWith(fetch(event.request).catch(() => caches.match(event.request)));
});"""

with open("static/sw.js", "w", encoding="utf-8") as f:
    f.write(sw_content.strip())

# 5. Templates me PWA metadata inject karein
pwa_tags = """
    <!-- PWA Setup -->
    <link rel="manifest" href="/static/manifest.json">
    <meta name="theme-color" content="#8b5cf6">
    <meta name="mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <script>
      if ('serviceWorker' in navigator) {
        window.addEventListener('load', () => {
          navigator.serviceWorker.register('/static/sw.js').catch(() => {});
        });
      }
    </script>
"""

template_folders = ["templates", "server/templates"]
for folder in template_folders:
    if os.path.exists(folder):
        for fname in os.listdir(folder):
            if fname.endswith(".html"):
                fpath = os.path.join(folder, fname)
                with open(fpath, "r", encoding="utf-8-sig") as f:
                    content = f.read()
                if "manifest.json" not in content and "</head>" in content:
                    content = content.replace("</head>", f"{pwa_tags}\n</head>")
                    with open(fpath, "w", encoding="utf-8") as f:
                        f.write(content)

print("PWA verification complete: manifest, icon, sw.js, and templates updated.")