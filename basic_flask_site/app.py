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

print("DEBUG: Starting app initialization")
# Ensure database schema and seed data are present
try:
    print("DEBUG: Calling pre_populate_data")
    pre_populate_data()
except Exception as e:
    print(f"DEBUG: Exception during pre_populate_data: {e}")
    pass

app.secret_key = secrets.token_hex(16)
print(f"DEBUG: Set app secret key: {app.secret_key[:10]}...")

def require_security_level(level):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            print(f"DEBUG: Security check for level {level}, function {f.__name__}")
            # checked logged in
            if 'user_id' not in session:
                print("DEBUG: User not logged in, redirecting to login")
                return redirect(url_for('login'))
            # verify sec level
            current_level = session.get('security_level', 0)
            print(f"DEBUG: User security level: {current_level}, required: {level}")
            if current_level < level:
                print("DEBUG: Insufficient security level, showing notfound.html")
                return render_template('notfound.html')

            print("DEBUG: Security check passed")
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.route("/")
def home():
    if 'user_id' not in session:
        print("DEBUG: User not logged in, redirecting to login")
        return redirect(url_for('login'))

    print("DEBUG: Home route accessed")
    return render_template("home.html")

@app.route("/enternew")
@require_security_level(3)
def add_new_baking_contest_user():
    print("DEBUG: Enternew route accessed")
    return render_template("enternew.html")

@app.route("/addrec", methods=["POST"])
def add_record_or_show_error():
    print("DEBUG: Addrec route accessed, method=POST")
    name = request.form.get('name', '')
    age = request.form.get('age', '')
    phone = request.form.get('phone', '')
    security_level = request.form.get('security_level', '')
    password = request.form.get('password', '')

    print(f"DEBUG: Form data - name: '{name}', age: '{age}', phone: '{phone}', security_level: '{security_level}', password: '[HIDDEN]'")

    res = validate_and_submit_input(name, age, phone, security_level, password)
    print(f"DEBUG: validate_and_submit_input returned: {res}")
    return render_template("addrec.html", res=res)

@app.route("/list")
@require_security_level(2)
def list_contest_users():
    print("DEBUG: List route accessed")
    res = get_users_data()
    print(f"DEBUG: get_users_data returned {len(res) if res else 0} records")
    return render_template("list.html", res=res)

@app.route("/contestResults")
@require_security_level(3)
def contest_results():
    print("DEBUG: ContestResults route accessed")
    res = get_contest_results()
    print(f"DEBUG: get_contest_results returned {len(res) if res else 0} records")
    return render_template("contestResults.html", res=res)

@app.route("/login", methods=['GET', 'POST'])
def login():
    print(f"DEBUG: Login route accessed, method: {request.method}")
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        password = request.form.get('password', '')
        print(f"DEBUG: Login attempt for user: '{name}'")

        try:
            print("DEBUG: Calling authenticate_user")
            user = authenticate_user(name, password)
            print(f"DEBUG: authenticate_user returned: {user}")
            if user:
                print(f"DEBUG: Login successful for user id {user['id']}, setting session")
                session['user_id'] = user['id']
                session['username'] = user['name']
                session['security_level'] = user['security_level']
                print(f"DEBUG: Session data set - user_id: {session['user_id']}, username: {session['username']}, security_level: {session['security_level']}")
                return redirect(url_for('home'))
            else:
                print("DEBUG: Invalid username or password")
                error = "Invalid username or password"
                return render_template('login.html', error=error)
        except Exception as e:
            # Catch any exceptions during authentication and show a user-friendly error
            print(f"DEBUG: Exception during authentication: {str(e)}")
            app.logger.error(f"Authentication error: {str(e)}")
            error = "An error occurred during login. Please try again."
            return render_template('login.html', error=error)

    print("DEBUG: Showing login form (GET request)")
    return render_template('login.html')

@app.route("/logout")
def logout():
    print("DEBUG: Logout route accessed")
    old_session = dict(session)  # Save old session for debug
    session.clear()
    print(f"DEBUG: Session cleared - was: {old_session}")
    return redirect(url_for('home'))

@app.route("/mycontestresults")
def my_contest_results():
    print("DEBUG: Mycontestresults route accessed")
    if 'user_id' not in session:
        print("DEBUG: User not logged in, redirecting to login")
        return redirect(url_for('login'))

    user_id = session['user_id']
    print(f"DEBUG: Getting contest results for user_id: {user_id}")
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
        print(f"DEBUG: Retrieved {len(results)} contest results from database")
    return render_template("mycontestresults.html", results=results)

@app.route("/addcontestentry")
def add_contest_entry_page():
    print("DEBUG: Addcontestentry route accessed")
    if 'user_id' not in session:
        print("DEBUG: User not logged in, redirecting to login")
        return redirect(url_for('login'))
    security_level = session.get('security_level', 0)
    print(f"DEBUG: User security level: {security_level}")
    if security_level < 1:  # min sec level 1 for adding contest entries
        print("DEBUG: Insufficient security level, showing unauthorized.html")
        return render_template('unauthorized.html')

    return render_template("addcontestentry.html")

@app.route("/submitentry", methods=["POST"])
def submit_contest_entry():
    print("DEBUG: Submitentry route accessed, method=POST")
    if 'user_id' not in session:
        print("DEBUG: User not logged in, redirecting to login")
        return redirect(url_for('login'))

    security_level = session.get('security_level', 0)
    print(f"DEBUG: User security level: {security_level}")
    if security_level < 1: # min sec level 1 for adding contest entries
        print("DEBUG: Insufficient security level, showing unauthorized.html")
        return render_template('unauthorized.html')

    item_name = request.form.get('item_name', '').strip()
    try:
        votes_excellent = int(request.form.get('votes_excellent', 0))
        votes_ok = int(request.form.get('votes_ok', 0))
        votes_bad = int(request.form.get('votes_bad', 0))
        print(f"DEBUG: Parsed form data - item_name: '{item_name}', votes_excellent: {votes_excellent}, votes_ok: {votes_ok}, votes_bad: {votes_bad}")
    except ValueError as e:
        print(f"DEBUG: ValueError parsing votes: {e}")
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

    print(f"DEBUG: Validation errors: {errors}")
    if errors:
        return render_template("addcontestentry.html", errors=errors)

    # all values valid, security level ok, insert into db
    print("DEBUG: All validation passed, inserting into database")
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
        print(f"DEBUG: Inserted contest entry for user {session['user_id']}")

    return render_template("addcontestentry.html", success=True)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)