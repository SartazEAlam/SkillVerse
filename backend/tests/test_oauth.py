"""Integration tests for OAuth 2.0 PKCE flow."""

from __future__ import annotations

from fastapi.testclient import TestClient


class TestOAuthPKCE:
    """Tests for GET /api/v1/auth/oauth/{provider}/authorize and POST callback."""

    def test_authorize_url_generation(self, client: TestClient) -> None:
        response = client.get(
            "/api/v1/auth/oauth/google/authorize",
            params={
                "code_challenge": "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM",
                "code_challenge_method": "S256",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "authorization_url" in data
        assert "accounts.google.com" in data["authorization_url"]
        assert "code_challenge=" in data["authorization_url"]
        assert "code_challenge_method=S256" in data["authorization_url"]
        assert "state=" in data["authorization_url"]
        assert "state" in data

    def test_authorize_unsupported_provider(self, client: TestClient) -> None:
        response = client.get(
            "/api/v1/auth/oauth/unsupported/authorize",
            params={
                "code_challenge": "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM",
                "code_challenge_method": "S256",
            },
        )
        assert response.status_code == 400

    def test_authorize_invalid_challenge_method(self, client: TestClient) -> None:
        response = client.get(
            "/api/v1/auth/oauth/google/authorize",
            params={
                "code_challenge": "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM",
                "code_challenge_method": "plain",
            },
        )
        assert response.status_code == 400

    def test_callback_invalid_state_csrf(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/auth/oauth/google/callback",
            json={
                "code": "mock_code",
                "code_verifier": "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk",
                "state": "unrecognized-or-expired-state-token",
            },
        )
        assert response.status_code == 401

    def test_callback_success_provisions_user(self, client: TestClient) -> None:
        # Step 1: Request authorize to generate valid state
        auth_resp = client.get(
            "/api/v1/auth/oauth/google/authorize",
            params={
                "code_challenge": "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM",
                "code_challenge_method": "S256",
            },
        )
        assert auth_resp.status_code == 200
        state = auth_resp.json()["state"]

        # Step 2: Callback with mock code: mock_<subId>:<email>:<name>
        cb_resp = client.post(
            "/api/v1/auth/oauth/google/callback",
            json={
                "code": "mock_google_123:oauthlearner@example.com:OAuth Learner",
                "code_verifier": "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk",
                "state": state,
            },
        )
        assert cb_resp.status_code == 200
        data = cb_resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["user"]["email"] == "oauthlearner@example.com"
        assert data["user"]["display_name"] == "OAuth Learner"
        assert data["user"]["email_verified"] is True
        assert data["user"]["role"] == "learner"

    def test_callback_subsequent_login_existing_user(self, client: TestClient) -> None:
        # First login provisions user
        resp1 = client.get(
            "/api/v1/auth/oauth/google/authorize",
            params={"code_challenge": "abc", "code_challenge_method": "S256"},
        )
        state1 = resp1.json()["state"]
        cb1 = client.post(
            "/api/v1/auth/oauth/google/callback",
            json={
                "code": "mock_google_456:repeat@example.com:Repeat User",
                "code_verifier": "verifier1",
                "state": state1,
            },
        )
        assert cb1.status_code == 200
        user_id = cb1.json()["user"]["id"]

        # Second login with same provider account logs in the same user
        resp2 = client.get(
            "/api/v1/auth/oauth/google/authorize",
            params={"code_challenge": "def", "code_challenge_method": "S256"},
        )
        state2 = resp2.json()["state"]
        cb2 = client.post(
            "/api/v1/auth/oauth/google/callback",
            json={
                "code": "mock_google_456:repeat@example.com:Repeat User",
                "code_verifier": "verifier2",
                "state": state2,
            },
        )
        assert cb2.status_code == 200
        assert cb2.json()["user"]["id"] == user_id

    def test_authorize_rejects_unauthorized_redirect_uri(self, client: TestClient) -> None:
        response = client.get(
            "/api/v1/auth/oauth/google/authorize",
            params={
                "code_challenge": "abc",
                "code_challenge_method": "S256",
                "redirect_uri": "https://attacker-controlled-site.com/steal-token",
            },
        )
        assert response.status_code == 400

    def test_callback_rejects_unauthorized_redirect_uri(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/auth/oauth/google/callback",
            params={"redirect_uri": "https://attacker-controlled-site.com/steal-token"},
            json={
                "code": "mock_code",
                "code_verifier": "verifier",
                "state": "any-state",
            },
        )
        assert response.status_code == 400
