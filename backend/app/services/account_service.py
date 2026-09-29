"""Account lifecycle: password reset, data export, account deletion (spec 7, 58, 59)."""
from __future__ import annotations

import hashlib
import secrets
from datetime import date, datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import inspect as sa_inspect, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import hash_password, verify_password
from app.models.activity import DailyActivity, StepRecord
from app.models.auth import PasswordResetToken
from app.models.insight import Notification, PerformanceInsight
from app.models.nutrition import (
    CustomFood, FavoriteFood, Meal, NutritionTarget, Recipe, TdeeEstimate,
)
from app.models.recovery import RecoveryMetric, SleepSession
from app.models.training import PersonalRecord, Workout
from app.models.user import BodyMetric, ConnectedHealthSource, Goal, Profile, User
from app.repositories import PasswordResetRepository, UserRepository

RESET_TTL = timedelta(hours=1)
DELETE_CONFIRM_PHRASE = "DELETE"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _as_aware(value: datetime | None) -> datetime | None:
    """SQLite hands back naive datetimes; treat them as UTC so comparisons never crash."""
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def _hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


# --------------------------------------------------------------- password reset
def request_password_reset(db: Session, email: str) -> str | None:
    """Create a single-use token. Returns the raw token (dev only) or None.

    The caller always reports success, so the endpoint cannot be used to discover
    which emails have accounts (no account enumeration).
    """
    user = UserRepository(db).by_email(email)
    if user is None or not user.is_active:
        return None
    raw = secrets.token_urlsafe(32)
    db.add(
        PasswordResetToken(
            user_id=user.id,
            token_hash=_hash_token(raw),
            expires_at=_now() + RESET_TTL,
        )
    )
    db.commit()
    return raw


def confirm_password_reset(db: Session, token: str, new_password: str) -> None:
    row = PasswordResetRepository(db).by_hash(_hash_token(token))
    if row is None or row.used_at is not None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid or already-used reset token")
    if _as_aware(row.expires_at) < _now():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Reset token has expired")
    user = db.get(User, row.user_id)
    if user is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid reset token")
    user.password_hash = hash_password(new_password)
    row.used_at = _now()
    db.commit()


# -------------------------------------------------------------------- export
def _row_to_dict(obj: object) -> dict:
    out: dict = {}
    for attr in sa_inspect(obj).mapper.column_attrs:
        value = getattr(obj, attr.key)
        if isinstance(value, (datetime, date)):
            value = value.isoformat()
        out[attr.key] = value
    return out


_USER_SCOPED = [
    BodyMetric, ConnectedHealthSource, Notification, PerformanceInsight,
    StepRecord, DailyActivity, SleepSession, RecoveryMetric,
    Meal, NutritionTarget, TdeeEstimate, FavoriteFood, CustomFood, Recipe,
    Workout, PersonalRecord,
]


def export_data(db: Session, user: User) -> dict:
    """Everything we hold about this user, in one JSON document (spec 59)."""
    data: dict = {}
    profile = db.scalar(select(Profile).where(Profile.user_id == user.id))
    if profile is not None:
        data["profiles"] = [_row_to_dict(profile)]
        goals = db.scalars(select(Goal).where(Goal.profile_id == profile.id)).all()
        data["goals"] = [_row_to_dict(g) for g in goals]
    for model in _USER_SCOPED:
        if not hasattr(model, "user_id"):
            continue
        rows = db.scalars(select(model).where(model.user_id == user.id)).all()
        data[model.__tablename__] = [_row_to_dict(r) for r in rows]
    return {
        "exported_at": _now(),
        "account": {
            "id": user.id,
            "email": user.email,
            "is_demo": user.is_demo,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        },
        "data": data,
    }


# -------------------------------------------------------------------- deletion
def delete_account(db: Session, user: User, password: str, confirm: str) -> None:
    """Hard delete. Rows cascade at the database level via ON DELETE CASCADE."""
    if confirm != DELETE_CONFIRM_PHRASE:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, f'Type {DELETE_CONFIRM_PHRASE} to confirm deletion'
        )
    if not verify_password(password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect password")
    db.delete(user)
    db.commit()
