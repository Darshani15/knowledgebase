import sqlite3
from werkzeug.security import generate_password_hash

conn = sqlite3.connect("database.db")

username = "divya"
password = generate_password_hash("admin123")

conn.execute(
    "INSERT INTO admin (username, password) VALUES (?, ?)",
    (username, password)
)

conn.commit()
conn.close()

print("Admin created successfully!")