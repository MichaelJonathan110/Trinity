"""Phase preparation: cut / bulk / recomp management (spec 66, 67).

A phase is a goal with a *rate* and a clock. The plan is judged on weekly
average bodyweight, never on a single day, because daily weight moves with
water, sodium and glycogen rather than tissue.
"""
from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin


class PreparationPhase(Base, TimestampMixin):
    __tablename__ = "preparation_phases"
    __table_args__ = (Index("ix_prep_phases_user", "user_id", "started_on"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    phase_type: Mapped[str] = mapped_column(String(16), nullable=False)  # cut|bulk|recomp|maintain
    started_on: Mapped[date] = mapped_column(Date, nullable=False)
    ended_on: Mapped[date | None] = mapped_column(Date)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    start_weight_kg: Mapped[float | None] = mapped_column(Numeric(5, 2))
    target_weight_kg: Mapped[float | None] = mapped_column(Numeric(5, 2))
    # Target rate as a percentage of bodyweight per week (e.g. -0.5 = lose 0.5%/wk).
    target_rate_pct_per_week: Mapped[float | None] = mapped_column(Numeric(4, 2))
    # The kcal/day adjustment the auto-coach has applied on top of the TDEE target.
    kcal_adjustment: Mapped[int] = mapped_column(default=0, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)

    refeeds: Mapped[list["RefeedEntry"]] = relationship(
        back_populates="phase", cascade="all, delete-orphan"
    )


class RefeedEntry(Base, TimestampMixin):
    """A planned or completed refeed / diet break, so the history is auditable."""
    __tablename__ = "refeed_entries"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    phase_id: Mapped[int | None] = mapped_column(
        ForeignKey("preparation_phases.id", ondelete="CASCADE"), index=True
    )
    occurred_on: Mapped[date] = mapped_column(Date, nullable=False)
    kind: Mapped[str] = mapped_column(String(16), nullable=False)  # refeed|diet_break
    days: Mapped[int] = mapped_column(default=1, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)

    phase: Mapped["PreparationPhase | None"] = relationship(back_populates="refeeds")
