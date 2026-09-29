"""Steps and daily activity (spec 40-42)."""
from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.activity import DayActivityOut, StepGoalIn, StepsIn, StepsOut
from app.services import activity_service

router = APIRouter(prefix="/activity", tags=["activity"])


@router.get("/steps")
def day_steps(
    day: date | None = None, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> dict:
    return activity_service.day_activity(db, user.id, day or date.today())


@router.post("/steps", response_model=StepsOut, status_code=status.HTTP_201_CREATED)
def log_steps(
    payload: StepsIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> object:
    return activity_service.upsert_steps(db, user.id, payload.model_dump())


@router.get("/steps/history")
def steps_history(
    days: int = Query(default=30, ge=1, le=400),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list:
    return activity_service.history(db, user.id, days)


@router.get("/steps/goal")
def get_goal(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    return {"step_goal": activity_service.step_goal(db, user.id)}


@router.put("/steps/goal")
def set_goal(
    payload: StepGoalIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> dict:
    return {"step_goal": activity_service.set_step_goal(db, user.id, payload.step_goal)}
