"""Preparation phases: cut / bulk / recomp with weekly-average tracking (spec 66, 67).

The phase is judged on weekly average bodyweight, never a single weigh-in. The
service returns the measured rate, the target rate, a verdict and a concrete,
clamped calorie suggestion - all labelled estimates.
"""
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.calculations.prep import (
    PHASE_DEFAULT_RATE, phase_verdict, rate_pct_per_week, suggest_kcal_adjustment,
    suggest_refeed, trend_kg_per_week, weekly_averages,
)
from app.models.prep import PreparationPhase, RefeedEntry
from app.models.user import BodyMetric


def active_phase(db: Session, user_id: int) -> PreparationPhase | None:
    return db.scalar(
        select(PreparationPhase)
        .where(PreparationPhase.user_id == user_id, PreparationPhase.is_active == True)  # noqa: E712
        .order_by(PreparationPhase.started_on.desc())
    )


def latest_weight(db: Session, user_id: int, on_or_before: date | None = None) -> float | None:
    stmt = select(BodyMetric).where(BodyMetric.user_id == user_id, BodyMetric.weight_kg.is_not(None))
    if on_or_before:
        stmt = stmt.where(BodyMetric.measured_on <= on_or_before)
    row = db.scalar(stmt.order_by(BodyMetric.measured_on.desc()).limit(1))
    return float(row.weight_kg) if row else None


def _weigh_ins(db: Session, user_id: int, since: date) -> list[dict]:
    rows = db.scalars(
        select(BodyMetric)
        .where(BodyMetric.user_id == user_id, BodyMetric.measured_on >= since)
        .order_by(BodyMetric.measured_on)
    )
    return [{"measured_on": r.measured_on,
             "weight_kg": float(r.weight_kg) if r.weight_kg is not None else None}
            for r in rows]


# How far back the trend reads, in weeks. A phase that began this morning has no
# weigh-ins of its own yet, so the trend also takes the recent weeks leading into
# it. Without this a fresh phase shows an empty chart for a fortnight, which is
# exactly when a user most wants to see where the rate is heading.
TREND_LOOKBACK_WEEKS = 8


def status(db: Session, user_id: int, phase: PreparationPhase) -> dict:
    """Full picture for the active phase: trend, verdict, calorie advice, refeed due."""
    since = min(phase.started_on, date.today() - timedelta(weeks=TREND_LOOKBACK_WEEKS))
    weeklies = weekly_averages(_weigh_ins(db, user_id, since))
    kg_per_week = trend_kg_per_week(weeklies)
    current_weight = latest_weight(db, user_id)
    actual_pct = rate_pct_per_week(kg_per_week, current_weight)

    target_pct = float(phase.target_rate_pct_per_week) if phase.target_rate_pct_per_week is not None \
        else PHASE_DEFAULT_RATE.get(phase.phase_type, 0.0)

    verdict = phase_verdict(phase.phase_type, actual_pct, target_pct)
    adjustment = suggest_kcal_adjustment(target_pct, actual_pct, current_weight)

    today = date.today()
    weeks_on_phase = max(0, (today - phase.started_on).days // 7)
    refeed = suggest_refeed(phase.phase_type, weeks_on_phase, actual_pct)

    total_change = None
    if phase.start_weight_kg is not None and current_weight is not None:
        total_change = round(current_weight - float(phase.start_weight_kg), 2)

    return {
        "phase": {
            "id": phase.id,
            "phase_type": phase.phase_type,
            "started_on": phase.started_on.isoformat(),
            "weeks_on_phase": weeks_on_phase,
            "start_weight_kg": float(phase.start_weight_kg) if phase.start_weight_kg is not None else None,
            "target_weight_kg": float(phase.target_weight_kg) if phase.target_weight_kg is not None else None,
            "target_rate_pct_per_week": target_pct,
            "kcal_adjustment": phase.kcal_adjustment,
            "notes": phase.notes,
        },
        "current_weight_kg": current_weight,
        "total_change_kg": total_change,
        "weekly_averages": [
            {"week_start": w["week_start"].isoformat(), "avg_kg": w["avg_kg"], "n": w["n"]}
            for w in weeklies
        ],
        "actual_kg_per_week": kg_per_week,
        "actual_pct_per_week": actual_pct,
        "verdict": verdict,
        "suggestion": adjustment,
        "refeed_due": refeed,
        "note": "Rates come from weekly average bodyweight, because daily weight moves with "
                "water, sodium and glycogen as well as tissue. Two full weeks are the minimum "
                "before a rate means anything.",
    }


def apply_adjustment(db: Session, phase: PreparationPhase, delta: int) -> PreparationPhase:
    """Record that the coach suggestion was accepted, so it is not offered twice."""
    phase.kcal_adjustment = int(phase.kcal_adjustment or 0) + int(delta)
    db.commit()
    db.refresh(phase)
    return phase


def list_refeeds(db: Session, user_id: int) -> list[RefeedEntry]:
    return list(
        db.scalars(
            select(RefeedEntry)
            .where(RefeedEntry.user_id == user_id)
            .order_by(RefeedEntry.occurred_on.desc())
        )
    )
