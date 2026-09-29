#!/usr/bin/env python3
"""Log TODAY's data for the demo user through the real API, so the Today page
shows live pillars (nutrition / recovery / training / activity).

Usage: python seed_today.py http://127.0.0.1:8000
Idempotent enough: steps/sleep/recovery upsert; meals add one item per category.
"""
import sys
from datetime import date, datetime, timedelta

import httpx

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000").rstrip("/")
API = f"{BASE}/api/v1"
DEMO = {"email": "demo@trinity.app", "password": "TrinityDemo123!"}
today = date.today()


def main() -> None:
    with httpx.Client(timeout=30.0) as c:
        tok = c.post(f"{API}/auth/login", json=DEMO).json()["access_token"]
        h = {"Authorization": f"Bearer {tok}"}

        # --- activity: today's steps -------------------------------------
        r = c.post(f"{API}/activity/steps", headers=h, json={
            "recorded_on": today.isoformat(), "steps": 11240,
            "distance_m": 8420.0, "active_kcal": 612.0, "active_minutes": 74,
        })
        print("steps:", r.status_code)

        # --- recovery: last night's sleep + subjective recovery ----------
        wake = datetime.combine(today, datetime.min.time()).replace(hour=6, minute=45)
        bed = wake - timedelta(minutes=445)
        r = c.post(f"{API}/recovery/sleep", headers=h, json={
            "bedtime": bed.isoformat(), "wake_at": wake.isoformat(),
            "quality": 4, "is_nap": False, "notes": "Slept well.",
        })
        print("sleep:", r.status_code)
        r = c.post(f"{API}/recovery/metrics", headers=h, json={
            "recorded_on": today.isoformat(), "subjective_score": 4,
            "soreness_score": 2, "resting_hr": 48, "hrv_ms": 92.0,
        })
        print("recovery:", r.status_code)

        # --- nutrition: one real meal today ------------------------------
        foods = c.get(f"{API}/nutrition/foods", headers=h, params={"limit": 3}).json()["items"]
        for i, f in enumerate(foods[:3]):
            r = c.post(f"{API}/nutrition/meals/items", headers=h,
                       params={"logged_on": today.isoformat(), "category": "breakfast"},
                       json={"food_id": f["id"], "quantity_g": 150})
            print(f"meal[{i}]:", r.status_code)

        # --- training: one workout today ---------------------------------
        ex = c.get(f"{API}/training/exercises", headers=h, params={"limit": 2}).json()
        if ex:
            payload = {
                "performed_on": today.isoformat(), "title": "Full body A",
                "status": "completed", "duration_min": 62, "notes": "Felt strong.",
                "exercises": [{
                    "exercise_id": ex[0]["id"], "position": 0,
                    "sets": [{"weight_kg": 60, "reps": 8, "is_warmup": False},
                             {"weight_kg": 65, "reps": 6, "is_warmup": False}],
                }],
            }
            r = c.post(f"{API}/training/workouts", headers=h, json=payload)
            print("workout:", r.status_code, r.text[:120])

        # --- confirm the Today payload now has data ----------------------
        t = c.get(f"{API}/insights/today", headers=h).json()
        filled = [p["key"] for p in t.get("pillars", []) if p.get("score") is not None]
        print("today pillars with data:", filled)
        print("headline:", t.get("headline"))


if __name__ == "__main__":
    main()
