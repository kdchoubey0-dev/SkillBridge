from __future__ import annotations

import os
import socket
import sqlite3
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path
from secrets import token_hex

from flask import (
    Flask,
    abort,
    flash,
    g,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "instance" / "skillbridge.db"
UPLOAD_FOLDER = BASE_DIR / "static" / "uploads"
ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg", "webp", "txt", "doc", "docx", "ppt", "pptx", "zip"}
MAX_CONTENT_LENGTH = 8 * 1024 * 1024

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ.get("SKILLBRIDGE_SECRET_KEY", "dev-skillbridge-secret-change-me"),
    DATABASE=DATABASE,
    UPLOAD_FOLDER=UPLOAD_FOLDER,
    MAX_CONTENT_LENGTH=MAX_CONTENT_LENGTH,
)

TRANSLATIONS = {
    "en": {
        "subtitle": "Project collaboration platform for practical learning",
        "dashboard": "Dashboard",
        "matching": "Skill Match",
        "projects": "Projects",
        "workspace": "Workspace",
        "proof": "Proof",
        "credits": "Credits",
        "coach": "AI Coach",
        "owner": "Owner",
        "admin": "Admin",
        "explore": "Explore Projects",
        "account": "Join SkillBridge",
        "logout": "Logout",
        "language": "Hindi",
    },
    "hi": {
        "subtitle": "Practical learning ke liye project collaboration platform",
        "dashboard": "Dashboard",
        "matching": "Skill Match",
        "projects": "Projects",
        "workspace": "Workspace",
        "proof": "Proof",
        "credits": "Credits",
        "coach": "AI Coach",
        "owner": "Owner",
        "admin": "Admin",
        "explore": "Projects Dekho",
        "account": "Join SkillBridge",
        "logout": "Logout",
        "language": "English",
    },
}

PROJECTS = [
    ("Community Health Finder", "Impact", 94, "Frontend,Maps,Research", "Frontend Developer,Research Lead,Accessibility Tester", "4 weeks", "Beginner friendly", "Recruiting", "A low-bandwidth directory for local clinics, volunteers, and emergency resources."),
    ("Open Tutor Kit", "Open Source", 91, "AI,Content,Language", "AI Prompt Builder,Lesson Writer,Translator", "6 weeks", "Intermediate", "Active sprint", "Reusable lesson tools for peer mentors in multilingual learning communities."),
    ("Micro Internship Board", "Startup", 88, "Product,Backend,Analytics", "Backend Developer,Product Analyst,QA Tester", "5 weeks", "Intermediate", "Recruiting", "Verified short work sprints for learners who need practical portfolio proof."),
    ("Accessible NGO Website", "Impact", 86, "HTML,Design,Docs", "HTML Developer,Visual Designer,Documentation Writer", "3 weeks", "Beginner friendly", "Mentor available", "Modern site and donation workflow for small nonprofit teams on slow networks."),
    ("Local Jobs Skill Map", "Career", 84, "Data,Research,Charts", "Data Collector,Chart Designer,Community Researcher", "4 weeks", "Beginner friendly", "New", "A simple dashboard that maps local job demand to practical learning paths."),
    ("Disaster Help Desk", "Impact", 82, "Backend,Security,Support", "API Developer,Security Reviewer,Support Coordinator", "7 weeks", "Advanced", "Planning", "A volunteer support queue for verified emergency requests and local responders."),
]

PEOPLE = [
    ("Nadia", "Backend mentor", 96, "APIs,Security,Reviews"),
    ("Luis", "UX researcher", 92, "Interviews,Accessibility,Spanish"),
    ("Dev", "Product lead", 89, "Roadmaps,Tasks,Community"),
    ("Aarav", "Full-stack builder", 87, "Flask,SQLite,Testing"),
]

