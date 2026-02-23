from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = "change_this_to_a_random_secret"  # production me strong secret use karo

DB_PATH = "users.db"

# ---------------- DB init ----------------
def init_db():
    if not os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                fullname TEXT
            );
        """)
        conn.commit()
        conn.close()
init_db()
# -----------------------------------------

def get_db_conn():
    return sqlite3.connect(DB_PATH)

# --------- Routes ----------
@app.route("/")
def home():
    if "user_id" in session:
        return f"Hello, {session.get('username')}! <a href='/logout'>Logout</a>"
    return redirect(url_for("login"))

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        fullname = request.form.get("fullname","").strip()

        if not username or not password:
            flash("Username & password required", "danger")
            return redirect(url_for("register"))

        password_hash = generate_password_hash(password)

        conn = get_db_conn()
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO users (username, password_hash, fullname) VALUES (?, ?, ?)",
                        (username, password_hash, fullname))
            conn.commit()
            flash("Registration successful. Please login.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Username already exists. Choose another.", "warning")
            return redirect(url_for("register"))
        finally:
            conn.close()

    return render_template("register.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("SELECT id, password_hash FROM users WHERE username=?", (username,))
        row = cur.fetchone()
        conn.close()

        if row and check_password_hash(row[1], password):
            session["user_id"] = row[0]
            session["username"] = username
            flash("Login successful", "success")
            return redirect(url_for("home"))
        else:
            flash("Invalid username or password", "danger")
            return redirect(url_for("login"))

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out", "info")
    return redirect(url_for("login"))

# run
if __name__ == "__main__":
    app.run(debug=True)
