import sqlite3
import bcrypt
from typing import Optional

DB_PATH = "users.db"


def init_db(path: str = DB_PATH) -> None:
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute(
        "CREATE TABLE IF NOT EXISTS users (email TEXT PRIMARY KEY, pw_hash BLOB, player_tag TEXT, playstyle TEXT, mute_toast INTEGER DEFAULT 0)"
    )
    cur.execute("PRAGMA table_info(users)")
    cols = {c[1] for c in cur.fetchall()}
    if "mute_toast" not in cols:
        cur.execute("ALTER TABLE users ADD COLUMN mute_toast INTEGER DEFAULT 0")
    conn.commit()
    conn.close()


def register_user(email: str, password: str, tag: str, playstyle: str, path: str = DB_PATH) -> None:
    pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute(
        "INSERT OR REPLACE INTO users (email, pw_hash, player_tag, playstyle, mute_toast) VALUES (?,?,?,?,0)",
        (email, pw_hash, tag, playstyle),
    )
    conn.commit()
    conn.close()


def get_user(email: str, path: str = DB_PATH) -> Optional[dict]:
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute("SELECT email, pw_hash, player_tag, playstyle, mute_toast FROM users WHERE email=?", (email,))
    row = cur.fetchone()
    conn.close()
    if row:
        return {
            "email": row[0],
            "pw_hash": row[1],
            "player_tag": row[2],
            "playstyle": row[3],
            "mute_toast": bool(row[4]),
        }
    return None


def load_credentials(path: str = DB_PATH) -> dict:
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute("SELECT email, pw_hash FROM users")
    creds = {
        row[0]: {"email": row[0], "name": row[0], "password": row[1]}
        for row in cur.fetchall()
    }
    conn.close()
    return {"usernames": creds}


def update_playstyle(email: str, playstyle: str, path: str = DB_PATH) -> None:
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute("UPDATE users SET playstyle=? WHERE email=?", (playstyle, email))
    conn.commit()
    conn.close()


def update_mute_toast(email: str, mute: bool, path: str = DB_PATH) -> None:
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET mute_toast=? WHERE email=?",
        (1 if mute else 0, email),
    )
    conn.commit()
    conn.close()
