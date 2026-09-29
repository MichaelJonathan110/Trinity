#!/usr/bin/env python3
"""Seed the rich demo history for EVERY user that lacks it (idempotent).
Lets the preview pane show real charts regardless of which account is signed in.
Usage: python seed_extra.py [email ...]
"""
import sys
from datetime import date, datetime, timedelta, timezone

sys.path.insert(0, ".")

from sqlalchemy import select  # noqa: E402

from app.database.session import SessionLocal  # noqa: E402
from app.models.activity import DailyActivity, StepRecord  # noqa: E402
from app.models.nutrition import Food, Meal, MealItem  # noqa: E402
from app.models.recovery import RecoveryMetric, SleepGoal, SleepSession  # noqa: E402
from app.models.training import (  # noqa: E402
    ExerciseLibrary, ExerciseSet, Workout, WorkoutExercise,
)
from app.models.user import BodyMetric, Goal, Profile, User  # noqa: E402

PLAN = [
    (2, "Upper A — Push Focus", [
        ("Barbell Bench Press", [(60, 10, True), (80, 8, False), (80, 8, False), (82.5, 6, False)]),
        ("Overhead Press", [(40, 10, False), (45, 8, False), (45, 7, False)]),
        ("Incline Dumbbell Press", [(26, 12, False), (28, 10, False), (28, 9, False)]),
        ("Lateral Raise", [(10, 15, False), (10, 15, False), (12, 12, False)]),
        ("Triceps Pushdown", [(30, 14, False), (32, 12, False), (32, 11, False)]),
    ]),
    (4, "Lower A — Squat Focus", [
        ("Barbell Back Squat", [(60, 8, True), (100, 8, False), (110, 6, False), (115, 5, False)]),
        ("Romanian Deadlift", [(80, 10, False), (90, 8, False), (95, 8, False)]),
        ("Leg Press", [(140, 12, False), (160, 12, False), (160, 10, False)]),
        ("Leg Curl, lying", [(45, 12, False), (50, 10, False), (50, 10, False)]),
        ("Standing Calf Raise", [(60, 15, False), (70, 14, False), (70, 12, False)]),
    ]),
    (1, "Upper B — Pull Focus", [
        ("Pull-Up", [(0, 10, False), (0, 9, False), (0, 8, False)]),
        ("Barbell Row", [(60, 10, False), (70, 8, False), (70, 8, False)]),
        ("Seated Cable Row", [(55, 12, False), (60, 10, False), (60, 10, False)]),
        ("Face Pull", [(25, 15, False), (27.5, 15, False), (27.5, 12, False)]),
        ("Barbell Curl", [(30, 12, False), (35, 10, False), (35, 9, False)]),
    ]),
]

MEALS = [
    ("breakfast", [("Oats, rolled, dry", 80), ("Milk, semi-skimmed", 250),
                   ("Blueberries, raw", 100), ("Whey protein isolate, powder", 30)]),
    ("lunch", [("Chicken breast, skinless, raw", 200), ("White rice, cooked", 200),
               ("Broccoli, steamed", 150), ("Olive oil, extra virgin", 10)]),
    ("dinner", [("Salmon, Atlantic, farmed, raw", 180), ("Sweet potato, baked", 200),
                ("Spinach, raw", 60)]),
    ("snacks", [("Greek yogurt, plain, 0% fat", 170), ("Almonds, raw", 28),
                ("Banana, raw", 118)]),
]


def ensure_profile(db, user):
    prof = db.scalar(select(Profile).where(Profile.user_id == user.id))
    if prof is None:
        prof = Profile(
            user_id=user.id, display_name=user.email.split("@")[0].title(),
            birth_date=date(1995, 4, 12), sex="male", height_cm=180.0, body_fat_pct=15.5,
            training_experience="intermediate", training_frequency=4, session_minutes=70,
            activity_level="moderately_active", units="metric", timezone="Europe/London",
        )
        db.add(prof)
        db.flush()
    if not db.scalar(select(Goal).where(Goal.profile_id == prof.id)):
        db.add(Goal(profile_id=prof.id, goal_type="lean_bulk", rate_kg_per_week=0.25,
                    target_weight_kg=84.0, started_on=date.today() - timedelta(days=28)))
    if not db.scalar(select(SleepGoal).where(SleepGoal.user_id == user.id)):
        db.add(SleepGoal(user_id=user.id, target_minutes=480))
    db.commit()


