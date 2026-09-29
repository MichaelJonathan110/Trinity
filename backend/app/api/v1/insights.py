"""Daily Performance and the insight engine (spec 43, 44, 66, 91)."""
from datetime import date, datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_profile
from app.database.session import get_db
from app.models.insight import PerformanceInsight
from app.models.user import User
from app.services import insight_service, recovery_service

router = APIRouter(prefix="/insights", tags=["insights"])


@router.get("/today")
def today(
    day: date | None = None,
    profile=Depends(get_profile),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """The central Today view. Every field is computed from stored rows; nothing is invented."""
    day = day or date.today()
    pillars = insight_service.pillar_scores(db, user.id, day)
    readiness = recovery_service.compute_readiness(db, user.id, day)
    insights = insight_service.today_insights(db, user.id, day)
    return {
        "for_date": day.isoformat(),
        "greeting": insight_service.greeting_for(datetime.now()),
        "display_name": profile.display_name,
        "pillars": pillars,
        "readiness": readiness,
        "headline": insight_service.headline(db, user.id, day, pillars, readiness),
        "insights": insights,
        "has_data": any(p["score"] is not None for p in pillars),
    }


@router.get("/feed")
def feed(
    days: int = Query(default=14, ge=1, le=120),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list:
    """Insights generated on demand and cached per day; we do not store fake history (spec 66)."""
    out = []
    today_d = date.today()
    for i in range(days):
        d = today_d.fromordinal(today_d.toordinal() - i)
        for ins in insight_service.today_insights(db, user.id, d):
            out.append(ins)
    return out[:120]


@router.post("/persist", status_code=201)
def persist_insights(
    day: date | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Optionally snapshot today's insights into the table (used by the worker)."""
    day = day or date.today()
    created = 0
    for ins in insight_service.today_insights(db, user.id, day):
        db.add(PerformanceInsight(user_id=user.id, **ins))
        created += 1
    db.commit()
    return {"created": created}
