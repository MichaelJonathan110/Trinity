# API

Base path: `/api/v1`. JSON in, JSON out. Auth via `Authorization: Bearer <access_token>`.

## Auth — `/auth`

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/auth/register` | Create account |
| POST | `/auth/login` | Exchange credentials for tokens |
| POST | `/auth/refresh` | Exchange refresh token for a new access token |
| POST | `/auth/logout` | Invalidate refresh token |
| GET  | `/auth/me` | Current user |

## Account — `/account`

Account lifecycle: recovery, portability and erasure (spec 7, 58, 59).

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/account/password-reset/request` | Email a single-use reset link. Always `200`; the response never reveals whether the address exists |
| POST | `/account/password-reset/confirm` | Set a new password with a valid, unused, unexpired token |
| GET | `/account/export` | Download everything we hold about you as JSON |
| DELETE | `/account` | Permanently delete the account and all rows (body must carry `password` + `confirm` = `DELETE`) |

## Notifications — `/notifications`

In-app notification feed and per-kind preferences (spec 21, 59).

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/notifications?unread_only=&limit=` | List your notifications, newest first |
| POST | `/notifications/{id}/read` | Mark one as read |
| POST | `/notifications/read-all` | Mark all as read |
| GET | `/notifications/preferences` | Read per-kind on/off state |
| PUT | `/notifications/preferences` | Enable/disable a kind |

## Profile & body — `/profile`, `/body-metrics`

| Method | Path | Purpose |
|--------|------|---------|
| GET/PUT | `/profile` | Read/update profile |
| GET/POST | `/body-metrics` | List / add a dated measurement |
| DELETE | `/body-metrics/{id}` | Remove a measurement |
| GET/PUT | `/goals` | Read/update goals and macro targets |

## Nutrition — `/foods`, `/meals`, `/hydration`

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/foods/search?q=` | Search foods (Redis-cached; USDA fallback if key set) |
| POST | `/foods` | Create a custom food |
| GET/POST | `/foods/{id}/servings` | List / add servings |
| GET/POST | `/meals?date=` | List / log a meal |
| POST/DELETE | `/meals/{id}/items` | Add / remove meal items |
| GET/POST/DELETE | `/favorites` | Manage favourite foods |
| GET/POST | `/hydration` | Daily water intake |

## Training — `/exercises`, `/programs`, `/workouts`

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/exercises?muscle=&equipment=` | Browse the library |
| GET/POST/PUT/DELETE | `/programs` | Manage programs |
| GET/POST | `/workouts` | List / log a session |
| POST/DELETE | `/workouts/{id}/sets` | Add / remove sets |
| GET | `/workouts/calendar?year=&month=` | Month view |
| GET | `/workouts/heatmap?year=` | Yearly activity heatmap |
| GET | `/personal-records` | Best efforts per exercise |

## Recovery — `/sleep`, `/soreness`

| Method | Path | Purpose |
|--------|------|---------|
| GET/POST | `/sleep` | Sleep logs |
| GET | `/sleep/stats?range=` | Averages and trends |
| GET/POST | `/soreness` | Soreness logs |

## Activity — `/steps`

| Method | Path | Purpose |
|--------|------|---------|
| GET/POST | `/steps` | Daily steps |
| GET | `/steps/stats?range=` | Averages, streak, goal-hit rate |

## Intelligence — `/insights`

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/insights/readiness?date=` | Training readiness score + breakdown |
| GET | `/insights/performance?date=` | Daily performance score |
| GET | `/insights/daily?date=` | Combined daily dashboard payload |
| GET | `/insights/nutrition?range=` | Nutrition insights |
| GET | `/insights/recovery?range=` | Recovery insights |

## Conventions

- Dates are ISO-8601 (`YYYY-MM-DD`) in the user's local day.
- Lists are paginated with `limit`/`offset` where unbounded.
- All errors use `{ "detail": "..." }` with a correct status code.
- `422` carries field-level validation detail.
