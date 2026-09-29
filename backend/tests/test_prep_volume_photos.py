"""API tests for the four bodybuilding features:
muscle volume + progressive overload, RIR/set-type, progress photos, and the
Preparation phase tracker.
"""
import io
from datetime import date, timedelta

import pytest

from app.models.training import ExerciseLibrary


@pytest.fixture()
def exercises(db_session):
    """Two known exercises with distinct muscle profiles."""
    bench = ExerciseLibrary(
        name="Barbell Bench Press", primary_muscle="Chest",
        secondary_muscles="Front Delts,Triceps", equipment="Barbell",
    )
    row = ExerciseLibrary(
        name="Seated Cable Row", primary_muscle="Lats",
        secondary_muscles="Biceps", equipment="Cable",
    )
    db_session.add_all([bench, row])
    db_session.commit()
    db_session.refresh(bench)
    db_session.refresh(row)
    return {"bench": bench.id, "row": row.id}


def _log(client, headers, exercise_id, *, days_ago=0, weight=60.0, reps=10, rir=2.0,
         set_type="normal", sets=3):
    payload = {
        "performed_on": (date.today() - timedelta(days=days_ago)).isoformat(),
        "title": "Push",
        "exercises": [{
            "exercise_id": exercise_id,
            "position": 0,
            "sets": [
                {"set_index": i + 1, "weight_kg": weight, "reps": reps, "rir": rir,
                 "set_type": set_type}
                for i in range(sets)
            ],
        }],
    }
    return client.post("/api/v1/training/workouts", json=payload, headers=headers)


class TestRirAndSetType:
    def test_rir_and_set_type_round_trip(self, client, auth_headers, exercises):
        r = _log(client, auth_headers, exercises["bench"], rir=1.0, set_type="drop")
        assert r.status_code == 201, r.text
        sets = r.json()["exercises"][0]["sets"]
        assert sets[0]["rir"] == 1.0
        assert sets[0]["set_type"] == "drop"

    def test_rir_out_of_range_is_rejected(self, client, auth_headers, exercises):
        r = _log(client, auth_headers, exercises["bench"], rir=99.0)
        assert r.status_code == 422


class TestWeeklyVolume:
    def test_volume_counts_fractional_sets_per_muscle(self, client, auth_headers, exercises):
        _log(client, auth_headers, exercises["bench"], sets=4)  # Chest 4, delts 2, tris 2
        _log(client, auth_headers, exercises["row"], days_ago=1, sets=4)  # Lats 4, biceps 2
        r = client.get("/api/v1/training/volume?weeks=4", headers=auth_headers)
        assert r.status_code == 200, r.text
        body = r.json()
        by_muscle = {m["muscle"]: m for m in body["muscles"]}
        # 4 sets in a 4-week window -> 1.0 set/week.
        assert by_muscle["Chest"]["sets_per_week"] == 1.0
        assert by_muscle["Front Delts"]["sets_per_week"] == 0.5
        assert by_muscle["Biceps"]["sets_per_week"] == 0.5
        assert body["trained_count"] >= 4

    def test_warmups_do_not_count_toward_volume(self, client, auth_headers, exercises):
        payload = {
            "performed_on": date.today().isoformat(),
            "title": "Push",
            "exercises": [{
                "exercise_id": exercises["bench"],
                "sets": [
                    {"set_index": 1, "weight_kg": 40, "reps": 10, "is_warmup": True},
                    {"set_index": 2, "weight_kg": 60, "reps": 10},
                ],
            }],
        }
        assert client.post("/api/v1/training/workouts", json=payload,
                           headers=auth_headers).status_code == 201
        body = client.get("/api/v1/training/volume?weeks=1", headers=auth_headers).json()
        chest = next(m for m in body["muscles"] if m["muscle"] == "Chest")
        assert chest["sets_per_week"] == 1.0

    def test_volume_requires_auth(self, client):
        assert client.get("/api/v1/training/volume").status_code == 401


class TestProgressionAdvice:
    def test_first_session_is_a_baseline(self, client, auth_headers, exercises):
        _log(client, auth_headers, exercises["bench"])
        r = client.get(
            f"/api/v1/training/progression/{exercises['bench']}/advice", headers=auth_headers
        )
        assert r.status_code == 200
        assert r.json()["action"] == "baseline"

    def test_more_reps_at_the_same_load_advises_more_weight(self, client, auth_headers, exercises):
        _log(client, auth_headers, exercises["bench"], days_ago=7, reps=8)
        _log(client, auth_headers, exercises["bench"], days_ago=0, reps=10)
        r = client.get(
            f"/api/v1/training/progression/{exercises['bench']}/advice", headers=auth_headers
        )
        assert r.json()["action"] == "increase"

    def test_no_history_says_so(self, client, auth_headers, exercises):
        r = client.get(
            f"/api/v1/training/progression/{exercises['row']}/advice", headers=auth_headers
        )
        assert r.json()["exists"] is False


