path = "server/app.py"
with open(path, "r", encoding="utf-8-sig") as f:
    text = f.read()

# get_db ko get_db_connection se replace karein
text = text.replace("conn = get_db()\n", "conn = get_db_connection()\n")
text = text.replace("conn = get_db()", "conn = get_db_connection()")

# Fallback definition ensure karein agar function name alag ho
if "def get_db():" not in text and "def get_db_connection():" in text:
    text = text.replace("def get_db_connection():", "def get_db_connection():\n    pass\nget_db = get_db_connection\n")

with open(path, "w", encoding="utf-8") as f:
    f.write(text)

print("get_db name error resolved!")