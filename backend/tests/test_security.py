"""Unit tests for security utilities (password hashing, JWT)."""

from __future__ import annotations

import jwt
import pytest

from app.modules.auth.security import (
    create_access_token,
    decode_access_token,
    generate_refresh_token,
    generate_verification_token,
    hash_password,
    hash_token,
    verify_password,
)


class TestPasswordHashing:
    """Tests for Argon2 password hashing."""

    def test_hash_and_verify(self) -> None:
        password = "SecureP@ss1"
        hashed = hash_password(password)
        assert hashed != password
        assert verify_password(password, hashed)

    def test_wrong_password(self) -> None:
        hashed = hash_password("SecureP@ss1")
        assert not verify_password("WrongP@ss1", hashed)

    def test_different_hashes(self) -> None:
        """Same password should produce different hashes (salt)."""
        h1 = hash_password("SecureP@ss1")
        h2 = hash_password("SecureP@ss1")
        assert h1 != h2


class TestJWT:
    """Tests for JWT token creation and validation."""

    def test_create_and_decode(self) -> None:
        token = create_access_token(user_id="user-123", role="learner")
        payload = decode_access_token(token)
        assert payload["sub"] == "user-123"
        assert payload["role"] == "learner"
        assert payload["type"] == "access"

    def test_invalid_token(self) -> None:
        with pytest.raises(jwt.PyJWTError):
            decode_access_token("not.a.valid.token")

    def test_extra_claims(self) -> None:
        token = create_access_token(
            user_id="user-123",
            role="admin",
            extra_claims={"email_verified": True},
        )
        payload = decode_access_token(token)
        assert payload["email_verified"] is True


class TestTokenGeneration:
    """Tests for refresh and verification token generation."""

    def test_refresh_token_uniqueness(self) -> None:
        tokens = {generate_refresh_token() for _ in range(100)}
        assert len(tokens) == 100

    def test_verification_token_uniqueness(self) -> None:
        tokens = {generate_verification_token() for _ in range(100)}
        assert len(tokens) == 100

    def test_hash_token_deterministic(self) -> None:
        token = "test-token-value"
        assert hash_token(token) == hash_token(token)

    def test_hash_token_different_inputs(self) -> None:
        assert hash_token("token-a") != hash_token("token-b")
