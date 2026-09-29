from datetime import date
from pydantic import BaseModel


class InsightOut(BaseModel):
    id: int
    for_date: date
    domain: str
    severity: str
    title: str
    body: str


class PillarScore(BaseModel):
    key: str
    label: str
    score: int | None
    detail: str


class TodayOut(BaseModel):
    for_date: date
    greeting: str
    pillars: list[PillarScore]
    readiness: dict
    headline: str
    insights: list[InsightOut]
