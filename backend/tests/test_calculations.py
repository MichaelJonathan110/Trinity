"""Unit tests for app.calculations - pure, deterministic, no I/O."""
from datetime import date, datetime

import pytest

from app.calculations import bodycomp, nutrition, recovery, training


# --------------------------------------------------------------- bodycomp
class TestBmr:
    def test_male(self):
        # 10*80 + 6.25*180 - 5*30 + 5 = 1780.0
        assert bodycomp.bmr_mifflin_st_jeor("male", 80, 180, 30) == 1780.0

    def test_female(self):
        # 800 + 1125 - 150 - 161 = 1614.0
        assert bodycomp.bmr_mifflin_st_jeor("female", 80, 180, 30) == 1614.0

    def test_unspecified_is_midpoint(self):
        male = bodycomp.bmr_mifflin_st_jeor("male", 80, 180, 30)
        female = bodycomp.bmr_mifflin_st_jeor("female", 80, 180, 30)
        mid = bodycomp.bmr_mifflin_st_jeor("unspecified", 80, 180, 30)
        assert abs(mid - (male + female) / 2) < 0.5

    def test_tdee_uses_activity_multiplier(self):
        assert bodycomp.estimate_tdee(1780.0, "moderate") == 2759.0
        assert bodycomp.estimate_tdee(1780.0, "sedentary") == 2136.0

    def test_cut_is_20pct_below_maintenance(self):
        assert bodycomp.calorie_target_for_goal(2500.0, "cut") == 2000.0
        assert bodycomp.calorie_target_for_goal(2500.0, "maintain") == 2500.0

    def test_macros_protein_anchored_to_weight(self):
        m = bodycomp.macro_targets(2200.0, 80.0, "cut")
        assert m["protein_g"] == 176.0          # 2.2 g/kg * 80
        assert m["fat_g"] > 0 and m["carbs_g"] > 0
        kcal = m["protein_g"] * 4 + m["carbs_g"] * 4 + m["fat_g"] * 9
        assert abs(kcal - 2200.0) < 5

    def test_age_from_handles_birthday_not_yet_reached(self):
        assert bodycomp.age_from(date(1990, 6, 15), date(2026, 9, 29)) == 36
        assert bodycomp.age_from(date(1990, 12, 31), date(2026, 9, 29)) == 35
        assert bodycomp.age_from(None) is None

    def test_adaptive_tdee_falls_back_with_little_data(self):
        r = bodycomp.adaptive_tdee(2000.0, -0.5, 5, fallback_tdee=2500.0)
        assert r["method"] == "mifflin_st_jeor_activity"
        assert r["tdee_kcal"] == 2500.0
        assert r["confidence"] == "low"

    def test_adaptive_tdee_uses_observed_balance(self):
        # ate 2500/day, gained 1 kg over 28 days -> surplus 275/day -> TDEE ~2225
        r = bodycomp.adaptive_tdee(2500.0, 1.0, 28, fallback_tdee=2500.0)
        assert r["method"] == "adaptive"
        assert r["tdee_kcal"] == pytest.approx(2225.0, abs=1.0)


# -------------------------------------------------------------- nutrition
class TestNutrition:
    def test_scale_nutrients(self):
        per100 = {"calories_kcal": 100, "protein_g": 10, "carbs_g": 20, "fat_g": 5}
        out = nutrition.scale_nutrients(per100, 150)
        assert out == {"kcal": 150.0, "protein_g": 15.0, "carbs_g": 30.0, "fat_g": 7.5}

    def test_serving_to_grams_uses_own_serving_weight(self):
        assert nutrition.serving_to_grams(2, 30) == 60.0

    def test_serving_to_grams_rejects_undefined_weight(self):
        with pytest.raises(ValueError):
            nutrition.serving_to_grams(1, None)
        with pytest.raises(ValueError):
            nutrition.serving_to_grams(1, 0)

    def test_meal_totals_sums_items(self):
        items = [
            {"kcal": 100, "protein_g": 10, "carbs_g": 5, "fat_g": 2},
            {"kcal": 250, "protein_g": 20, "carbs_g": 30, "fat_g": 8},
        ]
        t = nutrition.meal_totals(items)
        assert t == {"kcal": 350.0, "protein_g": 30.0, "carbs_g": 35.0, "fat_g": 10.0}

    def test_recipe_totals_derived_from_ingredients(self):
        ing = [{"per_100g": {"calories_kcal": 200, "protein_g": 10}, "quantity_g": 50}]
        t = nutrition.recipe_totals(ing)
        assert t["kcal"] == 100.0
        assert t["protein_g"] == 5.0


# --------------------------------------------------------------- recovery
class TestRecovery:
    def test_sleep_duration_overnight(self):
        assert recovery.sleep_duration_minutes(
            datetime(2026, 1, 1, 23, 0), datetime(2026, 1, 2, 7, 0)
        ) == 480

    def test_sleep_duration_inverted_returns_zero(self):
        assert recovery.sleep_duration_minutes(
            datetime(2026, 1, 2, 7, 0), datetime(2026, 1, 1, 23, 0)
        ) == 0

    def test_sleep_score_full_night_no_quality(self):
        assert recovery.sleep_score(480, 480) == 90

    def test_sleep_score_bounded(self):
        assert 0 <= recovery.sleep_score(0, 480) <= 100
        assert 0 <= recovery.sleep_score(1200, 480, quality=5) <= 100

    def test_consistency_needs_three_points(self):
        assert recovery.consistency_score([10, 20]) == 0
        assert recovery.consistency_score([0, 0, 0]) == 100

    def test_readiness_all_green_is_100(self):
        r = recovery.readiness_score(480, 480, days_since_rest=0, subjective=5, steps_yesterday=10000)
        assert r["score"] == 100
        assert r["label"] == "good"

    def test_readiness_without_data_reports_insufficient(self):
        r = recovery.readiness_score(None, days_since_rest=0)
        assert 0 <= r["score"] <= 100

    def test_readiness_penalises_training_load(self):
        fresh = recovery.readiness_score(480, days_since_rest=0)
        loaded = recovery.readiness_score(480, days_since_rest=4)
        assert loaded["score"] < fresh["score"]


# --------------------------------------------------------------- training
class TestTraining:
    def test_set_volume(self):
        assert training.set_volume(100, 5) == 500.0
        assert training.set_volume(None, 5) == 0.0

    def test_session_volume_excludes_warmups(self):
        sets = [
            {"weight_kg": 60, "reps": 10, "is_warmup": True},
            {"weight_kg": 100, "reps": 5, "is_warmup": False},
            {"weight_kg": 100, "reps": 4, "is_warmup": False},
        ]
        assert training.session_volume(sets) == 900.0

    def test_epley_1rm(self):
        assert training.epley_1rm(100, 5) == 116.7
        assert training.epley_1rm(100, 0) is None

    def test_best_e1rm_ignores_warmups(self):
        sets = [
            {"weight_kg": 60, "reps": 5, "is_warmup": True},
            {"weight_kg": 100, "reps": 5, "is_warmup": False},
        ]
        assert training.best_e1rm(sets) == 116.7
