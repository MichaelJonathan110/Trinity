"""Aggregate API router (spec 51)."""
from fastapi import APIRouter

from app.api.v1 import (
    account, activity, auth, insights, notifications, nutrition, prep, profile, recovery, training,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(account.router)
api_router.include_router(profile.router)
api_router.include_router(nutrition.router)
api_router.include_router(training.router)
api_router.include_router(prep.router)
api_router.include_router(recovery.router)
api_router.include_router(activity.router)
api_router.include_router(insights.router)
api_router.include_router(notifications.router)
