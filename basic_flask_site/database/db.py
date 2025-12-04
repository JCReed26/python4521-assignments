import os
import sqlite3
import hashlib
from cryptography.fernet import Fernet
import secrets

# Resolve DB path to repo root/basic_flask_site/database.db
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database.db")

def get_or_create_key():
    print("DEBUG: get_or_create_key called")
    key_file = 'secret.key'
    if os.path.exists(key_file):
        print(f"DEBUG: Loading key from existing file: {key_file}")
        with open(key_file, 'rb') as f:
            key = f.read()
            print(f"DEBUG: Loaded key: {key[:10]}...")
            return key
    else:
        print(f"DEBUG: Creating new key file: {key_file}")
        new_key = Fernet.generate_key()
        with open(key_file, 'wb') as f:
            f.write(new_key)
        print(f"DEBUG: Created new key: {new_key[:10]}...")
        return new_key

print("DEBUG: Calling get_or_create_key on module import")
key = get_or_create_key()

print("DEBUG: Creating Fernet instance")
fernet = Fernet(key)

def encrypt_data(data):
    """Encrypt sensitive data."""
    if data is None:
        print(f"DEBUG: encrypt_data called with None, returning None")
        return None
    print(f"DEBUG: encrypt_data called with '{data}'")
    try:
        encrypted = fernet.encrypt(data.encode()).decode()
        print(f"DEBUG: encrypt_data encrypted '{data}' -> '{encrypted[:20]}...'")
        return encrypted
    except Exception as e:
        print(f"DEBUG: encrypt_data failed to encrypt '{data}', error: {e}")
        print(f"DEBUG: Returning raw data as fallback: '{data}'")
        # If encryption fails, return the original data as fallback for compatibility
        return data

def decrypt_data(encrypted_data):
    """Decrypt sensitive data."""
    if encrypted_data is None:
        print(f"DEBUG: decrypt_data called with None, returning None")
        return None
    print(f"DEBUG: decrypt_data called with '{encrypted_data[:20]}...'")
    try:
        # Try to decrypt the data
        decrypted = fernet.decrypt(encrypted_data.encode()).decode()
        print(f"DEBUG: decrypt_data decrypted to '{decrypted}'")
        return decrypted
    except Exception as e:
        print(f"DEBUG: decrypt_data failed to decrypt '{encrypted_data[:20]}...', error: {e}")
        print(f"DEBUG: Returning raw data as fallback: '{encrypted_data}'")
        # If decryption fails, return the original data as fallback for compatibility
        return encrypted_data

