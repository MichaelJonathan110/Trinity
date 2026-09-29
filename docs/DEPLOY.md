# Deploying TRINITY

Two hosts, three pieces:

| Piece | Host | Why |
|-------|------|-----|
| Frontend (React/Vite PWA, static) | **Vercel** | Static build, global CDN, free |
| API (FastAPI) | **Render** (Docker web service) | Vercel cannot run a long-lived Python server |
| Database (PostgreSQL 16) | **Render** (managed Postgres) | Managed, backed up, free tier |

Redis is **optional** — the app degrades silently without it (`app/core/cache.py`).
You do not need a Redis instance to run in production.

```
Browser ──► Vercel (static SPA)
                │  fetch  VITE_API_BASE + /api/v1/...
                ▼
        Render (FastAPI + Postgres)
```

---

## 0. Prerequisites

- A GitHub account
- A Vercel account (sign in with GitHub)
- A Render account (sign in with GitHub)
- Git installed locally

---

## 1. Push the code to GitHub

> **This repository is already initialised and committed.** `main` contains a
> single squashed initial commit plus a docs fix. There is **no remote yet** —
> you only need to create the GitHub repo and push.

### 1.1 Create the repo on GitHub

GitHub → **New repository** → name `trinity` → **Public** → do **not** add a
README/.gitignore/license (the repo already has them) → **Create**.

### 1.2 Point the local repo at it and push

```bash
cd /c/Users/kohja/trinity
git remote add origin https://github.com/<your-username>/trinity.git
git push -u origin main
```

Sanity check before pushing (should print **nothing**):

```bash
git ls-files | grep -E '(^|/)\.env$|(^|/)media/'
```

> If `git push` asks for a password, GitHub no longer accepts account
> passwords. Create a **Personal Access Token** (GitHub → Settings → Developer
> settings → Personal access tokens → Tokens (classic) → scope `repo`) and paste
> it as the password. No SSH key is set up on this machine.

**Never commit `.env`.** The included `.gitignore` already excludes it; only the
`.env.example` templates (placeholders only) are tracked.

---

## 2. Deploy the backend (Render)

### 2.1 Blueprint (recommended)

Render → **New +** → **Blueprint** → connect the `trinity` repo. Render reads
`render.yaml` at the repo root and creates the database + web service for you.

When prompted, set these environment variables:

| Key | Value |
|-----|-------|
| `SECRET_KEY` | a long random string (Render can generate one) |
| `CORS_ORIGINS` | your Vercel URL, e.g. `https://trinity.vercel.app` |
| `USDA_API_KEY` | *(optional)* FoodData Central key |

`DATABASE_URL` is wired automatically from the managed database.

### 2.2 Manual (if you prefer clicking)

1. **New +** → **PostgreSQL** → name `trinity-db`, plan **Free** → Create.
2. **New +** → **Web Service** → connect the repo.
   - **Runtime**: Docker
   - **Dockerfile path**: `backend/Dockerfile`
   - **Docker context**: `backend`
   - **Health check path**: `/health`
3. Add environment variables:
   - `DATABASE_URL` → copy the **Internal Database URL** from the database page.
     The app rewrites `postgresql://` to `postgresql+psycopg://` automatically.
   - `SECRET_KEY` → long random string
   - `CORS_ORIGINS` → your Vercel URL
4. Deploy. On boot the entrypoint waits for the DB, runs `alembic upgrade head`,
   then starts uvicorn.

Your API is now at `https://<service-name>.onrender.com`.
Check `https://<service-name>.onrender.com/health` → `{"status":"ok"}`.

---

## 3. Deploy the frontend (Vercel)

1. Vercel → **Add New…** → **Project** → import the `trinity` repo.
2. **Root Directory**: `frontend` (important — the repo is a monorepo).
3. Framework preset: **Vite**. Build command `npm run build`, output `dist`
   (already pinned in `frontend/vercel.json`).
4. **Environment Variables** → add:
   - `VITE_API_BASE` = `https://<service-name>.onrender.com/api/v1`

   > The variable is **`VITE_API_BASE`** (read by `frontend/src/lib/api.ts`).
   > Not `VITE_API_BASE_URL`. Include the `/api/v1` suffix.
5. **Deploy**.

`frontend/vercel.json` also rewrites every path to `index.html` so client-side
routes (`/nutrition`, `/training`, …) work on refresh.

---

## 4. Wire the two together

- In **Render**, set `CORS_ORIGINS` to the exact Vercel origin (no trailing
  slash): `https://trinity.vercel.app`. Redeploy the backend.
- In **Vercel**, make sure `VITE_API_BASE` points at the Render URL **including**
  `/api/v1`. Redeploy the frontend.

---

## 5. Verify

```bash
curl https://<service-name>.onrender.com/health
# {"status":"ok","app":"TRINITY","env":"production"}

curl https://<service-name>.onrender.com/openapi.json | head
```

Then open the Vercel URL, register an account, and confirm the network tab
shows calls to `https://<service-name>.onrender.com/api/v1/...` returning 200.

---

## 6. Seed demo data (optional)

```bash
# From a shell with the Render database's *external* URL:
cd backend
DATABASE_URL='postgresql+psycopg://...external...' python seed_demo.py
```

---

## Environment variable reference

Names must match `backend/app/core/config.py` (`Settings`) exactly.

| Variable | Used by | Notes |
|----------|---------|-------|
| `ENV` | backend | `production` on Render |
| `SECRET_KEY` | backend | long random string |
| `ACCESS_TOKEN_MINUTES` | backend | default 30 |
| `REFRESH_TOKEN_DAYS` | backend | default 30 |
| `DATABASE_URL` | backend | managed by Render |
| `CORS_ORIGINS` | backend | comma-separated, no spaces |
| `USDA_API_KEY` | backend | optional |
| `MEDIA_ROOT` | backend | progress-photo dir |
| `REDIS_URL` | backend | optional / unused in prod |
| `VITE_API_BASE` | frontend (build-time) | full API base incl. `/api/v1` |

---

## Notes & limitations

- **Free Postgres expires** after ~30 days on Render; upgrade or re-create.
- **Progress photos** are stored on the service's local disk (`MEDIA_ROOT`) and
  are **lost on redeploy** on the free plan. Add a persistent disk (paid) and
  point `MEDIA_ROOT` at its mount path for durable storage.
- **Free web services sleep** after 15 min idle; the first request takes ~30 s.
- **Redis** is unused in this setup; leave `REDIS_URL` unset.
- `VITE_*` variables are inlined at **build time**. After changing
  `VITE_API_BASE` you must **redeploy** the Vercel project for it to take effect.
