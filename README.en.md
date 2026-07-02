<p align="center">
  <a href="README.md">🇧🇷 Português</a> &nbsp;|&nbsp; <strong>🇺🇸 English</strong>
</p>

# Study Schedule

🔗 **Live site:** [cronograma-projeto.onrender.com](https://cronograma-projeto.onrender.com/)

Complete study management system with integrated Pomodoro timer, hour tracking, class timetable, and gamification.

![Cronograma](screenshots/cronograma-en.png)

## Stack

- **Backend:** FastAPI + SQLAlchemy + SQLite
- **Frontend:** Vanilla JS + Chart.js
- **Runtime:** Python 3.8+

## Features

- **Pomodoro Timer** — 25min focus with 5min breaks, area/task selection
- **Areas/Subjects** — Registration with color, category, type (online/presential)
- **Tasks** — CRUD with priority, due date, pomodoro goal
- **Study Sessions** — Manual time logging per area
- **Gamification** — XP, coins, streak, achievements, levels
- **Timetable** — Weekly grid for presential classes
- **Summary/Stats** — Pie chart with hours per area (Chart.js)
- **8 Themes** — Dark, light, ocean, purple, forest, midnight, pastel, contrast

## How to Run

### 1. Activate virtual environment

```bash
source .venv/bin/activate
```

### 2. Start server

```bash
cd cronograma/app
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Access

Open http://localhost:8000 in your browser.

## Project Structure

```
Cronograma(Projeto)/
├── cronograma/
│   ├── app/
│   │   ├── main.py              # FastAPI + DB + gamification
│   │   ├── static/
│   │   │   ├── index.html       # Main interface
│   │   │   ├── style.css        # Styles + themes
│   │   │   ├── app.js           # Frontend logic
│   │   │   ├── store.js         # Global state + gamification
│   │   │   ├── foco.js          # Pomodoro timer
│   │   │   ├── auth.js          # Authentication
│   │   │   └── theme.js         # Theme manager
│   │   └── cronograma.db        # SQLite database
│   ├── requirements.txt
│   ├── docker-compose.yml
│   └── Dockerfile
├── icon_images/                 # Project icons
└── README.md
```

## API Endpoints

| Method | Route | Description |
|--------|-------|-------------|
| POST | `/auth/register` | Register user |
| POST | `/auth/login` | Login (returns JWT) |
| GET | `/areas` | List areas |
| POST | `/areas` | Create area |
| PATCH | `/areas/{id}` | Update area |
| DELETE | `/areas/{id}` | Delete area |
| GET | `/tasks` | List tasks |
| POST | `/tasks` | Create task |
| PATCH | `/tasks/{id}` | Update task |
| DELETE | `/tasks/{id}` | Delete task |
| GET | `/sessoes` | List sessions |
| POST | `/sessoes` | Create session |
| GET | `/sessoes/resumo` | Summary by period |
| POST | `/pomodoro/completar` | Complete pomodoro |
| GET | `/gamification-summary` | Gamification summary |
| POST | `/coins/buy-freeze` | Buy freeze (10 coins) |

## Gamification

- **XP:** minutes studied + 5 XP per completed task
- **Level:** `XP = 100 × level^1.5`
- **Coins:** +3 per pomodoro, +1 per 10min session
- **Streak:** consecutive study days (freezes available)
- **Achievements:** categories XP, streak, pomodoro, tasks, level, coins

## License

MIT
