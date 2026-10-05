"""Preparation phase API: cut / bulk / recomp management (spec 66, 67)."""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database.session import get_db
from app.models.prep import PreparationPhase, RefeedEntry
from app.models.user import User
from app.schemas.prep import AdjustmentIn, PhaseIn, PhaseOut, PhasePatch, RefeedIn, RefeedOut
from app.services import prep_service

router = APIRouter(prefix="/prep", tags=["preparation"])


@router.get("/phase")
def read_phase(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    """The active phase with its weekly-average trend, verdict and calorie advice."""
    phase = prep_service.active_phase(db, user.id)
    if phase is None:
        return {"active": False, "note": "No preparation phase is running. Start one to track a cut, bulk or recomp."}
    return {"active": True, **prep_service.status(db, user.id, phase)}


@router.get("/weight-series")
def weight_series(
    granularity: str = Query(default="weekly", pattern="^(daily|weekly|monthly)$"),
    months: int = Query(default=12, ge=1, le=36),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Bodyweight over time at daily, weekly or monthly resolution.

    Daily shows the raw weigh-ins (noisy by design); weekly and monthly average
    them, because a single day's weight moves with water, sodium and glycogen as
    well as tissue. Only real weigh-ins are returned - gaps stay gaps.
    """
    return prep_service.weight_series(db, user.id, granularity, months)


@router.post("/phase", response_model=PhaseOut, status_code=status.HTTP_201_CREATED)
def start_phase(
    payload: PhaseIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> object:
    """Start a phase and close any running one, so only one is ever active."""
    today = payload.started_on or date.today()
    for p in db.scalars(
        select(PreparationPhase).where(
            PreparationPhase.user_id == user.id, PreparationPhase.is_active == True  # noqa: E712
        )
    ):
        p.is_active = False
        p.ended_on = today

    start_weight = payload.start_weight_kg or prep_service.latest_weight(db, user.id, today)
    phase = PreparationPhase(
        user_id=user.id, phase_type=payload.phase_type, started_on=today,
        is_active=True, start_weight_kg=start_weight,
        target_weight_kg=payload.target_weight_kg,
        target_rate_pct_per_week=payload.target_rate_pct_per_week,
        target_weeks=payload.target_weeks,
        notes=payload.notes,
    )
    db.add(phase)
    db.commit()
    db.refresh(phase)
    return phase


@router.patch("/phase", response_model=PhaseOut)
def update_phase(
    payload: PhasePatch, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> object:
    phase = prep_service.active_phase(db, user.id)
    if phase is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No active preparation phase")
    for field, value in payload.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(phase, field, value)
    db.commit()
    db.refresh(phase)
    return phase


@router.post("/phase/adjustment")
def accept_adjustment(
    payload: AdjustmentIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> dict:
    """Accept (or decline) the coach's suggested kcal change on the active phase."""
    phase = prep_service.active_phase(db, user.id)
    if phase is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No active preparation phase")
    if payload.apply:
        prep_service.apply_adjustment(db, phase, payload.delta_kcal)
    return {"ok": True, "kcal_adjustment": phase.kcal_adjustment, "applied": payload.apply}


@router.post("/phase/end", response_model=PhaseOut)
def end_phase(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> object:
    phase = prep_service.active_phase(db, user.id)
    if phase is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No active preparation phase")
    phase.is_active = False
    phase.ended_on = date.today()
    db.commit()
    db.refresh(phase)
    return phase


@router.get("/refeeds", response_model=list[RefeedOut])
def list_refeeds(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list:
    return prep_service.list_refeeds(db, user.id)


@router.post("/refeeds", response_model=RefeedOut, status_code=status.HTTP_201_CREATED)
def add_refeed(
    payload: RefeedIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> object:
    phase = prep_service.active_phase(db, user.id)
    entry = RefeedEntry(
        user_id=user.id, phase_id=phase.id if phase else None,
        occurred_on=payload.occurred_on, kind=payload.kind, days=payload.days,
        notes=payload.notes,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry
