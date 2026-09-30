import os

path = "templates/admin.html"
if os.path.exists(path):
    with open(path, "r", encoding="utf-8") as f:
        html = f.read()

    # Table wrapper check
    if 'id="nodesTableBody"' not in html:
        table_code = """
        <div style="margin-top: 30px; background: rgba(15,23,42,0.6); border: 1px solid rgba(0,240,255,0.2); border-radius: 12px; padding: 20px;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:15px;">
                <h3 style="color:#00f0ff; margin:0; font-size:18px; letter-spacing:1px;">OPERATOR NODES LIFECYCLE CONTROLS</h3>
                <span style="color:#94a3b8; font-size:12px;">Real-Time Dynamic Nodes</span>
            </div>
            <div style="overflow-x: auto;">
                <table style="width: 100%; border-collapse: collapse; text-align: left; font-size: 14px;">
                    <thead>
                        <tr style="border-bottom: 2px solid rgba(0,240,255,0.3); color: #94a3b8;">
                            <th style="padding: 10px;">ID</th>
                            <th style="padding: 10px;">OPERATOR</th>
                            <th style="padding: 10px;">STATUS</th>
                            <th style="padding: 10px;">LIFECYCLE</th>
                            <th style="padding: 10px;">CALENDAR LOCK</th>
                            <th style="padding: 10px;">TIME WINDOW</th>
                            <th style="padding: 10px;">ACTIONS</th>
                        </tr>
                    </thead>
                    <tbody id="nodesTableBody">
                    </tbody>
                </table>
            </div>
        </div>
        """
        # Global broadcast hub ke upar ya body ke end se pehle add karein
        if "GLOBAL BROADCAST HUB" in html:
            html = html.replace('<div class="broadcast-hub"', table_code + '\n<div class="broadcast-hub"')
            if '<div class="broadcast-hub"' not in html:
                pos = html.find("GLOBAL BROADCAST HUB")
                parent_start = html.rfind("<div", 0, pos)
                html = html[:parent_start] + table_code + "\n" + html[parent_start:]
        else:
            html = html.replace("</body>", table_code + "\n</body>")

    # Script tag ensure karein
    if '/static/admin_actions.js' not in html:
        html = html.replace("</body>", '<script src="/static/admin_actions.js"></script>\n</body>')

    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print("Admin HTML verified with complete Action Buttons Table!")
else:
    print("templates/admin.html not found, checking server embedding...")