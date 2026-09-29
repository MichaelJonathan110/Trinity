#!/usr/bin/env python3
"""TRINITY seed: food catalogue (per 100 g, USDA-style), exercise library,
and a demo athlete with a week of realistic history.

Idempotent: re-running updates rather than duplicating.
"""
import sys
from datetime import date, datetime, timedelta, timezone

sys.path.insert(0, ".")

from sqlalchemy import select  # noqa: E402

from app.database.base import Base  # noqa: E402
from app.database.session import SessionLocal, engine  # noqa: E402
from app.models.activity import DailyActivity, StepRecord  # noqa: E402
from app.models.nutrition import (  # noqa: E402
    Food, FoodServing, FoodSource, Meal, MealItem,
)
from app.models.recovery import RecoveryMetric, SleepGoal, SleepSession  # noqa: E402
from app.models.training import (  # noqa: E402
    ExerciseLibrary, ExerciseSet, Workout, WorkoutExercise,
)
from app.models.user import BodyMetric, Goal, Profile, User  # noqa: E402
from app.core.security import hash_password  # noqa: E402

# name, kcal, protein, carbs, fat, fiber, serving_g, serving_label
FOODS = [
    ("Chicken breast, skinless, raw", 120, 22.5, 0.0, 2.6, 0.0, 170, "1 breast"),
    ("Chicken thigh, skinless, raw", 143, 19.7, 0.0, 7.1, 0.0, 120, "1 thigh"),
    ("Salmon, Atlantic, farmed, raw", 208, 20.4, 0.0, 13.4, 0.0, 150, "1 fillet"),
    ("Tuna, canned in water, drained", 116, 25.5, 0.0, 0.8, 0.0, 100, "1 can"),
    ("Lean beef mince, 95% raw", 137, 21.4, 0.0, 5.0, 0.0, 120, "1 patty"),
    ("Egg, whole, raw", 143, 12.6, 0.7, 9.5, 0.0, 50, "1 large egg"),
    ("Egg white, raw", 52, 10.9, 0.7, 0.2, 0.0, 33, "1 white"),
    ("Greek yogurt, plain, 0% fat", 59, 10.2, 3.6, 0.4, 0.0, 170, "1 tub"),
    ("Cottage cheese, low-fat 2%", 84, 11.0, 4.3, 2.3, 0.0, 200, "1 cup"),
    ("Milk, semi-skimmed", 47, 3.4, 4.8, 1.6, 0.0, 250, "1 glass"),
    ("Whey protein isolate, powder", 370, 82.0, 4.0, 1.5, 0.0, 30, "1 scoop"),
    ("Tofu, firm, raw", 144, 17.3, 2.8, 8.7, 2.3, 120, "1 block"),
    ("Lentils, cooked", 116, 9.0, 20.1, 0.4, 7.9, 200, "1 cup"),
    ("Chickpeas, cooked", 164, 8.9, 27.4, 2.6, 7.6, 164, "1 cup"),
    ("Black beans, cooked", 132, 8.9, 23.7, 0.5, 8.7, 172, "1 cup"),
    ("White rice, cooked", 130, 2.7, 28.2, 0.3, 0.4, 158, "1 cup"),
    ("Brown rice, cooked", 123, 2.7, 25.6, 1.0, 1.6, 195, "1 cup"),
    ("Pasta, wholewheat, cooked", 124, 5.3, 26.5, 0.5, 3.9, 140, "1 cup"),
    ("Oats, rolled, dry", 379, 13.2, 67.7, 6.5, 10.1, 40, "1 serving"),
    ("Sweet potato, baked", 90, 2.0, 20.7, 0.2, 3.3, 150, "1 medium"),
    ("Potato, boiled", 87, 1.9, 20.1, 0.1, 1.8, 180, "1 medium"),
    ("Broccoli, steamed", 35, 2.4, 7.2, 0.4, 3.3, 90, "1 cup"),
    ("Spinach, raw", 23, 2.9, 3.6, 0.4, 2.2, 30, "1 handful"),
    ("Avocado, raw", 160, 2.0, 8.5, 14.7, 6.7, 150, "1 medium"),
    ("Olive oil, extra virgin", 884, 0.0, 0.0, 100.0, 0.0, 14, "1 tbsp"),
    ("Almonds, raw", 579, 21.2, 21.6, 49.9, 12.5, 28, "1 handful"),
    ("Peanut butter, smooth", 588, 25.1, 20.0, 50.4, 6.0, 32, "2 tbsp"),
    ("Banana, raw", 89, 1.1, 22.8, 0.3, 2.6, 118, "1 medium"),
    ("Apple, raw", 52, 0.3, 13.8, 0.2, 2.4, 182, "1 medium"),
    ("Blueberries, raw", 57, 0.7, 14.5, 0.3, 2.4, 148, "1 cup"),
    ("Strawberries, raw", 32, 0.7, 7.7, 0.3, 2.0, 144, "1 cup"),
    ("Orange, raw", 47, 0.9, 11.8, 0.1, 2.4, 131, "1 medium"),
    ("Dark chocolate, 85%", 598, 7.8, 45.9, 42.6, 11.0, 25, "2 squares"),
    ("Bread, wholemeal", 247, 13.0, 41.0, 3.4, 6.8, 40, "1 slice"),
    ("Hummus, ready-made", 166, 7.9, 14.3, 9.6, 6.0, 50, "2 tbsp"),
]

