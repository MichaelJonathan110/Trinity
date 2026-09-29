"""Sleep and recovery (spec 23-28, 49)."""
from datetime import date, datetime, time

from sqlalchemy import Date, DateTime, ForeignKey, Index, Numeric, String, Text, Time
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class SleepGoal(Base, TimestampMixin):
    __tablename__ = "sleep_goals"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True)
    target_minutes: Mapped[int] = mapped_column(default=480, nullable=False)
    target_bedtime: Mapped[time | None] = mapped_column(Time)
    target_wake: Mapped[time | None] = mapped_column(Time)


class SleepSession(Base, TimestampMixin):
    """One night. duration_min is stored, not recomputed on read, so history is stable."""
    __tablename__ = "sleep_sessions"
    __table_args__ = (Index("ix_sleep_user_date", "user_id", "slept_on"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    slept_on: Mapped[date] = mapped_column(Date, nullable=False)   # the wake-up date
    bedtime: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    wake_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duration_min: Mapped[int] = mapped_column(nullable=False)
    quality: Mapped[int | None] = mapped_column()          # 1-5 self-reported
    is_nap: Mapped[bool] = mapped_column(default=False, nullable=False)
    source: Mapped[str] = mapped_column(String(24), default="manual", nullable=False)  # manual|health
    notes: Mapped[str | None] = mapped_column(Text)


class RecoveryMetric(Base, TimestampMixin):
    """Subjective + derived readiness inputs. Application estimate only (spec 28, 67)."""
    __tablename__ = "recovery_metrics"
    __table_args__ = (Index("ix_recovery_user_date", "user_id", "recorded_on"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    recorded_on: Mapped[date] = mapped_column(Date, nullable=False)
    subjective_score: Mapped[int | None] = mapped_column()   # 1-5 how recovered the user feels
    soreness_score: Mapped[int | None] = mapped_column()     # 1-5
    resting_hr: Mapped[int | None] = mapped_column()
    hrv_ms: Mapped[float | None] = mapped_column(Numeric(6, 1))
    readiness_score: Mapped[int | None] = mapped_column()    # derived, 0-100
    readiness_label: Mapped[str | None] = mapped_column(String(16))
    notes: Mapped[str | None] = mapped_column(Text)
