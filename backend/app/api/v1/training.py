"""Exercise library, workouts, programs, calendar, PRs (spec 29-39)."""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user
from app.database.session import get_db
from app.models.training import (
    ExerciseLibrary, PersonalRecord, TrainingProgram, TrainingProgramDay, Workout, WorkoutExercise,
)
from app.models.user import User
from app.schemas.training import (
    ExerciseOut, ProgramIn, ProgramOut, WorkoutExerciseCreate, WorkoutIn, WorkoutOut,
)
from app.services import training_service, volume_service

router = APIRouter(prefix="/training", tags=["training"])

# How each stored record type is described to the user. The raw type is jargon
# ("e1rm", "volume"), so every PR is sent with a plain label, its unit and a
# one-line explanation - the API does the translation once, not each client.
PR_META: dict[str, dict[str, str]] = {
    "weight": {
        "label": "Heaviest weight",
        "unit": "kg",
        "detail": "The heaviest load lifted for any set of this exercise.",
    },
    "e1rm": {
        "label": "Estimated 1RM",
        "unit": "kg",
        "detail": "Best estimated one-rep max from the weight and reps logged. An estimate, not a tested max.",
    },
    "volume": {
        "label": "Best session volume",
        "unit": "kg",
        "detail": "Most total weight moved in a single session: every rep times its load, added up.",
    },
    "reps": {
        "label": "Most reps",
        "unit": "reps",
        "detail": "Highest number of reps completed in one set of this exercise.",
    },
}


def _program_dict(p: TrainingProgram) -> dict:
    """One serialisation shape for a program, used by every program endpoint.

    Returning the ORM object directly against a response_model whose `days` was
    typed `list[dict]` made POST /training/programs fail response validation with
    a 500, so "save program" never worked. Building the dict here (days as plain
    objects) keeps create, list and activate identical and fixes that.
    """
    days = sorted(p.days, key=lambda d: d.day_index)
    return {
        "id": p.id,
        "name": p.name,
        "description": p.description,
        "goal": p.goal,
        "weeks": p.weeks,
        "is_active": p.is_active,
        "template_slug": p.template_slug,
        "source_name": p.source_name,
        "source_url": p.source_url,
        "attribution_note": p.attribution_note,
        "days": [
            {"day_index": d.day_index, "title": d.title, "is_rest": d.is_rest}
            for d in days
        ],
    }


