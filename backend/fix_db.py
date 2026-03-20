import sqlite3
import hashlib
import os
import base64
import secrets

def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")

def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 260_000)
    return f"pbkdf2_sha256$260000${_b64url_encode(salt)}${_b64url_encode(dk)}"

conn = sqlite3.connect('cxmind.db')
c = conn.cursor()
hashed = hash_password("password123")
try:
    c.execute("INSERT INTO users (org_id, email, password_hash, role, is_active, token_version, created_at) VALUES (1, 'admin@example.com', ?, 'admin', 1, 1, datetime('now'))", (hashed,))
    conn.commit()
    print("SUCCESS")
except sqlite3.IntegrityError as e:
    print("FAILED:", e)