def seed_body(db, user):
    start_w = 80.0
    n = 0
    for i in range(14, -1, -1):
        d = date.today() - timedelta(days=i)
        if not db.scalar(select(BodyMetric).where(
                BodyMetric.user_id == user.id, BodyMetric.measured_on == d)):
            db.add(BodyMetric(
                user_id=user.id, measured_on=d,
                weight_kg=round(start_w + (14 - i) * 0.05, 2),
                body_fat_pct=round(15.5 - (14 - i) * 0.04, 1),
                waist_cm=round(82.0 - (14 - i) * 0.05, 2),
            ))
            n += 1
    return n


def seed_days(db, user):
    n = 0
    for i in range(7, -1, -1):
        d = date.today() - timedelta(days=i)
        wake = datetime.combine(d, datetime.min.time(), tzinfo=timezone.utc).replace(hour=6, minute=45)
        bed = wake - timedelta(minutes=440 + (i % 4) * 25)
        if not db.scalar(select(SleepSession).where(
                SleepSession.user_id == user.id, SleepSession.slept_on == d)):
            db.add(SleepSession(
                user_id=user.id, slept_on=d, bedtime=bed, wake_at=wake,
                duration_min=int((wake - bed).total_seconds() // 60),
                quality=3 + (i % 3), source="manual",
            ))
            n += 1
        if not db.scalar(select(StepRecord).where(
                StepRecord.user_id == user.id, StepRecord.recorded_on == d)):
            steps = 8200 + (i * 431) % 5200
            db.add(StepRecord(
                user_id=user.id, recorded_on=d, steps=steps,
                distance_m=round(steps * 0.78, 1), active_kcal=round(steps * 0.04, 1),
                active_minutes=int(steps / 110), source="manual",
            ))
            db.add(DailyActivity(user_id=user.id, recorded_on=d, step_goal=10000))
        if not db.scalar(select(RecoveryMetric).where(
                RecoveryMetric.user_id == user.id, RecoveryMetric.recorded_on == d)):
            db.add(RecoveryMetric(
                user_id=user.id, recorded_on=d, subjective_score=3 + (i % 3),
                soreness_score=2 + (i % 3), resting_hr=52 + (i % 6),
                hrv_ms=round(58 + (i % 9) * 2.5, 1),
            ))
    return n


def seed_training(db, user):
    if db.scalar(select(Workout).where(Workout.user_id == user.id)):
        return 0
    lib = {e.name: e for e in db.scalars(select(ExerciseLibrary)).all()}
    n = 0
    for days_ago, title, exercises in PLAN:
        d = date.today() - timedelta(days=days_ago)
        w = Workout(user_id=user.id, performed_on=d, title=title, status="completed",
                    duration_min=68,
                    started_at=datetime.combine(d, datetime.min.time(), tzinfo=timezone.utc).replace(hour=18),
                    finished_at=datetime.combine(d, datetime.min.time(), tzinfo=timezone.utc).replace(hour=19, minute=8))
        db.add(w)
        db.flush()
        for pos, (ex_name, sets) in enumerate(exercises):
            we = WorkoutExercise(workout_id=w.id, exercise_id=lib[ex_name].id, position=pos)
            db.add(we)
            db.flush()
            for si, (kg, reps, warm) in enumerate(sets):
                db.add(ExerciseSet(workout_exercise_id=we.id, set_index=si,
                                   weight_kg=kg or None, reps=reps, rpe=None,
                                   rest_sec=120, is_warmup=warm))
        n += 1
    return n


def seed_meals(db, user):
    if db.scalar(select(Meal).where(Meal.user_id == user.id)):
        return 0
    foods = {f.name: f for f in db.scalars(select(Food)).all()}
    today = date.today()
    n = 0
    for cat, items in MEALS:
        m = Meal(user_id=user.id, logged_on=today, category=cat)
        db.add(m)
        db.flush()
        for fname, grams in items:
            food = foods[fname]
            fac = grams / 100.0
            db.add(MealItem(
                meal_id=m.id, food_id=food.id, quantity_g=grams, serving_label=f"{grams} g",
                kcal=round(float(food.calories_kcal) * fac, 2),
                protein_g=round(float(food.protein_g) * fac, 2),
                carbs_g=round(float(food.carbs_g) * fac, 2),
                fat_g=round(float(food.fat_g) * fac, 2),
            ))
        n += 1
    return n


def main():
    db = SessionLocal()
    try:
        users = list(db.scalars(select(User)).all())
        wanted = set(sys.argv[1:])
        for u in users:
            if wanted and u.email not in wanted:
                continue
            ensure_profile(db, u)
            b = seed_body(db, u)
            d = seed_days(db, u)
            w = seed_training(db, u)
            m = seed_meals(db, u)
            db.commit()
            print(f"{u.email}: body+{b} days+{d} workouts+{w} meals+{m}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
