"""Phase-rate maths for Preparation (spec 66, 67).

Bodyweight is a noisy daily signal: water, sodium, glycogen and gut content move
it by a kilogram in either direction. Every judgement here is therefore made on
WEEKLY AVERAGES and on the trend of those averages, never on a single weigh-in.

Energy equivalence: 1 kg of body mass ~ 7700 kcal, so a weekly rate of
`kg_per_week` implies a daily energy imbalance of `kg_per_week * 7700 / 7`.
"""
from datetime import date, timedelta

KCAL_PER_KG = 7700.0

# What each phase is trying to do, as a percentage of bodyweight per week.
# These are sensible defaults a coach would start from, not laws of nature.
PHASE_DEFAULT_RATE: dict[str, float] = {
    "cut": -0.7,      # lose ~0.7% of bodyweight per week
    "recomp": 0.0,    # hold weight, change composition
    "maintain": 0.0,
    "bulk": 0.35,     # gain ~0.35% per week (lean-gain pace)
}

# A rate inside this band (percentage points per week) counts as "on plan".
RATE_TOLERANCE_PCT = 0.25

# Largest single kcal change the auto-coach will suggest at once.
MAX_KCAL_ADJUSTMENT = 300


def week_start(d: date) -> date:
    """Monday of the ISO week containing `d`."""
    return d - timedelta(days=d.weekday())


def weekly_averages(rows: list[dict]) -> list[dict]:
    """Collapse weigh-ins into one average per ISO week.

    `rows` are {measured_on: date, weight_kg: float|None}; rows without a weight
    are skipped. Returns [{week_start, avg_kg, n}] sorted oldest first.
    """
    buckets: dict[date, list[float]] = {}
    for r in rows:
        w = r.get("weight_kg")
        if w is None:
            continue
        ws = week_start(r["measured_on"])
        buckets.setdefault(ws, []).append(float(w))
    out = [
        {"week_start": ws, "avg_kg": round(sum(v) / len(v), 3), "n": len(v)}
        for ws, v in buckets.items()
    ]
    out.sort(key=lambda r: r["week_start"])
    return out


def trend_kg_per_week(weeklies: list[dict], lookback: int = 4) -> float | None:
    """Least-squares slope of the last `lookback` weekly averages, in kg/week.

    Needs at least two weeks of data; returns None rather than inventing a trend.
    """
    pts = weeklies[-lookback:]
    if len(pts) < 2:
        return None
    xs = [(p["week_start"] - pts[0]["week_start"]).days / 7.0 for p in pts]
    ys = [p["avg_kg"] for p in pts]
    n = len(xs)
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    denom = sum((x - mean_x) ** 2 for x in xs)
    if denom == 0:
        return None
    slope = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys)) / denom
    return round(slope, 3)


def rate_pct_per_week(kg_per_week: float | None, current_weight_kg: float | None) -> float | None:
    """Convert kg/week into percentage of bodyweight per week."""
    if kg_per_week is None or not current_weight_kg:
        return None
    return round(kg_per_week / current_weight_kg * 100.0, 2)


def phase_verdict(phase_type: str, actual_pct: float | None, target_pct: float | None) -> dict:
    """Compare the measured rate against the plan's target rate.

    Returns a label plus a plain-language read, and never claims more precision
    than the data supports (two weeks is the minimum to say anything at all).
    """
    if actual_pct is None:
        return {
            "verdict": "unknown",
            "label": "Not enough data yet",
            "detail": "Two full weeks of weekly averages are needed before a rate means anything.",
        }
    target = target_pct if target_pct is not None else PHASE_DEFAULT_RATE.get(phase_type, 0.0)
    delta = actual_pct - target
    if abs(delta) <= RATE_TOLERANCE_PCT:
        return {
            "verdict": "on_plan",
            "label": "On plan",
            "detail": f"Moving {actual_pct:+.2f}%/week against a {target:+.2f}%/week target.",
        }
    if phase_type in ("cut", "recomp") and delta > 0:
        return {
            "verdict": "too_slow",
            "label": "Losing slower than planned" if phase_type == "cut" else "Not holding the line",
            "detail": f"Actual {actual_pct:+.2f}%/week vs target {target:+.2f}%/week.",
        }
    if phase_type == "bulk" and delta < 0:
        return {
            "verdict": "too_slow",
            "label": "Gaining slower than planned",
            "detail": f"Actual {actual_pct:+.2f}%/week vs target {target:+.2f}%/week.",
        }
    return {
        "verdict": "too_fast",
        "label": "Moving faster than planned",
        "detail": f"Actual {actual_pct:+.2f}%/week vs target {target:+.2f}%/week. "
                  "A faster rate is not automatically better - past about 1%/week "
                  "a cut risks muscle, and a bulk adds fat.",
    }


def suggest_kcal_adjustment(
    target_pct: float | None, actual_pct: float | None, current_weight_kg: float | None
) -> dict:
    """The daily kcal change that would move the actual rate onto the target rate.

    adjustment = (target_kg_per_week - actual_kg_per_week) * 7700 / 7, clamped to
    +/- 300 kcal so a single noisy week never triggers a wild swing.
    """
    if target_pct is None or actual_pct is None or not current_weight_kg:
        return {"suggested_kcal": 0, "reason": "Not enough data to adjust."}
    # Never fiddle with calories while the rate is already inside tolerance: a
    # 10-kcal nudge would be noise, not coaching.
    if abs(actual_pct - target_pct) <= RATE_TOLERANCE_PCT:
        return {"suggested_kcal": 0, "reason": "The rate is close enough to plan; no change needed."}
    target_kg = target_pct / 100.0 * current_weight_kg
    actual_kg = actual_pct / 100.0 * current_weight_kg
    raw = (target_kg - actual_kg) * KCAL_PER_KG / 7.0
    clamped = int(max(-MAX_KCAL_ADJUSTMENT, min(MAX_KCAL_ADJUSTMENT, round(raw / 10.0) * 10)))
    if clamped == 0:
        return {"suggested_kcal": 0, "reason": "The rate is close enough to plan; no change needed."}
    direction = "add" if clamped > 0 else "remove"
    return {
        "suggested_kcal": clamped,
        "reason": f"{direction.capitalize()} about {abs(clamped)} kcal/day to bring the rate back to plan.",
    }


def suggest_refeed(
    phase_type: str, weeks_on_phase: int, actual_pct: float | None
) -> dict | None:
    """When a cut has run long enough, suggest a planned refeed or diet break.

    Sustained energy restriction and a stalled rate are the classic reasons a
    coach programmes one. Returns None when nothing is due.
    """
    if phase_type != "cut":
        return None
    if weeks_on_phase >= 12:
        return {
            "kind": "diet_break",
            "label": "Diet break is due",
            "detail": f"{weeks_on_phase} weeks in a deficit. A 1-2 week break at maintenance "
                      "restores hormones, training quality and adherence before continuing.",
        }
    stalled = actual_pct is not None and actual_pct > -0.1
    if weeks_on_phase >= 6 and stalled:
        return {
            "kind": "refeed",
            "label": "Refeed is worth trying",
            "detail": f"{weeks_on_phase} weeks in a deficit and the rate has stalled. One or two "
                      "days at maintenance calories can restart it without undoing the phase.",
        }
    return None