ALL_SKILLS = ["Frontend", "Backend", "AI", "UX", "Research", "Communication", "Docs", "Data", "Language", "Product", "Security", "No-code", "Flask", "SQLite"]
DEFAULT_TASKS = [
    ("Design onboarding flow", "To do", "UX", "Mina", "Today"),
    ("Build project API schema", "Doing", "Backend", "Aarav", "Tomorrow"),
    ("Translate workspace labels", "Verified", "Language", "You", "Done"),
]


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = sqlite3.connect(app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(error: Exception | None = None) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db() -> None:
    DATABASE.parent.mkdir(exist_ok=True)
    UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'learner',
            skills TEXT NOT NULL DEFAULT 'Frontend,Research,Communication',
            goal TEXT NOT NULL DEFAULT 'Build a social-impact web app with a global team.',
            credits INTEGER NOT NULL DEFAULT 128,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL UNIQUE,
            type TEXT NOT NULL,
            fit INTEGER NOT NULL,
            skills TEXT NOT NULL,
            roles TEXT NOT NULL,
            duration TEXT NOT NULL,
            level TEXT NOT NULL,
            status TEXT NOT NULL,
            summary TEXT NOT NULL,
            owner_id INTEGER,
            owner_name TEXT,
            owner_email TEXT
        );

        CREATE TABLE IF NOT EXISTS people (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            role TEXT NOT NULL,
            match_score INTEGER NOT NULL,
            skills TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            project_id INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'Review pending',
            created_at TEXT NOT NULL,
            UNIQUE(user_id, project_id),
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(project_id) REFERENCES projects(id)
        );

        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            status TEXT NOT NULL,
            skill TEXT NOT NULL,
            owner TEXT NOT NULL,
            due TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT NOT NULL,
            text TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS proof_uploads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            original_filename TEXT NOT NULL,
            stored_filename TEXT NOT NULL,
            uploaded_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            label TEXT NOT NULL,
            amount INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        """
    )
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    db.execute(
        "INSERT OR IGNORE INTO users (name, email, password_hash, role, created_at) VALUES (?, ?, ?, ?, ?)",
        ("Admin", "kdchoubey0@gmail.com", generate_password_hash("admin123"), "admin", now),
    )
    db.executemany(
        "INSERT OR IGNORE INTO projects (title, type, fit, skills, roles, duration, level, status, summary) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        PROJECTS,
    )
    ensure_project_owner_columns(db)
    db.executemany(
        "INSERT OR IGNORE INTO people (name, role, match_score, skills) VALUES (?, ?, ?, ?)",
        PEOPLE,
    )
    admin = db.execute("SELECT id FROM users WHERE email = ?", ("kdchoubey0@gmail.com",)).fetchone()
    if admin:
        seed_user_workspace(db, admin["id"])
    db.commit()
    db.close()


def ensure_project_owner_columns(db: sqlite3.Connection) -> None:
    columns = {row["name"] for row in db.execute("PRAGMA table_info(projects)").fetchall()}
    migrations = {
        "owner_id": "ALTER TABLE projects ADD COLUMN owner_id INTEGER",
        "owner_name": "ALTER TABLE projects ADD COLUMN owner_name TEXT",
        "owner_email": "ALTER TABLE projects ADD COLUMN owner_email TEXT",
    }
    for column, statement in migrations.items():
        if column not in columns:
            db.execute(statement)


def seed_user_workspace(db: sqlite3.Connection, user_id: int) -> None:
    count = db.execute("SELECT COUNT(*) AS total FROM tasks WHERE user_id = ?", (user_id,)).fetchone()["total"]
    if count == 0:
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        db.executemany(
            "INSERT INTO tasks (user_id, title, status, skill, owner, due, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            [(user_id, title, status, skill, owner, due, now) for title, status, skill, owner, due in DEFAULT_TASKS],
        )
    msg_count = db.execute("SELECT COUNT(*) AS total FROM messages").fetchone()["total"]
    if msg_count == 0:
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        db.executemany(
            "INSERT INTO messages (user_id, name, text, created_at) VALUES (?, ?, ?, ?)",
            [
                (None, "Aarav", "I pushed the first task model and need UX review.", now),
                (None, "Mina", "I can review low-bandwidth screens today.", now),
            ],
        )
    ledger_count = db.execute("SELECT COUNT(*) AS total FROM ledger WHERE user_id = ?", (user_id,)).fetchone()["total"]
    if ledger_count == 0:
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        db.executemany(
            "INSERT INTO ledger (user_id, label, amount, created_at) VALUES (?, ?, ?, ?)",
            [
                (user_id, "Mentored landing page review", 24, now),
                (user_id, "Spent on API review", -12, now),
                (user_id, "Translated project brief", 18, now),
            ],
        )


def current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return get_db().execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


@app.context_processor
def inject_globals():
    lang = request.args.get("lang", session.get("lang", "en"))
    lang = lang if lang in TRANSLATIONS else "en"
    session["lang"] = lang
    return {
        "current_user": current_user(),
        "lang": lang,
        "t": lambda key: TRANSLATIONS[lang].get(key, key),
        "all_skills": ALL_SKILLS,
    }


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if current_user() is None:
            flash("Please login first to continue.", "warning")
            return redirect(url_for("auth", lang=session.get("lang", "en")))
        return view(*args, **kwargs)
    return wrapped_view


def admin_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        user = current_user()
        if not user or user["role"] != "admin":
            flash("Admin access requires the admin account.", "warning")
            return redirect(url_for("auth", lang=session.get("lang", "en")))
        return view(*args, **kwargs)
    return wrapped_view


def split_csv(value: str) -> list[str]:
    return [item.strip() for item in (value or "").split(",") if item.strip()]


def project_score(project: sqlite3.Row, user: sqlite3.Row | None) -> int:
    selected = set(split_csv(user["skills"] if user else "Frontend,Research,Communication"))
    project_skills = set(split_csv(project["skills"]))
    overlap = len({s.lower() for s in selected} & {s.lower() for s in project_skills})
    return min(99, int(project["fit"]) + overlap * 3)


def load_projects(project_type: str = "All") -> list[dict]:
    db = get_db()
    valid_types = {row["type"] for row in db.execute("SELECT DISTINCT type FROM projects").fetchall()}
    if project_type != "All" and project_type not in valid_types:
        project_type = "All"
    if project_type == "All":
        rows = db.execute("SELECT * FROM projects ORDER BY fit DESC").fetchall()
    else:
        rows = db.execute("SELECT * FROM projects WHERE type = ? ORDER BY fit DESC", (project_type,)).fetchall()
    user = current_user()
    projects = []
    for row in rows:
        item = dict(row)
        item["skills_list"] = split_csv(row["skills"])
        item["roles_list"] = split_csv(row["roles"])
        item["score"] = project_score(row, user)
        projects.append(item)
    return sorted(projects, key=lambda item: item["score"], reverse=True)


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def dashboard():
    user = current_user()
    projects = load_projects()[:3]
    stats = {
        "contributors": "12.4k",
        "teams": "3.8k",
        "languages": "41",
        "credits": user["credits"] if user else 128,
    }
    return render_template("dashboard.html", active="dashboard", projects=projects, stats=stats)


@app.route("/matching", methods=["GET", "POST"])
@login_required
def matching():
    db = get_db()
    user = current_user()
    if request.method == "POST":
        skills = ",".join(request.form.getlist("skills"))
        goal = request.form.get("goal", "").strip() or user["goal"]
        db.execute("UPDATE users SET skills = ?, goal = ? WHERE id = ?", (skills, goal, user["id"]))
        db.commit()
        flash("Skill profile updated. Your project ranking is refreshed.", "success")
        return redirect(url_for("matching", lang=session.get("lang", "en")))
    people = db.execute("SELECT * FROM people ORDER BY match_score DESC").fetchall()
    return render_template("matching.html", active="matching", user=user, people=people, selected=split_csv(user["skills"]))


@app.route("/projects")
def projects():
    db = get_db()
    project_type = request.args.get("type", "All")
    types = [row["type"] for row in db.execute("SELECT DISTINCT type FROM projects ORDER BY type").fetchall()]
    if project_type != "All" and project_type not in types:
        project_type = "All"
    user = current_user()
    applied_project_ids = set()
    if user:
        applied_project_ids = {
            row["project_id"]
            for row in db.execute("SELECT project_id FROM applications WHERE user_id = ?", (user["id"],)).fetchall()
        }
    return render_template(
        "projects.html",
        active="projects",
        projects=load_projects(project_type),
        types=types,
        selected_type=project_type,
        applied_project_ids=applied_project_ids,
    )


@app.post("/projects/<int:project_id>/apply")
@login_required
def apply_project(project_id: int):
    db = get_db()
    user = current_user()
    project = db.execute("SELECT id FROM projects WHERE id = ?", (project_id,)).fetchone()
    if not project:
        abort(404)
    existing = db.execute(
        "SELECT id FROM applications WHERE user_id = ? AND project_id = ?",
        (user["id"], project_id),
    ).fetchone()
    if existing:
        flash("You have already requested to join this project.", "warning")
        return redirect(url_for("projects", lang=session.get("lang", "en")))
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    db.execute(
        "INSERT INTO applications (user_id, project_id, status, created_at) VALUES (?, ?, ?, ?)",
        (user["id"], project_id, "Review pending", now),
    )
    db.commit()
    flash("Project request submitted. Track it inside your workspace.", "success")
    return redirect(url_for("workspace", lang=session.get("lang", "en")))


@app.route("/owner", methods=["GET", "POST"])
@login_required
def owner_dashboard():
    db = get_db()
    user = current_user()
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        project_type = request.form.get("type", "").strip() or "Startup"
        summary = request.form.get("summary", "").strip()
        skills = request.form.get("skills", "").strip()
        roles = request.form.get("roles", "").strip()
        duration = request.form.get("duration", "").strip() or "4 weeks"
        level = request.form.get("level", "").strip() or "Beginner friendly"
        status = request.form.get("status", "").strip() or "Recruiting"
        if not title or not summary or not skills or not roles:
            flash("Project title, summary, skills, and roles are required.", "warning")
            return redirect(url_for("owner_dashboard", lang=session.get("lang", "en")))
        try:
            db.execute(
                """
                INSERT INTO projects
                (title, type, fit, skills, roles, duration, level, status, summary, owner_id, owner_name, owner_email)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    title,
                    project_type,
                    80,
                    skills,
                    roles,
                    duration,
                    level,
                    status,
                    summary,
                    user["id"],
                    user["name"],
                    user["email"],
                ),
            )
            db.commit()
            flash("Project registered successfully. It is now visible in Projects.", "success")
            return redirect(url_for("projects", lang=session.get("lang", "en")))
        except sqlite3.IntegrityError:
            flash("A project with this title already exists. Please use a different title.", "warning")
    owner_projects = db.execute(
        "SELECT * FROM projects WHERE owner_id = ? ORDER BY id DESC",
        (user["id"],),
    ).fetchall()
    recent_applications = db.execute(
        """
        SELECT applications.*, users.name AS applicant_name, users.email AS applicant_email, projects.title
        FROM applications
        JOIN users ON users.id = applications.user_id
        JOIN projects ON projects.id = applications.project_id
        WHERE projects.owner_id = ?
        ORDER BY applications.id DESC
        """,
        (user["id"],),
    ).fetchall()
    return render_template(
        "owner.html",
        active="owner",
        owner_projects=owner_projects,
        recent_applications=recent_applications,
    )


