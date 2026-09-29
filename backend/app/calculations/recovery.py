"""Sleep and readiness estimates. Application-generated only (spec 24, 28, 67)."""
from datetime import datetime


def sleep_duration_minutes(bedtime: datetime, wake_at: datetime) -> int:
    """Minutes asleep. Handles the normal overnight case; returns 0 if inverted."""
    delta = (wake_at - bedtime).total_seconds() / 60.0
    return int(round(delta)) if delta > 0 else 0


def sleep_score(duration_min: int, target_min: int = 480, quality: int | None = None) -> int:
    """0-100 heuristic. Duration is the main driver, self-reported quality refines it.
    This is NOT a medical measurement (spec 24, 67)."""
    if target_min <= 0:
        return 0
    ratio = duration_min / target_min
    if ratio >= 1.0:
        duration_pts = 70.0 - min((ratio - 1.0) * 40, 15)   # slight penalty for big oversleep
    else:
        duration_pts = max(0.0, 70.0 * (ratio ** 0.8))
    if quality is None:
        return int(round(max(0, min(duration_pts + 20, 100))))
    quality_pts = (max(1, min(quality, 5)) - 1) / 4 * 30
    return int(round(max(0, min(duration_pts + quality_pts, 100))))


def consistency_score(bedtimes: list[int]) -> int:
    """0-100 from the spread of bedtimes (minutes past 18:00). Tight = consistent.
    Uses the standard deviation of the sample (spec 23, 26)."""
    if len(bedtimes) < 3:
        return 0
    mean = sum(bedtimes) / len(bedtimes)
    variance = sum((b - mean) ** 2 for b in bedtimes) / len(bedtimes)
    sd = variance ** 0.5
    return int(round(max(0.0, 100.0 - min(sd / 90.0 * 100.0, 100.0))))


def readiness_score(
    sleep_min: int | None,
    sleep_target: int = 480,
    days_since_rest: int = 1,
    subjective: int | None = None,
    steps_yesterday: int | None = None,
) -> dict:
    """TRINITY Training Readiness, 0-100. An application estimate, not a diagnosis.
    Inputs are weighted and renormalised over whatever data exists (spec 28)."""
    parts: list[tuple[float, float]] = []   # (score 0-100, weight)
    if sleep_min is not None and sleep_min > 0:
        ratio = min(sleep_min / sleep_target, 1.15)
        parts.append((min(ratio, 1.0) * 100, 0.45))
    if subjective is not None:
        parts.append((((max(1, min(subjective, 5)) - 1) / 4) * 100, 0.25))
    # Consecutive training days without rest lower readiness.
    load_penalty = min(days_since_rest * 9, 30)
    parts.append((100 - load_penalty, 0.20))
    if steps_yesterday is not None:
        parts.append((min(steps_yesterday / 10000, 1.2) * 100, 0.10))

    total_w = sum(w for _, w in parts)
    if total_w == 0:
        return {"score": None, "label": "insufficient_data", "inputs": 0}
    score = int(round(sum(s * w for s, w in parts) / total_w))
    score = max(0, min(score, 100))
    label = "good" if score >= 75 else "moderate" if score >= 55 else "low"
    return {"score": score, "label": label, "inputs": len(parts)}
