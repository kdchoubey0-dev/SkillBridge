# SkillBridge

SkillBridge is a Python-based collaborative learning and work platform prototype. It helps learners find real projects, build teams, manage tasks, create proof of work, and use skill credits for peer support and mentorship.

## Project Goal

Many students and self-learners have theoretical knowledge but do not get enough access to real-world projects, teamwork, mentorship, and verified work experience. SkillBridge solves this problem by creating a platform where users can learn by building real projects with other people.

## Main Features

- Create account and login system
- Skill-based collaborator matching
- Open project catalog with filters
- Project application tracker
- Project workspace with task board
- AI sprint planner for next task guidance
- Team room for project communication
- Proof of Work portfolio section
- Skill credit system for mentorship and peer help
- Responsive design for laptop and mobile screens
- Automatic port fallback if port 8000 is busy

## Tech Stack

- Python 3
- HTML
- CSS
- Python standard library HTTP server
- VS Code run configuration

## How To Run

Open the project folder in VS Code.

Run this command in the terminal:

```bash
python3 app.py
```

The terminal will show a local URL:

```text
SkillBridge is running at http://localhost:8000
```

Open that URL in your browser:

```text
http://localhost:8000
```

If port 8000 is already busy, the app will automatically start on another port such as:

```text
http://localhost:8001
```

## How To Stop

In the VS Code terminal, press:

```text
Control + C
```

## VS Code Run Button

This project includes VS Code configuration files inside the `.vscode` folder.

You can run the project using:

```text
Run and Debug > Run SkillBridge
```

You can also run:

```text
Command + Shift + P
Tasks: Run Task
Run SkillBridge
```

## Project Sections

### Dashboard

Shows recommended projects, platform metrics, and collaboration fit.

### Skill Matching

Allows users to select skills and find collaborators with complementary abilities.

### Projects

Displays real project opportunities with roles, required skills, difficulty level, duration, and application action.

### Workspace

Provides a task board, team messages, application tracker, and AI sprint planning suggestions.

### Proof of Work

Shows verified contribution records that can be used as a digital portfolio.

### Credits

Tracks skill credits earned or spent through mentorship, review, and peer support.

## Future Scope

- Database integration
- Persistent user accounts
- Real authentication security
- Admin dashboard
- Real-time chat
- File upload for proof of work
- Multilingual interface
- AI-based project recommendations

## Author

Satyam Kumar
