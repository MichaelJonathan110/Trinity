# Health Data Integrations

This document describes how TRINITY handles health and activity data coming from
the user's phone, and — just as importantly — what it does **not** do today.

## Why a PWA cannot read Apple Health or Health Connect directly

TRINITY ships as an installable **Progressive Web App**. A web application runs in
the browser sandbox and has no access to the platform health stores:

- **Apple Health / HealthKit** is a native iOS framework. There is no web API that
  exposes HealthKit data to a browser. Reading it requires a native app (Swift /
  Objective-C) that holds the HealthKit entitlement.
- **Android Health Connect** is a native Android API (formerly Google Fit). It is
  reachable only from an Android process that holds the relevant permissions; a
  web page cannot query it.

Because of this, any health-store integration in TRINITY is a **native-side
concern**. The web app can only receive data that has already been handed to it
through an API it controls.

## What IS implemented today

The backend models a health source so the product can grow into native bridges
without a schema change:

| Layer | Status | Notes |
|---|---|---|
| `connected_health_sources` table | **Implemented** | One row per connected source; `provider` is constrained to `apple_health`, `health_connect`, or `manual`. |
| Manual entry of steps / sleep | **Implemented** | The user types values in the app; they are stored as first-class daily records. |
| Reading Apple Health automatically | **Not implemented** | Requires a native iOS client (see below). |
| Reading Health Connect automatically | **Not implemented** | Requires a native Android client (see below). |
| Background sync from a phone | **Not implemented** | No native client exists yet. |

So today the practical path is the **manual fallback**: the user records steps and
sleep themselves, and the app treats `provider = manual` as the source of truth.
Nothing is inferred or fabricated — if the user enters nothing, the app shows
nothing for that day.

## Permissions and privacy that WOULD apply

If a native bridge is added later, the following apply and must be handled
honestly in the UI and in the store listings:

- **Apple HealthKit**: the app must declare the specific data types it reads
  (e.g. step count, sleep analysis), request read authorisation at runtime, and
  provide a privacy policy. HealthKit data must not be used for advertising and
  must not be written to iCloud without explicit consent.
- **Android Health Connect**: the app declares a set of `HealthPermission`
  scopes, requests them at runtime, and must justify each one. Health Connect
  enforces its own consent screen and lets the user revoke access at any time.
- **General**: data is personal and sensitive. Any server-side storage must be
  scoped strictly to the authenticated user, exported only on request, and
  deleted on account deletion (see the account endpoints).

## Future path and trade-offs

A realistic way to add real health-store reads later is a **thin native
wrapper** around the existing web app, e.g. Capacitor or a bespoke shell:

| Option | How it works | Trade-offs |
|---|---|---|
| Capacitor + community Health plugin | Wrap the PWA in a native container; a plugin reads HealthKit / Health Connect and posts to the TRINITY API | Fastest to ship; adds a native build step and app-store review; plugin quality varies |
| Bespoke native shell (Swift / Kotlin) | Full control over permissions, background sync and privacy copy | Highest effort and cost; two codebases to maintain |
| Health Connect bridge (Android only) | Native Android service reads Health Connect and pushes to the API | Solves Android only; iOS still needs HealthKit |
| Keep manual entry only | No native code at all | Zero integration risk; users must type their own numbers |

Whichever path is chosen, the server contract stays the same: the API receives
plain step/sleep records tagged with their `provider`, and the existing
`connected_health_sources` table records which source is connected.

## Current status summary

- **Implemented**: health-source model, manual step/sleep entry, per-user data
  scoping, account export and deletion.
- **Not implemented**: automatic reads from Apple Health or Health Connect, and
  background sync.
- **Manual fallback**: in use today and fully supported.
