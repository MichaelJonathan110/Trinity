# Engineering Decisions

Short decision records for the choices that shape TRINITY. Each entry states the
context, the decision, and the consequences we accept.

## ADR-001 — Frontend: React

**Context.** The UI is a dense, stateful, multi-screen app (Today, Nutrition,
Rest, Exercise, Steps, Account) with frequent partial updates.

**Decision.** Use React 18 with function components and hooks.

**Consequences.** A large ecosystem and predictable component model; a runtime
cost and a build step we accept. Server state and local UI state are kept
distinct (see ADR-012).

## ADR-002 — Frontend: TypeScript

**Context.** Many numeric domain objects (macros, TDEE, targets, sleep) flow
between API and UI; mistakes are costly and silent.

**Decision.** Write the frontend in TypeScript, type-checked in CI (`tsc --noEmit`).

**Consequences.** Compile-time safety and self-documenting contracts; slightly
more ceremony when shaping new API responses.

## ADR-003 — Backend: FastAPI

**Context.** We need a typed, async-capable HTTP API with automatic validation
and documentation.

**Decision.** Use FastAPI (Pydantic models, dependency injection) with Uvicorn.

**Consequences.** Request/response validation and OpenAPI docs come for free; we
keep business logic out of route handlers (see ADR-013).

## ADR-004 — Database: PostgreSQL

**Context.** Relational, strongly-consistent data (users, days, meals, workouts,
recovery) with foreign keys and cascade rules.

**Decision.** Use PostgreSQL with SQLAlchemy and Alembic migrations.

**Consequences.** Integrity enforced at the database, and account deletion can
rely on FK cascades; local development needs a running Postgres.

## ADR-005 — Cache: Redis

**Context.** Some reads are expensive or rate-limited (external food lookups,
recomputed insights).

**Decision.** Use Redis as an optional cache layer behind a small abstraction.

**Consequences.** Fast repeat reads and a place to throttle external calls; adds
an infrastructure dependency that must degrade gracefully when absent.

## ADR-006 — Distribution: PWA

**Context.** We want an installable app without maintaining two native codebases.

**Decision.** Ship an installable Progressive Web App (manifest + service worker
via `vite-plugin-pwa`).

**Consequences.** One codebase, offline shell caching, installable on mobile and
desktop; **no access to native health stores** (see ADR-011 and
`health-integrations.md`).

## ADR-007 — Authentication: JWT

**Context.** A stateless API used by a browser client, with refresh needed for
long sessions.

**Decision.** Short-lived access tokens plus refresh tokens; passwords hashed
with a strong one-way function. Access tokens are verified per request and all
data access is scoped to the authenticated user.

**Consequences.** No server session store needed; token handling and rotation
must be done carefully, and refresh tokens must be revocable.

## ADR-008 — Food data: USDA + caching

**Context.** Nutrition logging needs reliable food and nutrient data without us
curating a global database by hand.

**Decision.** Use USDA food data as the external source, normalised into our own
schema, with responses cached (ADR-005) to limit external calls and cost.

**Consequences.** Credible, public-domain data; the external API's availability
and rate limits become part of our reliability story, and we must handle misses
without inventing values.

## ADR-009 — Energy expenditure: Mifflin-St Jeor + adaptive estimate

**Context.** Daily energy targets must be defensible and improve with use.

**Decision.** Start from the Mifflin-St Jeor BMR equation, apply an activity
factor, then adjust from the user's own logged intake and weight trend over time.

**Consequences.** A well-understood baseline that personalises over time; the
adaptive step needs enough real data before it moves, and must not fabricate
precision when data is thin.

## ADR-010 — Health integrations: deferred

**Context.** Apple Health and Android Health Connect offer rich data but are
native-only (see `health-integrations.md`).

**Decision.** Defer automatic health-store reads. Ship the `connected_health_sources`
model and manual entry now, and add a native bridge later.

**Consequences.** We avoid a native codebase today and keep the schema ready; the
cost is that users must enter steps and sleep manually until a bridge exists.

## ADR-011 — Caching strategy

**Context.** Different data has different freshness needs.

**Decision.** Cache only what is expensive or externally sourced (external food
lookups, derived insights) with explicit, short TTLs; never cache a user's
personal reads in a way that could leak across users.

**Consequences.** Fewer external calls and faster repeat views; cache keys must
include the user scope, and correctness never depends on a warm cache.

## ADR-012 — State management

**Context.** The UI mixes remote data, transient UI state, and user preferences.

**Decision.** Keep three kinds of state separate: **server state** via a data
fetching/caching layer (React Query), **local UI state** in component state, and
**user preferences** (theme, units) in a small persisted store.

**Consequences.** Clear ownership and fewer stale-data bugs; contributors must
put state in the right bucket rather than one global store.

## ADR-013 — Layering: repositories between routes and services

**Context.** Route handlers were beginning to hold query details.

**Decision.** Put database queries in repository modules under `app/repositories/`,
keep business logic in services, and keep routes thin.

**Consequences.** Queries are testable and reusable, and routes stay readable;
the extra indirection is worth it as the surface grows.
