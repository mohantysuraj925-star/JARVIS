import os

win_card = """
<div style="margin: 12px 0; padding: 12px; background: rgba(139, 92, 246, 0.1); border: 1px solid rgba(168, 85, 247, 0.35); border-radius: 10px; text-align: left;">
    <div style="font-size: 11px; font-weight: 700; letter-spacing: 0.05em; text-transform: uppercase; color: #c084fc; margin-bottom: 6px;">Important for your download:</div>
    <ul style="font-size: 12px; color: #e9d5ff; line-height: 1.5; margin: 0; padding-left: 18px;">
        <li>Launch <b>JARVIS_Desktop_Setup.exe</b> from your Downloads folder.</li>
        <li>If SmartScreen appears, click <b>More info &rarr; Run anyway</b>.</li>
        <li>JARVIS assistant will initialize automatically.</li>
    </ul>
</div>
"""

apk_card = """
<div style="margin: 12px 0; padding: 12px; background: rgba(139, 92, 246, 0.1); border: 1px solid rgba(168, 85, 247, 0.35); border-radius: 10px; text-align: left;">
    <div style="font-size: 11px; font-weight: 700; letter-spacing: 0.05em; text-transform: uppercase; color: #c084fc; margin-bottom: 6px;">Important for your download:</div>
    <ul style="font-size: 12px; color: #e9d5ff; line-height: 1.5; margin: 0; padding-left: 18px;">
        <li>Tap download and enable <b>Allow from unknown sources</b>.</li>
        <li>Complete installation to register node on network.</li>
        <li>Or tap <b>Add to Home Screen</b> in mobile browser.</li>
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
            content = f.read()

        if "Important for your download:" not in content:
            updated = False
            for token in ["triggerDirectDownload('windows')", "get-package/windows"]:
                if token in content:
                    idx = content.find(token)
                    btn_start = content.rfind("<button", 0, idx)
                    if btn_start != -1:
                        content = content[:btn_start] + win_card + content[btn_start:]
                        updated = True
                        break

            for token in ["triggerDirectDownload('android')", "get-package/android"]:
                if token in content:
                    idx = content.find(token)
                    btn_start = content.rfind("<button", 0, idx)
                    if btn_start != -1:
                        content = content[:btn_start] + apk_card + content[btn_start:]
                        updated = True
                        break

            if updated:
                with open(p, "w", encoding="utf-8") as f:
                    f.write(content)
                print(f"Updated instructions in: {p}")
