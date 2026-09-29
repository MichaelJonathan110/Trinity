"""Account lifecycle endpoints: password reset, export, deletion (spec 7, 58, 59)."""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.database.session import get_db
from app.models.user import User
from app.schemas.account import (
    AccountDeleteIn, ExportOut, PasswordResetConfirmIn, PasswordResetRequestIn,
    PasswordResetRequestOut,
)
from app.services import account_service

router = APIRouter(prefix="/account", tags=["account"])


@router.post("/password-reset/request", response_model=PasswordResetRequestOut)
def request_password_reset(
    payload: PasswordResetRequestIn, db: Session = Depends(get_db)
) -> dict:
    """Always reports success: the response never reveals whether the email exists."""
    raw = account_service.request_password_reset(db, payload.email)
    dev_token = raw if get_settings().ENV != "production" else None
    return {"ok": True, "dev_token": dev_token}


@router.post("/password-reset/confirm")
def confirm_password_reset(
    payload: PasswordResetConfirmIn, db: Session = Depends(get_db)
) -> dict:
    account_service.confirm_password_reset(db, payload.token, payload.new_password)
    return {"ok": True}


@router.get("/export", response_model=ExportOut)
def export_account(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> dict:
    """Download everything we store about the signed-in user."""
    return account_service.export_data(db, user)


@router.post("/delete", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(
    payload: AccountDeleteIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """Irreversible. Requires the password and the literal word DELETE."""
    account_service.delete_account(db, user, payload.password, payload.confirm)
