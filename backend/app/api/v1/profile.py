"""Athlete profile, goals, body metrics, progress photos (spec 8, 9, 64, 65, 59)."""
from datetime import date
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.database.session import get_db
from app.models.user import BodyMetric, Goal, ProgressPhoto, User
from app.schemas.user import (
    BodyMetricIn, BodyMetricOut, GoalIn, GoalOut, ProfileIn, ProfileOut, ProgressPhotoOut,
)
from app.services import photo_service

router = APIRouter(prefix="/profile", tags=["profile"])


def _media_root() -> Path:
    return Path(get_settings().MEDIA_ROOT)


def _photo_out(p: ProgressPhoto) -> dict:
    return {
        "id": p.id, "taken_on": p.taken_on, "pose": p.pose, "weight_kg": p.weight_kg,
        "notes": p.notes, "content_type": p.content_type, "size_bytes": p.size_bytes,
        "url": f"/api/v1/profile/photos/{p.id}/file",
    }


@router.get("", response_model=ProfileOut)
def read_profile(user: User = Depends(get_current_user)) -> object:
    if user.profile is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Profile not set up yet")
    return user.profile


@router.patch("", response_model=ProfileOut)
def update_profile(
    payload: ProfileIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> object:
    profile = user.profile
    if profile is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Profile not set up yet")
    for field, value in payload.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(profile, field, value)
    db.commit()
    db.refresh(profile)
    return profile


@router.get("/goals", response_model=list[GoalOut])
def list_goals(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list:
    return list(
        db.scalars(
            select(Goal).where(Goal.profile_id == user.profile.id).order_by(Goal.started_on.desc())
        )
    )


@router.post("/goals", response_model=GoalOut, status_code=status.HTTP_201_CREATED)
def set_goal(
    payload: GoalIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> object:
    """Setting a new goal closes the previous active one (spec 65)."""
    current = db.scalars(
        select(Goal).where(Goal.profile_id == user.profile.id, Goal.is_active == True)  # noqa: E712
    ).all()
    today = payload.started_on or date.today()
    for g in current:
        g.is_active = False
        g.ended_on = today
    goal = Goal(
        profile_id=user.profile.id, goal_type=payload.goal_type,
        rate_kg_per_week=payload.rate_kg_per_week, target_weight_kg=payload.target_weight_kg,
        started_on=today, is_active=True,
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return goal


@router.get("/metrics", response_model=list[BodyMetricOut])
def list_metrics(
    days: int = 365, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list:
    return list(
        db.scalars(
            select(BodyMetric)
            .where(BodyMetric.user_id == user.id)
            .order_by(BodyMetric.measured_on.desc())
            .limit(days)
        )
    )


@router.post("/metrics", response_model=BodyMetricOut, status_code=status.HTTP_201_CREATED)
def add_metric(
    payload: BodyMetricIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> object:
    existing = db.scalar(
        select(BodyMetric).where(
            BodyMetric.user_id == user.id, BodyMetric.measured_on == payload.measured_on
        )
    )
    if existing:
        for field, value in payload.model_dump(exclude_unset=True).items():
            if value is not None:
                setattr(existing, field, value)
        db.commit()
        db.refresh(existing)
        return existing
    row = BodyMetric(user_id=user.id, **payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/metrics/{metric_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_metric(
    metric_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> None:
    row = db.get(BodyMetric, metric_id)
    if row is None or row.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Metric not found")
    db.delete(row)
    db.commit()


@router.get("/photos", response_model=list[ProgressPhotoOut])
def list_photos(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list:
    rows = db.scalars(
        select(ProgressPhoto)
        .where(ProgressPhoto.user_id == user.id)
        .order_by(ProgressPhoto.taken_on.desc(), ProgressPhoto.id.desc())
    )
    return [_photo_out(p) for p in rows]


@router.post("/photos", response_model=ProgressPhotoOut, status_code=status.HTTP_201_CREATED)
def upload_photo(
    file: UploadFile = File(...),
    taken_on: date = Form(...),
    pose: str = Form("front"),
    weight_kg: float | None = Form(None),
    notes: str | None = Form(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> object:
    """Store a physique photo. Only the metadata is kept in the DB; the file is on disk."""
    if pose not in ("front", "side", "back", "other"):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "pose must be front, side, back or other")
    content = file.file.read()
    stored_name, size = photo_service.save_photo(
        _media_root(), user.id, content, file.content_type or ""
    )
    row = ProgressPhoto(
        user_id=user.id, taken_on=taken_on, pose=pose, stored_name=stored_name,
        content_type=file.content_type or "image/jpeg", size_bytes=size,
        weight_kg=weight_kg, notes=notes,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _photo_out(row)


@router.get("/photos/{photo_id}/file")
def photo_file(
    photo_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Stream one photo, but only to its owner - ownership is re-checked here (spec 59)."""
    row = db.get(ProgressPhoto, photo_id)
    if row is None or row.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Photo not found")
    path = photo_service.photo_path(_media_root(), row.stored_name)
    return FileResponse(path, media_type=row.content_type)


@router.delete("/photos/{photo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_photo(
    photo_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> None:
    row = db.get(ProgressPhoto, photo_id)
    if row is None or row.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Photo not found")
    photo_service.delete_photo(_media_root(), row.stored_name)
    db.delete(row)
    db.commit()
