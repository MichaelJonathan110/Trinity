"""Preparation phase schemas (spec 66, 67)."""
from datetime import date

from pydantic import BaseModel, ConfigDict, Field

PHASE_TYPES = ("cut", "bulk", "recomp", "maintain")


class PhaseIn(BaseModel):
    phase_type: str = Field(pattern="^(cut|bulk|recomp|maintain)$")
    started_on: date | None = None
    start_weight_kg: float | None = Field(default=None, gt=20, lt=400)
    target_weight_kg: float | None = Field(default=None, gt=20, lt=400)
    # Target rate as % of bodyweight per week, e.g. -0.5 for a cut, +0.35 for a lean bulk.
    target_rate_pct_per_week: float | None = Field(default=None, ge=-2, le=2)
    # How long the phase is planned to run. A phase is a plan with a clock, so the
    # user sets the number of weeks up front (e.g. a 12-week contest prep block).
    target_weeks: int | None = Field(default=None, ge=1, le=104)
    notes: str | None = None


class PhasePatch(BaseModel):
    target_weight_kg: float | None = Field(default=None, gt=20, lt=400)
    target_rate_pct_per_week: float | None = Field(default=None, ge=-2, le=2)
    target_weeks: int | None = Field(default=None, ge=1, le=104)
    notes: str | None = None


class PhaseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    phase_type: str
    started_on: date
    ended_on: date | None
    is_active: bool
    start_weight_kg: float | None
    target_weight_kg: float | None
    target_rate_pct_per_week: float | None
    target_weeks: int | None
    kcal_adjustment: int
    notes: str | None


class RefeedIn(BaseModel):
    occurred_on: date
    kind: str = Field(pattern="^(refeed|diet_break)$")
    days: int = Field(default=1, ge=1, le=21)
    notes: str | None = None


class RefeedOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    occurred_on: date
    kind: str
    days: int
    notes: str | None


class AdjustmentIn(BaseModel):
    """The coach's suggested kcal delta, accepted or declined by the user."""
    delta_kcal: int = Field(ge=-1000, le=1000)
    apply: bool = True
