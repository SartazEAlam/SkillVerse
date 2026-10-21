"""Tests for rate limiting on auth endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient


class TestRateLimiting:
    """Tests rate limit enforcement on login and registration."""

    def test_login_rate_limit(self, client: TestClient) -> None:
        """Exceeding 10 login attempts within 15 minutes should return HTTP 429."""
        # 10 attempts allowed
        for i in range(10):
            resp = client.post(
                "/api/v1/auth/login",
                json={"email": f"test{i}@example.com", "password": "WrongPassword!9"},
            )
            assert resp.status_code == 401

        # 11th attempt must be blocked by rate limiter
        blocked = client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "WrongPassword!9"},
        )
        assert blocked.status_code == 429
        data = blocked.json()
        assert data["error"]["code"] == "RATE_LIMITED"
        assert "Retry-After" in blocked.headers
        assert "X-RateLimit-Limit" in blocked.headers

    def test_registration_rate_limit(self, client: TestClient) -> None:
        """Exceeding 5 registrations within 1 hour should return HTTP 429."""
        # 5 attempts allowed
        for i in range(5):
            resp = client.post(
                "/api/v1/auth/register",
                json={
                    "email": f"newuser{i}@example.com",
                    "password": "SecureP@ss1",
                    "display_name": f"User {i}",
                },
            )
            assert resp.status_code == 201

        # 6th attempt must be blocked
        blocked = client.post(
            "/api/v1/auth/register",
            json={
                "email": "anotheruser@example.com",
                "password": "SecureP@ss1",
                "display_name": "Another User",
            },
        )
        assert blocked.status_code == 429
        data = blocked.json()
        assert data["error"]["code"] == "RATE_LIMITED"
