import os

details_modal_code = """
<!-- Setup Details Modal -->
<div id="setupDetailsModal" class="fixed inset-0 bg-black/85 backdrop-blur-md hidden justify-center items-center z-[99999] p-4">
    <div class="glass-purple rounded-2xl p-6 max-w-lg w-full font-mono flex flex-col gap-4 border border-purple-500/50 shadow-2xl text-left">
        <div class="flex justify-between items-center border-b border-purple-500/30 pb-3">
            <h3 id="detailsModalTitle" class="font-cyber font-bold text-sm text-purple-100 flex items-center gap-2">
                <i data-lucide="info" class="w-4 h-4 text-purple-400"></i>
                <span>Installation Guide</span>
            </h3>
            <button onclick="closeDetailsModal()" class="text-purple-300 hover:text-white text-base">✕</button>
        </div>
        <div id="detailsModalBody" class="text-xs text-purple-200/90 space-y-3 leading-relaxed max-h-80 overflow-y-auto"></div>
        <div class="pt-2 text-right">
            <button onclick="closeDetailsModal()" class="purple-btn py-2 px-5 rounded-xl text-xs font-bold text-purple-100">
                Close
            </button>
        </div>
    </div>
</div>

<script>
function showDetails(platform) {
    const title = document.getElementById('detailsModalTitle');
    const body = document.getElementById('detailsModalBody');
    const modal = document.getElementById('setupDetailsModal');

    if (platform === 'windows') {
        title.innerHTML = '<i data-lucide="monitor" class="w-4 h-4 text-purple-400"></i> Windows Setup Details';
        body.innerHTML = `
            <p class="font-bold text-purple-300">Windows Client (.exe) Installation:</p>
            <ol class="list-decimal list-inside space-y-2 text-purple-200/80">
                <li>Download button par click karein aur setup package save karein.</li>
                <li>Apne <b>Downloads</b> folder me jakar <b>JARVIS_Desktop_Setup.exe</b> par double-click karein.</li>
                <li>Agar Windows SmartScreen prompt aaye, toh <b>"More info"</b> dabakar <b>"Run anyway"</b> chunein.</li>
                <li>Setup complete hote hi JARVIS assistant background me active ho jayega.</li>
            </ol>
        `;
    } else {
        title.innerHTML = '<i data-lucide="smartphone" class="w-4 h-4 text-purple-400"></i> Android Companion Details';
        body.innerHTML = `
            <p class="font-bold text-purple-300">Android Node (.apk / PWA) Installation:</p>
            <ol class="list-decimal list-inside space-y-2 text-purple-200/80">
                <li><b>Direct APK:</b> Download hone ke baad file par tap karein, <i>"Install unknown apps"</i> allow karein aur Install dabayein.</li>
                <li><b>Web App (PWA):</b> Mobile Chrome browser me 3-dots menu kholkar <b>"Install app"</b> ya <b>"Add to Home screen"</b> par tap karein.</li>
                <li>App Drawer aur Home Screen par standalone icon ready ho jayega.</li>
            </ol>
        `;
    }

    modal.classList.remove('hidden');
    modal.classList.add('flex');
    if (window.lucide) lucide.createIcons();
}

function closeDetailsModal() {
    const modal = document.getElementById('setupDetailsModal');
    modal.classList.remove('flex');
    modal.classList.add('hidden');
}
</script>
"""

template_dirs = ["templates", "server/templates"]
for tdir in template_dirs:
    for fname in ["user_dashboard.html", "admin_portal.html", "landing.html"]:
        fpath = os.path.join(tdir, fname)
        if os.path.exists(fpath):
            with open(fpath, "r", encoding="utf-8-sig") as f:
                html = f.read()

            if "setupDetailsModal" not in html and "</body>" in html:
                html = html.replace("</body>", details_modal_code + "\n</body>")

            win_btn = '<button onclick="showDetails(\'windows\')" class="mt-2 text-[11px] text-purple-400/80 hover:text-purple-200 underline block text-center">View Details</button>'
            android_btn = '<button onclick="showDetails(\'android\')" class="mt-2 text-[11px] text-purple-400/80 hover:text-purple-200 underline block text-center">View Details</button>'

            if 'showDetails(\'windows\')' not in html:
                html = html.replace("triggerDirectDownload('windows')", "triggerDirectDownload('windows')\n" + win_btn)
                html = html.replace("triggerDirectDownload('android')", "triggerDirectDownload('android')\n" + android_btn)

            with open(fpath, "w", encoding="utf-8") as f:
                f.write(html)

print("Setup Details modal & buttons added cleanly!")