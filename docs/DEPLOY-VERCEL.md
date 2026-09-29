# Deploying TRINITY — the card-free path (Vercel + Neon)

**Why this guide exists.** Render now asks for a credit card even on its free
tier, so it is not *actually* free. This path uses only hosts that are free
**without a card**:

| Piece | Host | Card needed? |
|-------|------|--------------|
| Frontend (React/Vite PWA, static) | **Vercel** | No |
| API (FastAPI, Python serverless function) | **Vercel** (second project) | No |
| Database (PostgreSQL 16) | **Neon** | No |

Redis stays **unset** — the app degrades silently without it (`app/core/cache.py`).

```
Browser ──► Vercel project #1 (static SPA, frontend/)
                │  fetch  VITE_API_BASE + /api/v1/...
                ▼
        Vercel project #2 (FastAPI via Mangum, backend/)
                │  psycopg3
                ▼
        Neon (managed Postgres)
```

Two Vercel **projects** from the same repo, because the frontend needs a
catch-all rewrite to `index.html` while the backend needs a catch-all rewrite to
the serverless function — they cannot share one project.

---

## 0. Prerequisites
- A GitHub account, a Vercel account (sign in with GitHub), a Neon account (GitHub login, no card)
- Git installed locally

---

## 1. Push the code to GitHub

```bash
cd /c/Users/kohja/trinity
git remote add origin https://github.com/<your-username>/trinity.git
git push -u origin main
```

> If `git push` asks for a password, GitHub no longer accepts account passwords.
> Create a **Personal Access Token** (Settings → Developer settings → Personal
> access tokens → Tokens (classic) → scope `repo`) and paste it as the password.

Sanity check before pushing (should print **nothing**):

```bash
git ls-files | grep -E '(^|/)\.env$|(^|/)media/'
```

---

## 2. Create the Neon database (no card)

1. **neon.tech** → sign in with GitHub → **Create project**.
2. Name it `trinity`, pick the region closest to you, Postgres 16.
3. On the project dashboard open **Connection string** and copy the
   **Pooled connection** string (host contains `-pooler`). It looks like:

   ```
   postgresql://neondb_owner:XXXX@ep-cool-name-123456-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require
   ```

   Keep this — it is your `DATABASE_URL`.

> The backend rewrites `postgresql://` → `postgresql+psycopg://` automatically
> (`app/core/config.py`), so paste the string **exactly as Neon gives it**.

---

## 3. Run the migrations against Neon

Migrations are **not** run by the serverless function; run them once from your
machine against the Neon URL.

```bash
cd /c/Users/kohja/trinity/backend
python -m venv .venv
source .venv/Scripts/activate        # Windows Git Bash; Linux/macOS: .venv/bin/activate
pip install -r requirements.txt

# paste your Neon pooled string between the quotes:
export DATABASE_URL='postgresql+psycopg://neondb_owner:XXXX@ep-...-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require'

alembic upgrade head
```

Expect it to end with `Running upgrade ... -> 0003_prep_volume_photos`. Verify:

```bash
alembic current        # should print 0003_prep_volume_photos (head)
```

*(Optional) seed demo data:* `python seed_demo.py` if that file exists in
`backend/`, otherwise skip — the app also works on an empty database.

---

## 4. Deploy the backend (Vercel project #2)

1. Vercel → **Add New…** → **Project** → import the `trinity` repo.
2. **Root Directory** → **Edit** → choose **`backend`**.
3. Framework preset: **Other**. Vercel detects `backend/api/index.py` and
   `backend/vercel.json` automatically; leave build/output empty.
4. **Environment Variables** → add:

   | Key | Value |
   |-----|-------|
   | `ENV` | `production` |
   | `SECRET_KEY` | a long random string |
   | `DATABASE_URL` | the Neon pooled string from step 2 |
   | `CORS_ORIGINS` | *(leave for now — set in step 6)* |
   | `ACCESS_TOKEN_MINUTES` | `30` |
   | `REFRESH_TOKEN_DAYS` | `30` |

