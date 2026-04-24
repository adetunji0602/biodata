from flask import Flask, render_template, request, send_file, redirect, url_for, session
import sqlite3, os, uuid
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "change_this_secret_in_production"

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

DB_PATH = "database.db"

def get_db():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        name TEXT,
        age TEXT,
        sex TEXT,
        occupation TEXT,
        photo TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS admin (
        username TEXT PRIMARY KEY,
        password TEXT,
        role TEXT
    )""")

    conn.commit()
    conn.close()

def seed_admins():
    conn = get_db()
    c = conn.cursor()

    users = [
        ("admin", generate_password_hash("admin123"), "admin"),
        ("staff", generate_password_hash("staff123"), "staff")
    ]

    for u in users:
        try:
            c.execute("INSERT INTO admin VALUES (?, ?, ?)", u)
        except:
            pass

    conn.commit()
    conn.close()

init_db()
seed_admins()

def login_required(role=None):
    def decorator(func):
        def wrapper(*args, **kwargs):
            if "user" not in session:
                return redirect(url_for("login"))
            if role and session.get("role") != role:
                return "Unauthorized", 403
            return func(*args, **kwargs)
        wrapper.__name__ = func.__name__
        return wrapper
    return decorator

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/submit", methods=["POST"])
def submit():
    name = request.form["name"]
    age = request.form["age"]
    sex = request.form["sex"]
    occupation = request.form["occupation"]
    photo = request.files["photo"]

    user_id = str(uuid.uuid4())[:8]
    filename = f"{user_id}_{secure_filename(photo.filename)}"
    photo_path = os.path.join(UPLOAD_FOLDER, filename)
    photo.save(photo_path)

    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?, ?)",
              (user_id, name, age, sex, occupation, photo_path))
    conn.commit()
    conn.close()

    pdf_path = f"{UPLOAD_FOLDER}/{user_id}.pdf"
    c = canvas.Canvas(pdf_path, pagesize=letter)
    c.drawString(50, 700, f"ID: {user_id}")
    c.drawString(50, 680, f"Name: {name}")
    c.drawString(50, 660, f"Age: {age}")
    c.drawString(50, 640, f"Sex: {sex}")
    c.drawString(50, 620, f"Occupation: {occupation}")
    c.drawImage(photo_path, 400, 620, width=100, height=100)
    c.save()

    return send_file(pdf_path, as_attachment=True)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM admin WHERE username=?", (username,))
        user = c.fetchone()
        conn.close()

        if user and check_password_hash(user[1], password):
            session["user"] = username
            session["role"] = user[2]
            return redirect(url_for("dashboard"))

        return "Invalid credentials"

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/dashboard")
@login_required()
def dashboard():
    return render_template("dashboard.html", role=session.get("role"))

@app.route("/admin")
@login_required(role="admin")
def admin():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM users")
    users = c.fetchall()
    conn.close()
    return render_template("admin.html", users=users)

@app.route("/staff")
@login_required(role="staff")
def staff():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, name, age, sex, occupation FROM users")
    users = c.fetchall()
    conn.close()
    return render_template("staff.html", users=users)

if __name__ == "__main__":
    app.run(debug=True)
