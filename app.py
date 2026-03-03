from flask import Flask, render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

app = Flask(__name__)
app.secret_key = "kb_project_super_secret_key_2026"


# ================= DATABASE CONNECTION =================
def get_db():
    conn = sqlite3.connect("database.db", timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


# ================= INITIALIZE DATABASE =================
def init_db():
    conn = get_db()

    conn.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS admin (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS problems (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        solution TEXT NOT NULL
    )
    """)

    # ✅ CREATE DEFAULT ADMIN (divya / admin123)
    admin_exists = conn.execute(
        "SELECT * FROM admin WHERE username=?",
        ("divya",)
    ).fetchone()

    if not admin_exists:
        conn.execute(
            "INSERT INTO admin (username, password) VALUES (?, ?)",
            ("divya", generate_password_hash("admin123"))
        )

    conn.commit()
    conn.close()


init_db()


# ======================================================
# ================= PUBLIC SECTION =====================
# ======================================================

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/ask", methods=["POST"])
def ask():
    if "user" not in session:
        return redirect("/user_login")

    question = request.form["question"]

    conn = get_db()
    results = conn.execute(
        "SELECT * FROM problems WHERE title LIKE ? OR description LIKE ?",
        ('%' + question + '%', '%' + question + '%')
    ).fetchall()
    conn.close()

    if results:
        return render_template("search.html", data=results)
    else:
        return render_template("search.html", data=[], message="No solution found.")


@app.route("/view/<int:id>")
def view(id):
    conn = get_db()
    problem = conn.execute("SELECT * FROM problems WHERE id=?", (id,)).fetchone()
    conn.close()
    return render_template("view.html", data=problem)


# ======================================================
# ================= ADMIN SECTION ======================
# ======================================================

@app.route("/admin_login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        admin = conn.execute(
            "SELECT * FROM admin WHERE username=?",
            (username,)
        ).fetchone()
        conn.close()

        if admin and check_password_hash(admin["password"], password):
            session.clear()
            session["admin"] = username
            return redirect("/dashboard")
        else:
            return render_template("admin_login.html", error="Invalid credentials")

    return render_template("admin_login.html")


@app.route("/dashboard")
def dashboard():
    if "admin" not in session:
        return redirect("/admin_login")

    conn = get_db()
    problems = conn.execute("SELECT * FROM problems").fetchall()
    conn.close()

    return render_template("dashboard.html", data=problems)


@app.route("/add", methods=["GET", "POST"])
def add():
    if "admin" not in session:
        return redirect("/admin_login")

    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]
        solution = request.form["solution"]

        conn = get_db()
        conn.execute(
            "INSERT INTO problems (title, description, solution) VALUES (?,?,?)",
            (title, description, solution)
        )
        conn.commit()
        conn.close()

        return redirect("/dashboard")

    return render_template("add.html")


@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):
    if "admin" not in session:
        return redirect("/admin_login")

    conn = get_db()
    problem = conn.execute("SELECT * FROM problems WHERE id=?", (id,)).fetchone()

    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]
        solution = request.form["solution"]

        conn.execute(
            "UPDATE problems SET title=?, description=?, solution=? WHERE id=?",
            (title, description, solution, id)
        )
        conn.commit()
        conn.close()

        return redirect("/dashboard")

    conn.close()
    return render_template("edit.html", data=problem)


@app.route("/delete/<int:id>")
def delete(id):
    if "admin" not in session:
        return redirect("/admin_login")

    conn = get_db()
    conn.execute("DELETE FROM problems WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect("/dashboard")


@app.route("/admin_logout")
def admin_logout():
    session.clear()
    return redirect("/")


# ======================================================
# ================= USER SECTION =======================
# ======================================================

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = generate_password_hash(request.form["password"])

        conn = get_db()
        try:
            conn.execute(
                "INSERT INTO users (username, password) VALUES (?,?)",
                (username, password)
            )
            conn.commit()
        except:
            conn.close()
            return render_template("register.html", error="Username already exists")

        conn.close()
        return redirect("/user_login")

    return render_template("register.html")


@app.route("/user_login", methods=["GET", "POST"])
def user_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE username=?",
            (username,)
        ).fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session.clear()
            session["user"] = username
            return redirect("/")
        else:
            return render_template("user_login.html", error="Invalid credentials")

    return render_template("user_login.html")


@app.route("/user_logout")
def user_logout():
    session.clear()
    return redirect("/")


# ======================================================
# ================= RUN APP ============================
# ======================================================

if __name__ == "__main__":
    app.run(debug=True)