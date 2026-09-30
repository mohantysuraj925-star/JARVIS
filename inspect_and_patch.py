path = "server/app.py"
with open(path, "r", encoding="utf-8-sig") as f:
    text = f.read()

# Ensure get_db and get_db_connection both exist safely
helper = """
def get_db_connection():
    import sqlite3
    db_path = "portal.db" if os.path.exists("portal.db") else "jarvis.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

get_db = get_db_connection
"""

if "def get_db_connection():" not in text and "def get_db():" not in text:
    text = helper + "\n" + text
elif "get_db = get_db_connection" not in text:
    text = text.replace("def get_db_connection():", "def get_db_connection():\n    pass\nget_db = get_db_connection\n")

with open(path, "w", encoding="utf-8") as f:
    f.write(text)

print("DB connection helpers normalized!")