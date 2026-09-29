import os
import re

# 1. FIX MICROPHONE & FORCE UNMUTE in ui.py & main.py
if os.path.exists("ui.py"):
  with open("ui.py", "r", encoding="utf-8", errors="ignore") as f:
    u = f.read()

  # Force Unmute on startup
  u = re.sub(r"self\._is_muted\s*=\s*True", "self._is_muted = False", u)
  u = re.sub(
      r'self\._mute_btn\.setText\("MUTED"\)',
      'self._mute_btn.setText("MIC ACTIVE")',
      u,
  )

  # Force Animated Face HUD
  u = re.sub(r'self\._hud_mode\s*=\s*["\']core["\']', 'self._hud_mode = "face"', u)
  u = re.sub(
      r'self\.current_hud\s*=\s*["\']core["\']', 'self.current_hud = "face"', u
  )
  u = re.sub(
      r'self\._hud_toggle_btn\.setText\("HUD: CORE"\)',
      'self._hud_toggle_btn.setText("HUD: FACE")',
      u,
  )

  # Fix Tool Execution / Command text bar routing
  if "def _on_text_submitted" in u:
    # Ensure text commands trigger tool dispatcher
    u = re.sub(
        r"def _on_text_submitted\(self.*?\):",
        "def _on_text_submitted(self, text):\n        self._append_log(f'You:"
        " {text}')\n        if hasattr(self, '_controller'):"
        " self._controller.handle_user_prompt(text)",
        u,
        count=1,
    )

  with open("ui.py", "w", encoding="utf-8") as f:
    f.write(u)

# 2. FIX MAIN.PY - Unblock Tools & Audio Streaming
if os.path.exists("main.py"):
  with open("main.py", "r", encoding="utf-8", errors="ignore") as f:
    m = f.read()

  # Re-enable tool handlers for browser, apps, and youtube
  m = re.sub(r"#\s*from actions import", "from actions import", m)
  m = re.sub(
      r"is_muted\s*=\s*True", "is_muted = False", m
  )  # Unmute main audio loop

  # Ensure tools are provided to Gemini model
  if "tools=" not in m and "self.tools" in m:
    m = m.replace("model=MODEL", "model=MODEL, tools=self.tools")

  with open("main.py", "w", encoding="utf-8") as f:
    f.write(m)

print(">>> ALL AUDIO, HUD FACE, & TOOL COMMANDS RESTORED! <<<")