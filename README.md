# SkillBridge

SkillBridge is a Flask and SQLite based collaborative learning platform prototype. It helps learners discover real projects, find collaborators, manage tasks, upload proof of work, and use skill credits for mentorship or peer support.

This project was completed by **Satyam Kumar** with **Kanhaiya Kumar Choubey** as a team member, under the guidance of **Dr. Arvind Selwal, Assistant Professor**. His guidance helped shape the project direction, practical workflow, and academic presentation quality.

## Project Goal

Many students and self-learners understand theory but do not get enough access to real-world projects, teamwork, mentorship, and verified contribution history. SkillBridge solves this by creating a platform where learners can join practical projects, collaborate with peers, and build proof of work.

## Main Features

- Flask based backend, no Python standard `http.server` usage
- SQLite database for persistent users, projects, tasks, applications, messages, uploads, and credit ledger
- Account registration and login
- Secure password hashing using Werkzeug security helpers
- Admin dashboard
- Skill-based project ranking
- Collaborator matching section
- Open project catalog with category filters
- Project owner dashboard for CEOs, founders, NGOs, and team leads
- Project registration form for owners to publish opportunities
- Project application tracker
- Workspace task board
- AI-style sprint planner actions
- Team room messaging
- Proof of work upload system
- Download protected uploaded proof files
- Skill credit wallet and ledger
- Multilingual English/Hindi interface toggle
- Responsive modern frontend for laptop and mobile screens
- VS Code launch and task configuration

## Tech Stack

- Python 3
- Flask
- SQLite
- Jinja2 templates
- Werkzeug password hashing and file utilities
- HTML5
- CSS3
- VS Code configuration

## Folder Structure

```text
SkillBridge/
├── app.py                      # Main Flask application and SQLite setup
├── requirements.txt            # Python dependencies
├── README.md                   # Project documentation
├── index.html                  # Static note/redirect placeholder
├── styles.css                  # Compatibility import for static CSS
├── instance/                   # Local SQLite database folder, ignored by git
├── static/
│   ├── img/
│   │   ├── skillbridge-logo.svg              # Full brand lockup
│   │   ├── skillbridge-mark.svg              # App icon and favicon
│   │   ├── skillbridge-wordmark.svg          # Horizontal wordmark
│   │   ├── skillbridge-presentation-logo.png # Light PPT logo
│   │   ├── skillbridge-presentation-logo-dark.png
│   │   └── skillbridge-icon-presentation.png # PPT icon
│   ├── css/
│   │   └── styles.css          # Main frontend styling
│   └── uploads/                # Uploaded proof files, ignored by git
├── templates/
│   ├── base.html
│   ├── dashboard.html
│   ├── auth.html
│   ├── matching.html
│   ├── projects.html
│   ├── workspace.html
│   ├── portfolio.html
│   ├── credits.html
│   ├── coach.html
│   ├── owner.html
│   └── admin.html
└── .vscode/
    ├── launch.json
    ├── tasks.json
    └── settings.json
```

## How To Run On Laptop

Open the project folder in VS Code or Terminal.

Create a virtual environment:

```bash
python3 -m venv .venv
```

Activate it on macOS/Linux:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
python3 -m pip install -r requirements.txt
```

Run the Flask app:

```bash
python3 app.py
```

Open the URL shown in the terminal. Usually it is:

```text
http://127.0.0.1:5000
```

If port 5000 is busy, the app automatically starts on the next free port, for example:

```text
http://127.0.0.1:5001
```

## VS Code Run Button

This project includes VS Code configuration files.

Use:

```text
Run and Debug > Run SkillBridge Flask
```

Or run tasks:

```text
Command + Shift + P
Tasks: Run Task
Install Requirements
Run SkillBridge Flask
```

## Database

SkillBridge uses SQLite. The database is created automatically when the app starts.

Default database path:

```text
instance/skillbridge.db
```

The database includes these tables:

- `users`
- `projects`
- `people`
- `applications`
- `tasks`
- `messages`
- `proof_uploads`
- `ledger`

To manually initialize the database:

```bash
flask --app app init-db
```

## Admin Access

Admin credentials are not displayed publicly in the user interface. For deployment, set a strong `SKILLBRIDGE_SECRET_KEY`, change seeded admin credentials, and keep administrator access private.

## Project Sections

### Dashboard

Shows project recommendations, metrics, and a quick platform overview.

### Skill Match

Learners select skills and goals. These skills influence project ranking.

### Projects

Shows real-world project opportunities with required roles, skills, duration, difficulty, and join action.

### Workspace

Provides task board, project application tracker, AI-style sprint planning suggestions, and team messages.

### Proof of Work

Allows learners to upload proof files and keep a visible contribution timeline.

### Credits

Tracks earned and spent skill credits for peer help and mentorship review.

### Admin Dashboard

Shows users, project applications, proof uploads, chat activity, and platform stats.

## Security Notes

- Passwords are hashed, not stored as plain text.
- Uploaded filenames are sanitized.
- Upload size is limited to 8 MB.
- Uploaded proof files require login to download.
- The default secret key is only for local development.

## Future Scope

- CSRF protection using Flask-WTF
- Email verification and password reset
- Separate learner, project owner, mentor, and admin roles
- Owner-side applicant shortlisting and approval workflow
- Project milestone tracking with deadlines and reviewer notes
- Real AI recommendation API integration
- AI-generated sprint plans based on project description and selected skills
- Notification system for project requests, task updates, and mentor reviews
- Public proof-of-work portfolio pages with shareable links
- Search, sorting, and advanced filters for project catalog
- Deployment on Render, Railway, PythonAnywhere, or a VPS
- Unit tests, integration tests, and CI workflow

## Author / Credits

- Completed by: **Satyam Kumar**
- Team Member: **Kanhaiya Kumar Choubey**
- Guided by: **Dr. Arvind Selwal, Assistant Professor**
- Project: **SkillBridge**
