import sqlite3
import os
import hashlib
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "portal.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def hash_pw(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    with get_db() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS licenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            hwid TEXT UNIQUE,
            days_allocated INTEGER DEFAULT 10,
            is_lifetime BOOLEAN DEFAULT 0,
            is_blocked BOOLEAN DEFAULT 0,
            first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS broadcasts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message TEXT NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS telemetry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            download_type TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        conn.execute(
            "INSERT OR IGNORE INTO users (username, password_hash, role) VALUES (?, ?, ?)",
            ("admin123", hash_pw("Suraj"), "admin")
        )

def register_user(username: str, password: str):
    if len(password) < 5:
        return False, "Password must be at least 5 characters"
    with get_db() as conn:
        try:
            cur = conn.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, 'user')",
                (username, hash_pw(password))
            )
            user_id = cur.lastrowid
            conn.execute("INSERT INTO licenses (user_id, days_allocated) VALUES (?, 10)", (user_id,))
            return True, "User registered successfully"
        except sqlite3.IntegrityError:
            return False, "Username already exists"

def authenticate_user(username: str, password: str):
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE username = ? AND password_hash = ?",
            (username, hash_pw(password))
        ).fetchone()
        return dict(row) if row else None

def get_broadcast():
    with get_db() as conn:
        row = conn.execute("SELECT message FROM broadcasts WHERE is_active = 1 ORDER BY id DESC LIMIT 1").fetchone()
        return row["message"] if row else None
