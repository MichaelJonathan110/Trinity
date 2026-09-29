"""Steps upsert and history (spec 40-42)."""
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.activity import DailyActivity, StepRecord


def upsert_steps(db: Session, user_id: int, payload: dict) -> StepRecord:
    row = db.scalar(
        select(StepRecord).where(
            StepRecord.user_id == user_id, StepRecord.recorded_on == payload["recorded_on"]
        )
    )
    if row is None:
        row = StepRecord(user_id=user_id, source="manual", **payload)
        db.add(row)
    else:
        for k, v in payload.items():
            setattr(row, k, v)
        row.source = "manual"
    db.commit()
    db.refresh(row)
    return row


def step_goal(db: Session, user_id: int) -> int:
    """Default 10,000 is a common convention, not a medical requirement (spec 41)."""
    row = db.scalar(select(DailyActivity).where(DailyActivity.user_id == user_id))
    return row.step_goal if row else 10000


def set_step_goal(db: Session, user_id: int, goal: int) -> int:
    row = db.scalar(
        select(DailyActivity).where(DailyActivity.user_id == user_id, DailyActivity.recorded_on == date.today())
    )
    if row is None:
        row = DailyActivity(user_id=user_id, recorded_on=date.today(), step_goal=goal)
        db.add(row)
    else:
        row.step_goal = goal
    # Keep one settings row per user for simplicity.
    existing = db.scalars(select(DailyActivity).where(DailyActivity.user_id == user_id)).all()
    for e in existing:
        e.step_goal = goal
    db.commit()
    return goal


def day_activity(db: Session, user_id: int, day: date) -> dict:
    row = db.scalar(select(StepRecord).where(StepRecord.user_id == user_id, StepRecord.recorded_on == day))
    return {
        "recorded_on": day,
        "steps": row.steps if row else 0,
        "step_goal": step_goal(db, user_id),
        "distance_m": float(row.distance_m) if row and row.distance_m is not None else None,
        "active_kcal": float(row.active_kcal) if row and row.active_kcal is not None else None,
        "active_minutes": row.active_minutes if row else None,
        "source": row.source if row else "none",
    }


def history(db: Session, user_id: int, days: int) -> list[dict]:
    start = date.today() - timedelta(days=days - 1)
    rows = list(
        db.scalars(
            select(StepRecord).where(StepRecord.user_id == user_id, StepRecord.recorded_on >= start)
        )
    )
    by_day = {r.recorded_on: r for r in rows}
    out = []
    for i in range(days):
        d = start + timedelta(days=i)
        r = by_day.get(d)
        out.append({
            "date": d.isoformat(),
            "steps": r.steps if r else 0,
            "distance_m": float(r.distance_m) if r and r.distance_m is not None else None,
            "active_kcal": float(r.active_kcal) if r and r.active_kcal is not None else None,
            "logged": r is not None,
        })
    return out
