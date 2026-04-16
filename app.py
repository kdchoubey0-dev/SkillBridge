from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from html import escape
from pathlib import Path
from secrets import token_hex
from socket import error as socket_error
from urllib.parse import parse_qs, urlencode, urlparse

PORT = 8000
ROOT = Path(__file__).parent


class SkillBridgeServer(ThreadingHTTPServer):
    allow_reuse_address = True

state = {
    "skills": {"Frontend", "Research", "Communication"},
    "goal": "Build a social-impact web app with a global team.",
    "credits": 128,
    "tasks": [
        {"id": 1, "title": "Design onboarding flow", "status": "To do", "skill": "UX", "owner": "Mina", "due": "Today"},
        {"id": 2, "title": "Build project API schema", "status": "Doing", "skill": "Backend", "owner": "Aarav", "due": "Tomorrow"},
        {"id": 3, "title": "Translate workspace labels", "status": "Verified", "skill": "Language", "owner": "You", "due": "Done"},
    ],
    "applications": [],
    "messages": [
        {"name": "Aarav", "text": "I pushed the first task model and need UX review."},
        {"name": "Mina", "text": "I can review low-bandwidth screens today."},
    ],
    "ledger": [
        {"label": "Mentored landing page review", "amount": "+24"},
        {"label": "Spent on API review", "amount": "-12"},
        {"label": "Translated project brief", "amount": "+18"},
    ],
}

users = {}
sessions = {}

projects = [
    {
        "title": "Community Health Finder",
        "type": "Impact",
        "fit": 94,
        "skills": ["Frontend", "Maps", "Research"],
        "roles": ["Frontend Developer", "Research Lead", "Accessibility Tester"],
        "duration": "4 weeks",
        "level": "Beginner friendly",
        "status": "Recruiting",
        "summary": "A low-bandwidth directory for local clinics, volunteers, and emergency resources.",
    },
    {
        "title": "Open Tutor Kit",
        "type": "Open Source",
        "fit": 91,
        "skills": ["AI", "Content", "Language"],
        "roles": ["AI Prompt Builder", "Lesson Writer", "Translator"],
        "duration": "6 weeks",
        "level": "Intermediate",
        "status": "Active sprint",
        "summary": "Reusable lesson tools for peer mentors in multilingual learning communities.",
    },
    {
        "title": "Micro Internship Board",
        "type": "Startup",
        "fit": 88,
        "skills": ["Product", "Backend", "Analytics"],
        "roles": ["Backend Developer", "Product Analyst", "QA Tester"],
        "duration": "5 weeks",
        "level": "Intermediate",
        "status": "Recruiting",
        "summary": "Verified short work sprints for learners who need practical portfolio proof.",
    },
    {
        "title": "Accessible NGO Website",
        "type": "Impact",
        "fit": 86,
        "skills": ["HTML", "Design", "Docs"],
        "roles": ["HTML Developer", "Visual Designer", "Documentation Writer"],
        "duration": "3 weeks",
        "level": "Beginner friendly",
        "status": "Mentor available",
        "summary": "Modern site and donation workflow for small nonprofit teams on slow networks.",
    },
    {
        "title": "Local Jobs Skill Map",
        "type": "Career",
        "fit": 84,
        "skills": ["Data", "Research", "Charts"],
        "roles": ["Data Collector", "Chart Designer", "Community Researcher"],
        "duration": "4 weeks",
        "level": "Beginner friendly",
        "status": "New",
        "summary": "A simple dashboard that maps local job demand to practical learning paths.",
    },
    {
        "title": "Disaster Help Desk",
        "type": "Impact",
        "fit": 82,
        "skills": ["Backend", "Security", "Support"],
        "roles": ["API Developer", "Security Reviewer", "Support Coordinator"],
        "duration": "7 weeks",
        "level": "Advanced",
        "status": "Planning",
        "summary": "A volunteer support queue for verified emergency requests and local responders.",
    },
]

people = [
    {"name": "Nadia", "role": "Backend mentor", "match": 96, "skills": ["APIs", "Security", "Reviews"]},
    {"name": "Luis", "role": "UX researcher", "match": 92, "skills": ["Interviews", "Accessibility", "Spanish"]},
    {"name": "Dev", "role": "Product lead", "match": 89, "skills": ["Roadmaps", "Tasks", "Community"]},
]

all_skills = ["Frontend", "Backend", "AI", "UX", "Research", "Communication", "Docs", "Data", "Language", "Product", "Security", "No-code"]


