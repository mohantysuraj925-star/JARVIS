import os
win_btn = """\n<button type="button" onclick="alert(\x27Windows Setup:\\n1. Downloads folder me jakar JARVIS_Desktop_Setup.exe par double-click karein.\\n2. Run anyway par click karein.\\n3. JARVIS assistant active ho jayega.\x27)" style="display:block;margin:10px auto 0;font-size:12px;color:#c084fc;text-decoration:underline;background:none;border:none;cursor:pointer;">View Details</button>"""
apk_btn = """\n<button type="button" onclick="alert(\x27Android Setup:\\n1. File download hone ke baad tap karein.\\n2. Install Unknown Apps allow karein aur Install dabayein.\\n3. App Drawer me standalone app ready ho jayegi.\x27)" style="display:block;margin:10px auto 0;font-size:12px;color:#c084fc;text-decoration:underline;background:none;border:none;cursor:pointer;">View Details</button>"""
for root, _, files in os.walk("."):
    for file in files:
        if file.endswith(".html"):
            p = os.path.join(root, file)
            with open(p, "r", encoding="utf-8-sig") as f:
                content = f.read()
            if "View Details" not in content and ("triggerDirectDownload" in content or "get-package" in content):
                content = content.replace("triggerDirectDownload(\x27windows\x27)", "triggerDirectDownload(\x27windows\x27)" + win_btn)
                content = content.replace("triggerDirectDownload(\x27android\x27)", "triggerDirectDownload(\x27android\x27)" + apk_btn)
                with open(p, "w", encoding="utf-8") as f:
                    f.write(content)
                print("Patched:", p)

