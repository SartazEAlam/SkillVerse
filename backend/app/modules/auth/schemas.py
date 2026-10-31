"""Pydantic schemas for auth module request/response validation."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.modules.auth.models import UserRole

# ── Password validation ─────────────────────────────
_PASSWORD_PATTERN = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=\[\]{}|;':\",./<>?\\`~])"
)
_MIN_PASSWORD_LENGTH = 8


def _validate_password(password: str) -> str:
    """Validate password strength per SECURITY.md rules."""
    if len(password) < _MIN_PASSWORD_LENGTH:
        msg = f"Password must be at least {_MIN_PASSWORD_LENGTH} characters."
        raise ValueError(msg)
    if not _PASSWORD_PATTERN.match(password):
        msg = (
            "Password must contain at least one uppercase letter, one lowercase letter, "
            "one digit, and one special character."
        )
        raise ValueError(msg)
    return password


# ── Request schemas ──────────────────────────────────


class RegisterRequest(BaseModel):
    """User registration request."""

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    display_name: str = Field(..., min_length=1, max_length=100)

    @field_validator("email", mode="after")
    @classmethod
    def normalize_email(cls, v: EmailStr) -> str:
        return str(v).strip().lower()

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        return _validate_password(v)


class LoginRequest(BaseModel):
    """User login request."""

    email: EmailStr
    password: str

    @field_validator("email", mode="after")
    @classmethod
    def normalize_email(cls, v: EmailStr) -> str:
        return str(v).strip().lower()


class RefreshRequest(BaseModel):
    """Token refresh request."""

    refresh_token: str


class VerifyEmailRequest(BaseModel):
    """Email verification request."""

    token: str


class ForgotPasswordRequest(BaseModel):
    """Password reset request (initiation)."""

    email: EmailStr

    @field_validator("email", mode="after")
    @classmethod
    def normalize_email(cls, v: EmailStr) -> str:
        return str(v).strip().lower()


class ResetPasswordRequest(BaseModel):
    """Password reset completion."""

    token: str
    new_password: str = Field(..., min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        return _validate_password(v)


class DeleteAccountRequest(BaseModel):
    """Account deletion request — requires password confirmation."""

    password: str


class OAuthCallbackRequest(BaseModel):
    """OAuth callback request with authorization code and PKCE verifier."""

    code: str
    code_verifier: str
    state: str


class OAuthAuthorizeResponse(BaseModel):
    """OAuth authorization initiation response."""

    authorization_url: str
    state: str


# ── Response schemas ─────────────────────────────────


class UserResponse(BaseModel):
    """Public user representation."""

    id: str
    email: str
    role: UserRole
    email_verified: bool
    display_name: str | None = None
    avatar_url: str | None = None
    bio: str | None = None
    timezone: str | None = None
    preferences: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    model_config = {"from_attributes": True}


class AuthTokenResponse(BaseModel):
    """Authentication token pair."""

    access_token: str
    refresh_token: str
    expires_in: int  # seconds


class RegisterResponse(BaseModel):
    """Registration response."""

    user: UserResponse


class LoginResponse(BaseModel):
    """Login response with tokens."""

    access_token: str
    refresh_token: str
    expires_in: int
    user: UserResponse


class MessageResponse(BaseModel):
    """Generic message response."""

    message: str


class DeleteAccountResponse(BaseModel):
    """Account deletion response."""

    status: str = "pending_deletion"
    grace_period_days: int = 30
    scheduled_deletion_at: datetime
    message: str