def h(value):
    return escape(str(value), quote=True)


def query(view, **params):
    data = {"view": view}
    data.update({key: value for key, value in params.items() if value})
    return urlencode(data)


def tags(items):
    return "".join(f'<span class="tag">{h(item)}</span>' for item in items)


def current_user(handler):
    cookie = handler.headers.get("Cookie", "")
    for part in cookie.split(";"):
        key, _, value = part.strip().partition("=")
        if key == "skillbridge_session" and value in sessions:
            return users.get(sessions[value])
    return None


def layout(view, content, user=None):
    links = [
        ("dashboard", "Dashboard"),
        ("matching", "Matching"),
        ("projects", "Projects"),
        ("workspace", "Workspace"),
        ("portfolio", "Proof"),
        ("credits", "Credits"),
        ("coach", "AI Coach"),
    ]
    nav = "".join(
        f'<a class="nav-item {"active" if view == key else ""}" href="/?{query(key)}">{label}</a>'
        for key, label in links
    )
    account = (
        f"""
        <div class="account-box">
          <span>{h(user["name"])}</span>
          <small>{h(user["email"])}</small>
          <form method="post" action="/action">
            <input type="hidden" name="action" value="logout">
            <button class="button compact" type="submit">Logout</button>
          </form>
        </div>
        """
        if user
        else '<a class="primary" href="/?view=login">Create Account</a>'
    )
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SkillBridge</title>
    <link rel="stylesheet" href="/styles.css">
  </head>
  <body>
    <div class="app">
      <aside class="sidebar">
        <a class="brand" href="/"><span>SB</span><strong>SkillBridge</strong></a>
        <nav>{nav}</nav>
      </aside>
      <main class="main">
        <header class="topbar">
          <div>
            <p>Open-source collaborative learning platform</p>
            <h1>SkillBridge</h1>
          </div>
          <div class="top-actions">
            <a class="button" href="/?view=projects">Explore Projects</a>
            {account}
          </div>
        </header>
        {content}
      </main>
    </div>
  </body>
