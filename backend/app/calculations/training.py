"""Training volume and 1RM estimation (spec 33, 34)."""


def set_volume(weight_kg: float | None, reps: int | None) -> float:
    """Volume load = weight x reps. Warm-ups are excluded by the caller."""
    if weight_kg is None or reps is None:
        return 0.0
    return round(float(weight_kg) * int(reps), 2)


def session_volume(sets: list[dict]) -> float:
    return round(
        sum(set_volume(s.get("weight_kg"), s.get("reps")) for s in sets if not s.get("is_warmup")),
        2,
    )


def epley_1rm(weight_kg: float | None, reps: int | None) -> float | None:
    """Epley: 1RM = w * (1 + reps/30). A standard ESTIMATE, not a tested max."""
    if weight_kg is None or reps is None or reps <= 0:
        return None
    return round(float(weight_kg) * (1 + int(reps) / 30.0), 1)


def best_e1rm(sets: list[dict]) -> float | None:
    values = [
        epley_1rm(s.get("weight_kg"), s.get("reps"))
        for s in sets
        if not s.get("is_warmup")
    ]
    values = [v for v in values if v is not None]
    return max(values) if values else None
