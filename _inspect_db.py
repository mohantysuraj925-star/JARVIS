import sqlite3, os

for p in ["portal.db", "server/portal.db"]:
    if not os.path.exists(p):
        print("MISSING:", p)
        continue
    print("==", p, os.path.getsize(p), "bytes")
    c = sqlite3.connect(p)
    cur = c.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    print("  tables:", [t[0] for t in cur.fetchall()])
    try:
        cur.execute("PRAGMA table_info(users)")
        print("  users cols:", [r[1] for r in cur.fetchall()])
    except Exception as e:
        print("  users err:", e)
    c.close()
