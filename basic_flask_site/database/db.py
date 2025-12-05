import os
import sqlite3
import hashlib
from cryptography.fernet import Fernet
import secrets

# Resolve DB path to repo root/basic_flask_site/database.db
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database.db")

def get_or_create_key():
    key_file = 'secret.key'
    if os.path.exists(key_file):
        with open(key_file, 'rb') as f:
            key = f.read()
            return key
    else:
        new_key = Fernet.generate_key()
        with open(key_file, 'wb') as f:
            f.write(new_key)
        return new_key

key = get_or_create_key()

fernet = Fernet(key)

def encrypt_data(data):
    """Encrypt sensitive data."""
    if data is None:
        return None
    try:
        encrypted = fernet.encrypt(data.encode()).decode()
        return encrypted
    except Exception as e:
        # If encryption fails, return the original data as fallback for compatibility
        return data

def decrypt_data(encrypted_data):
    """Decrypt sensitive data."""
    if encrypted_data is None:
        return None
    try:
        # Try to decrypt the data
        decrypted = fernet.decrypt(encrypted_data.encode()).decode()
        return decrypted
    except Exception as e:
        # If decryption fails, return the original data as fallback for compatibility
        return encrypted_data

def _connect():
    """Create a short-lived SQLite connection.

    Using per-operation connections avoids problems with global connections
    under multi-process WSGI servers (e.g., Apache mod_wsgi, gunicorn).
    """
    conn = sqlite3.connect(DB_PATH)
    return conn


def pre_populate_data():
    """Create schema and pre-populate rows if empty."""
    with _connect() as conn:
        cur = conn.cursor()

        # Create tables if they don't exist
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                age INTEGER NOT NULL,
                phone TEXT NOT NULL,
                security_level INTEGER NOT NULL,
                password TEXT NOT NULL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS entries (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                item_name TEXT NOT NULL,
                votes_excellent INTEGER NOT NULL DEFAULT 0,
                votes_ok INTEGER NOT NULL DEFAULT 0,
                votes_bad INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """
        )

        # Seed users if empty
        cur.execute("SELECT COUNT(*) FROM users")
        (user_count,) = cur.fetchone()
        if user_count == 0:
            users_seed = [
                (encrypt_data("ADMIN"), 30, encrypt_data("123-456-7890"), 3, encrypt_data("adminpwd")),
                (encrypt_data("Alice"), 28, encrypt_data("555-111-2222"), 2, encrypt_data("alicepwd")),
                (encrypt_data("Bob"), 35, encrypt_data("555-222-3333"), 1, encrypt_data("bobpwd")),
                (encrypt_data("Carol"), 42, encrypt_data("555-333-4444"), 3, encrypt_data("carolpwd")),
                (encrypt_data("Smith"), 37, encrypt_data("239-456-789"), 2, encrypt_data("smithpwd")),
            ]
            cur.executemany(
                "INSERT INTO users (name, age, phone, security_level, password) VALUES (?, ?, ?, ?, ?)",
                users_seed,
            )

        # Seed entries if empty
        cur.execute("SELECT COUNT(*) FROM entries")
        (entry_count,) = cur.fetchone()
        if entry_count == 0:
            # Fetch a few user ids to link
            cur.execute("SELECT id FROM users ORDER BY id LIMIT 3")
            user_ids = [row[0] for row in cur.fetchall()]
            if not user_ids:
                # Ensure at least one user exists to attach entries
                cur.execute(
                    "INSERT INTO users (name, age, phone, security_level, password) VALUES (?, ?, ?, ?, ?)",
                    ("TempUser", 30, "555-000-0000", 1, "temppwd"),
                )
                user_ids = [cur.lastrowid]

            entries_seed = [
                (user_ids[0], "Chocolate Cake", 12, 5, 1),
                (user_ids[min(1, len(user_ids) - 1)], "Apple Pie", 7, 9, 2),
                (user_ids[min(2, len(user_ids) - 1)], "Blueberry Muffins", 4, 8, 3),
                (user_ids[min(3, len(user_ids) - 1)], "Sugar Cookies", 7, 9, 3),
            ]
            cur.executemany(
                "INSERT INTO entries (user_id, item_name, votes_excellent, votes_ok, votes_bad) VALUES (?, ?, ?, ?, ?)",
                entries_seed,
            )

        conn.commit()

def get_contest_results():
    with _connect() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, user_id, item_name, votes_excellent, votes_ok, votes_bad
            FROM entries
            ORDER BY id
            """
        )
        results = cur.fetchall()
        return results

def get_users_data():
    with _connect() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT name, age, phone, security_level, password
            FROM users
            ORDER BY id
            """
        )
        raw_results = cur.fetchall()

        results = []
        for row in raw_results:
            decrypted_row = (
                decrypt_data(row[0]),  # name
                row[1],                # age
                decrypt_data(row[2]),  # phone
                row[3],                # security_level
                decrypt_data(row[4]),  # password
            )
            results.append(decrypted_row)
        return results

def validate_and_submit_input(name, age, phone, security_level, password):
    errors = []

    # Name: not empty and not spaces only
    if not name or not name.strip():
        errors.append("name")

    # Age: whole number > 0 and < 121
    try:
        age_i = int(str(age).strip())
        if age_i < 1 or age_i > 120:
            errors.append("age")
    except Exception:
        errors.append("age")

    # Phone: not empty and not spaces only
    if not phone or not phone.strip():
        errors.append("phone")

    # Security level: numeric between 1 and 3
    try:
        sec_i = int(str(security_level).strip())
        if sec_i < 1 or sec_i > 3:
            errors.append("sec")
    except Exception:
        errors.append("sec")

    # Password: not empty and not spaces only
    if not password or not password.strip():
        errors.append("pwd")

    if errors:
        return errors

    # Insert record
    with _connect() as conn:
        cur = conn.cursor()
        encrypted_name = encrypt_data(name.strip())
        encrypted_phone = encrypt_data(phone.strip())
        encrypted_password = encrypt_data(password)

        cur.execute(
            "INSERT INTO users (name, age, phone, security_level, password) VALUES (?, ?, ?, ?, ?)",
            (encrypted_name, age_i, encrypted_phone, sec_i, encrypted_password),
        )
        conn.commit()
        return ("success",)

def authenticate_user(name, password):

    with _connect() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, name, security_level, password FROM users")
        user_pass = cur.fetchall()

        for user in user_pass:
            try:
                decrypted_name = decrypt_data(user[1])
                if decrypted_name == name:
                    # verify password
                    decrypted_stored_password = decrypt_data(user[3])
                    if decrypted_stored_password == password:
                        return {
                            "id": user[0],
                            "name": decrypted_name,
                            "security_level": user[2],
                        }
            except Exception as e:
                continue
    return None

# Optional: ensure schema exists on import to avoid first-run errors
try:
    pre_populate_data()
except Exception as e:
    # Defer to app to call pre_populate_data() explicitly if needed
    pass