</html>"""


def dashboard():
    cards = "".join(
        f"""
        <article class="card">
          <div class="row"><h3>{h(project["title"])}</h3><span>{project["fit"]}% fit</span></div>
          <p>{h(project["summary"])}</p>
          <div class="tags">{tags(project["skills"])}</div>
          <a class="button" href="/?view=workspace">Request to join</a>
        </article>
        """
        for project in projects[:3]
    )
    metrics = "".join(
        f'<article class="metric"><strong>{number}</strong><span>{label}</span></article>'
        for number, label in [("12.4k", "verified contributors"), ("3.8k", "active teams"), ("41", "languages"), ("128", "your credits")]
    )
    return f"""
      <section>
        <div class="section-head">
          <h2>Dashboard</h2>
          <p>Find real teams, build public proof, and exchange skills without payment barriers.</p>
        </div>
        <div class="metrics">{metrics}</div>
        <div class="grid two">
          <section class="panel"><h2>Recommended Projects</h2>{cards}</section>
          <section class="panel">
            <h2>Collaboration Map</h2>
            <div class="map">
              <span>You</span><span>UX</span><span>API</span><span>Docs</span><span>Mentor</span>
            </div>
            <p><strong>92%</strong> team fit based on your selected skills.</p>
          </section>
        </div>
      </section>
    """


def matching():
    checks = "".join(
        f"""
        <label class="chip">
          <input class="check-input" type="checkbox" name="skills" value="{h(skill)}" {"checked" if skill in state["skills"] else ""}>
          <span>{h(skill)}</span>
        </label>
        """
        for skill in all_skills
    )
    people_cards = "".join(
        f"""
        <article class="card">
          <div class="row"><h3>{h(person["name"])}</h3><span>{person["match"]}%</span></div>
          <p>{h(person["role"])}</p>
          <div class="tags">{tags(person["skills"])}</div>
        </article>
        """
        for person in people
    )
    return f"""
      <section>
        <div class="section-head"><h2>Skill Matching</h2><p>Choose your strengths and find collaborators whose skills complete the team.</p></div>
        <div class="grid two">
          <section class="panel">
            <h2>Your Skill Profile</h2>
            <form method="post" action="/action">
              <input type="hidden" name="action" value="save_profile">
              <div class="chips">{checks}</div>
              <label>Current goal</label>
              <textarea name="goal" rows="4">{h(state["goal"])}</textarea>
              <button class="primary" type="submit">Save Profile</button>
            </form>
          </section>
          <section class="panel"><h2>Best Collaborators</h2>{people_cards}</section>
        </div>
      </section>
    """


def project_catalog(project_filter="All", user=None):
    options = ["All"] + sorted({project["type"] for project in projects})
    filter_bar = "".join(
        f'<a class="filter-pill {"active" if project_filter == option else ""}" href="/?{query("projects", project=option)}">{h(option)}</a>'
        for option in options
    )
    visible_projects = projects if project_filter == "All" else [project for project in projects if project["type"] == project_filter]
    cards = "".join(
        f"""
        <article class="project-card">
          <div class="project-head">
            <div>
              <span class="type">{h(project["type"])}</span>
              <h3>{h(project["title"])}</h3>
            </div>
            <strong>{project["fit"]}%</strong>
          </div>
          <p>{h(project["summary"])}</p>
          <div class="project-meta">
            <span>{h(project["duration"])}</span>
            <span>{h(project["level"])}</span>
            <span>{h(project["status"])}</span>
          </div>
          <h4>Open roles</h4>
          <div class="tags">{tags(project["roles"])}</div>
          <h4>Needed skills</h4>
          <div class="tags">{tags(project["skills"])}</div>
          {
            f'''
            <form method="post" action="/action">
              <input type="hidden" name="action" value="apply_project">
              <input type="hidden" name="project" value="{h(project["title"])}">
              <button class="primary full" type="submit">Request to join</button>
            </form>
            '''
            if user
            else '<a class="primary full" href="/?view=login">Create account to join</a>'
          }
        </article>
        """
        for project in visible_projects
    )
    return f"""
      <section>
        <div class="section-head project-title-row">
          <div>
            <h2>Open Projects</h2>
            <p>Pick a real project, understand the roles, and turn contributions into verified portfolio proof.</p>
          </div>
          <a class="button" href="/?view=matching">Improve Match</a>
        </div>
        <div class="filter-bar">{filter_bar}</div>
        <div class="project-grid">{cards}</div>
      </section>
    """


def login_page(message=""):
    note = f'<p class="form-note">{h(message)}</p>' if message else ""
    return f"""
      <section>
        <div class="section-head"><h2>Create Account or Login</h2><p>Use your SkillBridge account to join projects, save skills, and build proof of work.</p></div>
        {note}
        <div class="grid auth-grid">
          <section class="panel">
            <h2>Create Account</h2>
            <form method="post" action="/action" class="auth-form">
              <input type="hidden" name="action" value="create_account">
              <label>Full name</label>
              <input name="name" required placeholder="Your name">
              <label>Email</label>
              <input name="email" type="email" required placeholder="you@example.com">
              <label>Password</label>
              <input name="password" type="password" required minlength="4" placeholder="Minimum 4 characters">
              <button class="primary" type="submit">Create Account</button>
            </form>
          </section>
          <section class="panel">
            <h2>Login</h2>
            <form method="post" action="/action" class="auth-form">
              <input type="hidden" name="action" value="login">
              <label>Email</label>
              <input name="email" type="email" required placeholder="you@example.com">
              <label>Password</label>
              <input name="password" type="password" required placeholder="Your password">
              <button class="button" type="submit">Login</button>
            </form>
          </section>
        </div>
      </section>
    """


def workspace():
    applications = "".join(
        f"""
        <article class="application-card">
          <strong>{h(item["project"])}</strong>
          <span>{h(item["status"])}</span>
        </article>
        """
        for item in state["applications"]
    )
    if not applications:
        applications = '<p class="empty-state">No project applications yet. Explore projects and request to join one.</p>'
    columns = ""
    for status in ["To do", "Doing", "Verified"]:
        task_cards = "".join(
            f"""
            <article class="task">
              <div class="task-head">
                <h3>{h(task["title"])}</h3>
                <span>{h(task["skill"])}</span>
              </div>
              <div class="task-meta">
                <small>Owner: {h(task["owner"])}</small>
                <small>Due: {h(task["due"])}</small>
              </div>
              <form method="post" action="/action">
                <input type="hidden" name="action" value="move_task">
                <input type="hidden" name="id" value="{task["id"]}">
                <button class="button full" type="submit">Move</button>
              </form>
            </article>
            """
            for task in state["tasks"]
            if task["status"] == status
        )
        columns += f'<section class="column"><h2>{status}</h2>{task_cards}</section>'
    messages = "".join(f'<div class="message"><strong>{h(m["name"])}</strong><p>{h(m["text"])}</p></div>' for m in state["messages"])
    sprint_tasks = [
        ("Proof Check", "Add screenshot, link, reviewer name, and measurable result before verification."),
        ("Mentor Review", "Use 8 credits to get feedback before moving a task to verified."),
        ("Low Data QA", "Test the page on a small screen and reduce heavy visual elements if needed."),
    ]
    sprint_cards = "".join(f'<article class="sprint-card"><strong>{h(title)}</strong><p>{h(text)}</p></article>' for title, text in sprint_tasks)
    return f"""
      <section>
        <div class="section-head project-title-row">
          <div><h2>Project Workspace</h2><p>Manage tasks, applications, messages, and proof-ready sprint guidance.</p></div>
          <form method="post" action="/action">
            <input type="hidden" name="action" value="add_ai_task">
            <button class="primary" type="submit">Add AI Task</button>
          </form>
        </div>
        <div class="workspace-layout">
          <section class="panel board-panel">
            <h2>Task Board</h2>
            <div class="board">{columns}</div>
          </section>
          <section class="panel">
            <h2>AI Sprint Planner</h2>
            <div class="sprint-list">{sprint_cards}</div>
          </section>
          <section class="panel">
            <h2>Team Room</h2>
            {messages}
            <form class="message-form" method="post" action="/action">
              <input type="hidden" name="action" value="message">
              <input name="message" placeholder="Share an update">
              <button class="primary" type="submit">Send</button>
            </form>
          </section>
          <section class="panel">
            <h2>Application Tracker</h2>
            <div class="application-list">{applications}</div>
          </section>
        </div>
      </section>
    """


def portfolio():
    items = [
        ("UX", "Designed multilingual onboarding flow", "Reviewed by Mina"),
        ("API", "Defined project and proof models", "Verified by mentor"),
        ("Docs", "Published low-bandwidth contribution guide", "Open-source accepted"),
        ("Team", "Completed 3 peer reviews", "Community validated"),
    ]
    timeline = "".join(
        f"""
        <article class="proof">
          <strong>{h(code)}</strong>
          <div><h3>{h(title)}</h3><p>{h(text)}</p></div>
          <span>Verified</span>
        </article>
        """
        for code, title, text in items
    )
    return f"""
      <section>
        <div class="section-head"><h2>Proof of Work</h2><p>Verified work replaces empty certificates with visible contribution history.</p></div>
        <form method="post" action="/action"><input type="hidden" name="action" value="verify_work"><button class="primary" type="submit">Verify Work</button></form>
        <div class="timeline">{timeline}</div>
      </section>
    """


def credits():
    rows = "".join(f'<div class="ledger"><span>{h(item["label"])}</span><strong>{h(item["amount"])}</strong></div>' for item in state["ledger"])
    return f"""
      <section>
        <div class="section-head"><h2>Skill Credits</h2><p>Earn by helping others and spend credits when you need mentorship or review.</p></div>
        <div class="grid two">
          <section class="panel balance"><span>Available balance</span><strong>{state["credits"]}</strong></section>
          <section class="panel">
            <h2>Credit Ledger</h2>
            {rows}
            <div class="actions">
              <form method="post" action="/action"><input type="hidden" name="action" value="earn"><button class="primary" type="submit">Earn</button></form>
              <form method="post" action="/action"><input type="hidden" name="action" value="spend"><button class="button" type="submit">Spend</button></form>
            </div>
          </section>
        </div>
      </section>
    """


def coach():
    selected = ", ".join(sorted(state["skills"]))
    steps = [
        f"Pick one project with at least 85% match and request a small task using {selected}.",
        "Convert every completed task into proof with link, reviewer, role, and outcome.",
        "Use skill credits to get mentor review before publishing portfolio evidence.",
        "Keep low-bandwidth design enabled for learners with unstable internet access.",
    ]
    cards = "".join(f'<article class="card"><h3>Step {i}</h3><p>{h(step)}</p></article>' for i, step in enumerate(steps, 1))
    return f'<section><div class="section-head"><h2>AI Coach</h2><p>Guidance generated from your current profile.</p></div><div class="grid cards">{cards}</div></section>'


views = {
    "dashboard": dashboard,
    "matching": matching,
    "workspace": workspace,
    "portfolio": portfolio,
    "credits": credits,
    "coach": coach,
    "login": login_page,
}


def redirect(handler, view):
    handler.send_response(303)
    handler.send_header("Location", f"/?{query(view)}")
    handler.end_headers()


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/styles.css":
            data = (ROOT / "styles.css").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/css")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        params = parse_qs(parsed.query)
        view = params.get("view", ["dashboard"])[0]
        user = current_user(self)
        if view == "projects":
            content = project_catalog(params.get("project", ["All"])[0], user)
        else:
            view = view if view in views else "dashboard"
            content = views[view]()
        data = layout(view, content, user).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        data = parse_qs(self.rfile.read(length).decode("utf-8"))
        action = data.get("action", [""])[0]
        if action == "save_profile":
            state["skills"] = set(data.get("skills", []))
            state["goal"] = data.get("goal", [state["goal"]])[0]
            redirect(self, "dashboard")
        elif action == "create_account":
            name = data.get("name", [""])[0].strip()
            email = data.get("email", [""])[0].strip().lower()
            password = data.get("password", [""])[0]
            if not name or not email or len(password) < 4:
                self.send_response(303)
                self.send_header("Location", "/?view=login")
                self.end_headers()
                return
            users[email] = {"name": name, "email": email, "password": password}
            session_id = token_hex(24)
            sessions[session_id] = email
            self.send_response(303)
            self.send_header("Set-Cookie", f"skillbridge_session={session_id}; Path=/; HttpOnly")
            self.send_header("Location", "/?view=projects")
            self.end_headers()
        elif action == "login":
            email = data.get("email", [""])[0].strip().lower()
            password = data.get("password", [""])[0]
            user = users.get(email)
            if not user or user["password"] != password:
                self.send_response(303)
                self.send_header("Location", "/?view=login")
                self.end_headers()
                return
            session_id = token_hex(24)
            sessions[session_id] = email
            self.send_response(303)
            self.send_header("Set-Cookie", f"skillbridge_session={session_id}; Path=/; HttpOnly")
            self.send_header("Location", "/?view=dashboard")
            self.end_headers()
        elif action == "logout":
            self.send_response(303)
            self.send_header("Set-Cookie", "skillbridge_session=; Path=/; Max-Age=0")
            self.send_header("Location", "/?view=login")
            self.end_headers()
        elif action == "apply_project":
            project_name = data.get("project", ["Untitled project"])[0]
            if not any(item["project"] == project_name for item in state["applications"]):
                state["applications"].insert(0, {"project": project_name, "status": "Review pending"})
            redirect(self, "workspace")
        elif action == "add_ai_task":
            next_id = max(task["id"] for task in state["tasks"]) + 1
            selected = ", ".join(sorted(state["skills"])) or "Collaboration"
            state["tasks"].insert(
                0,
                {
                    "id": next_id,
                    "title": "Prepare proof-ready contribution",
                    "status": "To do",
                    "skill": selected.split(", ")[0],
                    "owner": "You",
                    "due": "Next sprint",
                },
            )
            redirect(self, "workspace")
        elif action == "move_task":
            task_id = int(data.get("id", [0])[0])
            order = {"To do": "Doing", "Doing": "Verified", "Verified": "To do"}
            for task in state["tasks"]:
                if task["id"] == task_id:
                    task["status"] = order[task["status"]]
            redirect(self, "workspace")
        elif action == "message":
            message = data.get("message", [""])[0].strip()
            if message:
                state["messages"].append({"name": "You", "text": message})
            redirect(self, "workspace")
        elif action == "verify_work":
            state["credits"] += 10
            state["ledger"].insert(0, {"label": "Proof verified by peer reviewer", "amount": "+10"})
            redirect(self, "credits")
        elif action == "earn":
            state["credits"] += 8
            state["ledger"].insert(0, {"label": "Completed peer help session", "amount": "+8"})
            redirect(self, "credits")
        elif action == "spend":
            state["credits"] = max(0, state["credits"] - 8)
            state["ledger"].insert(0, {"label": "Booked mentor review", "amount": "-8"})
            redirect(self, "credits")
        else:
            redirect(self, "dashboard")


if __name__ == "__main__":
    server = None
    active_port = PORT
    for port in range(PORT, PORT + 20):
        try:
            server = SkillBridgeServer(("localhost", port), Handler)
            active_port = port
            break
        except OSError as error:
            if getattr(error, "errno", None) != 48:
                raise
    if server is None:
        raise socket_error("No free port found from 8000 to 8019")
    print(f"SkillBridge is running at http://localhost:{active_port}")
    if active_port != PORT:
        print(f"Port {PORT} was busy, so SkillBridge started on {active_port}")
    print("Press Control + C to stop")
    server.serve_forever()
