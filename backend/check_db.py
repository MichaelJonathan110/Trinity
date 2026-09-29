#!/usr/bin/env python3
"""Count seeded history rows per user straight from the DB (no credentials)."""
import sys

sys.path.insert(0, ".")

from sqlalchemy import func, select  # noqa: E402

from app.database.session import SessionLocal  # noqa: E402
from app.models.activity import StepRecord  # noqa: E402
from app.models.nutrition import Meal, MealItem  # noqa: E402
from app.models.recovery import SleepSession  # noqa: E402
from app.models.training import ExerciseSet, Workout, WorkoutExercise  # noqa: E402
from app.models.user import BodyMetric, User  # noqa: E402

db = SessionLocal()
try:
    for u in db.scalars(select(User)).all():
        def c(model):
            return db.scalar(select(func.count()).select_from(model).where(model.user_id == u.id))
        print(f"{u.email}")
        print(f"  workouts={c(Workout)} sleep={c(SleepSession)} steps={c(StepRecord)}")
        print(f"  meals={c(Meal)} body_metrics={c(BodyMetric)}")
        wid = db.scalars(select(Workout.id).where(Workout.user_id == u.id)).all()
        if wid:
            sets = db.scalar(select(func.count()).select_from(ExerciseSet).where(
                ExerciseSet.workout_exercise_id.in_(
                    select(WorkoutExercise.id).where(WorkoutExercise.workout_id.in_(wid)))))
            items = db.scalar(select(func.count()).select_from(MealItem).where(
                MealItem.meal_id.in_(select(Meal.id).where(Meal.user_id == u.id))))
            print(f"  exercise_sets={sets} meal_items={items}")
        for w in db.scalars(select(Workout).where(Workout.user_id == u.id)).all():
            print(f"    workout {w.performed_on} {w.title!r} status={w.status} dur={w.duration_min}")
finally:
    db.close()
