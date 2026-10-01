import os

targets = [
    os.path.join("server", "templates", "user_dashboard.html"),
    os.path.join("templates", "user_dashboard.html"),
    os.path.join("server", "templates", "portal.html"),
    os.path.join("templates", "portal.html")
]

big_style = 'style="width: 100%; min-height: 56px; font-size: 15px; font-weight: bold; letter-spacing: 1px; display: flex; align-items: center; justify-content: center; gap: 12px; border-radius: 14px; padding: 14px 20px; text-transform: uppercase;"'

for p in targets:
    if os.path.exists(p):
        with open(p, "r", encoding="utf-8-sig") as f:
            c = f.read()

        c = c.replace("class=\"purple-btn w-full py-3.5", "class=\"purple-btn w-full py-5 text-lg")
        c = c.replace("class=\"purple-btn py-2", "class=\"purple-btn w-full py-5 text-lg")
        
        # Direct button tags par forceful size style inject
        c = c.replace("onclick=\"triggerDirectDownload('windows')\"", f"{big_style} onclick=\"triggerDirectDownload('windows')\"")
        c = c.replace("onclick=\"triggerDirectDownload('android')\"", f"{big_style} onclick=\"triggerDirectDownload('android')\"")

        with open(p, "w", encoding="utf-8") as f:
            f.write(c)
        print("Force enlarged in:", p)
