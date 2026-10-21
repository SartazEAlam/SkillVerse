"""Security utilities: password hashing (Argon2), JWT token management, and helpers."""

from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

from app.config import settings

# ── Password hashing (Argon2id) ─────────────────────

_password_hash = PasswordHash((Argon2Hasher(),))


def hash_password(password: str) -> str:
    """Hash a plaintext password with Argon2id."""
    return _password_hash.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    """Verify a plaintext password against an Argon2id hash."""
    return _password_hash.verify(password, hashed)


# ── JWT tokens ───────────────────────────────────────


def create_access_token(
    user_id: str,
    role: str,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """Create a signed JWT access token."""
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": user_id,
        "role": role,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_access_token_expire_minutes),
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT access token. Raises jwt.PyJWTError on failure."""
    payload: dict[str, Any] = jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )
    if payload.get("type") != "access":
        raise jwt.InvalidTokenError("Not an access token")
    return payload


# ── Refresh tokens ───────────────────────────────────


def generate_refresh_token() -> str:
    """Generate a cryptographically random refresh token string."""
    return secrets.token_urlsafe(48)


def hash_token(token: str) -> str:
    """SHA-256 hash a token for safe database storage."""
    return hashlib.sha256(token.encode()).hexdigest()


# ── Verification / reset tokens ──────────────────────


def generate_verification_token() -> str:
    """Generate a short-lived verification token."""
    return secrets.token_urlsafe(32)
