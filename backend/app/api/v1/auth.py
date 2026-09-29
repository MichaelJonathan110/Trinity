"""Authentication endpoints (spec 7, 51)."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.security import decode_token
from app.database.session import get_db
from app.models.user import User
from app.schemas.auth import LoginIn, RefreshIn, RegisterIn, TokenOut
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterIn, db: Session = Depends(get_db)) -> dict:
    user = auth_service.register(db, payload.email, payload.password, payload.display_name)
    return auth_service.issue_tokens(user)


@router.post("/login", response_model=TokenOut)
def login(payload: LoginIn, db: Session = Depends(get_db)) -> dict:
    user = auth_service.authenticate(db, payload.email, payload.password)
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()
    return auth_service.issue_tokens(user)


@router.post("/refresh", response_model=TokenOut)
def refresh(payload: RefreshIn, db: Session = Depends(get_db)) -> dict:
    claims = decode_token(payload.refresh_token, expected_kind="refresh")
    if not claims:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid refresh token")
    user = db.get(User, int(claims["sub"]))
    if user is None or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found")
    return auth_service.issue_tokens(user)


@router.get("/me")
def me(user: User = Depends(get_current_user)) -> dict:
    return {"id": user.id, "email": user.email, "is_demo": user.is_demo,
            "has_profile": user.profile is not None}


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout() -> None:
    """Stateless JWT: the client discards its tokens. Documented, not a fake."""
    return None
