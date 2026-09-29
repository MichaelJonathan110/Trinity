# Architecture

## Overview

```
Browser (React PWA)
      |  HTTPS / JSON
      v
FastAPI  ──  PostgreSQL   (source of truth)
      └────  Redis        (cache: food search, daily summaries)
      └────  USDA FoodData Central (optional, live food search)
```

The frontend is a static SPA/PWA. The backend owns all business logic and
persistence; the client never computes authoritative values that the server
also needs (targets, readiness) — it renders what the API returns.

## Backend layering

```
app/
├── api/v1/routers/     HTTP layer only: parse, authorize, delegate
├── schemas/            Pydantic v2 request/response models
├── services/           Business logic; orchestrates repositories
├── repositories/       Data access; the only place that touches the Session
├── models/             SQLAlchemy 2.0 ORM entities
├── calculations/       Pure functions: BMR, TDEE, macros, readiness (unit-tested)
├── integrations/       External clients (USDA)
├── core/               Config, security, logging
└── database.py         Engine, session factory, Base
```

Rules:

- Routers contain **no** business logic and **no** SQL.
- Services never build queries directly; they call repositories.
- `calculations/` is pure and deterministic — no I/O, no DB, fully unit-testable.
- Every response shape is a Pydantic schema; ORM models never leak to the client.

## Frontend structure

```
src/
├── components/   Shared, presentation-only (Button, Card, Stat, charts)
├── features/     Domain UI (nutrition, training, recovery, activity, account)
├── pages/        Route-level screens that compose features
├── hooks/        Data hooks (TanStack Query wrappers)
├── services/     API client and typed endpoint functions
├── stores/       Small UI/preferences stores (Zustand)
├── styles/       Design tokens and global CSS
└── types/        Shared TypeScript types
```

Server state lives in **TanStack Query**; only UI/preference state (theme,
active filters) lives in Zustand. These are never mixed.

## Configuration

All configuration is environment-driven (`app/core/config.py`, Pydantic
`BaseSettings`). No secrets in code. See `.env.example`.

## Error handling

- Domain errors raise typed exceptions mapped to HTTP status codes centrally.
- Validation failures return FastAPI's 422 with field-level detail.
- The frontend surfaces a single, human-readable message per failure.
