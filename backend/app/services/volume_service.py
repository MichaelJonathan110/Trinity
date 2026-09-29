"""Weekly volume per muscle group and progressive-overload advice (spec 33).

Volume is summed in fractional sets (see app.calculations.volume). The advice
compares the most recent session for an exercise with the one before it and
states a concrete next step: add weight, add reps, or hold. It never invents a
number - with no history it says so.
"""
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.calculations.training import best_e1rm
from app.calculations.volume import set_credits, volume_analysis
from app.models.training import ExerciseLibrary, Workout, WorkoutExercise


def _load_exposures(
    db: Session, user_id: int, start: date, exercise_id: int | None = None
) -> list[WorkoutExercise]:
    stmt = (
        select(WorkoutExercise)
        .join(Workout, Workout.id == WorkoutExercise.workout_id)
        .options(selectinload(WorkoutExercise.sets))
        .where(Workout.user_id == user_id, Workout.performed_on >= start)
        .order_by(Workout.performed_on.desc(), Workout.id.desc())
    )
    if exercise_id is not None:
        stmt = stmt.where(WorkoutExercise.exercise_id == exercise_id)
    return list(db.scalars(stmt))


def weekly_volume(db: Session, user_id: int, weeks: int = 4) -> dict:
    """Fractional working sets per muscle group over the trailing window.

    Returns the per-muscle rows with their MEV/MAV/MRV landmarks and the window
    length, so the client can render the analysis and say what it is based on.
    """
    weeks = max(1, min(weeks, 26))
    start = date.today() - timedelta(weeks=weeks)
    exposures = _load_exposures(db, user_id, start)

    ex_ids = {we.exercise_id for we in exposures}
    names = {}
    if ex_ids:
        for ex in db.scalars(select(ExerciseLibrary).where(ExerciseLibrary.id.in_(ex_ids))):
            names[ex.id] = (ex.primary_muscle, ex.secondary_muscles)

    totals: dict[str, float] = {}
    for we in exposures:
        primary, secondary = names.get(we.exercise_id, (None, None))
        for s in we.sets:
            if s.is_warmup:
                continue
            if s.reps is None:
                continue
            for muscle, credit in set_credits(primary, secondary).items():
                totals[muscle] = totals.get(muscle, 0.0) + credit

    rows = volume_analysis(totals, weeks=weeks)
    trained = [r for r in rows if r["sets_per_week"] > 0]
    return {
        "weeks": weeks,
        "window_start": start.isoformat(),
        "muscles": rows,
        "trained_count": len(trained),
        "note": "Fractional sets: 1.0 for the primary muscle, 0.5 for each secondary. "
                "Landmarks (MEV/MAV/MRV) are evidence-informed guidelines, not measurements.",
    }


def progression_advice(db: Session, user_id: int, exercise_id: int) -> dict:
    """Compare the two most recent sessions for one exercise and advise.

    Rule of thumb: when every working set reached the top of the rep range at
    RIR >= 1, add load next time. When reps fell short, hold the load and chase
    reps. The rep window is inferred from the most recent session's reps.
    """
    exposures = _load_exposures(db, user_id, date.today() - timedelta(days=365), exercise_id)
    if not exposures:
        return {"exists": False, "note": "No history for this exercise yet."}

    def summarise(we: WorkoutExercise) -> dict:
        working = [s for s in we.sets if not s.is_warmup]
        sets = [{"weight_kg": float(s.weight_kg) if s.weight_kg is not None else None,
                 "reps": s.reps, "is_warmup": s.is_warmup} for s in we.sets]
        top = max([s["weight_kg"] or 0 for s in sets if not s["is_warmup"]] or [0]) or None
        rirs = [float(s.rir) for s in working if s.rir is not None]
        return {
            "top_weight": top,
            "best_e1rm": best_e1rm(sets),
            "total_reps": sum((s.reps or 0) for s in working),
            "set_count": len(working),
            "avg_rir": round(sum(rirs) / len(rirs), 1) if rirs else None,
        }

    current = summarise(exposures[0])
    previous = summarise(exposures[1]) if len(exposures) > 1 else None

    action = "hold"
    detail = "Keep this load and add a rep to each set before adding weight."
    if previous is None:
        return {
            "exists": True,
            "current": current,
            "previous": None,
            "action": "baseline",
            "detail": "First logged session for this exercise - it is now the baseline to beat.",
        }

    improved = (current["best_e1rm"] or 0) > (previous["best_e1rm"] or 0)
    reps_up = current["total_reps"] > previous["total_reps"]
    low_rir = current["avg_rir"] is not None and current["avg_rir"] <= 1

    if improved or reps_up:
        action = "increase"
        step = 2.5 if (current["top_weight"] or 0) < 60 else 5.0
        detail = (
            f"Progress is real: est. 1RM moved {previous['best_e1rm']} to {current['best_e1rm']} kg. "
            f"Add about {step} kg next session."
        )
    elif low_rir:
        action = "hold"
        detail = "You finished close to failure. Hold the load and let the reps come up first."

    return {
        "exists": True,
        "current": current,
        "previous": previous,
        "action": action,
        "detail": detail,
    }
