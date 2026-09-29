from datetime import date
from pydantic import BaseModel, ConfigDict, Field


class ProfileIn(BaseModel):
    display_name: str | None = None
    birth_date: date | None = None
    sex: str | None = None
    height_cm: float | None = Field(default=None, gt=50, lt=260)
    body_fat_pct: float | None = Field(default=None, ge=2, le=70)
    training_experience: str | None = None
    training_frequency: int | None = Field(default=None, ge=0, le=14)
    session_minutes: int | None = Field(default=None, ge=10, le=300)
    activity_level: str | None = None
    units: str | None = None
    theme_pref: str | None = None
    timezone: str | None = None


class ProfileOut(ProfileIn):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    display_name: str


class GoalIn(BaseModel):
    goal_type: str
    rate_kg_per_week: float | None = Field(default=None, ge=-1.5, le=1.5)
    target_weight_kg: float | None = Field(default=None, gt=20, lt=400)
    started_on: date | None = None


class GoalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    goal_type: str
    rate_kg_per_week: float | None
    target_weight_kg: float | None
    started_on: date
    ended_on: date | None
    is_active: bool


# Circumferences in centimetres. All optional: a user measures what they have a
# tape for, and a missing measurement is never filled in with a guess (spec 64).
class BodyMetricIn(BaseModel):
    measured_on: date
    weight_kg: float | None = Field(default=None, gt=20, lt=400)
    body_fat_pct: float | None = Field(default=None, ge=2, le=70)
    waist_cm: float | None = Field(default=None, gt=30, lt=250)
    neck_cm: float | None = Field(default=None, gt=15, lt=80)
    shoulder_cm: float | None = Field(default=None, gt=50, lt=220)
    chest_cm: float | None = Field(default=None, gt=40, lt=220)
    arm_cm: float | None = Field(default=None, gt=15, lt=90)
    forearm_cm: float | None = Field(default=None, gt=12, lt=60)
    thigh_cm: float | None = Field(default=None, gt=25, lt=120)
    calf_cm: float | None = Field(default=None, gt=15, lt=80)
    hip_cm: float | None = Field(default=None, gt=50, lt=220)
    notes: str | None = None


class BodyMetricOut(BodyMetricIn):
    model_config = ConfigDict(from_attributes=True)
    id: int


class ProgressPhotoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    taken_on: date
    pose: str
    weight_kg: float | None
    notes: str | None
    content_type: str
    size_bytes: int
    url: str
