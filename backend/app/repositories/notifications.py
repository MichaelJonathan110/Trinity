"""Notification queries."""
from sqlalchemy import select

from app.models.insight import Notification
from app.repositories.base import Repository


class NotificationRepository(Repository[Notification]):
    model = Notification

    def for_user(self, user_id: int, limit: int = 50, unread_only: bool = False) -> list[Notification]:
        stmt = select(Notification).where(Notification.user_id == user_id)
        if unread_only:
            stmt = stmt.where(Notification.read_at.is_(None))
        stmt = stmt.order_by(Notification.created_at.desc()).limit(limit)
        return list(self.db.execute(stmt).scalars().all())
