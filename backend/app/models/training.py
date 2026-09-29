"""Exercise library, programs, logged workouts, PRs (spec 29-39, 49)."""
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin


class ExerciseLibrary(Base, TimestampMixin):
    __tablename__ = "exercise_library"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160), unique=True, nullable=False)
    primary_muscle: Mapped[str] = mapped_column(String(48), nullable=False, index=True)
    secondary_muscles: Mapped[str | None] = mapped_column(String(200))   # comma-separated
    equipment: Mapped[str | None] = mapped_column(String(64))
    movement_pattern: Mapped[str | None] = mapped_column(String(48))     # push|pull|squat|hinge|carry|core
    instructions: Mapped[str | None] = mapped_column(Text)
    media_ref: Mapped[str | None] = mapped_column(String(255))
    created_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))


class TrainingProgram(Base, TimestampMixin):
    """A user program, or a copy made from a documented template (spec 38, 39)."""
    __tablename__ = "training_programs"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    goal: Mapped[str | None] = mapped_column(String(32))
    weeks: Mapped[int | None] = mapped_column()
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # Attribution is mandatory for anything derived from a published routine (spec 39).
    template_slug: Mapped[str | None] = mapped_column(String(80))
    source_name: Mapped[str | None] = mapped_column(String(160))
    source_url: Mapped[str | None] = mapped_column(String(255))
    source_published_on: Mapped[date | None] = mapped_column(Date)
    attribution_note: Mapped[str | None] = mapped_column(Text)

    days: Mapped[list["TrainingProgramDay"]] = relationship(
        back_populates="program", cascade="all, delete-orphan"
    )


class TrainingProgramDay(Base):
    __tablename__ = "training_program_days"
    __table_args__ = (UniqueConstraint("program_id", "day_index", name="uq_program_day"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    program_id: Mapped[int] = mapped_column(ForeignKey("training_programs.id", ondelete="CASCADE"), index=True)
    day_index: Mapped[int] = mapped_column(nullable=False)   # 0=Monday
    title: Mapped[str] = mapped_column(String(120), nullable=False)  # "Chest + Triceps" or "Rest"
    is_rest: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    exercise_ids: Mapped[str | None] = mapped_column(Text)   # JSON list of exercise ids, in order

    program: Mapped["TrainingProgram"] = relationship(back_populates="days")


class Workout(Base, TimestampMixin):
    __tablename__ = "workouts"
    __table_args__ = (Index("ix_workouts_user_date", "user_id", "performed_on"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    program_id: Mapped[int | None] = mapped_column(ForeignKey("training_programs.id", ondelete="SET NULL"))
    performed_on: Mapped[date] = mapped_column(Date, nullable=False)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="completed", nullable=False)  # completed|modified|skipped
    duration_min: Mapped[int | None] = mapped_column()
    notes: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    exercises: Mapped[list["WorkoutExercise"]] = relationship(
        back_populates="workout", cascade="all, delete-orphan"
    )


class WorkoutExercise(Base):
    __tablename__ = "workout_exercises"
    id: Mapped[int] = mapped_column(primary_key=True)
    workout_id: Mapped[int] = mapped_column(ForeignKey("workouts.id", ondelete="CASCADE"), index=True)
    exercise_id: Mapped[int] = mapped_column(ForeignKey("exercise_library.id", ondelete="RESTRICT"), index=True)
    position: Mapped[int] = mapped_column(default=0, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)

    workout: Mapped["Workout"] = relationship(back_populates="exercises")
    sets: Mapped[list["ExerciseSet"]] = relationship(
        back_populates="workout_exercise", cascade="all, delete-orphan", order_by="ExerciseSet.set_index"
    )


class ExerciseSet(Base):
    __tablename__ = "exercise_sets"
    __table_args__ = (UniqueConstraint("workout_exercise_id", "set_index", name="uq_set_index"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    workout_exercise_id: Mapped[int] = mapped_column(
        ForeignKey("workout_exercises.id", ondelete="CASCADE"), index=True
    )
    set_index: Mapped[int] = mapped_column(nullable=False)
    weight_kg: Mapped[float | None] = mapped_column(Numeric(6, 2))
    reps: Mapped[int | None] = mapped_column()
    rpe: Mapped[float | None] = mapped_column(Numeric(3, 1))
    # Reps in reserve: how many reps the set had left. The honest autoregulation
    # signal - two identical sets are not the same stimulus at RIR 1 and RIR 4.
    rir: Mapped[float | None] = mapped_column(Numeric(3, 1))
    # normal | drop | myo_rep | rest_pause | amrap | failure. Warm-ups use is_warmup.
    set_type: Mapped[str | None] = mapped_column(String(16), default="normal")
    rest_sec: Mapped[int | None] = mapped_column()
    is_warmup: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    workout_exercise: Mapped["WorkoutExercise"] = relationship(back_populates="sets")


class ExerciseNote(Base, TimestampMixin):
    __tablename__ = "exercise_notes"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    exercise_id: Mapped[int] = mapped_column(ForeignKey("exercise_library.id", ondelete="CASCADE"), index=True)
    workout_id: Mapped[int | None] = mapped_column(ForeignKey("workouts.id", ondelete="SET NULL"))
    body: Mapped[str] = mapped_column(Text, nullable=False)


class PersonalRecord(Base, TimestampMixin):
    __tablename__ = "personal_records"
    __table_args__ = (Index("ix_pr_user_exercise", "user_id", "exercise_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    exercise_id: Mapped[int] = mapped_column(ForeignKey("exercise_library.id", ondelete="CASCADE"), index=True)
    record_type: Mapped[str] = mapped_column(String(16), nullable=False)  # weight|reps|e1rm|volume
    value: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False)
    weight_kg: Mapped[float | None] = mapped_column(Numeric(6, 2))
    reps: Mapped[int | None] = mapped_column()
    achieved_on: Mapped[date] = mapped_column(Date, nullable=False)
    workout_id: Mapped[int | None] = mapped_column(ForeignKey("workouts.id", ondelete="SET NULL"))
