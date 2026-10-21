"""Integration tests for Users API (profile management, preferences, GDPR export, soft deletion)."""

from __future__ import annotations

from fastapi.testclient import TestClient


class TestUserProfile:
    """Tests for GET and PATCH /api/v1/users/me."""

    def test_get_me_unauthorized(self, client: TestClient) -> None:
        response = client.get("/api/v1/users/me")
        assert response.status_code == 401

    def test_get_me_success(self, client: TestClient, auth_headers: dict[str, str]) -> None:
        response = client.get("/api/v1/users/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["display_name"] == "Test User"
        assert data["role"] == "learner"

    def test_update_me_profile_fields(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        update_data = {
            "display_name": "Updated Name",
            "bio": "Software developer & lifelong learner",
            "timezone": "Europe/London",
            "avatar_url": "https://example.com/avatar.png",
        }
        response = client.patch("/api/v1/users/me", json=update_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["display_name"] == "Updated Name"
        assert data["bio"] == "Software developer & lifelong learner"
        assert data["timezone"] == "Europe/London"
        assert data["avatar_url"] == "https://example.com/avatar.png"

        # Verify persistence with GET
        get_resp = client.get("/api/v1/users/me", headers=auth_headers)
        assert get_resp.status_code == 200
        assert get_resp.json()["display_name"] == "Updated Name"


class TestUserPreferences:
    """Tests for PATCH /api/v1/users/me/preferences."""

    def test_update_preferences(self, client: TestClient, auth_headers: dict[str, str]) -> None:
        pref_data = {
            "theme": "dark",
            "reduced_motion": True,
            "language": "en",
        }
        response = client.patch(
            "/api/v1/users/me/preferences", json=pref_data, headers=auth_headers
        )
        assert response.status_code == 200


class TestGDPRExport:
    """Tests for GET /api/v1/users/me/export."""

    def test_export_data_structure(self, client: TestClient, auth_headers: dict[str, str]) -> None:
        response = client.get("/api/v1/users/me/export", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "manifest" in data
        assert data["manifest"]["format_version"] == "1.0"
        assert "user" in data
        assert data["user"]["email"] == "test@example.com"
        assert "profile" in data
        assert data["profile"]["display_name"] == "Test User"


class TestAccountDeletion:
    """Tests for DELETE /api/v1/users/me."""

    def test_delete_account_wrong_password(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        response = client.request(
            "DELETE",
            "/api/v1/users/me",
            json={"password": "WrongPassword!9"},
            headers=auth_headers,
        )
        assert response.status_code == 401

    def test_delete_account_success(self, client: TestClient, auth_headers: dict[str, str]) -> None:
        response = client.request(
            "DELETE",
            "/api/v1/users/me",
            json={"password": "SecureP@ss1"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pending_deletion"
        assert data["grace_period_days"] == 30
        assert "scheduled_deletion_at" in data

        # Subsequent login attempt should fail
        login_resp = client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "SecureP@ss1"},
        )
        assert login_resp.status_code == 401
