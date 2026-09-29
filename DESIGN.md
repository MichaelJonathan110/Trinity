# TRINITY — Design System

> Fuel. Recover. Perform.

## 1. Identity
TRINITY is a **premium dark fitness application**. Surfaces are graphite/charcoal; the
accent is a single restrained orange. It should read like a product from a professional
fitness-technology company — strong typography, generous whitespace, subtle borders, clear
hierarchy — and never like an AI-generated dashboard.

Data visualization takes its *principles* from Apple Health / Apple Fitness (calm density,
legible numbers, meaningful color) but with an **original TRINITY identity**: no copied
layouts, charts, or assets.

## 2. Principles
1. **Data first.** The number the user came for is the largest thing on the screen.
2. **Restraint.** One accent moment per screen. Everything else is neutral.
3. **Calm density.** Show what is actionable; move the rest to history.
4. **Honest.** Estimates are labelled estimates. No invented values, ever.

## 3. Color tokens
Never hardcode colors in components — use these tokens only.

### Night theme (default)
| Token | Value | Use |
|---|---|---|
| `--bg` | `#0E1116` | app background (graphite, not pure black) |
| `--surface` | `#161A21` | primary surface |
| `--surface-2` | `#1D222A` | secondary / inset surface |
| `--text-primary` | `#F3F5F7` | primary text |
| `--text-secondary` | `#9BA3AE` | labels, secondary |
| `--text-tertiary` | `#6B7280` | hints, disabled |
| `--border` | `#262C35` | subtle borders |
| `--border-strong` | `#333B45` | dividers needing emphasis |
| `--accent` | `#FF6B2C` | the one accent |
| `--accent-ink` | `#1A0F07` | text on accent |
| `--accent-quiet` | `rgba(255,107,44,.14)` | accent tint (active nav bg, etc.) |
| `--success` | `#3FB950` | positive state only |
| `--warning` | `#D29922` | caution state only |
| `--danger` | `#F85149` | error state only |
| `--info` | `#4C8DFF` | informational only |

### Day theme
| Token | Value |
|---|---|
| `--bg` | `#FAFAF8` |
| `--surface` | `#FFFFFF` |
| `--surface-2` | `#F3F3F0` |
| `--text-primary` | `#15171C` |
| `--text-secondary` | `#5A6270` |
| `--text-tertiary` | `#8A919C` |
| `--border` | `#E4E4DF` |
| `--border-strong` | `#D2D2CB` |
| `--accent` | `#E35D05` |
| `--accent-ink` | `#FFFFFF` |
| `--accent-quiet` | `rgba(227,93,5,.10)` |
| `--success` | `#1F8A3B` |
| `--warning` | `#9A6B00` |
| `--danger` | `#C33A2E` |
| `--info` | `#2563EB` |

**Accent discipline:** accent marks exactly one thing per screen (primary CTA, or the active
nav item, or a single highlighted metric). Never accent + glow + badge at once. Status colors
mark state only — never decoration.

## 4. Typography
**Manrope** (variable) for UI and numerals.
*Reason:* a geometric grotesque with athletic tension and excellent large numerals; more
characterful than the Inter/Geist default while staying highly legible. Fallback:
`system-ui, -apple-system, Segoe UI, Roboto, sans-serif`.
Weights: **400 / 500 / 600 / 700 only.** No 800/900.
All data numerals use `font-variant-numeric: tabular-nums` so columns and metrics align.

| Token | Size / line-height | Use |
|---|---|---|
| `--fs-metric` | 44 / 48 | hero metric (calories remaining, readiness) |
| `--fs-display` | 32 / 38 | page title |
| `--fs-h2` | 22 / 28 | section title |
| `--fs-h3` | 18 / 24 | card title |
| `--fs-body` | 15 / 22 | body |
| `--fs-sm` | 13 / 18 | labels, secondary |
| `--fs-xs` | 12 / 16 | hints, captions |

## 5. Spacing, radius, elevation
- **Spacing scale (px):** 4, 8, 12, 16, 24, 32, 48, 64, 96. Use generously; whitespace is structure.
- **Radius:** `--r-sm: 6px` (controls, inputs), `--r-md: 10px` (cards, panels), `--r-pill: 999px`
  (pills **only** where a pill is meaningful — e.g. a real status chip). Not every element is a pill.
- **Elevation:** flat by default. `--shadow-1: 0 1px 2px rgba(0,0,0,.24)` for popovers/menus only.
  No page-wide floating cards, no glow.

## 6. Motion (MOTION dial = 2)
- Transitions **120–200ms ease-out** on state change (hover, focus, expand).
- **No infinite loops or pulses.** Motion guides attention to a moment, then stops.
- Respect `prefers-reduced-motion: reduce` — disable non-essential transitions.

## 7. Theme behaviour (spec §45–46)
- **Automatic is the default.** Day 06:00–17:59, Night 18:00–05:59, using the **device local timezone**
  (`Intl.DateTimeFormat().resolvedOptions().timeZone`) — never hardcoded UTC.
- The theme flips live when the boundary is crossed, without a page refresh.
- Manual override (Day / Night / Automatic) is persisted per user.
- Both themes must meet contrast requirements (see §8).

## 8. Accessibility
- Text contrast ≥ 4.5:1 (body) and ≥ 3:1 (large text / UI borders / chart segments).
- Never rely on color alone — pair with label, icon, or shape.
- Visible focus rings on every interactive element; full keyboard operation.
- Semantic HTML; labelled controls; no hover-only functionality.

## 9. Prohibited (antislop)
No blue-purple or rainbow gradients · no neon/pastel palettes · no blurred radial orbs ·
no glassmorphism stacks · no uniform pill radius · no page-wide soft shadows · no glow ·
no background grid/blueprint · no decorative emoji · no Lucide-default icon set without a
reason · no arrows on every button · no left color stripes · no "AI Powered" capsules ·
no eyebrow badge above the H1 · no pulsing status dots · no fake terminal window ·
no bento mosaic · no invented numbers or deltas.
