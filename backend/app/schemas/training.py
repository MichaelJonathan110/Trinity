from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, Field

# Intensity techniques that change how a set counts toward volume (spec 33).
SET_TYPES = ("normal", "drop", "myo_rep", "rest_pause", "amrap", "failure")


class ExerciseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    primary_muscle: str
    secondary_muscles: str | None
    equipment: str | None
    movement_pattern: str | None
    instructions: str | None


class SetIn(BaseModel):
    set_index: int = Field(ge=1, le=60)
    weight_kg: float | None = Field(default=None, ge=0, le=1000)
    reps: int | None = Field(default=None, ge=0, le=1000)
    rpe: float | None = Field(default=None, ge=1, le=10)
    # Reps in reserve: 0 = failure, 4 = four reps left. The honest effort signal.
    rir: float | None = Field(default=None, ge=0, le=10)
    set_type: str | None = Field(default=None, pattern="^(normal|drop|myo_rep|rest_pause|amrap|failure)$")
    rest_sec: int | None = Field(default=None, ge=0, le=3600)
    is_warmup: bool = False


class SetOut(SetIn):
    model_config = ConfigDict(from_attributes=True)
    id: int


class WorkoutExerciseIn(BaseModel):
    exercise_id: int
    position: int = 0
    notes: str | None = None


class WorkoutExerciseCreate(WorkoutExerciseIn):
    """An exercise as submitted when logging a workout, with every set validated.

    The sets used to be passed through unvalidated, so an impossible RIR (or a
    negative weight) was stored silently. Parsing them here rejects bad input
    with a 422 instead.
    """
    sets: list[SetIn] = []


class WorkoutExerciseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    exercise_id: int
    position: int
    notes: str | None
    sets: list[SetOut] = []


class WorkoutIn(BaseModel):
    performed_on: date
    title: str
    program_id: int | None = None
    status: str = "completed"
    duration_min: int | None = Field(default=None, ge=0, le=600)
    notes: str | None = None


class WorkoutOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    performed_on: date
    title: str
    status: str
    duration_min: int | None
    notes: str | None
    exercises: list[WorkoutExerciseOut] = []


class ProgramDayIn(BaseModel):
    day_index: int = Field(ge=0, le=6)
    title: str
    is_rest: bool = False
    exercise_ids: list[int] = []


class ProgramDayOut(BaseModel):
    """Serialised program day. Built explicitly from the ORM row so the JSON stays
    a plain object regardless of how the row is loaded (the previous `list[dict]`
    annotation could not validate ORM instances and returned a 500 on save)."""
    model_config = ConfigDict(from_attributes=True)
    day_index: int
    title: str
    is_rest: bool


class ProgramIn(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    description: str | None = None
    goal: str | None = None
    weeks: int | None = None
    days: list[ProgramDayIn] = []


class ProgramOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    description: str | None
    goal: str | None
    weeks: int | None
    is_active: bool
    template_slug: str | None
    source_name: str | None
    source_url: str | None
    attribution_note: str | None
    days: list[ProgramDayOut] = []


class CalendarDay(BaseModel):
    day: date
    status: str            # completed | modified | skipped | rest | none
    workout_id: int | None = None
    title: str | None = None


class MuscleVolume(BaseModel):
    """One muscle group's weekly fractional-set count against its landmarks."""
    muscle: str
    sets_per_week: float
    mev: int
    mav: int
    mrv: int
    status: str            # none|below_mev|maintenance|optimal|above_mrv


class VolumeReport(BaseModel):
    weeks: int
    window_start: date
    muscles: list[MuscleVolume]
    trained_count: int
    note: str


class ProgressionAdvice(BaseModel):
    exists: bool
    note: str | None = None
    current: dict | None = None
    previous: dict | None = None
    action: str | None = None
    detail: str | None = None
