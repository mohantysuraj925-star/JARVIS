import os, re

target = os.path.join("server", "templates", "user_dashboard.html")
if not os.path.exists(target):
    target = os.path.join("templates", "user_dashboard.html")

new_download_section = """
<!-- Downloads Section Perfected -->
<div class="grid grid-cols-1 lg:grid-cols-2 gap-6 my-6">
    <!-- Windows Row -->
    <div class="p-5 rounded-2xl bg-purple-950/40 border border-purple-500/30 text-left flex flex-col justify-center shadow-lg">
        <div class="flex items-center gap-2 mb-3">
            <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span class="text-xs font-bold tracking-wide uppercase text-purple-200 font-cyber">HOW TO SETUP (STEP-BY-STEP)</span>
        </div>
        <ul class="text-xs text-purple-100/90 space-y-2 list-none pl-0">
            <li class="flex items-start gap-2">
                <span class="text-purple-400 font-bold">1.</span>
                <span>Click the button to download <b>JARVIS_Desktop_Setup.exe</b>.</span>
            </li>
            <li class="flex items-start gap-2">
                <span class="text-purple-400 font-bold">2.</span>
                <span>Open Downloads, double-click the file, and select <b>"More info" &rarr; "Run anyway"</b>.</span>
            </li>
            <li class="flex items-start gap-2">
                <span class="text-purple-400 font-bold">3.</span>
                <span><b>Wait up to 2 minutes</b> for the assistant daemon to launch and go live.</span>
            </li>
            <li class="flex items-start gap-2">
                <span class="text-purple-400 font-bold">4.</span>
                <span>Paste your designated <b>API Key</b> when prompted to authenticate.</span>
            </li>
        </ul>
    </div>
    <button type="button" onclick="triggerDirectDownload('windows')" class="w-full p-6 rounded-2xl bg-gradient-to-br from-purple-900/40 via-purple-950/60 to-black/70 border-2 border-purple-500/40 hover:border-purple-400 flex items-center justify-between gap-6 group transition-all duration-300 shadow-2xl hover:shadow-purple-500/20 active:scale-[0.98]">
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
    </button>

    <!-- Android Row -->
    <div class="p-5 rounded-2xl bg-purple-950/40 border border-purple-500/30 text-left flex flex-col justify-center shadow-lg">
        <div class="flex items-center gap-2 mb-3">
            <span class="w-2 h-2 rounded-full bg-cyan-400 animate-pulse"></span>
            <span class="text-xs font-bold tracking-wide uppercase text-purple-200 font-cyber">HOW TO SETUP (STEP-BY-STEP)</span>
        </div>
        <ul class="text-xs text-purple-100/90 space-y-2 list-none pl-0">
            <li class="flex items-start gap-2">
                <span class="text-purple-400 font-bold">1.</span>
                <span>Tap the button to download the Android package (.apk).</span>
            </li>
            <li class="flex items-start gap-2">
                <span class="text-purple-400 font-bold">2.</span>
                <span>Open file, enable <b>"Install unknown apps"</b>, and install.</span>
            </li>
            <li class="flex items-start gap-2">
                <span class="text-purple-400 font-bold">3.</span>
                <span>Open the app and <b>wait up to 2 minutes</b> to establish connection.</span>
            </li>
            <li class="flex items-start gap-2">
                <span class="text-purple-400 font-bold">4.</span>
                <span>Enter your <b>API Key</b> to link the mobile companion to server.</span>
            </li>
        </ul>
    </div>
    <button type="button" onclick="triggerDirectDownload('android')" class="w-full p-6 rounded-2xl bg-gradient-to-br from-purple-900/40 via-purple-950/60 to-black/70 border-2 border-purple-500/40 hover:border-purple-400 flex items-center justify-between gap-6 group transition-all duration-300 shadow-2xl hover:shadow-purple-500/20 active:scale-[0.98]">
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
    </button>
</div>
"""

for p in ["server/templates/user_dashboard.html", "templates/user_dashboard.html"]:
    if os.path.exists(p):
        with open(p, "r", encoding="utf-8-sig") as f:
            c = f.read()

        # Download cards container search and clean replacement
        pattern = r'(<div[^>]*class="[^"]*(?:grid-cols-2|grid)[^"]*"[^>]*>[\s\S]*?Windows Client[\s\S]*?Android Node[\s\S]*?</div>\s*</div>)'
        if re.search(pattern, c):
            c = re.sub(pattern, new_download_section, c, count=1)
        else:
            # Fallback direct hook
            w_idx = c.find("Windows Client")
            if w_idx != -1:
                start_div = c.rfind("<div", 0, c.rfind("<div", 0, w_idx))
                a_idx = c.find("Android Node")
                end_div = c.find("</div>", c.find("</div>", a_idx) + 1) + 6
                c = c[:start_div] + new_download_section + c[end_div:]

        with open(p, "w", encoding="utf-8") as f:
            f.write(c)
        print("Updated:", p)
