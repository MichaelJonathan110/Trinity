"""Weight entered with height on the Account page must persist and unlock TDEE.

Regression guard: weight is a dated body metric, not a profile column, so the
Account page saves height (PATCH /profile) and weight (POST /profile/metrics)
from the same card and button. Before this, weight sat behind its own button and
a user who saved the profile left weight unset, so TDEE stayed blocked on it.
"""
from datetime import date

from sqlalchemy import select

from app.models.user import BodyMetric


class TestWeightUnlocksTdee:
    def _save_profile_card(self, client, headers, *, weight):
        """Mirror exactly what the Account page's single Save does."""
        patched = client.patch(
            "/api/v1/profile",
            headers=headers,
            json={
                "display_name": "Fixture Athlete",
                "birth_date": "1995-06-01",
                "sex": "male",
                "height_cm": 178,
                "activity_level": "moderate",
            },
        )
        assert patched.status_code == 200, patched.text
        if weight is not None:
            metric = client.post(
                "/api/v1/profile/metrics",
                headers=headers,
                json={"measured_on": date.today().isoformat(), "weight_kg": weight},
            )
            assert metric.status_code == 201, metric.text
            return metric
        return None

    def test_saving_weight_with_height_makes_tdee_ready(self, client, auth_headers):
        self._save_profile_card(client, auth_headers, weight=77.5)
        tdee = client.get("/api/v1/nutrition/tdee", headers=auth_headers)
        assert tdee.status_code == 200, tdee.text
        body = tdee.json()
        assert body["ready"] is True, body
        assert "weight" not in body.get("missing", [])
        assert body["tdee_kcal"] > body["bmr_kcal"] > 0

    def test_profile_without_weight_is_blocked_on_weight(self, client, auth_headers):
        self._save_profile_card(client, auth_headers, weight=None)
        body = client.get("/api/v1/nutrition/tdee", headers=auth_headers).json()
        assert body["ready"] is False
        assert "weight" in body["missing"]

    def test_weight_is_written_to_body_metrics(self, client, auth_headers, db_session):
        self._save_profile_card(client, auth_headers, weight=81.2)
        rows = list(db_session.scalars(select(BodyMetric)))
        assert [float(r.weight_kg) for r in rows] == [81.2]

    def test_resaving_same_day_updates_rather_than_duplicates(self, client, auth_headers, db_session):
        self._save_profile_card(client, auth_headers, weight=80.0)
        self._save_profile_card(client, auth_headers, weight=79.4)
        rows = list(db_session.scalars(select(BodyMetric)))
        assert len(rows) == 1  # one weigh-in per day, corrected in place
        assert float(rows[0].weight_kg) == 79.4
