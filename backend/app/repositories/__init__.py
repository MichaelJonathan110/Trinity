"""Data-access layer. Services depend on these, not on the ORM directly."""
from app.repositories.base import Repository
from app.repositories.notifications import NotificationRepository
from app.repositories.password_resets import PasswordResetRepository
from app.repositories.users import UserRepository

__all__ = [
    "Repository",
    "UserRepository",
    "NotificationRepository",
    "PasswordResetRepository",
]
