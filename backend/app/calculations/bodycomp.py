"""Energy expenditure and macro targets.

BMR - Mifflin-St Jeor (1990), the standard predictive equation:
    male:   10*kg + 6.25*cm - 5*age + 5
    female: 10*kg + 6.25*cm - 5*age - 161
These are ESTIMATES, not measurements (spec 17, 18, 19, 67).
"""
from datetime import date

# Standard activity multipliers applied to BMR.
ACTIVITY_MULTIPLIERS: dict[str, float] = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "active": 1.725,
    "very_active": 1.9,
}

# Goal -> daily kcal delta from maintenance, and macro split (protein/carbs/fat).
# Protein is prioritised for resistance-training users (spec 20).
MACRO_SPLITS: dict[str, dict] = {
    "cut":       {"kcal_delta": -0.20, "protein_g_per_kg": 2.2, "fat_pct": 0.25},
    "maintain":  {"kcal_delta": 0.0,   "protein_g_per_kg": 1.9, "fat_pct": 0.28},
    "lean_bulk": {"kcal_delta": 0.10,  "protein_g_per_kg": 2.0, "fat_pct": 0.25},
    "bulk":      {"kcal_delta": 0.18,  "protein_g_per_kg": 1.8, "fat_pct": 0.25},
    "strength":  {"kcal_delta": 0.05,  "protein_g_per_kg": 2.0, "fat_pct": 0.30},
    "custom":    {"kcal_delta": 0.0,   "protein_g_per_kg": 1.8, "fat_pct": 0.28},
}


def age_from(birth_date: date | None, today: date | None = None) -> int | None:
    if birth_date is None:
        return None
    today = today or date.today()
    return today.year - birth_date.year - (
        (today.month, today.day) < (birth_date.month, birth_date.day)
    )


def bmr_mifflin_st_jeor(sex: str, weight_kg: float, height_cm: float, age: int) -> float:
    """Return BMR in kcal/day. 'unspecified' averages the two constants."""
    base = 10 * weight_kg + 6.25 * height_cm - 5 * age
    if sex == "male":
        return round(base + 5, 1)
    if sex == "female":
        return round(base - 161, 1)
    return round(base - 78, 1)  # midpoint of +5 and -161


def estimate_tdee(bmr_kcal: float, activity_level: str) -> float:
    """Initial TDEE estimate: BMR x activity multiplier (spec 19)."""
    return round(bmr_kcal * ACTIVITY_MULTIPLIERS.get(activity_level, 1.375), 1)


def calorie_target_for_goal(tdee_kcal: float, goal_type: str) -> float:
    split = MACRO_SPLITS.get(goal_type, MACRO_SPLITS["maintain"])
    return round(tdee_kcal * (1 + split["kcal_delta"]), 1)


def macro_targets(kcal_target: float, weight_kg: float, goal_type: str) -> dict:
    """Protein anchored to bodyweight; fat a % of kcal; carbs fill the remainder."""
    split = MACRO_SPLITS.get(goal_type, MACRO_SPLITS["maintain"])
    protein_g = round(split["protein_g_per_kg"] * weight_kg, 1)
    fat_g = round(kcal_target * split["fat_pct"] / 9, 1)
    remaining = kcal_target - (protein_g * 4) - (fat_g * 9)
    carbs_g = round(max(remaining, 0) / 4, 1)
    return {"kcal": kcal_target, "protein_g": protein_g, "carbs_g": carbs_g, "fat_g": fat_g}


def adaptive_tdee(
    avg_intake_kcal: float,
    weight_change_kg: float,
    days: int,
    fallback_tdee: float,
    min_days: int = 14,
) -> dict:
    """Estimate TDEE from observed energy balance.

    1 kg of body mass is taken as ~7700 kcal. If the user ate `avg_intake_kcal`
    per day and gained `weight_change_kg` over `days`, the implied daily surplus
    is weight_change*7700/days, so TDEE ~= intake - surplus.
    Returns the estimate plus a confidence tier driven by data volume (spec 19).
    """
    if days < min_days or abs(weight_change_kg) < 0.05:
        return {
            "tdee_kcal": round(fallback_tdee, 1),
            "method": "mifflin_st_jeor_activity",
            "confidence": "low",
            "days_of_data": days,
        }
    daily_surplus = (weight_change_kg * 7700) / days
    tdee = round(avg_intake_kcal - daily_surplus, 1)
    # Guard against nonsense from noisy logs.
    tdee = max(min(tdee, fallback_tdee * 1.6), fallback_tdee * 0.6)
    confidence = "high" if days >= 42 else "medium" if days >= 28 else "low"
    return {
        "tdee_kcal": tdee,
        "method": "adaptive",
        "confidence": confidence,
        "days_of_data": days,
    }
