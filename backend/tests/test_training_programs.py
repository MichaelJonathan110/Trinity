"""Training programs: saving a program must work (regression test).

Before the fix, POST /training/programs returned a 500 because the response model
could not validate the ORM program's days. This locks the behaviour down.
"""


class TestProgramSave:
    def test_create_program_succeeds_and_returns_days(self, client, auth_headers):
        payload = {
            "name": "Upper / Lower",
            "goal": "hypertrophy",
            "days": [
                {"day_index": 0, "title": "Upper A", "is_rest": False},
                {"day_index": 1, "title": "Rest", "is_rest": True},
                {"day_index": 2, "title": "Lower A", "is_rest": False},
            ],
        }
        r = client.post("/api/v1/training/programs", json=payload, headers=auth_headers)
        assert r.status_code == 201, r.text
        body = r.json()
        assert body["name"] == "Upper / Lower"
        assert body["is_active"] is False
        assert len(body["days"]) == 3
        assert body["days"][1] == {"day_index": 1, "title": "Rest", "is_rest": True}

    def test_saved_program_appears_in_list(self, client, auth_headers):
        client.post(
            "/api/v1/training/programs",
            json={
                "name": "Push / Pull / Legs",
                "days": [{"day_index": 0, "title": "Push", "is_rest": False}],
            },
            headers=auth_headers,
        )
        r = client.get("/api/v1/training/programs", headers=auth_headers)
        assert r.status_code == 200
        names = [p["name"] for p in r.json()]
        assert "Push / Pull / Legs" in names

    def test_activate_program(self, client, auth_headers):
        created = client.post(
            "/api/v1/training/programs",
            json={"name": "Strength Block", "days": []},
            headers=auth_headers,
        ).json()
        r = client.post(
            f"/api/v1/training/programs/{created['id']}/activate", headers=auth_headers
        )
        assert r.status_code == 200
        assert r.json()["active_program_id"] == created["id"]

    def test_programs_require_auth(self, client):
        assert client.get("/api/v1/training/programs").status_code == 401
        assert client.post("/api/v1/training/programs", json={"name": "x"}).status_code == 401

    def test_blank_name_rejected(self, client, auth_headers):
        r = client.post(
            "/api/v1/training/programs", json={"name": ""}, headers=auth_headers
        )
        assert r.status_code == 422
