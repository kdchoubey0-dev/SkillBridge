from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from html import escape
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse

PORT = 8000
ROOT = Path(__file__).parent

state = {
    "skills": {"Frontend", "Research", "Communication"},
    "goal": "Build a social-impact web app with a global team.",
    "credits": 128,
    "tasks": [
        {"id": 1, "title": "Design onboarding flow", "status": "To do", "skill": "UX"},
        {"id": 2, "title": "Build project API schema", "status": "Doing", "skill": "Backend"},
        {"id": 3, "title": "Translate workspace labels", "status": "Verified", "skill": "Language"},
    ],
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

projects = [
    {
        "title": "Community Health Finder",
        "type": "Impact",
        "fit": 94,
        "skills": ["Frontend", "Maps", "Research"],
        "summary": "A low-bandwidth directory for local clinics, volunteers, and emergency resources.",
    },
    {
        "title": "Open Tutor Kit",
        "type": "Open Source",
        "fit": 91,
        "skills": ["AI", "Content", "Language"],
        "summary": "Reusable lesson tools for peer mentors in multilingual learning communities.",
    },
    {
        "title": "Micro Internship Board",
        "type": "Startup",
        "fit": 88,
        "skills": ["Product", "Backend", "Analytics"],
        "summary": "Verified short work sprints for learners who need practical portfolio proof.",
    },
    {
        "title": "Accessible NGO Website",
        "type": "Impact",
        "fit": 86,
        "skills": ["HTML", "Design", "Docs"],
        "summary": "Modern site and donation workflow for small nonprofit teams on slow networks.",
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


def query(view):
    return urlencode({"view": view})


def tags(items):
    return "".join(f'<span class="tag">{h(item)}</span>' for item in items)


def layout(view, content):
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
          <a class="primary" href="/?view=projects">Join Project</a>
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
          <input type="checkbox" name="skills" value="{h(skill)}" {"checked" if skill in state["skills"] else ""}>
          {h(skill)}
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


def project_catalog():
    cards = "".join(
        f"""
        <article class="card project">
          <span class="type">{h(project["type"])}</span>
          <h3>{h(project["title"])}</h3>
          <p>{h(project["summary"])}</p>
          <div class="tags">{tags(project["skills"])}</div>
          <a class="button" href="/?view=workspace">Request to join</a>
        </article>
        """
        for project in projects
    )
    return f"""
      <section>
        <div class="section-head"><h2>Open Projects</h2><p>Pick a project where your contribution can become verified portfolio evidence.</p></div>
        <div class="grid cards">{cards}</div>
      </section>
    """


def workspace():
    columns = ""
    for status in ["To do", "Doing", "Verified"]:
        task_cards = "".join(
            f"""
            <article class="task">
              <div class="row"><h3>{h(task["title"])}</h3><span>{h(task["skill"])}</span></div>
              <form method="post" action="/action">
                <input type="hidden" name="action" value="move_task">
                <input type="hidden" name="id" value="{task["id"]}">
                <button class="button" type="submit">Move</button>
              </form>
            </article>
            """
            for task in state["tasks"]
            if task["status"] == status
        )
        columns += f'<section class="column"><h2>{status}</h2>{task_cards}</section>'
    messages = "".join(f'<div class="message"><strong>{h(m["name"])}</strong><p>{h(m["text"])}</p></div>' for m in state["messages"])
    return f"""
      <section>
        <div class="section-head"><h2>Project Workspace</h2><p>Manage real tasks, team roles, messages, and contribution evidence.</p></div>
        <div class="grid two">
          <section class="panel board">{columns}</section>
          <section class="panel">
            <h2>Team Room</h2>
            {messages}
            <form class="message-form" method="post" action="/action">
              <input type="hidden" name="action" value="message">
              <input name="message" placeholder="Share an update">
              <button class="primary" type="submit">Send</button>
            </form>
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
    "projects": project_catalog,
    "workspace": workspace,
    "portfolio": portfolio,
    "credits": credits,
    "coach": coach,
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
        view = view if view in views else "dashboard"
        data = layout(view, views[view]()).encode("utf-8")
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
    server = ThreadingHTTPServer(("localhost", PORT), Handler)
    print(f"SkillBridge is running at http://localhost:{PORT}")
    print("Press Control + C to stop")
    server.serve_forever()
