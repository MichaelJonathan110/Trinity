"""Sleep and recovery (spec 23-28)."""
from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database.session import get_db
from app.models.recovery import RecoveryMetric
from app.models.user import User
from app.schemas.recovery import RecoveryIn, RecoveryOut, SleepGoalIn, SleepIn, SleepOut
from app.services import recovery_service

router = APIRouter(prefix="/recovery", tags=["recovery"])


@router.post("/sleep", response_model=SleepOut, status_code=status.HTTP_201_CREATED)
def log_sleep(
    payload: SleepIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> object:
    return recovery_service.log_sleep(db, user.id, payload.model_dump())


@router.get("/sleep")
def sleep_history(
    days: int = Query(default=30, ge=1, le=400),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list:
    return recovery_service.sleep_history(db, user.id, days)


@router.get("/sleep/average")
def sleep_average(
    days: int = Query(default=7, ge=1, le=90),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    return recovery_service.recent_average(db, user.id, days)


@router.get("/sleep/goal")
def get_sleep_goal(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    g = recovery_service.sleep_goal(db, user.id)
    return {"target_minutes": g.target_minutes}


@router.put("/sleep/goal")
def set_sleep_goal(
    payload: SleepGoalIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> dict:
    g = recovery_service.sleep_goal(db, user.id)
    g.target_minutes = payload.target_minutes
    db.commit()
    return {"target_minutes": g.target_minutes}


@router.get("/metrics", response_model=list[RecoveryOut])
def list_metrics(
    days: int = Query(default=90, ge=1, le=400),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list:
    return list(
        db.scalars(
            select(RecoveryMetric)
            .where(RecoveryMetric.user_id == user.id)
            .order_by(RecoveryMetric.recorded_on.desc())
            .limit(days)
        )
    )


@router.post("/metrics", response_model=RecoveryOut, status_code=status.HTTP_201_CREATED)
def log_recovery(
    payload: RecoveryIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> object:
    """Store the subjective inputs and the derived readiness estimate together (spec 28)."""
    existing = db.scalar(
        select(RecoveryMetric).where(
            RecoveryMetric.user_id == user.id, RecoveryMetric.recorded_on == payload.recorded_on
        )
    )
    data = payload.model_dump()
    if existing:
        for k, v in data.items():
            if v is not None:
                setattr(existing, k, v)
        row = existing
    else:
        row = RecoveryMetric(user_id=user.id, **data)
        db.add(row)
    db.flush()
    readiness = recovery_service.compute_readiness(db, user.id, payload.recorded_on)
    row.readiness_score = readiness.get("score")
    row.readiness_label = readiness.get("label")
    db.commit()
    db.refresh(row)
    return row


@router.get("/readiness")
def readiness(
    day: date | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    return recovery_service.compute_readiness(db, user.id, day or date.today())
