import os
import sqlite3

# Resolve DB path to repo root/basic_flask_site/database.db
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database.db")

def _connect():
    """Create a short-lived SQLite connection.

    Using per-operation connections avoids problems with global connections
    under multi-process WSGI servers (e.g., Apache mod_wsgi, gunicorn).
    """
    return sqlite3.connect(DB_PATH)

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
                ("PDiana", 28, "555-111-2222", 1, "alicepwd"),
                ("TJones", 35, "555-222-3333", 2, "bobpwd"),
                ("AMath", 42, "555-333-4444", 3, "carolpwd"),
                ("BSmith", 37, "239-456-789", 2, "smithpwd"),
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
        return cur.fetchall()

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
        return cur.fetchall()

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
        cur.execute(
            "INSERT INTO users (name, age, phone, security_level, password) VALUES (?, ?, ?, ?, ?)",
            (name.strip(), age_i, phone.strip(), sec_i, password),
        )
        conn.commit()
        return ("success",)

# Optional: ensure schema exists on import to avoid first-run errors
try:
    pre_populate_data()
except Exception:
    # Defer to app to call pre_populate_data() explicitly if needed
    pass
