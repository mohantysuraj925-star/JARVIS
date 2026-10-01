import os, re

win_text = """
<div class="mt-4 p-4 rounded-xl bg-purple-950/40 border border-purple-500/30 text-left">
    <div class="flex items-center gap-2 mb-2.5">
        <span class="w-2 h-2 rounded-full bg-emerald-400"></span>
        <span class="text-xs font-bold tracking-wide uppercase text-purple-200">How to Setup (Step-by-Step)</span>
    </div>
    <ul class="text-xs text-purple-100/90 space-y-2 list-none pl-0">
        <li class="flex items-start gap-2">
            <span class="text-purple-400 font-bold">1.</span>
            <span>Click below to download <b>JARVIS_Desktop_Setup.exe</b>.</span>
        </li>
        <li class="flex items-start gap-2">
            <span class="text-purple-400 font-bold">2.</span>
            <span>Open your Downloads folder, double-click the file, and if prompted select <b>"More info" &rarr; "Run anyway"</b>.</span>
        </li>
        <li class="flex items-start gap-2">
            <span class="text-purple-400 font-bold">3.</span>
            <span><b>Wait up to 2 minutes</b> for the assistant daemon to launch and go live.</span>
        </li>
        <li class="flex items-start gap-2">
            <span class="text-purple-400 font-bold">4.</span>
            <span>Paste your designated <b>API Key</b> when prompted to authenticate and start using JARVIS.</span>
        </li>
    </ul>
</div>
"""

apk_text = """
<div class="mt-4 p-4 rounded-xl bg-purple-950/40 border border-purple-500/30 text-left">
    <div class="flex items-center gap-2 mb-2.5">
        <span class="w-2 h-2 rounded-full bg-cyan-400"></span>
        <span class="text-xs font-bold tracking-wide uppercase text-purple-200">How to Setup (Step-by-Step)</span>
    </div>
    <ul class="text-xs text-purple-100/90 space-y-2 list-none pl-0">
        <li class="flex items-start gap-2">
            <span class="text-purple-400 font-bold">1.</span>
            <span>Tap the button below to download the Android package (.apk).</span>
        </li>
        <li class="flex items-start gap-2">
            <span class="text-purple-400 font-bold">2.</span>
            <span>Tap the downloaded file, allow <b>"Install unknown apps"</b>, and complete the installation.</span>
        </li>
        <li class="flex items-start gap-2">
            <span class="text-purple-400 font-bold">3.</span>
            <span>Open the app and <b>wait up to 2 minutes</b> to establish node connection.</span>
        </li>
        <li class="flex items-start gap-2">
            <span class="text-purple-400 font-bold">4.</span>
            <span>Enter your <b>API Key</b> to link the mobile companion to your JARVIS server.</span>
        </li>
    </ul>
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
            c = f.read()

        c = re.sub(r'<div class="[^"]*rounded-xl bg-purple-950/30 border border-purple-500/20 text-left my-4[\s\S]*?</ul>\s*</div>', win_text, c, count=1)
        c = re.sub(r'<div class="[^"]*rounded-xl bg-purple-950/30 border border-purple-500/20 text-left my-4[\s\S]*?</ul>\s*</div>', apk_text, c, count=1)

        c = re.sub(r'<div class="mt-4 p-4 rounded-xl bg-purple-950/40 border border-purple-500/30 text-left">[\s\S]*?</ul>\s*</div>', win_text, c, count=1)
        c = re.sub(r'<div class="mt-4 p-4 rounded-xl bg-purple-950/40 border border-purple-500/30 text-left">[\s\S]*?</ul>\s*</div>', apk_text, c, count=1)

        c = re.sub(r'<div style="margin: 12px 0; padding: 12px; background: rgba\(139, 92, 246, 0.1\)[\s\S]*?</ul>\s*</div>', win_text, c, count=1)
        c = re.sub(r'<div style="margin: 12px 0; padding: 12px; background: rgba\(139, 92, 246, 0.1\)[\s\S]*?</ul>\s*</div>', apk_text, c, count=1)

        with open(p, "w", encoding="utf-8") as f:
            f.write(c)
        print("Updated instructions with 2-min wait & API key in:", p)