def _connect():
    """Create a short-lived SQLite connection.

    Using per-operation connections avoids problems with global connections
    under multi-process WSGI servers (e.g., Apache mod_wsgi, gunicorn).
    """
    print(f"DEBUG: _connect called, connecting to DB: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    print(f"DEBUG: Connected to database: {DB_PATH}")
    return conn


def pre_populate_data():
    """Create schema and pre-populate rows if empty."""
    print("DEBUG: pre_populate_data called")
    with _connect() as conn:
        cur = conn.cursor()
        print("DEBUG: Creating database tables if they don't exist")

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
        print("DEBUG: Users table created/verified")
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
        print("DEBUG: Entries table created/verified")

        # Seed users if empty
        cur.execute("SELECT COUNT(*) FROM users")
        (user_count,) = cur.fetchone()
        print(f"DEBUG: User count in database: {user_count}")
        if user_count == 0:
            print("DEBUG: No users found, adding seed data")
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
            print(f"DEBUG: Inserted {len(users_seed)} seed users")

        # Seed entries if empty
        cur.execute("SELECT COUNT(*) FROM entries")
        (entry_count,) = cur.fetchone()
        print(f"DEBUG: Entry count in database: {entry_count}")
        if entry_count == 0:
            print("DEBUG: No entries found, adding seed entries")
            # Fetch a few user ids to link
            cur.execute("SELECT id FROM users ORDER BY id LIMIT 3")
            user_ids = [row[0] for row in cur.fetchall()]
            print(f"DEBUG: Retrieved user IDs: {user_ids}")
            if not user_ids:
                print("DEBUG: No users available, creating temp user")
                # Ensure at least one user exists to attach entries
                cur.execute(
                    "INSERT INTO users (name, age, phone, security_level, password) VALUES (?, ?, ?, ?, ?)",
                    ("TempUser", 30, "555-000-0000", 1, "temppwd"),
                )
                user_ids = [cur.lastrowid]
                print(f"DEBUG: Created temp user with ID: {user_ids[0]}")

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
            print(f"DEBUG: Inserted {len(entries_seed)} seed entries")

        conn.commit()
        print("DEBUG: pre_populate_data completed, transaction committed")

def get_contest_results():
    print("DEBUG: get_contest_results called")
    with _connect() as conn:
        cur = conn.cursor()
        print("DEBUG: Executing SELECT query on entries table")
        cur.execute(
            """
            SELECT id, user_id, item_name, votes_excellent, votes_ok, votes_bad
            FROM entries
            ORDER BY id
            """
        )
        results = cur.fetchall()
        print(f"DEBUG: Retrieved {len(results)} contest results from database")
        return results

def get_users_data():
    print("DEBUG: get_users_data called")
    with _connect() as conn:
        cur = conn.cursor()
        print("DEBUG: Executing SELECT query on users table")
        cur.execute(
            """
            SELECT name, age, phone, security_level, password
            FROM users
            ORDER BY id
            """
        )
        raw_results = cur.fetchall()
        print(f"DEBUG: Retrieved {len(raw_results)} raw user records from database")

        results = []
        for i, row in enumerate(raw_results):
            print(f"DEBUG: Decrypting user record {i+1}: encrypted_name={row[0][:20] if row[0] else None}...")
            decrypted_row = (
                decrypt_data(row[0]),  # name
                row[1],                # age
                decrypt_data(row[2]),  # phone
                row[3],                # security_level
                decrypt_data(row[4]),  # password
            )
            print(f"DEBUG: Decrypted user record {i+1}: name='{decrypted_row[0]}', age={decrypted_row[1]}, phone='{decrypted_row[2]}', level={decrypted_row[3]}")
            results.append(decrypted_row)
        print(f"DEBUG: Returning {len(results)} decrypted user records")
        return results

def validate_and_submit_input(name, age, phone, security_level, password):
    print(f"DEBUG: validate_and_submit_input called with name='{name}', age='{age}', phone='{phone}', security_level='{security_level}', password='[HIDDEN]'")
    errors = []

    # Name: not empty and not spaces only
    if not name or not name.strip():
        print("DEBUG: Validation failed: name is empty or only spaces")
        errors.append("name")

    # Age: whole number > 0 and < 121
    try:
        age_i = int(str(age).strip())
        print(f"DEBUG: Parsed age: {age_i}")
        if age_i < 1 or age_i > 120:
            print(f"DEBUG: Validation failed: age {age_i} out of range (1-120)")
            errors.append("age")
    except Exception:
        print(f"DEBUG: Validation failed: could not parse age '{age}'")
        errors.append("age")

    # Phone: not empty and not spaces only
    if not phone or not phone.strip():
        print("DEBUG: Validation failed: phone is empty or only spaces")
        errors.append("phone")

    # Security level: numeric between 1 and 3
    try:
        sec_i = int(str(security_level).strip())
        print(f"DEBUG: Parsed security level: {sec_i}")
        if sec_i < 1 or sec_i > 3:
            print(f"DEBUG: Validation failed: security level {sec_i} out of range (1-3)")
            errors.append("sec")
    except Exception:
        print(f"DEBUG: Validation failed: could not parse security level '{security_level}'")
        errors.append("sec")

    # Password: not empty and not spaces only
    if not password or not password.strip():
        print("DEBUG: Validation failed: password is empty or only spaces")
        errors.append("pwd")

    print(f"DEBUG: Validation errors: {errors}")
    if errors:
        print(f"DEBUG: Returning validation errors: {errors}")
        return errors

    print("DEBUG: All validations passed, inserting new user record")
    # Insert record
    with _connect() as conn:
        cur = conn.cursor()
        print(f"DEBUG: Attempting to encrypt name: {name.strip()}")
        encrypted_name = encrypt_data(name.strip())
        print(f"DEBUG: Attempting to encrypt phone: {phone.strip()}")
        encrypted_phone = encrypt_data(phone.strip())
        print(f"DEBUG: Attempting to encrypt password")
        encrypted_password = encrypt_data(password)

        cur.execute(
            "INSERT INTO users (name, age, phone, security_level, password) VALUES (?, ?, ?, ?, ?)",
            (encrypted_name, age_i, encrypted_phone, sec_i, encrypted_password),
        )
        conn.commit()
        print(f"DEBUG: User record inserted successfully for {name.strip()}")
        return ("success",)

def authenticate_user(name, password):
    print(f"DEBUG: authenticate_user called with name='{name}', password='[HIDDEN]'")

    with _connect() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, name, security_level, password FROM users")
        user_pass = cur.fetchall()
        print(f"DEBUG: Retrieved {len(user_pass)} users from database")

        for user in user_pass:
            print(f"DEBUG: Checking user id={user[0]}, encrypted name={user[1][:10] if user[1] else None}...")
            try:
                decrypted_name = decrypt_data(user[1])
                print(f"DEBUG: Decrypted name '{user[1][:20]}...' -> '{decrypted_name}'")
                if decrypted_name == name:
                    print(f"DEBUG: Name matches '{name}', checking password...")
                    # verify password
                    decrypted_stored_password = decrypt_data(user[3])
                    print(f"DEBUG: Decrypted password '{user[3][:20]}...' -> '{decrypted_stored_password}'")
                    if decrypted_stored_password == password:
                        print(f"DEBUG: Password matches, returning user data for id={user[0]}")
                        return {
                            "id": user[0],
                            "name": decrypted_name,
                            "security_level": user[2],
                        }
                    else:
                        print(f"DEBUG: Password does not match")
                else:
                    print(f"DEBUG: Name does not match, expected '{decrypted_name}', got '{name}'")
            except Exception as e:
                print(f"DEBUG: Exception during decryption: {e}")
                continue
    print("DEBUG: authenticate_user returning None - no match found")
    return None

# Optional: ensure schema exists on import to avoid first-run errors
print("DEBUG: Running pre_populate_data on module import")
try:
    pre_populate_data()
except Exception as e:
    print(f"DEBUG: Exception during pre_populate_data on import: {e}")
    # Defer to app to call pre_populate_data() explicitly if needed
    pass
