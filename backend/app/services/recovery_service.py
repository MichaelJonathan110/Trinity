"""Sleep logging, trends, and readiness (spec 23-28). All outputs are estimates."""
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.calculations.recovery import consistency_score, readiness_score, sleep_duration_minutes, sleep_score
from app.models.activity import StepRecord
from app.models.recovery import RecoveryMetric, SleepGoal, SleepSession
from app.models.training import Workout


def log_sleep(db: Session, user_id: int, payload: dict) -> SleepSession:
    duration = sleep_duration_minutes(payload["bedtime"], payload["wake_at"])
    session = SleepSession(
        user_id=user_id,
        slept_on=payload["wake_at"].date(),
        bedtime=payload["bedtime"],
        wake_at=payload["wake_at"],
        duration_min=duration,
        quality=payload.get("quality"),
        is_nap=payload.get("is_nap", False),
        source="manual",
        notes=payload.get("notes"),
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def sleep_goal(db: Session, user_id: int) -> SleepGoal:
    goal = db.scalar(select(SleepGoal).where(SleepGoal.user_id == user_id))
    if goal is None:
        goal = SleepGoal(user_id=user_id, target_minutes=480)
        db.add(goal)
        db.commit()
        db.refresh(goal)
    return goal


def sleep_history(db: Session, user_id: int, days: int) -> list[dict]:
    start = date.today() - timedelta(days=days - 1)
    rows = list(
        db.scalars(
            select(SleepSession)
            .where(SleepSession.user_id == user_id, SleepSession.slept_on >= start, SleepSession.is_nap == False)  # noqa: E712
            .order_by(SleepSession.slept_on)
        )
    )
    goal = sleep_goal(db, user_id).target_minutes
    return [
        {
            "date": r.slept_on.isoformat(),
            "duration_min": r.duration_min,
            "quality": r.quality,
            "score": sleep_score(r.duration_min, goal, r.quality),
            "bedtime": r.bedtime.isoformat(),
            "wake_at": r.wake_at.isoformat(),
        }
        for r in rows
    ]


def recent_average(db: Session, user_id: int, days: int) -> dict:
    hist = sleep_history(db, user_id, days)
    if not hist:
        return {"days": 0, "avg_minutes": None, "avg_score": None, "consistency": None}
    return {
        "days": len(hist),
        "avg_minutes": round(sum(h["duration_min"] for h in hist) / len(hist)),
        "avg_score": round(sum(h["score"] for h in hist) / len(hist)),
        "consistency": consistency_score([_bedtime_offset(h["bedtime"]) for h in hist]),
    }


def _bedtime_offset(iso: str) -> int:
    """Minutes past 18:00, so a 23:15 bedtime and a 00:40 bedtime compare sensibly."""
    t = iso.split("T")[1][:5]
    h, m = int(t[:2]), int(t[3:5])
    minutes = h * 60 + m
    return (minutes - 18 * 60) % (24 * 60)


def compute_readiness(db: Session, user_id: int, day: date | None = None) -> dict:
    day = day or date.today()
    last_sleep = db.scalar(
        select(SleepSession)
        .where(SleepSession.user_id == user_id, SleepSession.slept_on <= day, SleepSession.is_nap == False)  # noqa: E712
        .order_by(SleepSession.slept_on.desc())
        .limit(1)
    )
    goal = sleep_goal(db, user_id).target_minutes
    recent = list(
        db.scalars(
            select(RecoveryMetric)
            .where(RecoveryMetric.user_id == user_id, RecoveryMetric.recorded_on <= day)
            .order_by(RecoveryMetric.recorded_on.desc())
            .limit(1)
        )
    )
    subjective = recent[0].subjective_score if recent else None

    # Days since the most recent rest day (no workout logged).
    days_since_rest = 1
    for i in range(1, 8):
        d = day - timedelta(days=i)
        has = db.scalar(select(Workout.id).where(Workout.user_id == user_id, Workout.performed_on == d))
        if not has:
            days_since_rest = i
            break

    steps_y = db.scalar(
        select(StepRecord.steps).where(StepRecord.user_id == user_id, StepRecord.recorded_on == day - timedelta(days=1))
    )
    result = readiness_score(
        sleep_min=last_sleep.duration_min if last_sleep else None,
        sleep_target=goal,
        days_since_rest=days_since_rest,
        subjective=subjective,
        steps_yesterday=steps_y,
    )
    result["note"] = "TRINITY Training Readiness is an application estimate, not a medical measurement."
    result["sleep_minutes"] = last_sleep.duration_min if last_sleep else None
    result["sleep_target_minutes"] = goal
    return result
