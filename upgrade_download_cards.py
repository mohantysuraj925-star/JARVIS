import os, re

pro_win_block = """
<!-- Windows Download Card Enhanced -->
<div class="glass-purple p-6 rounded-2xl border border-purple-500/40 bg-gradient-to-b from-purple-950/40 to-black/60 shadow-xl flex flex-col justify-between hover:border-purple-400/60 transition-all duration-300">
    <div>
        <div class="flex items-center justify-between pb-4 border-b border-purple-500/20 mb-4">
            <div class="flex items-center gap-3">
                <div class="w-12 h-12 rounded-xl bg-purple-500/20 border border-purple-500/40 flex items-center justify-center text-purple-300 shadow-inner">
                    <i data-lucide="monitor" class="w-7 h-7"></i>
                </div>
                <div>
                    <h3 class="font-cyber font-bold text-lg text-purple-100 tracking-wide">Windows Client</h3>
                    <p class="text-xs text-purple-300/60 font-mono">x86_64 Architecture // Standalone Daemon</p>
                </div>
            </div>
            <span class="px-2.5 py-1 text-[11px] font-mono font-semibold rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 flex items-center gap-1.5">
                <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping"></span> STABLE
            </span>
        </div>

        <div class="p-4 rounded-xl bg-purple-950/30 border border-purple-500/20 text-left my-4 space-y-2.5">
            <div class="flex items-center gap-2">
                <span class="w-2 h-2 rounded-full bg-purple-400"></span>
                <span class="text-xs font-cyber font-bold tracking-wider text-purple-300 uppercase">Deployment Guidelines</span>
            </div>
            <ul class="text-xs text-purple-200/80 space-y-2 font-mono pl-1 list-none">
                <li class="flex items-start gap-2.5">
                    <span class="text-purple-400 font-bold">01.</span>
                    <span>Launch <b>JARVIS_Desktop_Setup.exe</b> from your Downloads folder.</span>
                </li>
                <li class="flex items-start gap-2.5">
                    <span class="text-purple-400 font-bold">02.</span>
                    <span>If Windows SmartScreen prompts, click <b>More info &rarr; Run anyway</b>.</span>
                </li>
                <li class="flex items-start gap-2.5">
                    <span class="text-purple-400 font-bold">03.</span>
                    <span>Background core service registers automatically upon launch.</span>
                </li>
            </ul>
        </div>
    </div>

    <div class="pt-3">
        <button type="button" onclick="triggerDirectDownload('windows')" class="purple-btn w-full py-3.5 px-6 rounded-xl font-cyber font-bold text-sm tracking-wide text-purple-100 flex items-center justify-center gap-3 shadow-lg hover:shadow-purple-500/30 active:scale-[0.98] transition-all">
            <i data-lucide="download" class="w-5 h-5"></i>
            <span>DOWNLOAD CLIENT (WINDOWS .EXE)</span>
        </button>
    </div>
</div>
"""

pro_apk_block = """
<!-- Android Download Card Enhanced -->
<div class="glass-purple p-6 rounded-2xl border border-purple-500/40 bg-gradient-to-b from-purple-950/40 to-black/60 shadow-xl flex flex-col justify-between hover:border-purple-400/60 transition-all duration-300">
    <div>
        <div class="flex items-center justify-between pb-4 border-b border-purple-500/20 mb-4">
            <div class="flex items-center gap-3">
                <div class="w-12 h-12 rounded-xl bg-purple-500/20 border border-purple-500/40 flex items-center justify-center text-purple-300 shadow-inner">
                    <i data-lucide="smartphone" class="w-7 h-7"></i>
                </div>
                <div>
                    <h3 class="font-cyber font-bold text-lg text-purple-100 tracking-wide">Android Node</h3>
                    <p class="text-xs text-purple-300/60 font-mono">ARM64 Architecture // Companion PWA</p>
                </div>
            </div>
            <span class="px-2.5 py-1 text-[11px] font-mono font-semibold rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 flex items-center gap-1.5">
                <span class="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-ping"></span> READY
            </span>
        </div>

        <div class="p-4 rounded-xl bg-purple-950/30 border border-purple-500/20 text-left my-4 space-y-2.5">
            <div class="flex items-center gap-2">
                <span class="w-2 h-2 rounded-full bg-purple-400"></span>
                <span class="text-xs font-cyber font-bold tracking-wider text-purple-300 uppercase">Deployment Guidelines</span>
            </div>
            <ul class="text-xs text-purple-200/80 space-y-2 font-mono pl-1 list-none">
                <li class="flex items-start gap-2.5">
                    <span class="text-purple-400 font-bold">01.</span>
                    <span>Enable <b>Allow from unknown sources</b> when prompted by Android.</span>
                </li>
                <li class="flex items-start gap-2.5">
                    <span class="text-purple-400 font-bold">02.</span>
                    <span>Complete package installation to register node on local network.</span>
                </li>
                <li class="flex items-start gap-2.5">
                    <span class="text-purple-400 font-bold">03.</span>
                    <span>Alternatively tap <b>Add to Home Screen</b> via mobile browser menu.</span>
                </li>
            </ul>
        </div>
    </div>

    <div class="pt-3">
        <button type="button" onclick="triggerDirectDownload('android')" class="purple-btn w-full py-3.5 px-6 rounded-xl font-cyber font-bold text-sm tracking-wide text-purple-100 flex items-center justify-center gap-3 shadow-lg hover:shadow-purple-500/30 active:scale-[0.98] transition-all">
            <i data-lucide="download" class="w-5 h-5"></i>
            <span>DOWNLOAD COMPANION (ANDROID .APK)</span>
        </button>
    </div>
</div>
"""

targets = [
    os.path.join("server", "templates", "user_dashboard.html"),
    os.path.join("templates", "user_dashboard.html"),
    os.path.join("server", "templates", "portal.html"),
    os.path.join("templates", "portal.html")
]

for p in targets:
    if os.path.exists(p):
        with open(p, "r", encoding="utf-8-sig") as f:
            content = f.read()

        # Windows card replace pattern
        pat_win = r'(<!-- Windows Download Card[\s\S]*?)(<button[\s\S]*?triggerDirectDownload\(\x27windows\x27\)[\s\S]*?</button>[\s\S]*?</div>)'
        if re.search(pat_win, content):
            content = re.sub(pat_win, pro_win_block, content, count=1)
        
        # Android card replace pattern
        pat_apk = r'(<!-- Android Download Card[\s\S]*?)(<button[\s\S]*?triggerDirectDownload\(\x27android\x27\)[\s\S]*?</button>[\s\S]*?</div>)'
        if re.search(pat_apk, content):
            content = re.sub(pat_apk, pro_apk_block, content, count=1)

        with open(p, "w", encoding="utf-8") as f:
            f.write(content)
        print("Upgraded download layout in:", p)
