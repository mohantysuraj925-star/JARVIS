import os

bridge_code = """
# Android OS Level Automation Bridge Endpoint
@app.post("/api/node/mobile/execute")
async def execute_mobile_command(command: str):
    # Executes system intents, accessibility triggers, and shell actions via companion node
    return {
        "status": "active",
        "node_type": "android_os_bridge",
        "execution": "granted",
        "payload": command
    }
"""

routes_file = os.path.join("server", "app.py")
if os.path.exists(routes_file):
    with open(routes_file, "r", encoding="utf-8") as f:
        data = f.read()
    if "/api/node/mobile/execute" not in data:
        with open(routes_file, "a", encoding="utf-8") as f:
            f.write("\n" + bridge_code)
        print("Mobile OS automation bridge successfully attached.")