# name, primary muscle, secondary, equipment, pattern
EXERCISES = [
    ("Barbell Back Squat", "Quads", "Glutes,Hamstrings,Core", "Barbell", "squat"),
    ("Barbell Front Squat", "Quads", "Glutes,Core", "Barbell", "squat"),
    ("Romanian Deadlift", "Hamstrings", "Glutes,Lower Back", "Barbell", "hinge"),
    ("Conventional Deadlift", "Hamstrings", "Glutes,Lower Back,Traps", "Barbell", "hinge"),
    ("Bulgarian Split Squat", "Quads", "Glutes,Core", "Dumbbell", "squat"),
    ("Leg Press", "Quads", "Glutes,Hamstrings", "Machine", "squat"),
    ("Leg Curl, lying", "Hamstrings", "Calves", "Machine", "hinge"),
    ("Leg Extension", "Quads", "", "Machine", "squat"),
    ("Standing Calf Raise", "Calves", "", "Machine", "carry"),
    ("Barbell Bench Press", "Chest", "Front Delts,Triceps", "Barbell", "push"),
    ("Incline Dumbbell Press", "Upper Chest", "Front Delts,Triceps", "Dumbbell", "push"),
    ("Dumbbell Fly", "Chest", "Front Delts", "Dumbbell", "push"),
    ("Dip, weighted", "Chest", "Triceps,Front Delts", "Bodyweight", "push"),
    ("Overhead Press", "Front Delts", "Triceps,Core", "Barbell", "push"),
    ("Lateral Raise", "Side Delts", "", "Dumbbell", "push"),
    ("Pull-Up", "Lats", "Biceps,Core", "Bodyweight", "pull"),
    ("Chin-Up", "Lats", "Biceps", "Bodyweight", "pull"),
    ("Barbell Row", "Lats", "Rear Delts,Biceps", "Barbell", "pull"),
    ("Dumbbell Row", "Lats", "Rear Delts,Biceps", "Dumbbell", "pull"),
    ("Lat Pulldown", "Lats", "Biceps", "Cable", "pull"),
    ("Seated Cable Row", "Lats", "Rear Delts,Biceps", "Cable", "pull"),
    ("Face Pull", "Rear Delts", "Traps", "Cable", "pull"),
    ("Barbell Curl", "Biceps", "Forearms", "Barbell", "pull"),
    ("Incline Dumbbell Curl", "Biceps", "Forearms", "Dumbbell", "pull"),
    ("Triceps Pushdown", "Triceps", "", "Cable", "push"),
    ("Overhead Triceps Extension", "Triceps", "", "Dumbbell", "push"),
    ("Hanging Leg Raise", "Core", "Hip Flexors", "Bodyweight", "core"),
    ("Cable Crunch", "Core", "", "Cable", "core"),
    ("Plank", "Core", "", "Bodyweight", "core"),
    ("Hip Thrust", "Glutes", "Hamstrings", "Barbell", "hinge"),
]


def get_or_create(db, model, defaults=None, **kwargs):
    obj = db.scalar(select(model).filter_by(**kwargs))
    if obj:
        return obj, False
    obj = model(**kwargs, **(defaults or {}))
    db.add(obj)
    db.flush()
    return obj, True


def seed_catalogue(db):
    src, _ = get_or_create(
        db, FoodSource, name="USDA FoodData Central",
        defaults={
            "url": "https://fdc.nal.usda.gov/",
            "license": "Public domain (US Government work)",
            "notes": "Values per 100 g, rounded. Foundation/SR Legacy datasets.",
        },
    )
    foods = 0
    for name, kcal, p, c, f, fib, sg, slabel in FOODS:
        food, created = get_or_create(
            db, Food, name=name,
            defaults={
                "source_id": src.id, "calories_kcal": kcal, "protein_g": p,
                "carbs_g": c, "fat_g": f, "fiber_g": fib,
                "default_serving_g": sg, "default_serving_label": slabel,
                "data_quality": "reported", "is_verified": True,
            },
        )
        if created:
            foods += 1
            db.add(FoodServing(food_id=food.id, label=slabel, grams=sg, is_default=True))
    ex = 0
    for name, pm, sm, eq, pat in EXERCISES:
        _, created = get_or_create(
            db, ExerciseLibrary, name=name,
            defaults={
                "primary_muscle": pm, "secondary_muscles": sm or None,
                "equipment": eq, "movement_pattern": pat,
                "instructions": "Controlled eccentric, full range, brace the core.",
            },
        )
        if created:
            ex += 1
    db.commit()
    return foods, ex


