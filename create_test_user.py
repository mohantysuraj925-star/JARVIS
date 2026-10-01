import sqlite3
import time
from datetime import datetime

conn = sqlite3.connect("portal.db")
c = conn.cursor()

# Super Admin Fix
now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
c.execute("INSERT OR REPLACE INTO users (id, username, password, role, created_at, days_remaining, is_unlimited, is_active, last_seen) VALUES (1, 'admin123', 'suraj', 'admin', ?, 9999, 1, 1, ?)", (now_str, time.time()))

# Random Verified Operator Node
c.execute("INSERT OR REPLACE INTO users (username, password, role, created_at, days_remaining, is_unlimited, is_active, last_seen) VALUES ('user777', 'pass777', 'operator', ?, 10, 0, 1, ?)", (now_str, time.time()))

conn.commit()
conn.close()
print("Credentials inserted into database successfully!")