class TestProgressPhotos:
    @pytest.fixture(autouse=True)
    def _media(self, tmp_path, monkeypatch):
        """Write uploads to a temp dir so tests never touch the repo's media folder."""
        from app.api.v1 import profile as profile_api
        monkeypatch.setattr(profile_api, "_media_root", lambda: tmp_path)

    def _png(self) -> bytes:
        # 1x1 PNG - enough to prove the upload path, not a real physique shot.
        return bytes.fromhex(
            "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
            "890000000a49444154789c6360000002000100ffff03000006000557bfabd400"
            "00000049454e44ae426082"
        )

    def test_upload_list_and_fetch_own_photo(self, client, auth_headers):
        r = client.post(
            "/api/v1/profile/photos",
            headers=auth_headers,
            data={"taken_on": date.today().isoformat(), "pose": "front", "weight_kg": "80.5"},
            files={"file": ("shot.png", io.BytesIO(self._png()), "image/png")},
        )
        assert r.status_code == 201, r.text
        photo = r.json()
        assert photo["pose"] == "front"
        assert photo["weight_kg"] == 80.5

        listing = client.get("/api/v1/profile/photos", headers=auth_headers).json()
        assert len(listing) == 1

        fetched = client.get(photo["url"], headers=auth_headers)
        assert fetched.status_code == 200
        assert fetched.content == self._png()

    def test_rejects_a_non_image(self, client, auth_headers):
        r = client.post(
            "/api/v1/profile/photos",
            headers=auth_headers,
            data={"taken_on": date.today().isoformat(), "pose": "front"},
            files={"file": ("notes.txt", io.BytesIO(b"hello"), "text/plain")},
        )
        assert r.status_code == 415

    def test_another_user_cannot_fetch_the_photo(self, client, auth_headers):
        created = client.post(
            "/api/v1/profile/photos",
            headers=auth_headers,
            data={"taken_on": date.today().isoformat(), "pose": "back"},
            files={"file": ("shot.png", io.BytesIO(self._png()), "image/png")},
        ).json()
        other = client.post("/api/v1/auth/register", json={
            "email": "intruder@example.com", "password": "TrinityTest123",
            "display_name": "Intruder",
        }).json()
        other_headers = {"Authorization": f"Bearer {other['access_token']}"}
        assert client.get(created["url"], headers=other_headers).status_code == 404

    def test_delete_photo(self, client, auth_headers):
        created = client.post(
            "/api/v1/profile/photos",
            headers=auth_headers,
            data={"taken_on": date.today().isoformat(), "pose": "side"},
            files={"file": ("shot.png", io.BytesIO(self._png()), "image/png")},
        ).json()
        assert client.delete(f"/api/v1/profile/photos/{created['id']}",
                             headers=auth_headers).status_code == 204
        assert client.get("/api/v1/profile/photos", headers=auth_headers).json() == []


class TestPreparationPhase:
    def _weigh_ins(self, client, headers, start_kg, per_week):
        """One weigh-in per week for four weeks, moving `per_week` kg each week."""
        for i in range(4):
            client.post(
                "/api/v1/profile/metrics",
                headers=headers,
                json={
                    "measured_on": (date.today() - timedelta(days=7 * (3 - i))).isoformat(),
                    "weight_kg": round(start_kg + per_week * i, 2),
                },
            )

    def test_no_phase_reports_inactive(self, client, auth_headers):
        r = client.get("/api/v1/prep/phase", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["active"] is False

    def test_cut_tracks_weekly_average_and_verdict(self, client, auth_headers):
        self._weigh_ins(client, auth_headers, 80.0, -0.4)
        created = client.post(
            "/api/v1/prep/phase",
            headers=auth_headers,
            json={"phase_type": "cut", "target_rate_pct_per_week": -0.5},
        )
        assert created.status_code == 201, created.text
        assert created.json()["start_weight_kg"] == 78.8  # latest weigh-in, used as the start

        body = client.get("/api/v1/prep/phase", headers=auth_headers).json()
        assert body["active"] is True
        assert len(body["weekly_averages"]) == 4
        assert body["actual_kg_per_week"] == -0.4
        assert body["verdict"]["verdict"] in ("on_plan", "too_slow", "too_fast")
        assert body["suggestion"]["suggested_kcal"] <= 0  # cutting -> remove, never add

    def test_starting_a_second_phase_closes_the_first(self, client, auth_headers):
        first = client.post("/api/v1/prep/phase", headers=auth_headers,
                            json={"phase_type": "cut"}).json()
        client.post("/api/v1/prep/phase", headers=auth_headers, json={"phase_type": "bulk"})
        active = client.get("/api/v1/prep/phase", headers=auth_headers).json()
        assert active["phase"]["phase_type"] == "bulk"
        assert active["phase"]["id"] != first["id"]

    def test_accept_adjustment_records_it(self, client, auth_headers):
        client.post("/api/v1/prep/phase", headers=auth_headers, json={"phase_type": "cut"})
        r = client.post("/api/v1/prep/phase/adjustment", headers=auth_headers,
                        json={"delta_kcal": -150, "apply": True})
        assert r.status_code == 200
        assert r.json()["kcal_adjustment"] == -150

    def test_refeed_can_be_logged(self, client, auth_headers):
        client.post("/api/v1/prep/phase", headers=auth_headers, json={"phase_type": "cut"})
        r = client.post("/api/v1/prep/refeeds", headers=auth_headers, json={
            "occurred_on": date.today().isoformat(), "kind": "refeed", "days": 2,
        })
        assert r.status_code == 201
        assert client.get("/api/v1/prep/refeeds", headers=auth_headers).json()[0]["days"] == 2

    def test_invalid_phase_type_is_rejected(self, client, auth_headers):
        r = client.post("/api/v1/prep/phase", headers=auth_headers, json={"phase_type": "sprint"})
        assert r.status_code == 422

    def test_prep_requires_auth(self, client):
        assert client.get("/api/v1/prep/phase").status_code == 401
