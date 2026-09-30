path = "server/app.py"
with open(path, "r", encoding="utf-8-sig") as f:
    text = f.read()

# 1. Lucide icons script load ensure karein
if "unpkg.com/lucide" not in text:
    text = text.replace("<head>", '<head>\n  <script src="https://unpkg.com/lucide@latest"></script>')

# 2. Purana table/markup clean karke professional modular card grid inject karein
clean_box_section = """
      <!-- OPERATOR LIFECYCLE MANAGEMENT GRID -->
      <div style="margin-top:24px;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px; border-bottom:1px solid rgba(0,240,255,0.15); padding-bottom:8px;">
          <div style="display:flex; align-items:center; gap:8px;">
            <i data-lucide="shield-check" style="width:18px; height:18px; color:#00f0ff;"></i>
            <span style="color:#00f0ff; font-size:13px; font-weight:700; letter-spacing:1px; text-transform:uppercase;">
              Operator Lifecycle Management Matrix
            </span>
          </div>
          <span style="font-size:11px; color:#64748b; font-family:monospace;">SECURE RUNTIME SYNC</span>
        </div>
        
        <div id="masterNodesContainer" style="display:grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap:12px;">
          <!-- Node boxes dynamically rendered here -->
        </div>
      </div>
"""

# Agar masterNodesContainer nahi hai toh Global Broadcast Hub ke baad add karein
if "masterNodesContainer" not in text:
    if "GLOBAL BROADCAST HUB" in text:
        pos = text.find("GLOBAL BROADCAST HUB")
        div_end = text.find("</div>", pos)
        div_end = text.find("</div>", div_end + 6)
        text = text[:div_end+6] + "\n" + clean_box_section + text[div_end+6:]
    else:
        text = text.replace("</body>", clean_box_section + "\n</body>")

with open(path, "w", encoding="utf-8") as f:
    f.write(text)

print("Modular box matrix and Lucide icons successfully integrated!")