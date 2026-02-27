from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = "rehab_secret_key"   # Required for session login protection


# -------------------------
# Database Initialization
# -------------------------
def init_db():
    conn = sqlite3.connect("rehab.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient TEXT,
        date TEXT,
        start_time TEXT,
        duration INTEGER,
        score INTEGER,
        missed INTEGER,
        success_rate REAL
    )
    """)

    conn.commit()
    conn.close()


init_db()


# -------------------------
# Home Route
# -------------------------
@app.route("/")
def home():
    return redirect(url_for("login"))


# -------------------------
# Login Route
# -------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # Hardcoded login (you can change later)
        if username == "doctor" and password == "1234":
            session["logged_in"] = True
            return redirect(url_for("dashboard"))
        else:
            error = "Invalid Username or Password"

    return render_template("login.html", error=error)


# -------------------------
# Dashboard Route
# -------------------------
@app.route("/dashboard")
def dashboard():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    conn = sqlite3.connect("rehab.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM sessions ORDER BY id DESC")
    data = cursor.fetchall()

    conn.close()

    return render_template("dashboard.html", sessions=data)


# -------------------------
# Logout Route
# -------------------------
@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    return redirect(url_for("login"))


# -------------------------
# Run App
# -------------------------
if __name__ == "__main__":
    app.run(debug=True)