@router.get("/exercises")
def list_exercises(
    q: str = Query(default="", max_length=60),
    muscle: str | None = None,
    limit: int = Query(default=60, ge=1, le=200),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list:
    stmt = select(ExerciseLibrary)
    if q:
        like = f"%{q.lower()}%"
        stmt = stmt.where(or_(func.lower(ExerciseLibrary.name).like(like),
                              func.lower(ExerciseLibrary.primary_muscle).like(like)))
    if muscle:
        stmt = stmt.where(ExerciseLibrary.primary_muscle == muscle)
    rows = db.scalars(stmt.order_by(ExerciseLibrary.primary_muscle, ExerciseLibrary.name).limit(limit))
    return [ExerciseOut.model_validate(r).model_dump() for r in rows]


@router.get("/exercises/{exercise_id}/last-session")
def last_session(
    exercise_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> dict:
    """The previous performance for this exercise, so the user never has to remember it (spec 32)."""
    result = training_service.last_session(db, user.id, exercise_id)
    if result is None:
        return {"exists": False, "note": "No previous session logged for this exercise."}
    return {"exists": True, **result, "performed_on": result["performed_on"].isoformat()}


@router.get("/workouts")
def list_workouts(
    days: int = Query(default=90, ge=1, le=800),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list:
    from datetime import timedelta
    start = date.today() - timedelta(days=days)
    rows = db.scalars(
        select(Workout)
        .options(selectinload(Workout.exercises).selectinload(WorkoutExercise.sets))
        .where(Workout.user_id == user.id, Workout.performed_on >= start)
        .order_by(Workout.performed_on.desc())
    )
    return [
        {"id": w.id, "performed_on": w.performed_on.isoformat(), "title": w.title,
         "status": w.status, "duration_min": w.duration_min, "notes": w.notes,
         "exercises": len(w.exercises),
         "sets": sum(len(e.sets) for e in w.exercises)}
        for w in rows
    ]


@router.post("/workouts", response_model=WorkoutOut, status_code=status.HTTP_201_CREATED)
def create_workout(
    payload: dict, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> object:
    """payload: {workout fields..., exercises: [{exercise_id, position, notes, sets: [...]}]}
    Sets, volume and PRs are all derived from what is actually logged (spec 31-34)."""
    try:
        base = WorkoutIn(**{k: v for k, v in payload.items() if k != "exercises"})
        exercises = [WorkoutExerciseCreate(**e) for e in payload.get("exercises", [])]
    except Exception as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc))
    if not exercises:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "A workout needs at least one exercise")
    workout = training_service.save_workout(
        db, user.id, base.model_dump(), [e.model_dump() for e in exercises]
    )
    return workout


@router.get("/workouts/{workout_id}")
def get_workout(
    workout_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> dict:
    w = db.scalar(
        select(Workout)
        .options(selectinload(Workout.exercises).selectinload(WorkoutExercise.sets))
        .where(Workout.id == workout_id)
    )
    if w is None or w.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Workout not found")
    return WorkoutOut.model_validate(w).model_dump()


@router.delete("/workouts/{workout_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workout(
    workout_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> None:
    w = db.get(Workout, workout_id)
    if w is None or w.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Workout not found")
    db.delete(w)
    db.commit()


@router.get("/programs")
def list_programs(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list:
    rows = db.scalars(
        select(TrainingProgram)
        .options(selectinload(TrainingProgram.days))
        .where(TrainingProgram.user_id == user.id)
        .order_by(TrainingProgram.is_active.desc(), TrainingProgram.name)
    )
    return [_program_dict(p) for p in rows]


@router.post("/programs", response_model=ProgramOut, status_code=status.HTTP_201_CREATED)
def create_program(
    payload: ProgramIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> object:
    program = TrainingProgram(
        user_id=user.id, name=payload.name, description=payload.description,
        goal=payload.goal, weeks=payload.weeks,
    )
    db.add(program)
    db.flush()
    import json as _json
    for d in payload.days:
        db.add(TrainingProgramDay(
            program_id=program.id, day_index=d.day_index, title=d.title,
            is_rest=d.is_rest, exercise_ids=_json.dumps(d.exercise_ids),
        ))
    db.commit()
    db.refresh(program)
    return _program_dict(program)


@router.post("/programs/{program_id}/activate", status_code=status.HTTP_200_OK)
def activate_program(
    program_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> dict:
    program = db.get(TrainingProgram, program_id)
    if program is None or program.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Program not found")
    for p in db.scalars(select(TrainingProgram).where(TrainingProgram.user_id == user.id)):
        p.is_active = False
    program.is_active = True
    db.commit()
    return {"ok": True, "active_program_id": program.id}


@router.delete("/programs/{program_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_program(
    program_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> None:
    program = db.get(TrainingProgram, program_id)
    if program is None or program.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Program not found")
    db.delete(program)
    db.commit()


@router.get("/calendar")
def calendar(
    year: int = Query(default_factory=lambda: date.today().year, ge=2000, le=2100),
    program_id: int | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list:
    return training_service.calendar(db, user.id, year, program_id)


@router.get("/summary")
def yearly_summary(
    year: int = Query(default_factory=lambda: date.today().year, ge=2000, le=2100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    return training_service.yearly_summary(db, user.id, year)


@router.get("/prs")
def list_prs(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list:
    """Personal records with the exercise name and a plain-language label.

    Each record carries `exercise_name` and a `label`/`unit`/`detail` triple so a
    client can render "Bench press - Estimated 1RM - 112.5 kg" without knowing
    what `record_type` values exist or what they mean.
    """
    rows = list(
        db.scalars(
            select(PersonalRecord)
            .where(PersonalRecord.user_id == user.id)
            .order_by(PersonalRecord.achieved_on.desc())
        )
    )
    names = {
        e.id: e.name
        for e in db.scalars(
            select(ExerciseLibrary).where(
                ExerciseLibrary.id.in_({r.exercise_id for r in rows} or {-1})
            )
        )
    }
    out = []
    for r in rows:
        meta = PR_META.get(r.record_type, {})
        out.append({
            "id": r.id,
            "exercise_id": r.exercise_id,
            "exercise_name": names.get(r.exercise_id),
            "record_type": r.record_type,
            "label": meta.get("label", r.record_type),
            "unit": meta.get("unit", ""),
            "detail": meta.get("detail"),
            "value": float(r.value),
            "weight_kg": float(r.weight_kg) if r.weight_kg else None,
            "reps": r.reps,
            "achieved_on": r.achieved_on.isoformat(),
        })
    return out


@router.get("/progression/{exercise_id}")
def progression(
    exercise_id: int,
    days: int = Query(default=180, ge=7, le=800),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list:
    """Per-session volume and best estimated 1RM for one exercise (spec 33)."""
    from datetime import timedelta
    from app.calculations.training import best_e1rm, session_volume
    start = date.today() - timedelta(days=days)
    rows = db.scalars(
        select(WorkoutExercise)
        .join(Workout, Workout.id == WorkoutExercise.workout_id)
        .options(selectinload(WorkoutExercise.sets), selectinload(WorkoutExercise.workout))
        .where(
            WorkoutExercise.exercise_id == exercise_id,
            Workout.user_id == user.id,
            Workout.performed_on >= start,
        )
        .order_by(Workout.performed_on)
    )
    out = []
    for we in rows:
        sets = [{"weight_kg": float(s.weight_kg) if s.weight_kg is not None else None,
                 "reps": s.reps, "is_warmup": s.is_warmup} for s in we.sets]
        out.append({
            "date": we.workout.performed_on.isoformat(),
            "volume": session_volume(sets),
            "best_e1rm": best_e1rm(sets),
            "top_weight": max([s["weight_kg"] or 0 for s in sets] or [0]) or None,
        })
    return out


@router.get("/volume")
def weekly_volume(
    weeks: int = Query(default=4, ge=1, le=26),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Fractional weekly sets per muscle group against MEV/MAV/MRV landmarks (spec 33)."""
    return volume_service.weekly_volume(db, user.id, weeks)


@router.get("/progression/{exercise_id}/advice")
def progression_advice(
    exercise_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> dict:
    """Concrete next step for one exercise: add load, add reps, or hold (spec 33)."""
    return volume_service.progression_advice(db, user.id, exercise_id)
