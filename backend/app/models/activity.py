"""Steps and daily activity (spec 40-42, 49)."""
from datetime import date

from sqlalchemy import Date, ForeignKey, Index, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class StepRecord(Base, TimestampMixin):
    __tablename__ = "step_records"
    __table_args__ = (
        UniqueConstraint("user_id", "recorded_on", name="uq_steps_user_date"),
        Index("ix_steps_user_date", "user_id", "recorded_on"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    recorded_on: Mapped[date] = mapped_column(Date, nullable=False)
    steps: Mapped[int] = mapped_column(nullable=False)
    distance_m: Mapped[float | None] = mapped_column(Numeric(10, 1))
    active_kcal: Mapped[float | None] = mapped_column(Numeric(7, 2))
    active_minutes: Mapped[int | None] = mapped_column()
    source: Mapped[str] = mapped_column(String(24), default="manual", nullable=False)


class DailyActivity(Base, TimestampMixin):
    """Per-day roll-up used by the cross-domain engine (spec 43)."""
    __tablename__ = "daily_activity"
    __table_args__ = (UniqueConstraint("user_id", "recorded_on", name="uq_activity_user_date"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    recorded_on: Mapped[date] = mapped_column(Date, nullable=False)
    step_goal: Mapped[int] = mapped_column(default=10000, nullable=False)
    notes: Mapped[str | None] = mapped_column(String(255))