5. **Deploy**. You get a URL like `https://trinity-api.vercel.app`.
6. **Verify the function responds:**

   ```bash
   curl https://trinity-api.vercel.app/health
   # {"status":"ok","app":"TRINITY","env":"production"}

   curl -s https://trinity-api.vercel.app/openapi.json | head -c 200
   ```

   > If `/health` returns **404**, the catch-all rewrite is being swallowed by
   > the platform. Fix: in `backend/vercel.json` change the destination from
   > `/api/index` to `/api` and redeploy. (The bundled file uses `/api/index`.)

---

## 5. Deploy the frontend (Vercel project #1)

1. Vercel → **Add New…** → **Project** → import the **same** `trinity` repo.
2. **Root Directory** → choose **`frontend`** (important — monorepo).
3. Framework preset: **Vite** (build `npm run build`, output `dist` — pinned in
   `frontend/vercel.json`).
4. **Environment Variables** → add:

   | Key | Value |
   |-----|-------|
   | `VITE_API_BASE` | `https://trinity-api.vercel.app/api/v1` |

   > The name is **`VITE_API_BASE`** (read by `frontend/src/lib/api.ts`), **not**
   > `VITE_API_BASE_URL`. It must include the `/api/v1` suffix.

5. **Deploy**. You get a URL like `https://trinity.vercel.app`.

---

## 6. Wire the two together

- In the **backend** project (Vercel #2) → Settings → Environment Variables →
  set `CORS_ORIGINS` to the exact frontend origin, no trailing slash:

  ```
  https://trinity.vercel.app
  ```

  → **Redeploy** the backend (Deployments → ⋯ → Redeploy).
- In the **frontend** project (Vercel #1), confirm `VITE_API_BASE` points at the
  backend URL **including** `/api/v1` → **Redeploy** if you changed it.

> `VITE_*` variables are inlined at **build time**. After changing
> `VITE_API_BASE` you must redeploy the frontend for it to take effect.

---

## 7. Verify end to end

```bash
curl https://trinity-api.vercel.app/health
```

Then open the frontend URL → **register an account** → open the browser Network
 tab and confirm calls to `https://trinity-api.vercel.app/api/v1/...` return **200**.

---

## Environment variable reference

Names must match `backend/app/core/config.py` (`Settings`) exactly.

| Variable | Used by | Notes |
|----------|---------|-------|
| `ENV` | backend | `production` on Vercel |
| `SECRET_KEY` | backend | long random string |
| `ACCESS_TOKEN_MINUTES` | backend | default 30 |
| `REFRESH_TOKEN_DAYS` | backend | default 30 |
| `DATABASE_URL` | backend | Neon pooled connection string |
| `CORS_ORIGINS` | backend | comma-separated, no spaces |
| `USDA_API_KEY` | backend | optional |
| `MEDIA_ROOT` | backend | progress-photo dir |
| `REDIS_URL` | backend | optional / leave unset in prod |
| `VITE_API_BASE` | frontend (build-time) | full API base incl. `/api/v1` |

---

## Notes & limitations

- **Serverless = ephemeral disk.** Progress photos written to `MEDIA_ROOT` do
  **not** persist across invocations on Vercel. For durable photo storage you
  need object storage (e.g. Vercel Blob / S3); until then treat photos as
  best-effort. Everything else (nutrition, training, recovery, activity) is in
  Postgres and persists normally.
- **Cold starts.** The first request after idle takes ~1 s while the Python
  function boots; subsequent requests are fast.
- **Neon free tier** gives 0.5 GB storage and auto-suspends when idle (wakes on
  the next query in ~0.5 s). No card required.
- **Migrations are manual** (step 3). After adding a new Alembic revision, run
  `alembic upgrade head` again against the Neon URL.
- **Redis** is unused in this setup; leave `REDIS_URL` unset.
