from datetime import date
from pydantic import BaseModel, ConfigDict, Field


class StepsIn(BaseModel):
    recorded_on: date
    steps: int = Field(ge=0, le=200000)
    distance_m: float | None = Field(default=None, ge=0, le=200000)
    active_kcal: float | None = Field(default=None, ge=0, le=10000)
    active_minutes: int | None = Field(default=None, ge=0, le=1440)


class StepsOut(StepsIn):
    model_config = ConfigDict(from_attributes=True)
    id: int
    source: str


class StepGoalIn(BaseModel):
    step_goal: int = Field(ge=1000, le=100000)


class DayActivityOut(BaseModel):
    recorded_on: date
    steps: int
    step_goal: int
    distance_m: float | None
    active_kcal: float | None
    active_minutes: int | None
    source: str
