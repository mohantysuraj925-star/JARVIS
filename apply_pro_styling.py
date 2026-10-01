import os

win_card = """
<div class="mt-4 p-3.5 rounded-xl bg-purple-950/30 border border-purple-500/20 text-left backdrop-blur-sm">
    <div class="flex items-center gap-2 mb-2">
        <span class="w-1.5 h-1.5 rounded-full bg-purple-400 animate-pulse"></span>
        <span class="text-[11px] font-semibold tracking-wider uppercase text-purple-300">Deployment Notice</span>
    </div>
    <ul class="text-[12px] text-purple-200/80 space-y-1.5 leading-relaxed list-none pl-1">
        <li class="flex items-start gap-2">
            <span class="text-purple-400 font-mono text-[10px] mt-0.5">01</span>
            <span>Launch <b>JARVIS_Desktop_Setup.exe</b> from your local Downloads folder.</span>
        </li>
        <li class="flex items-start gap-2">
            <span class="text-purple-400 font-mono text-[10px] mt-0.5">02</span>
            <span>If SmartScreen appears, select <b>More info &rarr; Run anyway</b>.</span>
        </li>
        <li class="flex items-start gap-2">
            <span class="text-purple-400 font-mono text-[10px] mt-0.5">03</span>
            <span>Background system daemon initializes automatically upon completion.</span>
        </li>
    </ul>
</div>
"""

apk_card = """
<div class="mt-4 p-3.5 rounded-xl bg-purple-950/30 border border-purple-500/20 text-left backdrop-blur-sm">
    <div class="flex items-center gap-2 mb-2">
        <span class="w-1.5 h-1.5 rounded-full bg-purple-400 animate-pulse"></span>
        <span class="text-[11px] font-semibold tracking-wider uppercase text-purple-300">Deployment Notice</span>
    </div>
    <ul class="text-[12px] text-purple-200/80 space-y-1.5 leading-relaxed list-none pl-1">
        <li class="flex items-start gap-2">
            <span class="text-purple-400 font-mono text-[10px] mt-0.5">01</span>
            <span>Enable <b>Allow from unknown sources</b> when prompted by Android.</span>
        </li>
        <li class="flex items-start gap-2">
            <span class="text-purple-400 font-mono text-[10px] mt-0.5">02</span>
            <span>Complete installation to register client node on local network.</span>
        </li>
        <li class="flex items-start gap-2">
            <span class="text-purple-400 font-mono text-[10px] mt-0.5">03</span>
            <span>Alternatively tap <b>Add to Home Screen</b> via browser menu (PWA).</span>
        </li>
    </ul>
</div>
"""

target_files = [
    r"server\templates\user_dashboard.html",
    r"templates\user_dashboard.html",
    r"server\templates\portal.html",
    r"templates\portal.html"
]

for p in target_files:
    if os.path.exists(p):
        with open(p, "r", encoding="utf-8-sig") as f:
            content = f.read()

        # Purane raw style box ko replace karein
        while "Important for your download:" in content:
            start = content.find('<div style="background: rgba(139, 92, 246, 0.1);')
            end = content.find('</div>\n</div>', start)
            if start != -1 and end != -1:
                content = content[:start] + content[end+7:]
            else:
                start2 = content.find('<div style="background:')
                end2 = content.find('</ul>\n</div>', start2)
                if start2 != -1 and end2 != -1:
                    content = content[:start2] + content[end2+12:]
                else:
                    break

        # Sahi clean positioning me naya design inject karein
        if "Deployment Notice" not in content:
            if "triggerDirectDownload('windows')" in content:
                idx = content.find("triggerDirectDownload('windows')")
                b_start = content.rfind("<button", 0, idx)
                if b_start != -1:
                    content = content[:b_start] + win_card + "\n" + content[b_start:]

            if "triggerDirectDownload('android')" in content:
                idx = content.find("triggerDirectDownload('android')")
                b_start = content.rfind("<button", 0, idx)
                if b_start != -1:
                    content = content[:b_start] + apk_card + "\n" + content[b_start:]

        with open(p, "w", encoding="utf-8") as f:
            f.write(content)
        print("Updated styling in:", p)
