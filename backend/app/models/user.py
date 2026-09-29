"""Identity, athlete profile, body metrics, goals, progress photos (spec 8, 9, 49, 64)."""
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    profile: Mapped["Profile | None"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )


class Profile(Base, TimestampMixin):
    __tablename__ = "profiles"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    birth_date: Mapped[date | None] = mapped_column(Date)
    sex: Mapped[str | None] = mapped_column(String(16))            # male | female | unspecified
    height_cm: Mapped[float | None] = mapped_column(Numeric(5, 2))
    body_fat_pct: Mapped[float | None] = mapped_column(Numeric(4, 1))
    training_experience: Mapped[str | None] = mapped_column(String(32))  # beginner..advanced
    training_frequency: Mapped[int | None] = mapped_column()            # sessions per week
    session_minutes: Mapped[int | None] = mapped_column()
    activity_level: Mapped[str | None] = mapped_column(String(32))      # sedentary..very_active
    units: Mapped[str] = mapped_column(String(8), default="metric", nullable=False)
    theme_pref: Mapped[str] = mapped_column(String(10), default="auto", nullable=False)  # auto|day|night
    timezone: Mapped[str | None] = mapped_column(String(64))

    user: Mapped["User"] = relationship(back_populates="profile")
    goals: Mapped[list["Goal"]] = relationship(back_populates="profile", cascade="all, delete-orphan")


class Goal(Base, TimestampMixin):
    """One active goal at a time; history kept for the trend view (spec 65)."""
    __tablename__ = "goals"
    id: Mapped[int] = mapped_column(primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("profiles.id", ondelete="CASCADE"), index=True)
    goal_type: Mapped[str] = mapped_column(String(24), nullable=False)   # cut|maintain|lean_bulk|bulk|strength|custom
    rate_kg_per_week: Mapped[float | None] = mapped_column(Numeric(4, 2))
    target_weight_kg: Mapped[float | None] = mapped_column(Numeric(5, 2))
    started_on: Mapped[date] = mapped_column(Date, nullable=False)
    ended_on: Mapped[date | None] = mapped_column(Date)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    profile: Mapped["Profile"] = relationship(back_populates="goals")


class BodyMetric(Base, TimestampMixin):
    """Historical weight / body-fat / circumference log (spec 9, 64).

    Circumferences are tracked as a set because physique change shows in the tape
    measure long before it shows on the scale (waist down while weight is flat is
    the classic recomposition signal).
    """
    __tablename__ = "body_metrics"
    __table_args__ = (Index("ix_body_metrics_user_date", "user_id", "measured_on"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    measured_on: Mapped[date] = mapped_column(Date, nullable=False)
    weight_kg: Mapped[float | None] = mapped_column(Numeric(5, 2))
    body_fat_pct: Mapped[float | None] = mapped_column(Numeric(4, 1))
    waist_cm: Mapped[float | None] = mapped_column(Numeric(5, 2))
    # Extra circumferences (all optional, all centimetres).
    neck_cm: Mapped[float | None] = mapped_column(Numeric(5, 2))
    shoulder_cm: Mapped[float | None] = mapped_column(Numeric(5, 2))
    chest_cm: Mapped[float | None] = mapped_column(Numeric(5, 2))
    arm_cm: Mapped[float | None] = mapped_column(Numeric(5, 2))       # relaxed, largest arm
    forearm_cm: Mapped[float | None] = mapped_column(Numeric(5, 2))
    thigh_cm: Mapped[float | None] = mapped_column(Numeric(5, 2))
    calf_cm: Mapped[float | None] = mapped_column(Numeric(5, 2))
    hip_cm: Mapped[float | None] = mapped_column(Numeric(5, 2))
    notes: Mapped[str | None] = mapped_column(Text)


class ProgressPhoto(Base, TimestampMixin):
    """A physique photo. The file lives on disk; only its metadata is in the DB.

    Photos are private to the owning user: the file route checks ownership before
    streaming a byte, and the stored filename is opaque (spec 59).
    """
    __tablename__ = "progress_photos"
    __table_args__ = (Index("ix_progress_photos_user_date", "user_id", "taken_on"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    taken_on: Mapped[date] = mapped_column(Date, nullable=False)
    pose: Mapped[str] = mapped_column(String(16), default="front", nullable=False)  # front|side|back|other
    stored_name: Mapped[str] = mapped_column(String(255), nullable=False)  # relative path under MEDIA_ROOT
    content_type: Mapped[str] = mapped_column(String(64), nullable=False)
    size_bytes: Mapped[int] = mapped_column(nullable=False)
    weight_kg: Mapped[float | None] = mapped_column(Numeric(5, 2))
    notes: Mapped[str | None] = mapped_column(Text)


class ConnectedHealthSource(Base, TimestampMixin):
    """Explicit, user-granted health data connections only (spec 25, 59)."""
    __tablename__ = "connected_health_sources"
    __table_args__ = (UniqueConstraint("user_id", "provider", name="uq_health_user_provider"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)  # apple_health|health_connect|manual
    scopes: Mapped[str | None] = mapped_column(Text)                    # JSON list of granted scopes
    is_connected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
