from cryptography.fernet import Fernet
import os
from flask import (
    Flask,
    render_template,
    request,
    session,
    redirect,
    url_for,
    )
import secrets
from database.db import (
    pre_populate_data,
    get_users_data,
    get_contest_results,
    validate_and_submit_input,
    authenticate_user,
    decrypt_data,
    _connect,
    )
from functools import wraps

app = Flask(__name__)

# Ensure database schema and seed data are present
try:
    pre_populate_data()
except Exception as e:
    pass

app.secret_key = secrets.token_hex(16)

def require_security_level(level):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # checked logged in
            if 'user_id' not in session:
                return redirect(url_for('login'))
            # verify sec level
            current_level = session.get('security_level', 0)
            if current_level < level:
                return render_template('notfound.html')

            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.route("/")
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    return render_template("home.html")

@app.route("/enternew")
@require_security_level(3)
def add_new_baking_contest_user():
    return render_template("enternew.html")

@app.route("/addrec", methods=["POST"])
def add_record_or_show_error():
    name = request.form.get('name', '')
    age = request.form.get('age', '')
    phone = request.form.get('phone', '')
    security_level = request.form.get('security_level', '')
    password = request.form.get('password', '')

    res = validate_and_submit_input(name, age, phone, security_level, password)
    return render_template("addrec.html", res=res)

@app.route("/list")
@require_security_level(2)
def list_contest_users():
    res = get_users_data()
    return render_template("list.html", res=res)

@app.route("/contestResults")
@require_security_level(3)
def contest_results():
    res = get_contest_results()
    return render_template("contestResults.html", res=res)

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        password = request.form.get('password', '')

        try:
            user = authenticate_user(name, password)
            if user:
                session['user_id'] = user['id']
                session['username'] = user['name']
                session['security_level'] = user['security_level']
                return redirect(url_for('home'))
            else:
                error = "Invalid username or password"
                return render_template('login.html', error=error)
        except Exception as e:
            # Catch any exceptions during authentication and show a user-friendly error
            app.logger.error(f"Authentication error: {str(e)}")
            error = "An error occurred during login. Please try again."
            return render_template('login.html', error=error)

    return render_template('login.html')

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route("/mycontestresults")
def my_contest_results():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    with _connect() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT item_name, votes_excellent, votes_ok, votes_bad
            FROM entries
            WHERE user_id = ?
            """, (user_id,)
        )
        results = cur.fetchall()
    return render_template("mycontestresults.html", results=results)

@app.route("/addcontestentry")
def add_contest_entry_page():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    security_level = session.get('security_level', 0)
    if security_level < 1:  # min sec level 1 for adding contest entries
        return render_template('unauthorized.html')

    return render_template("addcontestentry.html")

@app.route("/submitentry", methods=["POST"])
def submit_contest_entry():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    security_level = session.get('security_level', 0)
    if security_level < 1: # min sec level 1 for adding contest entries
        return render_template('unauthorized.html')

    item_name = request.form.get('item_name', '').strip()
    try:
        votes_excellent = int(request.form.get('votes_excellent', 0))
        votes_ok = int(request.form.get('votes_ok', 0))
        votes_bad = int(request.form.get('votes_bad', 0))
    except ValueError as e:
        return render_template("addcontestentry.html", error="Votes must be integers.")

    errors = []
    if not item_name or not item_name.strip():
        errors.append("item_name")
    if votes_excellent < 0:
        errors.append("votes_excellent")
    if votes_ok < 0:
        errors.append("votes_ok")
    if votes_bad < 0:
        errors.append("votes_bad")

    if errors:
        return render_template("addcontestentry.html", errors=errors)

    # all values valid, security level ok, insert into db
    with _connect() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO entries
            (user_id, item_name, votes_excellent, votes_ok, votes_bad)
            VALUES (?, ?, ?, ?, ?)
            """,
            (session['user_id'], item_name, votes_excellent, votes_ok, votes_bad)
        )
        conn.commit()

    return render_template("addcontestentry.html", success=True)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)