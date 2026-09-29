"""Pure functions only: no DB, no IO, no framework. Fully unit-tested (spec 68, 69)."""
from app.calculations.bodycomp import (
    ACTIVITY_MULTIPLIERS, bmr_mifflin_st_jeor, estimate_tdee, age_from,
    calorie_target_for_goal, adaptive_tdee, MACRO_SPLITS,
)
from app.calculations.nutrition import (
    scale_nutrients, serving_to_grams, meal_totals, recipe_totals,
)
from app.calculations.training import set_volume, session_volume, epley_1rm, best_e1rm
from app.calculations.recovery import (
    sleep_duration_minutes, sleep_score, consistency_score, readiness_score,
)

__all__ = [
    "ACTIVITY_MULTIPLIERS", "bmr_mifflin_st_jeor", "estimate_tdee", "age_from",
    "calorie_target_for_goal", "adaptive_tdee", "MACRO_SPLITS",
    "scale_nutrients", "serving_to_grams", "meal_totals", "recipe_totals",
    "set_volume", "session_volume", "epley_1rm", "best_e1rm",
    "sleep_duration_minutes", "sleep_score", "consistency_score", "readiness_score",
]
