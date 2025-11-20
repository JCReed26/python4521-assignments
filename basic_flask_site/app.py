from flask import Flask, render_template, request
from database.db import (
    conn,
    pre_populate_data,
    get_users_data,
    get_contest_results,
    validate_and_submit_input,
)

app = Flask(__name__)

# Ensure database schema and seed data are present
try:
    pre_populate_data()
except Exception:
    pass

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/enternew")
def add_new_baking_content_user():
    return render_template("enternew.html")

@app.route("/addrec", methods=["POST"])
def add_record_or_show_error():
    res = validate_and_submit_input(
        request.form.get('name', ''),
        request.form.get('age', ''),
        request.form.get('phone', ''),
        request.form.get('security_level', ''),
        request.form.get('password', ''),
    )
    return render_template("addrec.html", res=res)

@app.route("/list")
def list_contest_users():
    res = get_users_data()
    return render_template("list.html", res=res)

@app.route("/contestResults")
def contest_results():
    res = get_contest_results()
    return render_template("contestResults.html", res=res)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
