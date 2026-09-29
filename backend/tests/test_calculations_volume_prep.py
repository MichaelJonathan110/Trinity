"""Unit tests for the pure maths behind volume landmarks and phase rates."""
from datetime import date, timedelta

from app.calculations.prep import (
    phase_verdict, rate_pct_per_week, suggest_kcal_adjustment, trend_kg_per_week,
    weekly_averages,
)
from app.calculations.volume import (
    canonical_muscle, landmark_status, set_credits, volume_analysis,
)


class TestVolumeMaths:
    def test_primary_gets_a_full_set_and_secondaries_half(self):
        credits = set_credits("Chest", "Front Delts, Triceps")
        assert credits == {"Chest": 1.0, "Front Delts": 0.5, "Triceps": 0.5}

    def test_catalogue_labels_roll_up_into_canonical_groups(self):
        assert canonical_muscle("Upper Chest") == "Chest"
        assert canonical_muscle("lats") == "Lats"
        assert canonical_muscle("abs") == "Core"
        assert canonical_muscle("not a muscle") is None

    def test_secondary_never_double_counts_the_primary(self):
        credits = set_credits("Chest", "Chest")
        assert credits == {"Chest": 1.0}

    def test_landmark_bands(self):
        assert landmark_status(0, "Chest") == "none"
        assert landmark_status(5, "Chest") == "below_mev"      # MEV 8
        assert landmark_status(10, "Chest") == "maintenance"    # 8 <= x < 11.2
        assert landmark_status(14, "Chest") == "optimal"        # <= MRV 22
        assert landmark_status(30, "Chest") == "above_mrv"

    def test_analysis_divides_by_the_window_length(self):
        rows = volume_analysis({"Chest": 28.0}, weeks=4)
        chest = next(r for r in rows if r["muscle"] == "Chest")
        assert chest["sets_per_week"] == 7.0
        assert chest["status"] == "below_mev"


class TestPhaseMaths:
    def test_weekly_averages_bucket_by_iso_week(self):
        monday = date(2026, 1, 5)
        rows = [
            {"measured_on": monday, "weight_kg": 80.0},
            {"measured_on": monday + timedelta(days=2), "weight_kg": 82.0},
            {"measured_on": monday + timedelta(days=7), "weight_kg": 79.0},
            {"measured_on": monday + timedelta(days=3), "weight_kg": None},  # skipped
        ]
        weekly = weekly_averages(rows)
        assert len(weekly) == 2
        assert weekly[0]["avg_kg"] == 81.0
        assert weekly[0]["n"] == 2
        assert weekly[1]["avg_kg"] == 79.0

    def test_trend_is_none_without_two_weeks(self):
        one = weekly_averages([{"measured_on": date(2026, 1, 5), "weight_kg": 80.0}])
        assert trend_kg_per_week(one) is None

    def test_trend_is_the_weekly_slope(self):
        monday = date(2026, 1, 5)
        rows = [
            {"measured_on": monday + timedelta(days=7 * i), "weight_kg": 80.0 - 0.5 * i}
            for i in range(4)
        ]
        assert trend_kg_per_week(weekly_averages(rows)) == -0.5

    def test_rate_is_a_percentage_of_bodyweight(self):
        assert rate_pct_per_week(-0.4, 80.0) == -0.5
        assert rate_pct_per_week(None, 80.0) is None
        assert rate_pct_per_week(-0.4, None) is None

    def test_verdict_is_unknown_before_two_weeks(self):
        assert phase_verdict("cut", None, -0.5)["verdict"] == "unknown"

    def test_verdict_on_plan_within_tolerance(self):
        assert phase_verdict("cut", -0.5, -0.5)["verdict"] == "on_plan"
        assert phase_verdict("cut", -0.3, -0.5)["verdict"] == "on_plan"

    def test_cut_losing_too_slowly(self):
        assert phase_verdict("cut", 0.1, -0.5)["verdict"] == "too_slow"

    def test_bulk_gaining_too_fast_warns_about_fat(self):
        verdict = phase_verdict("bulk", 1.2, 0.35)
        assert verdict["verdict"] == "too_fast"
        assert "fat" in verdict["detail"]

    def test_adjustment_is_clamped_and_directional(self):
        # Losing far too slowly in a cut -> remove calories.
        cut = suggest_kcal_adjustment(-0.5, 0.5, 80.0)
        assert cut["suggested_kcal"] < 0
        assert cut["suggested_kcal"] >= -300
        # Gaining too slowly in a bulk -> add calories.
        bulk = suggest_kcal_adjustment(0.5, -0.5, 80.0)
        assert bulk["suggested_kcal"] > 0
        assert bulk["suggested_kcal"] <= 300

    def test_no_adjustment_when_data_is_missing(self):
        assert suggest_kcal_adjustment(None, None, None)["suggested_kcal"] == 0