@app.route("/workspace")
@login_required
def workspace():
    db = get_db()
    user = current_user()
    tasks = db.execute("SELECT * FROM tasks WHERE user_id = ? ORDER BY id DESC", (user["id"],)).fetchall()
    task_counts = {status: 0 for status in ["To do", "Doing", "Verified"]}
    for task in tasks:
        task_counts[task["status"]] = task_counts.get(task["status"], 0) + 1
    applications = db.execute(
        """
        SELECT applications.*, projects.title
        FROM applications
        JOIN projects ON projects.id = applications.project_id
        WHERE applications.user_id = ?
        ORDER BY applications.id DESC
        """,
        (user["id"],),
    ).fetchall()
    messages = db.execute("SELECT * FROM messages ORDER BY id DESC LIMIT 8").fetchall()
    return render_template(
        "workspace.html",
        active="workspace",
        tasks=tasks,
        task_counts=task_counts,
        applications=applications,
        messages=messages,
    )


@app.post("/tasks/add-ai")
@login_required
def add_ai_task():
    db = get_db()
    user = current_user()
    first_skill = split_csv(user["skills"])[0] if split_csv(user["skills"]) else "Collaboration"
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    db.execute(
        "INSERT INTO tasks (user_id, title, status, skill, owner, due, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (user["id"], "Prepare proof-ready contribution", "To do", first_skill, "You", "Next sprint", now),
    )
    db.commit()
    flash("AI planner added a proof-ready task.", "success")
    return redirect(url_for("workspace", lang=session.get("lang", "en")))


