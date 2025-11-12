import sqlite3

db_path = " database.db"

try: 
    conn = sqlite3.connect(db_path)
except Exception as e:
    raise ConnectionError(f"unable to connect to db {e}")