import sqlite3

conn = sqlite3.connect("jarvis.db")
c = conn.cursor()
c.execute("CREATE TABLE IF NOT EXISTS portal_stats (key TEXT PRIMARY KEY, val INTEGER)")
c.execute("INSERT OR IGNORE INTO portal_stats (key, val) VALUES (?, ?)", ("downloads", 142))
conn.commit()
conn.close()
print("DB Synced Successfully!")