@app.post("/tasks/<int:task_id>/move")
@login_required
def move_task(task_id: int):
    db = get_db()
    user = current_user()
    task = db.execute("SELECT * FROM tasks WHERE id = ? AND user_id = ?", (task_id, user["id"])).fetchone()
    if not task:
        abort(404)
    next_status = {"To do": "Doing", "Doing": "Verified", "Verified": "To do"}[task["status"]]
    db.execute("UPDATE tasks SET status = ? WHERE id = ?", (next_status, task_id))
    db.commit()
    flash(f"Task moved to {next_status}.", "success")
    return redirect(url_for("workspace", lang=session.get("lang", "en")))


@app.post("/messages")
@login_required
def send_message():
    text = request.form.get("message", "").strip()
    if len(text) > 280:
        flash("Message is too long. Please keep it under 280 characters.", "warning")
        return redirect(url_for("workspace", lang=session.get("lang", "en")))
    if text:
        db = get_db()
        user = current_user()
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        db.execute("INSERT INTO messages (user_id, name, text, created_at) VALUES (?, ?, ?, ?)", (user["id"], user["name"], text, now))
        db.commit()
        flash("Team update sent.", "success")
    return redirect(url_for("workspace", lang=session.get("lang", "en")))


@app.route("/portfolio", methods=["GET", "POST"])
def portfolio():
    db = get_db()
    user = current_user()
    if request.method == "POST" and user is None:
        flash("Please login before uploading proof of work.", "warning")
        return redirect(url_for("auth", lang=session.get("lang", "en")))
    if request.method == "POST":
        title = request.form.get("title", "").strip() or "Proof file"
        file = request.files.get("proof_file")
        if not file or not file.filename:
            flash("Please choose a proof file.", "warning")
        elif not allowed_file(file.filename):
            flash("File type is not allowed.", "danger")
        else:
            original = secure_filename(file.filename)
            stored = f"{token_hex(8)}-{original}"
            file.save(UPLOAD_FOLDER / stored)
            now = datetime.now(timezone.utc).isoformat(timespec="seconds")
            db.execute(
                "INSERT INTO proof_uploads (user_id, title, original_filename, stored_filename, uploaded_at) VALUES (?, ?, ?, ?, ?)",
                (user["id"], title, original, stored, now),
            )
            db.execute("UPDATE users SET credits = credits + 6 WHERE id = ?", (user["id"],))
            db.execute("INSERT INTO ledger (user_id, label, amount, created_at) VALUES (?, ?, ?, ?)", (user["id"], "Uploaded proof file", 6, now))
            db.commit()
            flash("Proof uploaded and 6 credits added.", "success")
        return redirect(url_for("portfolio", lang=session.get("lang", "en")))
    uploads = []
    if user:
        uploads = db.execute("SELECT * FROM proof_uploads WHERE user_id = ? ORDER BY id DESC", (user["id"],)).fetchall()
    return render_template("portfolio.html", active="portfolio", uploads=uploads)


