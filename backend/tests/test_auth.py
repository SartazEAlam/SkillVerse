"""Integration tests for auth API endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient


class TestRegistration:
    """Tests for POST /api/v1/auth/register."""

    def test_register_success(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "new@example.com",
                "password": "SecureP@ss1",
                "display_name": "New User",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["user"]["email"] == "new@example.com"
        assert data["user"]["role"] == "learner"
        assert data["user"]["email_verified"] is False
        assert data["user"]["display_name"] == "New User"

    def test_register_duplicate_email(self, client: TestClient) -> None:
        # First registration
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "dup@example.com",
                "password": "SecureP@ss1",
                "display_name": "User 1",
            },
        )
        # Duplicate
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "dup@example.com",
                "password": "SecureP@ss1",
                "display_name": "User 2",
            },
        )
        assert response.status_code == 409

    def test_register_and_login_email_case_insensitivity(self, client: TestClient) -> None:
        # Register with mixed-case email
        reg_resp = client.post(
            "/api/v1/auth/register",
            json={
                "email": "CaseInsensitive@Example.com",
                "password": "SecureP@ss1",
                "display_name": "Case User",
            },
        )
        assert reg_resp.status_code == 201
        assert reg_resp.json()["user"]["email"] == "caseinsensitive@example.com"

        # Duplicate register with lowercase should be blocked
        dup_resp = client.post(
            "/api/v1/auth/register",
            json={
                "email": "caseinsensitive@example.com",
                "password": "SecureP@ss1",
                "display_name": "Case User 2",
            },
        )
        assert dup_resp.status_code == 409

        # Login with uppercase should succeed
        login_resp = client.post(
            "/api/v1/auth/login",
            json={
                "email": "CASEINSENSITIVE@EXAMPLE.COM",
                "password": "SecureP@ss1",
            },
        )
        assert login_resp.status_code == 200

    def test_register_weak_password(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "weak@example.com",
                "password": "short",
                "display_name": "Weak User",
            },
        )
        assert response.status_code == 422  # Pydantic validation

    def test_register_invalid_email(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "password": "SecureP@ss1",
                "display_name": "Invalid Email",
            },
        )
        assert response.status_code == 422


class TestLogin:
    """Tests for POST /api/v1/auth/login."""

    def test_login_success(self, client: TestClient, registered_user: dict) -> None:
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "SecureP@ss1"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["expires_in"] > 0
        assert data["user"]["email"] == "test@example.com"

    def test_login_wrong_password(self, client: TestClient, registered_user: dict) -> None:
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "WrongP@ss1"},
        )
        assert response.status_code == 401

    def test_login_nonexistent_user(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "noone@example.com", "password": "SecureP@ss1"},
        )
        assert response.status_code == 401

    def test_login_generic_error_message(self, client: TestClient) -> None:
        """Login errors should use generic messages to prevent email enumeration."""
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "noone@example.com", "password": "SecureP@ss1"},
        )
        data = response.json()
        error_msg = data.get("error", {}).get("message") or data.get("detail", {}).get(
            "error", {}
        ).get("message")
        assert "Invalid email or password" in error_msg


class TestTokenRefresh:
    """Tests for POST /api/v1/auth/refresh."""

    def test_refresh_success(self, client: TestClient, auth_tokens: dict) -> None:
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": auth_tokens["refresh_token"]},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        # New refresh token should be different (rotation)
        assert data["refresh_token"] != auth_tokens["refresh_token"]

    def test_refresh_invalid_token(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid-token"},
        )
        assert response.status_code == 401

    def test_refresh_reuse_revoked_token(self, client: TestClient, auth_tokens: dict) -> None:
        """Using a refresh token after rotation should fail."""
        # First refresh (revokes original)
        client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": auth_tokens["refresh_token"]},
        )
        # Try to reuse old token
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": auth_tokens["refresh_token"]},
        )
        assert response.status_code == 401


class TestLogout:
    """Tests for POST /api/v1/auth/logout."""

    def test_logout_success(self, client: TestClient, auth_headers: dict[str, str]) -> None:
        response = client.post("/api/v1/auth/logout", headers=auth_headers)
        assert response.status_code == 200

    def test_logout_without_auth(self, client: TestClient) -> None:
        response = client.post("/api/v1/auth/logout")
        assert response.status_code == 401


class TestForgotPassword:
    """Tests for POST /api/v1/auth/forgot-password."""

    def test_always_returns_200(self, client: TestClient) -> None:
        """Should always return 200 to prevent email enumeration."""
        response = client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "noone@example.com"},
        )
        assert response.status_code == 200
