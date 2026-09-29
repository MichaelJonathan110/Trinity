"""Notification payloads (spec 21)."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class NotificationIn(BaseModel):
    kind: str = Field(min_length=1, max_length=32)
    title: str = Field(min_length=1, max_length=160)
    body: str | None = None
    scheduled_for: datetime | None = None


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    kind: str
    title: str
    body: str | None
    scheduled_for: datetime | None
    read_at: datetime | None
    is_enabled: bool
    created_at: datetime


class PreferenceIn(BaseModel):
    is_enabled: bool


class PreferenceOut(BaseModel):
    kind: str
    is_enabled: bool
