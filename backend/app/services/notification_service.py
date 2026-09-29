"""Notification feed and per-kind preferences (spec 21, 59)."""
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.insight import Notification
from app.models.notifications import NotificationPreference
from app.repositories import NotificationRepository

# The kinds the app can emit. A missing preference row means "enabled".
DEFAULT_KINDS = ("insight", "hydration", "sleep", "training", "weekly_summary", "system")


def list_for_user(
    db: Session, user_id: int, limit: int = 50, unread_only: bool = False
) -> list[Notification]:
    return NotificationRepository(db).for_user(user_id, limit=limit, unread_only=unread_only)


def create(
    db: Session, user_id: int, kind: str, title: str, body: str | None = None,
    scheduled_for: datetime | None = None,
) -> Notification:
    row = Notification(
        user_id=user_id, kind=kind, title=title, body=body, scheduled_for=scheduled_for
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def mark_read(db: Session, user_id: int, notification_id: int) -> Notification:
    row = db.get(Notification, notification_id)
    if row is None or row.user_id != user_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Notification not found")
    if row.read_at is None:
        row.read_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(row)
    return row


def preferences(db: Session, user_id: int) -> list[dict]:
    stored = {
        p.kind: p.is_enabled
        for p in db.scalars(
            select(NotificationPreference).where(NotificationPreference.user_id == user_id)
        )
    }
    return [{"kind": kind, "is_enabled": stored.get(kind, True)} for kind in DEFAULT_KINDS]


def set_preference(db: Session, user_id: int, kind: str, is_enabled: bool) -> dict:
    row = db.scalar(
        select(NotificationPreference).where(
            NotificationPreference.user_id == user_id, NotificationPreference.kind == kind
        )
    )
    if row is None:
        row = NotificationPreference(user_id=user_id, kind=kind, is_enabled=is_enabled)
        db.add(row)
    else:
        row.is_enabled = is_enabled
    db.commit()
    return {"kind": kind, "is_enabled": is_enabled}
