"""Workout logging, previous-session lookup, PR detection, calendar (spec 31-37)."""
from datetime import date, timedelta

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.calculations.training import best_e1rm, session_volume
from app.models.training import (
    ExerciseLibrary, ExerciseSet, PersonalRecord, TrainingProgram, TrainingProgramDay,
    Workout, WorkoutExercise,
)


def last_session(db: Session, user_id: int, exercise_id: int) -> dict | None:
    """The most recent completed exposure to an exercise, so the user never has to
    remember their previous weights (spec 32)."""
    we = db.scalar(
        select(WorkoutExercise)
        .join(Workout, Workout.id == WorkoutExercise.workout_id)
        .options(selectinload(WorkoutExercise.sets), selectinload(WorkoutExercise.workout))
        .where(WorkoutExercise.exercise_id == exercise_id, Workout.user_id == user_id)
        .order_by(Workout.performed_on.desc(), Workout.id.desc())
        .limit(1)
    )
    if we is None:
        return None
    sets = [{"weight_kg": float(s.weight_kg) if s.weight_kg is not None else None,
             "reps": s.reps, "is_warmup": s.is_warmup, "rir": float(s.rir) if s.rir is not None else None,
             "set_type": s.set_type} for s in we.sets]
    return {
        "performed_on": we.workout.performed_on,
        "title": we.workout.title,
        "sets": sets,
        "notes": we.notes or we.workout.notes,
        "volume": session_volume(sets),
        "best_e1rm": best_e1rm(sets),
    }


def save_workout(db: Session, user_id: int, payload: dict, exercises: list[dict]) -> Workout:
    workout = Workout(
        user_id=user_id,
        program_id=payload.get("program_id"),
        performed_on=payload["performed_on"],
        title=payload["title"],
        status=payload.get("status", "completed"),
        duration_min=payload.get("duration_min"),
        notes=payload.get("notes"),
    )
    db.add(workout)
    db.flush()
    for ex in exercises:
        if db.get(ExerciseLibrary, ex["exercise_id"]) is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, f"Exercise {ex['exercise_id']} not found")
        we = WorkoutExercise(
            workout_id=workout.id, exercise_id=ex["exercise_id"],
            position=ex.get("position", 0), notes=ex.get("notes"),
        )
        db.add(we)
        db.flush()
        for s in ex.get("sets", []):
            db.add(ExerciseSet(
                workout_exercise_id=we.id, set_index=s["set_index"],
                weight_kg=s.get("weight_kg"), reps=s.get("reps"), rpe=s.get("rpe"),
                rir=s.get("rir"), set_type=s.get("set_type") or "normal",
                rest_sec=s.get("rest_sec"), is_warmup=s.get("is_warmup", False),
            ))
    db.commit()
    db.refresh(workout)
    update_personal_records(db, user_id, workout)
    return workout


def update_personal_records(db: Session, user_id: int, workout: Workout) -> list[dict]:
    """Record a new PR only when the value actually beats the stored best (spec 34)."""
    new_prs = []
    for we in workout.exercises:
        sets = [{"weight_kg": float(s.weight_kg) if s.weight_kg is not None else None,
                 "reps": s.reps, "is_warmup": s.is_warmup} for s in we.sets]
        candidates = []
        top_weight = max([s["weight_kg"] or 0 for s in sets if not s["is_warmup"]] or [0])
        if top_weight > 0:
            candidates.append(("weight", top_weight, top_weight, None))
        e1rm = best_e1rm(sets)
        if e1rm:
            candidates.append(("e1rm", e1rm, None, None))
        vol = session_volume(sets)
        if vol > 0:
            candidates.append(("volume", vol, None, None))

        for record_type, value, weight_kg, reps in candidates:
            existing = db.scalar(
                select(PersonalRecord).where(
                    PersonalRecord.user_id == user_id,
                    PersonalRecord.exercise_id == we.exercise_id,
                    PersonalRecord.record_type == record_type,
                )
            )
            if existing is None:
                db.add(PersonalRecord(
                    user_id=user_id, exercise_id=we.exercise_id, record_type=record_type,
                    value=value, weight_kg=weight_kg, reps=reps,
                    achieved_on=workout.performed_on, workout_id=workout.id,
                ))
                new_prs.append({"exercise_id": we.exercise_id, "type": record_type, "value": value})
            elif value > float(existing.value):
                existing.value = value
                existing.weight_kg = weight_kg
                existing.reps = reps
                existing.achieved_on = workout.performed_on
                existing.workout_id = workout.id
                new_prs.append({"exercise_id": we.exercise_id, "type": record_type, "value": value})
    db.commit()
    return new_prs


def calendar(db: Session, user_id: int, year: int, program_id: int | None = None) -> list[dict]:
    """Status per day for the heatmap. 'rest' comes from the active program's rest days;
    'none' means no plan and no session - never an invented status (spec 36, 37)."""
    start, end = date(year, 1, 1), date(year, 12, 31)
    workouts = list(
        db.scalars(
            select(Workout).where(
                Workout.user_id == user_id,
                Workout.performed_on >= start,
                Workout.performed_on <= end,
            )
        )
    )
    by_day: dict[date, Workout] = {}
    for w in workouts:
        by_day[w.performed_on] = w

    rest_weekdays: set[int] = set()
    prog = db.get(TrainingProgram, program_id) if program_id else db.scalar(
        select(TrainingProgram).where(TrainingProgram.user_id == user_id, TrainingProgram.is_active == True)  # noqa: E712
    )
    if prog:
        days = db.scalars(select(TrainingProgramDay).where(TrainingProgramDay.program_id == prog.id))
        rest_weekdays = {d.day_index for d in days if d.is_rest}

    out = []
    d = start
    while d <= end:
        w = by_day.get(d)
        if w:
            status_ = w.status if w.status in ("completed", "modified", "skipped") else "completed"
        elif d.weekday() in rest_weekdays:
            status_ = "rest"
        else:
            status_ = "none"
        out.append({
            "day": d.isoformat(),
            "status": status_,
            "workout_id": w.id if w else None,
            "title": w.title if w else None,
        })
        d += timedelta(days=1)
    return out


def yearly_summary(db: Session, user_id: int, year: int) -> dict:
    days = calendar(db, user_id, year)
    completed = sum(1 for d in days if d["status"] in ("completed", "modified"))
    skipped = sum(1 for d in days if d["status"] == "skipped")
    planned = completed + skipped
    weeks = 52.0
    return {
        "year": year,
        "total_sessions": completed,
        "completed": completed,
        "skipped": skipped,
        "rest_days": sum(1 for d in days if d["status"] == "rest"),
        "consistency_pct": round(completed / planned * 100, 1) if planned else None,
        "avg_per_week": round(completed / weeks, 1),
    }
