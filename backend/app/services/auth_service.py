"""Registration and login. Passwords are hashed, never stored or logged (spec 7, 58)."""
from datetime import date

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import create_access_token, create_refresh_token, hash_password, verify_password
from app.models.user import Goal, Profile, User


def register(db: Session, email: str, password: str, display_name: str) -> User:
    if db.scalar(select(User).where(User.email == email.lower())):
        raise HTTPException(status.HTTP_409_CONFLICT, "An account with this email already exists")
    user = User(email=email.lower(), password_hash=hash_password(password))
    db.add(user)
    db.flush()
    db.add(Profile(user_id=user.id, display_name=display_name))
    db.flush()
    db.add(Goal(profile_id=user.profile.id, goal_type="maintain", started_on=date.today()))
    db.commit()
    db.refresh(user)
    return user


def authenticate(db: Session, email: str, password: str) -> User:
    user = db.scalar(select(User).where(User.email == email.lower()))
    if user is None or not verify_password(password, user.password_hash):
        # Identical message for both cases: no account enumeration.
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect email or password")
    return user


def issue_tokens(user: User) -> dict:
    sub = str(user.id)
    return {
        "access_token": create_access_token(sub),
        "refresh_token": create_refresh_token(sub),
        "token_type": "bearer",
    }
