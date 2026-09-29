"""Weekly training volume per muscle group (spec 33).

Volume is counted in *fractional sets*: a working set credits 1.0 to the primary
muscle and 0.5 to each secondary muscle it lists. That is the standard way to
compare a barbell row (which works lats and biceps) against a curl without
double-counting. Warm-up sets are never counted.

The landmarks below are the evidence-informed weekly set ranges popularised by
Israetel et al.: MEV (minimum effective volume), MAV (maximum adaptive volume,
the productive target band) and MRV (maximum recoverable volume). They are
GUIDELINES from the literature, not measurements of the individual - the UI says
so wherever they appear.
"""

# canonical muscle -> (MEV, MAV, MRV) sets per week
MUSCLE_LANDMARKS: dict[str, tuple[int, int, int]] = {
    "Chest":       (8, 14, 22),
    "Front Delts": (6, 10, 16),
    "Side Delts":  (8, 16, 26),
    "Rear Delts":  (6, 14, 24),
    "Lats":        (8, 14, 22),
    "Traps":       (4, 10, 18),
    "Biceps":      (6, 12, 20),
    "Triceps":     (6, 12, 20),
    "Forearms":    (2, 6, 12),
    "Quads":       (8, 14, 22),
    "Hamstrings":  (6, 12, 20),
    "Glutes":      (4, 10, 18),
    "Adductors":   (0, 6, 12),
    "Calves":      (6, 12, 20),
    "Core":        (0, 8, 16),
    "Lower Back":  (0, 6, 12),
}

# Catalogue muscle names that roll up into one canonical group, so "Upper Chest"
# and "Lower Chest" both count toward Chest instead of fragmenting the analysis.
MUSCLE_ALIASES: dict[str, str] = {
    "upper chest": "Chest",
    "lower chest": "Chest",
    "chest": "Chest",
    "pecs": "Chest",
    "front delts": "Front Delts",
    "anterior delts": "Front Delts",
    "side delts": "Side Delts",
    "lateral delts": "Side Delts",
    "rear delts": "Rear Delts",
    "posterior delts": "Rear Delts",
    "shoulders": "Front Delts",
    "lats": "Lats",
    "back": "Lats",
    "traps": "Traps",
    "biceps": "Biceps",
    "triceps": "Triceps",
    "forearms": "Forearms",
    "quads": "Quads",
    "quadriceps": "Quads",
    "hamstrings": "Hamstrings",
    "glutes": "Glutes",
    "adductors": "Adductors",
    "calves": "Calves",
    "core": "Core",
    "abs": "Core",
    "lower back": "Lower Back",
}


def canonical_muscle(name: str | None) -> str | None:
    """Map a catalogue muscle label to its canonical group, or None if unknown."""
    if not name:
        return None
    return MUSCLE_ALIASES.get(name.strip().lower())


def set_credits(primary_muscle: str | None, secondary_muscles: str | None) -> dict[str, float]:
    """Fractional-set credit for one working set.

    1.0 to the primary muscle, 0.5 to each secondary muscle. Unknown muscle
    labels are ignored rather than guessed at.
    """
    credits: dict[str, float] = {}
    primary = canonical_muscle(primary_muscle)
    if primary:
        credits[primary] = credits.get(primary, 0.0) + 1.0
    for raw in (secondary_muscles or "").split(","):
        sec = canonical_muscle(raw)
        if sec and sec != primary:
            credits[sec] = credits.get(sec, 0.0) + 0.5
    return credits


def landmark_status(sets: float, muscle: str) -> str:
    """Where a weekly set count sits relative to the landmarks (spec 33)."""
    mev, mav, mrv = MUSCLE_LANDMARKS.get(muscle, (0, 0, 0))
    if sets <= 0:
        return "none"
    if sets < mev:
        return "below_mev"
    if sets < mav * 0.8:
        return "maintenance"
    if sets <= mrv:
        return "optimal"
    return "above_mrv"


def volume_analysis(
    weekly_sets: dict[str, float], weeks: int = 1
) -> list[dict]:
    """One row per trained (or known) muscle group, sorted most-trained first.

    `weekly_sets` holds total fractional sets over the whole window; dividing by
    `weeks` gives the per-week figure the landmarks are defined against.
    """
    rows = []
    for muscle, (mev, mav, mrv) in MUSCLE_LANDMARKS.items():
        total = weekly_sets.get(muscle, 0.0)
        per_week = round(total / max(weeks, 1), 1)
        rows.append({
            "muscle": muscle,
            "sets_per_week": per_week,
            "mev": mev,
            "mav": mav,
            "mrv": mrv,
            "status": landmark_status(per_week, muscle),
        })
    rows.sort(key=lambda r: r["sets_per_week"], reverse=True)
    return rows
