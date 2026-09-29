"""BMR/TDEE/targets. Every number is stored with its inputs and labelled an estimate
(spec 17-20). Nothing here claims to measure metabolism."""
import json
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.calculations.bodycomp import (
    age_from, adaptive_tdee, bmr_mifflin_st_jeor, calorie_target_for_goal,
    estimate_tdee, macro_targets,
)
from app.models.nutrition import NutritionTarget, TdeeEstimate
from app.models.user import BodyMetric, Goal, Profile
from app.services import nutrition_service


def current_goal(db: Session, profile_id: int) -> Goal | None:
    return db.scalar(
        select(Goal).where(Goal.profile_id == profile_id, Goal.is_active == True)  # noqa: E712
        .order_by(Goal.started_on.desc())
    )


def latest_weight(db: Session, user_id: int, on_or_before: date | None = None) -> float | None:
    stmt = select(BodyMetric).where(BodyMetric.user_id == user_id, BodyMetric.weight_kg.is_not(None))
    if on_or_before:
        stmt = stmt.where(BodyMetric.measured_on <= on_or_before)
    row = db.scalar(stmt.order_by(BodyMetric.measured_on.desc()).limit(1))
    return float(row.weight_kg) if row else None


def compute(db: Session, user_id: int, profile: Profile, day: date | None = None) -> dict:
    day = day or date.today()
    weight = latest_weight(db, user_id, day)
    height = float(profile.height_cm) if profile.height_cm is not None else None
    age = age_from(profile.birth_date, day)
    missing = [name for name, v in (
        ("height", height), ("weight", weight), ("age", age), ("sex", profile.sex),
    ) if v is None]
    if missing:
        return {
            "ready": False,
            "missing": missing,
            "note": "Complete these profile fields to estimate your energy needs.",
        }

    bmr = bmr_mifflin_st_jeor(profile.sex or "unspecified", weight, height, age)
    tdee = estimate_tdee(bmr, profile.activity_level or "light")
    goal = current_goal(db, profile.id)
    goal_type = goal.goal_type if goal else "maintain"
    kcal_target = calorie_target_for_goal(tdee, goal_type)
    macros = macro_targets(kcal_target, weight, goal_type)

    # Adaptive refinement from real logs, if there is enough of them.
    window = 28
    hist = nutrition_service.history(db, user_id, window)
    logged = [h for h in hist if h["items"] > 0]
    earliest = day - timedelta(days=window - 1)
    w_start = latest_weight(db, user_id, earliest)
    w_end = weight
    days = len(logged)
    adaptive = adaptive_tdee(
        avg_intake_kcal=(sum(h["kcal"] for h in logged) / days) if days else 0.0,
        weight_change_kg=(w_end - w_start) if (w_start and w_end) else 0.0,
        days=days,
        fallback_tdee=tdee,
    )
    return {
        "ready": True,
        "bmr_kcal": bmr,
        "tdee_kcal": tdee,
        "tdee_method": "mifflin_st_jeor_activity",
        "activity_level": profile.activity_level or "light",
        "goal_type": goal_type,
        "kcal_target": kcal_target,
        "macros": macros,
        "adaptive": adaptive,
        "logged_days": days,
        "note": "Estimated from the Mifflin-St Jeor equation and your logged data. "
                "This is an estimate, not a laboratory measurement.",
    }


def persist(db: Session, user_id: int, result: dict, day: date | None = None) -> TdeeEstimate:
    day = day or date.today()
    adaptive = result.get("adaptive", {})
    row = TdeeEstimate(
        user_id=user_id, estimated_on=day,
        method=adaptive.get("method", result.get("tdee_method", "mifflin_st_jeor_activity")),
        bmr_kcal=result["bmr_kcal"],
        activity_multiplier=None,
        tdee_kcal=adaptive.get("tdee_kcal", result["tdee_kcal"]),
        confidence=adaptive.get("confidence", "low"),
        days_of_data=adaptive.get("days_of_data", 0),
        inputs_json=json.dumps({
            "goal_type": result.get("goal_type"),
            "activity_level": result.get("activity_level"),
            "logged_days": result.get("logged_days"),
        }),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def apply_targets(db: Session, user_id: int, result: dict, day: date | None = None) -> NutritionTarget:
    day = day or date.today()
    m = result["macros"]
    target = NutritionTarget(
        user_id=user_id, effective_from=day, kcal=m["kcal"],
        protein_g=m["protein_g"], carbs_g=m["carbs_g"], fat_g=m["fat_g"], source="calculated",
    )
    db.add(target)
    db.commit()
    db.refresh(target)
    return target
