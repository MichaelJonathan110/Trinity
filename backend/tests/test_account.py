"""Password reset, data export and account deletion (spec 7, 58, 59)."""
from app.services.account_service import DELETE_CONFIRM_PHRASE


class TestPasswordReset:
    def test_request_does_not_reveal_unknown_email(self, client):
        r = client.post(
            "/api/v1/account/password-reset/request", json={"email": "nobody@example.com"}
        )
        assert r.status_code == 200
        assert r.json()["ok"] is True
        assert r.json()["dev_token"] is None

    def test_full_reset_flow_changes_the_password(self, client):
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "reset@example.com",
                "password": "OriginalPass123",
                "display_name": "Reset User",
            },
        )
        req = client.post(
            "/api/v1/account/password-reset/request", json={"email": "reset@example.com"}
        )
        token = req.json()["dev_token"]
        assert token

        confirm = client.post(
            "/api/v1/account/password-reset/confirm",
            json={"token": token, "new_password": "BrandNewPass456"},
        )
        assert confirm.status_code == 200

        old = client.post(
            "/api/v1/auth/login",
            json={"email": "reset@example.com", "password": "OriginalPass123"},
        )
        assert old.status_code == 401
        new = client.post(
            "/api/v1/auth/login",
            json={"email": "reset@example.com", "password": "BrandNewPass456"},
        )
        assert new.status_code == 200

    def test_token_is_single_use(self, client):
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "once@example.com",
                "password": "OriginalPass123",
                "display_name": "Once User",
            },
        )
        token = client.post(
            "/api/v1/account/password-reset/request", json={"email": "once@example.com"}
        ).json()["dev_token"]
        first = client.post(
            "/api/v1/account/password-reset/confirm",
            json={"token": token, "new_password": "AnotherPass789"},
        )
        assert first.status_code == 200
        second = client.post(
            "/api/v1/account/password-reset/confirm",
            json={"token": token, "new_password": "YetAnother123"},
        )
        assert second.status_code == 400

    def test_bad_token_rejected(self, client):
        r = client.post(
            "/api/v1/account/password-reset/confirm",
            json={"token": "not-a-real-token", "new_password": "WhateverPass123"},
        )
        assert r.status_code == 400


class TestExport:
    def test_export_requires_auth(self, client):
        assert client.get("/api/v1/account/export").status_code == 401

    def test_export_returns_own_account(self, client, auth_headers):
        r = client.get("/api/v1/account/export", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert body["account"]["email"] == "fixture@example.com"
        assert "data" in body
        assert "body_metrics" in body["data"]


class TestDeletion:
    def test_wrong_confirmation_phrase_rejected(self, client, auth_headers):
        r = client.post(
            "/api/v1/account/delete",
            headers=auth_headers,
            json={"password": "TrinityTest123", "confirm": "nope"},
        )
        assert r.status_code == 400

    def test_wrong_password_rejected(self, client, auth_headers):
        r = client.post(
            "/api/v1/account/delete",
            headers=auth_headers,
            json={"password": "WrongPass999", "confirm": DELETE_CONFIRM_PHRASE},
        )
        assert r.status_code == 401

    def test_delete_removes_the_account(self, client, auth_headers):
        r = client.post(
            "/api/v1/account/delete",
            headers=auth_headers,
            json={"password": "TrinityTest123", "confirm": DELETE_CONFIRM_PHRASE},
        )
        assert r.status_code == 204
        login = client.post(
            "/api/v1/auth/login",
            json={"email": "fixture@example.com", "password": "TrinityTest123"},
        )
        assert login.status_code == 401
