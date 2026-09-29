"""Account lifecycle: password reset, data export, account deletion (spec 7, 58, 59)."""
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


class PasswordResetRequestIn(BaseModel):
    email: EmailStr


class PasswordResetRequestOut(BaseModel):
    ok: bool = True
    # Present only in development so the flow is testable without a mailer.
    dev_token: str | None = None


class PasswordResetConfirmIn(BaseModel):
    token: str = Field(min_length=8, max_length=200)
    new_password: str = Field(min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def strong_enough(cls, v: str) -> str:
        if v.isdigit() or v.isalpha():
            raise ValueError("Password must mix letters and numbers.")
        return v


class AccountDeleteIn(BaseModel):
    password: str
    confirm: str


class ExportOut(BaseModel):
    exported_at: datetime
    account: dict
    data: dict
