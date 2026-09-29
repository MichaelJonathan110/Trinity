"""Cross-domain insight engine. Every sentence is computed from stored rows (spec 21, 43, 44, 66).
No insight is emitted unless its supporting data exists."""
from datetime import date, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.activity import DailyActivity, StepRecord
from app.models.nutrition import NutritionTarget
from app.models.recovery import SleepSession
from app.models.training import TrainingProgram, TrainingProgramDay, Workout
from app.services import nutrition_service, recovery_service


CATEGORY_LABEL = {
    "breakfast": "breakfast", "lunch": "lunch", "dinner": "dinner",
    "snacks": "snacks", "pre_workout": "pre-workout", "post_workout": "post-workout",
}


def greeting_for(now: datetime) -> str:
    h = now.hour
    if h < 12:
        return "Good morning"
    if h < 18:
        return "Good afternoon"
    return "Good evening"


def _pct(part: float, whole: float) -> int | None:
    if not whole:
        return None
    return int(round(min(part / whole, 1.5) * 100))


def pillar_scores(db: Session, user_id: int, day: date) -> list[dict]:
    totals = nutrition_service.day_totals(db, user_id, day)
    sleep = db.scalar(
        select(SleepSession).where(SleepSession.user_id == user_id, SleepSession.slept_on == day, SleepSession.is_nap == False)  # noqa: E712
    )
    steps = db.scalar(select(StepRecord).where(StepRecord.user_id == user_id, StepRecord.recorded_on == day))
    goal_row = db.scalar(select(DailyActivity).where(DailyActivity.user_id == user_id, DailyActivity.recorded_on == day))
    step_goal = goal_row.step_goal if goal_row else 10000
    workout = db.scalar(select(Workout).where(Workout.user_id == user_id, Workout.performed_on == day))
    sleep_goal_min = recovery_service.sleep_goal(db, user_id).target_minutes

    nutrition_score = _pct(totals["kcal"], totals["target_kcal"] or 0) if totals["target_kcal"] else None
    protein_score = _pct(totals["protein_g"], totals["target_protein_g"] or 0) if totals["target_protein_g"] else None
    return [
        {"key": "nutrition", "label": "Nutrition", "score": nutrition_score,
         "detail": (f"{totals['kcal']:.0f} of {totals['target_kcal']:.0f} kcal logged"
                    if totals["target_kcal"] else f"{totals['kcal']:.0f} kcal logged, no target set")},
        {"key": "protein", "label": "Protein", "score": protein_score,
         "detail": (f"{totals['protein_g']:.0f} g of {totals['target_protein_g']:.0f} g"
                    if totals["target_protein_g"] else "no protein target set")},
        {"key": "rest", "label": "Rest", "score": _pct(sleep.duration_min, sleep_goal_min) if sleep else None,
         "detail": (f"{sleep.duration_min // 60}h {sleep.duration_min % 60:02d}m slept" if sleep else "no sleep logged for this night")},
        {"key": "exercise", "label": "Exercise", "score": 100 if workout and workout.status == "completed" else (60 if workout else None),
         "detail": (workout.title if workout else "no session logged")},
        {"key": "steps", "label": "Activity", "score": _pct(steps.steps, step_goal) if steps else None,
         "detail": (f"{steps.steps:,} of {step_goal:,} steps" if steps else "no step data")},
    ]


