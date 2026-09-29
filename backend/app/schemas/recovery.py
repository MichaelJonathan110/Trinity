from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, Field


class SleepIn(BaseModel):
    bedtime: datetime
    wake_at: datetime
    quality: int | None = Field(default=None, ge=1, le=5)
    is_nap: bool = False
    notes: str | None = None


class SleepOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    slept_on: date
    bedtime: datetime
    wake_at: datetime
    duration_min: int
    quality: int | None
    is_nap: bool
    source: str
    notes: str | None


class SleepGoalIn(BaseModel):
    target_minutes: int = Field(ge=240, le=720)
    target_bedtime: str | None = None
    target_wake: str | None = None


class RecoveryIn(BaseModel):
    recorded_on: date
    subjective_score: int | None = Field(default=None, ge=1, le=5)
    soreness_score: int | None = Field(default=None, ge=1, le=5)
    resting_hr: int | None = Field(default=None, ge=25, le=220)
    hrv_ms: float | None = Field(default=None, ge=0, le=400)
    notes: str | None = None


class RecoveryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    recorded_on: date
    subjective_score: int | None
    soreness_score: int | None
    resting_hr: int | None
    hrv_ms: float | None
    readiness_score: int | None
    readiness_label: str | None
    notes: str | None