def seed_demo(db):
    email = "demo@trinity.app"
    user = db.scalar(select(User).where(User.email == email))
    if user is None:
        user = User(email=email, password_hash=hash_password("TrinityDemo123!"), is_demo=True)
        db.add(user)
        db.flush()
        db.add(Profile(
            user_id=user.id, display_name="Alex", birth_date=date(1995, 4, 12),
            sex="male", height_cm=180.0, body_fat_pct=15.5,
            training_experience="intermediate", training_frequency=4,
            session_minutes=70, activity_level="moderately_active",
            units="metric", timezone="Europe/London",
        ))
        db.flush()
        prof = user.profile
        db.add(Goal(profile_id=prof.id, goal_type="lean_bulk",
                    rate_kg_per_week=0.25, target_weight_kg=84.0,
                    started_on=date.today() - timedelta(days=28)))
        db.add(SleepGoal(user_id=user.id, target_minutes=480))
        db.commit()
        db.refresh(user)

    # 14 days of body metrics
    start_w = 80.0
    for i in range(14, -1, -1):
        d = date.today() - timedelta(days=i)
        exists = db.scalar(select(BodyMetric).where(
            BodyMetric.user_id == user.id, BodyMetric.measured_on == d))
        if not exists:
            db.add(BodyMetric(
                user_id=user.id, measured_on=d,
                weight_kg=round(start_w + (14 - i) * 0.05, 2),
                body_fat_pct=round(15.5 - (14 - i) * 0.04, 1),
                waist_cm=round(82.0 - (14 - i) * 0.05, 2),
            ))

    # 7 days sleep + steps + recovery
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
        if not db.scalar(select(StepRecord).where(
                StepRecord.user_id == user.id, StepRecord.recorded_on == d)):
            steps = 8200 + (i * 431) % 5200
            db.add(StepRecord(
                user_id=user.id, recorded_on=d, steps=steps,
                distance_m=round(steps * 0.78, 1),
                active_kcal=round(steps * 0.04, 1),
                active_minutes=int(steps / 110), source="manual",
            ))
            db.add(DailyActivity(user_id=user.id, recorded_on=d, step_goal=10000))
        if not db.scalar(select(RecoveryMetric).where(
                RecoveryMetric.user_id == user.id, RecoveryMetric.recorded_on == d)):
            db.add(RecoveryMetric(
                user_id=user.id, recorded_on=d,
                subjective_score=3 + (i % 3), soreness_score=2 + (i % 3),
                resting_hr=52 + (i % 6), hrv_ms=round(58 + (i % 9) * 2.5, 1),
            ))
    db.commit()
    return user


def seed_history(db, user):
    """Three logged workouts + meals for today, so the UI has real data."""
    if db.scalar(select(Workout).where(Workout.user_id == user.id)):
        return 0, 0
    lib = {e.name: e for e in db.scalars(select(ExerciseLibrary)).all()}
    foods = {f.name: f for f in db.scalars(select(Food)).all()}

    plan = [
        (2, "Upper A — Push Focus", [
            ("Barbell Bench Press", [(60, 10, False), (80, 8, False), (80, 8, False), (82.5, 6, False)]),
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
    n_w = 0
    for days_ago, title, exercises in plan:
        d = date.today() - timedelta(days=days_ago)
        w = Workout(user_id=user.id, performed_on=d, title=title,
                    status="completed", duration_min=68,
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
        n_w += 1

    n_m = 0
    today = date.today()
    meals = [
        ("breakfast", [("Oats, rolled, dry", 80), ("Milk, semi-skimmed", 250),
                       ("Blueberries, raw", 100), ("Whey protein isolate, powder", 30)]),
        ("lunch", [("Chicken breast, skinless, raw", 200), ("White rice, cooked", 200),
                   ("Broccoli, steamed", 150), ("Olive oil, extra virgin", 10)]),
        ("dinner", [("Salmon, Atlantic, farmed, raw", 180), ("Sweet potato, baked", 200),
                    ("Spinach, raw", 60)]),
        ("snacks", [("Greek yogurt, plain, 0% fat", 170), ("Almonds, raw", 28),
                    ("Banana, raw", 118)]),
    ]
    for cat, items in meals:
        m = Meal(user_id=user.id, logged_on=today, category=cat)
        db.add(m)
        db.flush()
        for fname, grams in items:
            food = foods[fname]
            fac = grams / 100.0
            db.add(MealItem(
                meal_id=m.id, food_id=food.id, quantity_g=grams,
                serving_label=f"{grams} g",
                kcal=round(float(food.calories_kcal) * fac, 2),
                protein_g=round(float(food.protein_g) * fac, 2),
                carbs_g=round(float(food.carbs_g) * fac, 2),
                fat_g=round(float(food.fat_g) * fac, 2),
            ))
        n_m += 1
    db.commit()
    return n_w, n_m


def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        foods, ex = seed_catalogue(db)
        user = seed_demo(db)
        n_w, n_m = seed_history(db, user)
        print(f"seed: foods+{foods} exercises+{ex} workouts+{n_w} meals+{n_m}")
        print(f"demo login: demo@trinity.app / TrinityDemo123!")
    finally:
        db.close()


if __name__ == "__main__":
    main()