def today_insights(db: Session, user_id: int, day: date) -> list[dict]:
    out: list[dict] = []
    totals = nutrition_service.day_totals(db, user_id, day)

    if totals["target_kcal"] and totals["kcal"] > 0:
        remaining = totals["target_kcal"] - totals["kcal"]
        if remaining > 0:
            out.append(_i(day, "nutrition", "info", "Calories remaining",
                          f"{remaining:.0f} kcal left of today's target."))
        else:
            out.append(_i(day, "nutrition", "info", "Calories logged",
                          f"{abs(remaining):.0f} kcal above today's target."))
    if totals["target_protein_g"] and totals["protein_g"] > 0:
        gap = totals["target_protein_g"] - totals["protein_g"]
        if gap > 5:
            out.append(_i(day, "nutrition", "info", "Protein target",
                          f"{gap:.0f} g of protein still to go."))

    logged_categories = {m.category for m in totals["meals"]}
    missing = [CATEGORY_LABEL[c] for c in ("breakfast", "lunch", "dinner") if c not in logged_categories]
    if logged_categories and missing:
        out.append(_i(day, "nutrition", "info", "Meals still open",
                      f"You have logged {', '.join(sorted(CATEGORY_LABEL[c] for c in logged_categories))} "
                      f"but no {', '.join(missing)} yet."))

    # 7-day nutrition consistency vs target.
    hist = nutrition_service.history(db, user_id, 7)
    logged = [h for h in hist if h["items"] > 0]
    if len(logged) >= 3 and totals["target_kcal"]:
        avg_p = sum(h["protein_g"] for h in logged) / len(logged)
        if totals["target_protein_g"] and avg_p < totals["target_protein_g"] * 0.93:
            short = (1 - avg_p / totals["target_protein_g"]) * 100
            out.append(_i(day, "nutrition", "info", "Weekly protein",
                          f"Average protein over {len(logged)} logged days is {short:.0f}% below target."))

    avg_sleep = recovery_service.recent_average(db, user_id, 7)
    if avg_sleep["days"] >= 3 and avg_sleep["avg_minutes"]:
        h, m = divmod(avg_sleep["avg_minutes"], 60)
        out.append(_i(day, "rest", "info", "Weekly sleep",
                      f"Average sleep this week is {h}h {m:02d}m over {avg_sleep['days']} nights."))
        goal_min = recovery_service.sleep_goal(db, user_id).target_minutes
        below = [h2 for h2 in recovery_service.sleep_history(db, user_id, 7) if h2["duration_min"] < goal_min]
        if len(below) >= 3:
            out.append(_i(day, "rest", "warning", "Below sleep target",
                          f"Sleep was under your target on {len(below)} of the last 7 nights."))

    # Recovery + training connection (spec 27).
    readiness = recovery_service.compute_readiness(db, user_id, day)
    yesterday = day - timedelta(days=1)
    y_workout = db.scalar(select(Workout).where(Workout.user_id == user_id, Workout.performed_on == yesterday))
    if y_workout and readiness.get("sleep_minutes") and readiness["sleep_minutes"] < readiness["sleep_target_minutes"]:
        out.append(_i(day, "cross", "info", "Recovery and training",
                      f"You trained ({y_workout.title}) on {yesterday.strftime('%d %b')} and slept "
                      f"{readiness['sleep_minutes'] // 60}h {readiness['sleep_minutes'] % 60:02d}m, "
                      f"below your {readiness['sleep_target_minutes'] // 60}h target."))

    # Steps trend vs previous week.
    this_week = _step_avg(db, user_id, day, 0)
    prev_week = _step_avg(db, user_id, day, 7)
    if this_week and prev_week:
        direction = "increased" if this_week > prev_week else "decreased"
        out.append(_i(day, "steps", "info", "Activity trend",
                      f"Step average {direction} from {prev_week:,.0f} to {this_week:,.0f}."))

    # Training frequency this month.
    month_start = day.replace(day=1)
    count = db.scalar(
        select(func.count(Workout.id)).where(
            Workout.user_id == user_id, Workout.performed_on >= month_start,
            Workout.performed_on <= day, Workout.status.in_(("completed", "modified")),
        )
    )
    if count:
        weeks_elapsed = max((day - month_start).days + 1, 1) / 7
        out.append(_i(day, "exercise", "info", "Training frequency",
                      f"{count} sessions this month ({count / weeks_elapsed:.1f} per week so far)."))

    return out


def _step_avg(db: Session, user_id: int, day: date, back: int) -> float | None:
    end = day - timedelta(days=back)
    start = end - timedelta(days=6)
    rows = list(
        db.scalars(
            select(StepRecord.steps).where(
                StepRecord.user_id == user_id, StepRecord.recorded_on >= start, StepRecord.recorded_on <= end
            )
        )
    )
    return sum(rows) / len(rows) if rows else None


def _i(day: date, domain: str, severity: str, title: str, body: str) -> dict:
    return {"for_date": day, "domain": domain, "severity": severity, "title": title, "body": body}


def headline(db: Session, user_id: int, day: date, pillars: list[dict], readiness: dict) -> str:
    """One honest sentence built from whatever pillars have data (spec 43, 91)."""
    by_key = {p["key"]: p for p in pillars}
    bits: list[str] = []
    if by_key["nutrition"]["score"] is not None:
        s = by_key["nutrition"]["score"]
        bits.append("nutrition is on track" if s >= 80 else f"nutrition is at {s}% of target")
    if by_key["rest"]["score"] is not None:
        s = by_key["rest"]["score"]
        bits.append("sleep is near your target" if s >= 85 else f"sleep reached {s}% of your goal")
    if by_key["exercise"]["score"] is not None:
        bits.append(f"today's session is {by_key['exercise']['detail'].lower()}")
    if by_key["steps"]["score"] is not None:
        bits.append(f"you are at {by_key['steps']['score']}% of your step goal")
    if not bits:
        return "Log your first entry to start building today's picture."
    return "Today: " + ", ".join(bits) + "."
