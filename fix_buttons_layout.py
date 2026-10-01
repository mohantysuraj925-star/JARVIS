import os, re

targets = [
    os.path.join("server", "templates", "user_dashboard.html"),
    os.path.join("templates", "user_dashboard.html"),
    os.path.join("server", "templates", "portal.html"),
    os.path.join("templates", "portal.html")
]

big_win = """<button type="button" onclick="triggerDirectDownload('windows')" class="w-full h-full min-h-[170px] p-6 rounded-2xl bg-gradient-to-br from-purple-900/40 via-purple-950/60 to-black/70 border-2 border-purple-500/40 hover:border-purple-400 flex items-center justify-between gap-6 group transition-all duration-300 shadow-2xl hover:shadow-purple-500/20 active:scale-[0.98]">
    <div class="flex items-center gap-5 text-left">
        <div class="w-16 h-16 rounded-2xl bg-purple-500/20 border border-purple-400/40 flex items-center justify-center text-purple-300 group-hover:scale-110 group-hover:bg-purple-500/30 transition-all shadow-inner">
            <i data-lucide="monitor" class="w-9 h-9 text-purple-200"></i>
        </div>
        <div>
            <div class="text-xl font-bold font-cyber text-white tracking-wide group-hover:text-purple-200 transition-colors">Windows Client</div>
            <div class="text-xs text-purple-300/70 font-mono mt-1">.EXE STANDALONE // 64-BIT</div>
        </div>
    </div>
    <div class="w-12 h-12 rounded-xl bg-purple-500/20 border border-purple-400/30 flex items-center justify-center text-purple-300 group-hover:bg-purple-500 group-hover:text-white transition-all shadow-md">
        <i data-lucide="download" class="w-6 h-6"></i>
    </div>
</button>"""

big_apk = """<button type="button" onclick="triggerDirectDownload('android')" class="w-full h-full min-h-[170px] p-6 rounded-2xl bg-gradient-to-br from-purple-900/40 via-purple-950/60 to-black/70 border-2 border-purple-500/40 hover:border-purple-400 flex items-center justify-between gap-6 group transition-all duration-300 shadow-2xl hover:shadow-purple-500/20 active:scale-[0.98]">
    <div class="flex items-center gap-5 text-left">
        <div class="w-16 h-16 rounded-2xl bg-purple-500/20 border border-purple-400/40 flex items-center justify-center text-purple-300 group-hover:scale-110 group-hover:bg-purple-500/30 transition-all shadow-inner">
            <i data-lucide="smartphone" class="w-9 h-9 text-purple-200"></i>
        </div>
        <div>
            <div class="text-xl font-bold font-cyber text-white tracking-wide group-hover:text-purple-200 transition-colors">Android Node</div>
            <div class="text-xs text-purple-300/70 font-mono mt-1">.APK COMPANION // MOBILE</div>
        </div>
    </div>
    <div class="w-12 h-12 rounded-xl bg-purple-500/20 border border-purple-400/30 flex items-center justify-center text-purple-300 group-hover:bg-purple-500 group-hover:text-white transition-all shadow-md">
        <i data-lucide="download" class="w-6 h-6"></i>
    </div>
</button>"""

for p in targets:
    if os.path.exists(p):
        with open(p, "r", encoding="utf-8-sig") as f:
            c = f.read()

        c = re.sub(r'<button[^>]*triggerDirectDownload\(\x27windows\x27\)[\s\S]*?</button>', big_win, c)
        c = re.sub(r'<button[^>]*triggerDirectDownload\(\x27android\x27\)[\s\S]*?</button>', big_apk, c)

        # Agar pehle triggerDirectDownload hook nahi laga tha
        c = re.sub(r'<button[^>]*>[\s\S]*?Windows Client[\s\S]*?\.EXE STANDALONE[\s\S]*?</button>', big_win, c)
        c = re.sub(r'<button[^>]*>[\s\S]*?Android Node[\s\S]*?\.APK COMPANION[\s\S]*?</button>', big_apk, c)

        with open(p, "w", encoding="utf-8") as f:
            f.write(c)
        print("Updated layout in:", p)
