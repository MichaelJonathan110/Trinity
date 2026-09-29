"""Notification feed and preferences (spec 21)."""


class TestNotificationFeed:
    def test_requires_auth(self, client):
        assert client.get("/api/v1/notifications").status_code == 401

    def test_create_then_list(self, client, auth_headers):
        created = client.post(
            "/api/v1/notifications",
            headers=auth_headers,
            json={"kind": "insight", "title": "Protein was low", "body": "Add 30 g."},
        )
        assert created.status_code == 201
        listing = client.get("/api/v1/notifications", headers=auth_headers)
        assert listing.status_code == 200
        titles = [n["title"] for n in listing.json()]
        assert "Protein was low" in titles

    def test_mark_read(self, client, auth_headers):
        created = client.post(
            "/api/v1/notifications",
            headers=auth_headers,
            json={"kind": "system", "title": "Welcome"},
        ).json()
        assert created["read_at"] is None
        read = client.post(
            f"/api/v1/notifications/{created['id']}/read", headers=auth_headers
        )
        assert read.status_code == 200
        assert read.json()["read_at"] is not None

    def test_unread_only_filter(self, client, auth_headers):
        first = client.post(
            "/api/v1/notifications",
            headers=auth_headers,
            json={"kind": "system", "title": "Read me"},
        ).json()
        client.post(
            "/api/v1/notifications",
            headers=auth_headers,
            json={"kind": "system", "title": "Leave me"},
        )
        client.post(f"/api/v1/notifications/{first['id']}/read", headers=auth_headers)
        unread = client.get(
            "/api/v1/notifications?unread_only=true", headers=auth_headers
        ).json()
        assert [n["title"] for n in unread] == ["Leave me"]

    def test_missing_notification_is_404(self, client, auth_headers):
        r = client.post("/api/v1/notifications/999999/read", headers=auth_headers)
        assert r.status_code == 404


class TestPreferences:
    def test_defaults_are_all_enabled(self, client, auth_headers):
        r = client.get("/api/v1/notifications/preferences", headers=auth_headers)
        assert r.status_code == 200
        assert all(p["is_enabled"] for p in r.json())

    def test_toggle_persists(self, client, auth_headers):
        r = client.put(
            "/api/v1/notifications/preferences/sleep",
            headers=auth_headers,
            json={"is_enabled": False},
        )
        assert r.status_code == 200
        assert r.json() == {"kind": "sleep", "is_enabled": False}
        prefs = client.get("/api/v1/notifications/preferences", headers=auth_headers).json()
        sleep = next(p for p in prefs if p["kind"] == "sleep")
        assert sleep["is_enabled"] is False