@app.route("/uploads/<path:filename>")
@login_required
def uploaded_file(filename: str):
    user = current_user()
    row = get_db().execute("SELECT * FROM proof_uploads WHERE stored_filename = ?", (filename,)).fetchone()
    if not row or (row["user_id"] != user["id"] and user["role"] != "admin"):
        abort(404)
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename, as_attachment=True)


@app.route("/credits")
def credits():
    user = current_user()
    if user:
        ledger = get_db().execute("SELECT * FROM ledger WHERE user_id = ? ORDER BY id DESC", (user["id"],)).fetchall()
        balance = user["credits"]
    else:
        ledger = [
            {"label": "Mentored landing page review", "amount": 24},
            {"label": "Spent on API review", "amount": -12},
            {"label": "Translated project brief", "amount": 18},
        ]
        balance = 128
    return render_template("credits.html", active="credits", ledger=ledger, user=user, balance=balance)


@app.post("/credits/<action>")
@login_required
def update_credits(action: str):
    db = get_db()
    user = current_user()
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    if action == "earn":
        amount, label = 8, "Completed peer help session"
    elif action == "spend":
        amount, label = -8, "Booked mentor review"
    else:
        abort(404)
    if action == "spend" and user["credits"] < 8:
        flash("Not enough credits to book this review.", "warning")
        return redirect(url_for("credits", lang=session.get("lang", "en")))
    db.execute("UPDATE users SET credits = credits + ? WHERE id = ?", (amount, user["id"]))
    db.execute("INSERT INTO ledger (user_id, label, amount, created_at) VALUES (?, ?, ?, ?)", (user["id"], label, amount, now))
    db.commit()
    return redirect(url_for("credits", lang=session.get("lang", "en")))


