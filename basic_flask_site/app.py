from flask import Flask, render_template, render_template_string
from database.db import conn

app = Flask(__name__)
cur = conn.cursor()

@app.route("/health")
def health():
    return render_template_string("healthy")

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/enternew")
def add_new_baking_content_user():
    return render_template("enternew.html")

@app.route("/addrec")
def add_record_or_show_error():
    return render_template("addrec.html")

@app.route("/list")
def list_contest_users():
    return render_template("list.html")

@app.route("/contestResults")
def contest_results():
    return render_template("contestResults.html")

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)