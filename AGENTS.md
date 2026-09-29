# AGENTS.md — TRINITY

Read this before touching any UI. TRINITY follows the **antislop** rules
(skills: `antislop`, `antislop-ui`, `antislop-layoutmobile`).
**Read `DESIGN.md` first** — it is the source of truth for color, type, spacing, motion.

## Binding rules for every change
- **R-01** Every element earns its place: write the purpose or remove it. No decoration for decoration's sake.
- **R-04** Icons only when genuinely relevant to the content. **No emoji in UI text.**
- **R-05 / C-3** Layout follows content, not a template. Forbidden defaults: bento mosaic, fake terminal
  window, three-column pricing, left-edge color stripes, "How it works" always 3 steps, "trusted by" logo bar.
- **R-06** Typography is a brand decision (Manrope, see DESIGN.md), not a default pick.
- **R-09** No pill/eyebrow badge above an H1 restating the headline. No decorative status dots.
- **R-10 / R-11 / R-12 / R-13** Glass, glow, shadow, radius live at their dose caps (≤1–2 elements per screen).
- **R-17 / R-18 / R-38** Never invent metrics, deltas, activity feeds, or table rows. Real data or a
  labelled placeholder visible to the user.
- **R-19** No endless pulses or loops. Motion follows the MOTION dial in DESIGN.md.
- **R-23** Empty fields stay empty or carry honest placeholders (`Your Name`, `email@example.com`).
- **R-24 / R-26** No dead navigation, no non-functional controls. Unbuilt = omit or label "Coming soon".
- **R-27** Empty / loading / error states name the cause and the next action.
- **R-29** ≤3 core colors + 1 accent. One accent moment per screen.
- **R-31** Every badge, dot, and stripe must mark a real state.

## Delivery Gate
Before reporting any UI task done, run the core Delivery Gate **and** the `antislop-ui`
checklist (all answers must be yes). Report what was verified with raw evidence.
