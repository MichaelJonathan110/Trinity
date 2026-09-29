# TRINITY

> **Fuel. Recover. Perform.**

TRINITY is a personal athlete-performance application that unifies **nutrition,
recovery, training and daily activity** into a single, coherent picture of how an
athlete is actually doing — and what to do next.

It is not a calorie counter with extra tabs. Its reason to exist is the
*interaction* between domains: a hard training block changes recovery needs;
poor sleep changes training readiness; nutrition drives recovery. TRINITY is
built around that triangle — hence the name.

## Stack

| Layer     | Technology |
|-----------|------------|
| Frontend  | React 18 + TypeScript + Vite (PWA) |
| Backend   | FastAPI + SQLAlchemy 2.0 + Pydantic v2 |
| Database  | PostgreSQL 16 |
| Cache     | Redis 7 |
| Auth      | JWT (access + refresh), bcrypt |
| Container | Docker Compose |

## Quick start

```bash
cp .env.example .env

docker compose up --build
# frontend  http://localhost:5173
# api docs  http://localhost:8000/docs
```

### Running without Docker (development)

```bash
# Backend
cd backend
python -m venv .venv && . .venv/Scripts/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

## Documentation

- [`docs/architecture.md`](docs/architecture.md) — system design and layering
- [`docs/database.md`](docs/database.md) — schema and relationships
- [`docs/api.md`](docs/api.md) — REST endpoints
- [`docs/calculations.md`](docs/calculations.md) — BMR/TDEE, macros, readiness
- [`docs/pwa.md`](docs/pwa.md) — install, offline behaviour
- [`DESIGN.md`](DESIGN.md) — the visual system (read before touching UI)
- [`AGENTS.md`](AGENTS.md) — rules for automated contributors

## The four domains

1. **Nutrition** — food database, logging, servings, macros, hydration.
2. **Recovery** — sleep duration/quality, resting HR, HRV, soreness.
3. **Training** — exercise library, programs, set/rep logging, personal records.
4. **Activity** — daily steps, goals, trends.

Cross-domain **intelligence** ties them together: Training Readiness, Daily
Performance, and per-domain insights.

## Status

Under active construction. See `docs/` for current scope.

## Screenshots

Screenshots are captured from the running app against the seeded demo athlete
(`demo@trinity.app`), never mocked. To reproduce:

```bash
cd backend && python seed_demo.py        # demo athlete + a week of history
cd ../frontend && npm install && npm run dev
npx playwright install                   # or use an existing Chrome/Edge
node scripts/capture-screenshots.mjs     # writes docs/screenshots/*.png
```

Every screen is captured at a desktop width (1280px) and a mobile width
(390px) in `docs/screenshots/`:

| Screen | Route | Desktop | Mobile |
|--------|-------|---------|--------|
| Today | `/` | `today-desktop.png` | `today-mobile.png` |
| Nutrition | `/nutrition` | `nutrition-desktop.png` | `nutrition-mobile.png` |
| Rest | `/rest` | `rest-desktop.png` | `rest-mobile.png` |
| Exercise | `/exercise` | `exercise-desktop.png` | `exercise-mobile.png` |
| Steps | `/steps` | `steps-desktop.png` | `steps-mobile.png` |
| Account | `/account` | `account-desktop.png` | `account-mobile.png` |
| Sign in | `/login` | `login-desktop.png` | - |

If no headless browser is available, run the commands locally; never commit
placeholder images.
