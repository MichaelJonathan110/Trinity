"""Notification feed and preferences (spec 21)."""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.notification import NotificationIn, NotificationOut, PreferenceIn, PreferenceOut
from app.services import notification_service

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationOut])
def list_notifications(
    limit: int = Query(default=50, ge=1, le=200),
    unread_only: bool = False,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list:
    return notification_service.list_for_user(db, user.id, limit=limit, unread_only=unread_only)


@router.post("", response_model=NotificationOut, status_code=status.HTTP_201_CREATED)
def create_notification(
    payload: NotificationIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> object:
    return notification_service.create(
        db, user.id, payload.kind, payload.title, payload.body, payload.scheduled_for
    )


@router.get("/preferences", response_model=list[PreferenceOut])
def get_preferences(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[dict]:
    return notification_service.preferences(db, user.id)


@router.put("/preferences/{kind}", response_model=PreferenceOut)
def set_preference(
    kind: str,
    payload: PreferenceIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    return notification_service.set_preference(db, user.id, kind, payload.is_enabled)


@router.post("/{notification_id}/read", response_model=NotificationOut)
def mark_read(
    notification_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> object:
    return notification_service.mark_read(db, user.id, notification_id)