@app.route("/coach")
def coach():
    user = current_user()
    recommended = load_projects()[:3]
    skills = user["skills"] if user else "Frontend, Research, Communication"
    steps = [
        f"Best project matches: {', '.join(project['title'] for project in recommended)}.",
        f"Your strongest profile signals: {skills}.",
        "Pick one project, request a small task, and finish it in a public proof-friendly format.",
        "Upload screenshots, links, reviewer notes, and measurable outcomes to build your portfolio.",
        "Use credits for mentor reviews before marking work as verified.",
    ]
    return render_template("coach.html", active="coach", steps=steps)


@app.route("/admin")
@admin_required
def admin():
    db = get_db()
    stats = {
        "users": db.execute("SELECT COUNT(*) AS total FROM users").fetchone()["total"],
        "projects": db.execute("SELECT COUNT(*) AS total FROM projects").fetchone()["total"],
        "messages": db.execute("SELECT COUNT(*) AS total FROM messages").fetchone()["total"],
        "proofs": db.execute("SELECT COUNT(*) AS total FROM proof_uploads").fetchone()["total"],
    }
    users = db.execute("SELECT id, name, email, role, credits, created_at FROM users ORDER BY id DESC").fetchall()
    applications = db.execute(
        """
        SELECT users.name, projects.title, applications.status, applications.created_at
        FROM applications
        JOIN users ON users.id = applications.user_id
        JOIN projects ON projects.id = applications.project_id
        ORDER BY applications.id DESC
        """
    ).fetchall()
    proofs = db.execute(
        """
        SELECT users.name, proof_uploads.title, proof_uploads.original_filename, proof_uploads.uploaded_at
        FROM proof_uploads
        JOIN users ON users.id = proof_uploads.user_id
        ORDER BY proof_uploads.id DESC
        """
    ).fetchall()
    return render_template("admin.html", active="admin", stats=stats, users=users, applications=applications, proofs=proofs)


@app.route("/auth", methods=["GET", "POST"])
def auth():
    db = get_db()
    if request.method == "POST":
        mode = request.form.get("mode")
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if mode == "register":
            name = request.form.get("name", "").strip()
            if not name or not email or len(password) < 6:
                flash("Name, valid email, and 6 character password are required.", "warning")
            else:
                try:
                    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
                    cursor = db.execute(
                        "INSERT INTO users (name, email, password_hash, role, created_at) VALUES (?, ?, ?, ?, ?)",
                        (name, email, generate_password_hash(password), "learner", now),
                    )
                    seed_user_workspace(db, cursor.lastrowid)
                    db.commit()
                    session.clear()
                    session["user_id"] = cursor.lastrowid
                    flash("Account created. Welcome to SkillBridge.", "success")
                    return redirect(url_for("projects", lang=session.get("lang", "en")))
                except sqlite3.IntegrityError:
                    flash("This email is already registered. Please login.", "warning")
        elif mode == "login":
            user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
            if user and check_password_hash(user["password_hash"], password):
                seed_user_workspace(db, user["id"])
                db.commit()
                session.clear()
                session["user_id"] = user["id"]
                flash("Login successful.", "success")
                return redirect(url_for("dashboard", lang=session.get("lang", "en")))
            flash("Invalid email or password.", "danger")
    return render_template("auth.html", active="auth")


@app.post("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("auth"))


@app.cli.command("init-db")
def init_db_command() -> None:
    init_db()
    print("Initialized SkillBridge database.")


def find_available_port(start_port: int = 5000, attempts: int = 60, host: str = "127.0.0.1") -> int:
    for port in range(start_port, start_port + attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind((host, port))
            except OSError:
                continue
            return port
    raise RuntimeError(f"No free port found from {start_port} to {start_port + attempts - 1}")


def get_lan_ip() -> str | None:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("192.168.1.1", 80))
            return sock.getsockname()[0]
    except OSError:
        try:
            for item in socket.gethostbyname_ex(socket.gethostname())[2]:
                if not item.startswith("127."):
                    return item
        except OSError:
            return None
    return None


if __name__ == "__main__":
    init_db()
    requested_port = int(os.environ.get("PORT", "5000"))
    host = os.environ.get("HOST", "0.0.0.0")
    active_port = find_available_port(requested_port, host=host)
    if active_port != requested_port:
        print(f"Port {requested_port} is busy, so SkillBridge is running on {active_port}")
    print(f"Open SkillBridge at http://127.0.0.1:{active_port}")
    lan_ip = get_lan_ip()
    if lan_ip:
        print(f"Open from phone on same Wi-Fi: http://{lan_ip}:{active_port}")
    app.run(host=host, port=active_port, debug=True, use_reloader=False)
