path = "templates/portal.html"
with open(path, "r", encoding="utf-8-sig") as f:
    text = f.read()

# Add Refresh & Clear Buttons in console header
header_addon = """
                <div class="flex justify-between items-center border-b border-slate-800 pb-3">
                    <div class="flex items-center gap-2.5">
                        <i data-lucide="shield-alert" class="w-5 h-5 text-cyan-400"></i>
                        <h2 class="font-cyber font-bold text-sm tracking-wide text-slate-100">Super Master Control Console</h2>
                    </div>
                    <div class="flex items-center gap-2">
                        <button onclick="refreshMasterConsole()" class="flex items-center gap-1 bg-cyan-500/10 border border-cyan-500/30 text-cyan-300 px-2 py-1 rounded text-[10px] font-mono hover:bg-cyan-500/20" title="Force Refresh Data">
                            <i data-lucide="refresh-cw" class="w-3 h-3"></i> Refresh
                        </button>
                        <button onclick="clearAllMetricsToZero()" class="flex items-center gap-1 bg-rose-500/10 border border-rose-500/30 text-rose-400 px-2 py-1 rounded text-[10px] font-mono hover:bg-rose-500/20" title="Reset Counts to 0">
                            <i data-lucide="rotate-ccw" class="w-3 h-3"></i> Clear
                        </button>
                    </div>
                </div>
"""

import re
text = re.sub(r'<div class="flex justify-between items-center border-b border-slate-800 pb-3">[\s\S]*?</div>\s*</div>', header_addon.strip(), text, count=1)

# Attach confirmed downloads to buttons
text = text.replace('href="/get-package/windows"', 'href="javascript:void(0)" onclick="downloadWithConfirmation(\'windows\', \'/get-package/windows\', \'JARVIS_Desktop_Setup.exe\')"')
text = text.replace('href="/get-package/android"', 'href="javascript:void(0)" onclick="downloadWithConfirmation(\'android\', \'/get-package/android\', \'JARVIS_Node_Companion.apk\')"')

with open(path, "w", encoding="utf-8") as f:
    f.write(text)

print("Portal UI enhanced with Refresh, Clear, and Confirmed Downloads!")