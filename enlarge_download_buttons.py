import os, re

targets = [
    os.path.join("server", "templates", "user_dashboard.html"),
    os.path.join("templates", "user_dashboard.html"),
    os.path.join("server", "templates", "portal.html"),
    os.path.join("templates", "portal.html")
]

big_win_btn = """<button type="button" onclick="triggerDirectDownload('windows')" class="purple-btn w-full py-4 px-6 rounded-xl font-cyber font-bold text-base tracking-wider text-purple-100 flex items-center justify-center gap-3.5 shadow-xl hover:shadow-purple-500/40 active:scale-[0.98] transition-all duration-200 border border-purple-400/40 hover:border-purple-300">
    <i data-lucide="download" class="w-6 h-6 text-purple-200"></i>
    <span>DOWNLOAD CLIENT (WINDOWS .EXE)</span>
</button>"""

big_apk_btn = """<button type="button" onclick="triggerDirectDownload('android')" class="purple-btn w-full py-4 px-6 rounded-xl font-cyber font-bold text-base tracking-wider text-purple-100 flex items-center justify-center gap-3.5 shadow-xl hover:shadow-purple-500/40 active:scale-[0.98] transition-all duration-200 border border-purple-400/40 hover:border-purple-300">
    <i data-lucide="download" class="w-6 h-6 text-purple-200"></i>
    <span>DOWNLOAD COMPANION (ANDROID .APK)</span>
</button>"""

for p in targets:
    if os.path.exists(p):
        with open(p, "r", encoding="utf-8-sig") as f:
            c = f.read()

        c = re.sub(r'<button[^>]*triggerDirectDownload\(\x27windows\x27\)[\s\S]*?</button>', big_win_btn, c)
        c = re.sub(r'<button[^>]*triggerDirectDownload\(\x27android\x27\)[\s\S]*?</button>', big_apk_btn, c)

        with open(p, "w", encoding="utf-8") as f:
            f.write(c)
        print("Enlarged download buttons in:", p)
