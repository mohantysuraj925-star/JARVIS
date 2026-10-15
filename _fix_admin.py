import server.database as d

c = d.get_db()
c.execute(
    "UPDATE users SET password_hash = ? WHERE username = 'admin123'",
    (d.hash_pw("Suraj@2026"),),
)
c.commit()

print("auth Suraj@2026:", d.authenticate_user("admin123", "Suraj@2026") is not None)
