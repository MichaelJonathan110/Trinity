"""Password hashing (Argon2id) and JWT issue/verify (spec 7, 58).
Plaintext passwords are never stored or logged."""
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

# Argon2id is the default scheme; bcrypt kept as a verification fallback.
pwd_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")


def hash_password(raw: str) -> str:
    return pwd_context.hash(raw)


def verify_password(raw: str, hashed: str) -> bool:
    return pwd_context.verify(raw, hashed)


def _create_token(subject: str, expires: timedelta, kind: str) -> str:
    s = get_settings()
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": kind,
        "iat": int(now.timestamp()),
        "exp": int((now + expires).timestamp()),
    }
    return jwt.encode(payload, s.SECRET_KEY, algorithm=s.ALGORITHM)


def create_access_token(subject: str) -> str:
    return _create_token(subject, timedelta(minutes=get_settings().ACCESS_TOKEN_MINUTES), "access")


def create_refresh_token(subject: str) -> str:
    return _create_token(subject, timedelta(days=get_settings().REFRESH_TOKEN_DAYS), "refresh")


def decode_token(token: str, expected_kind: str | None = None) -> dict[str, Any] | None:
    """Return the claims, or None when the token is invalid/expired/wrong kind."""
    s = get_settings()
    try:
        claims = jwt.decode(token, s.SECRET_KEY, algorithms=[s.ALGORITHM])
    except JWTError:
        return None
    if expected_kind and claims.get("type") != expected_kind:
        return None
    return claims
