path = "server/app.py"
with open(path, "r", encoding="utf-8-sig") as f:
    text = f.read()

# Control table markup jo Global Broadcast Hub ke baad aayega
control_panel_section = """
      <!-- OPERATOR LIFECYCLE & ACCESS CONTROL MATRIX -->
      <div style="background:rgba(10,16,32,0.92); border:1px solid rgba(0,240,255,0.25); border-radius:14px; padding:20px; margin-top:20px; box-shadow:0 0 25px rgba(0,0,0,0.5);">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:14px; border-bottom:1px solid rgba(0,240,255,0.15); padding-bottom:10px;">
          <h3 style="color:#00f0ff; font-size:16px; letter-spacing:1px; text-transform:uppercase; margin:0;">
            ⚡ Operator Lifecycle & Access Control Engine
          </h3>
          <span style="font-size:12px; color:#94a3b8;">Real-Time Database Sync</span>
        </div>
        
        <div style="overflow-x:auto;">
          <table style="width:100%; border-collapse:collapse; min-width:750px; font-size:13px; text-align:left;">
            <thead>
              <tr style="background:rgba(0,240,255,0.06); color:#64748b; text-transform:uppercase; font-size:11px; letter-spacing:1px;">
                <th style="padding:10px;">ID</th>
                <th style="padding:10px;">Operator</th>
                <th style="padding:10px;">State</th>
                <th style="padding:10px;">Remaining Days</th>
                <th style="padding:10px;">Calendar Access</th>
                <th style="padding:10px;">Daily Time Window</th>
                <th style="padding:10px; text-align:center;">Master Control</th>
              </tr>
            </thead>
            <tbody id="masterNodesTableBody">
              <tr><td colspan="7" style="text-align:center; padding:18px; color:#64748b;">Loading nodes...</td></tr>
            </tbody>
          </table>
        </div>
      </div>
"""

# Agar table present nahi hai toh broadcast hub ke theek baad inject karein
if "masterNodesTableBody" not in text:
    if "GLOBAL BROADCAST HUB" in text:
        pos = text.find("GLOBAL BROADCAST HUB")
        div_end = text.find("</div>", pos)
        div_end = text.find("</div>", div_end + 6)
        text = text[:div_end+6] + "\n" + control_panel_section + text[div_end+6:]
    else:
        text = text.replace("</body>", control_panel_section + "\n</body>")

with open(path, "w", encoding="utf-8") as f:
    f.write(text)

print("Control Panel Table embedded into Master Console!")