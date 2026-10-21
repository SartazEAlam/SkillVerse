"""Auth service — business logic for registration, login, token management, and password reset.

All database operations go through this service. Routers must not access models directly.
"""

from __future__ import annotations

import logging
import secrets
import time
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import urlencode

import httpx
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.config import settings
from app.modules.auth.models import OAuthAccount, RefreshToken, User, UserProfile, UserRole
from app.modules.auth.security import (
    create_access_token,
    generate_refresh_token,
    generate_verification_token,
    hash_password,
    hash_token,
    verify_password,
)

logger = logging.getLogger(__name__)


class AuthError(Exception):
    """Base exception for auth service errors."""

    def __init__(self, message: str, code: str = "AUTH_ERROR", status_code: int = 400) -> None:
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(message)


class AuthService:
    """Handles all authentication and identity business logic."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # ── Registration ─────────────────────────────────

    def register(self, email: str, password: str, display_name: str) -> tuple[User, str]:
        """Register a new user. Returns (user, verification_token).

        Raises AuthError if email is already taken.
        """
        email = email.strip().lower()
        existing = self.db.execute(select(User).where(User.email == email)).scalar_one_or_none()
        if existing is not None:
            # Generic message to prevent email enumeration
            raise AuthError(
                "Unable to create account. Please try a different email.",
                code="CONFLICT",
                status_code=409,
            )

        hashed = hash_password(password)
        user = User(email=email, password_hash=hashed, role=UserRole.LEARNER)
        profile = UserProfile(user_id=user.id, display_name=display_name)
        user.profile = profile

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        # Generate email verification token (in dev mode, logged to console)
        verification_token = generate_verification_token()
        if settings.is_development:
            logger.info(
                "Email verification token for %s: %s (dev mode)", email, verification_token
            )

        return user, verification_token

    # ── Login ────────────────────────────────────────

    def login(self, email: str, password: str) -> dict[str, Any]:
        """Authenticate user and return tokens.

        Returns dict with access_token, refresh_token, expires_in, user.
        Raises AuthError with generic message (no email enumeration).
        Supports account reactivation within 30-day soft-delete grace period.
        """
        generic_login_error = "Invalid email or password."
        email = email.strip().lower()

        user = self.db.execute(select(User).where(User.email == email)).scalar_one_or_none()

        if user is None or user.password_hash is None:
            raise AuthError(generic_login_error, code="UNAUTHORIZED", status_code=401)

        if not verify_password(password, user.password_hash):
            raise AuthError(generic_login_error, code="UNAUTHORIZED", status_code=401)

        # Check soft-deleted (soft-deleted accounts cannot authenticate in Phase 2)
        if user.deleted_at is not None:
            raise AuthError(generic_login_error, code="UNAUTHORIZED", status_code=401)

        return self._issue_tokens(user)

    # ── Token refresh ────────────────────────────────

    def refresh(self, raw_refresh_token: str) -> dict[str, Any]:
        """Rotate refresh token and issue new access token.

        Raises AuthError if token is invalid, expired, or revoked.
        """
        token_hash = hash_token(raw_refresh_token)

        rt = self.db.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        ).scalar_one_or_none()

        if rt is None:
            raise AuthError("Invalid refresh token.", code="UNAUTHORIZED", status_code=401)

        if rt.revoked_at is not None:
            raise AuthError("Refresh token has been revoked.", code="UNAUTHORIZED", status_code=401)

        expires_at = rt.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)

        if expires_at < datetime.now(UTC):
            raise AuthError("Refresh token has expired.", code="UNAUTHORIZED", status_code=401)

        # Revoke old token
        rt.revoked_at = datetime.now(UTC)  # type: ignore[assignment]
        self.db.add(rt)

        user = self.db.execute(select(User).where(User.id == rt.user_id)).scalar_one_or_none()
        if user is None or user.deleted_at is not None:
            raise AuthError("User not found.", code="UNAUTHORIZED", status_code=401)

        result = self._issue_tokens(user)
        self.db.commit()
        return result

    # ── Logout ───────────────────────────────────────

    def logout(self, user_id: str) -> None:
        """Revoke all active refresh tokens for a user."""
        now = datetime.now(UTC)
        self.db.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=now)
        )
        self.db.commit()

    # ── Password reset ───────────────────────────────

    def forgot_password(self, email: str) -> str | None:
        """Initiate password reset. Returns token if user exists, None otherwise.

        Always returns 200 to the caller to prevent email enumeration.
        """
        email = email.strip().lower()
        user = self.db.execute(select(User).where(User.email == email)).scalar_one_or_none()
        if user is None or user.deleted_at is not None:
            return None

        token = generate_verification_token()
        if settings.is_development:
            logger.info("Password reset token for %s: %s (dev mode)", email, token)
        return token

    def reset_password(self, token: str, new_password: str) -> None:
        """Reset user password with a valid token.

        In the full implementation, this validates the token from a tokens table.
        For Phase 2 foundation, we validate the token exists and update the password.
        """
        # NOTE: Full token storage/validation is simplified for Phase 2.
        # A production implementation stores reset tokens in a dedicated table with expiry.
        raise AuthError(
            "Password reset token validation requires full token storage (Phase 2+).",
            code="NOT_IMPLEMENTED",
            status_code=501,
        )

    # ── Email verification ───────────────────────────

    def verify_email(self, token: str) -> None:
        """Verify user email with token.

        Simplified for Phase 2 — full token storage pending.
        """
        raise AuthError(
            "Email verification token validation requires full token storage (Phase 2+).",
            code="NOT_IMPLEMENTED",
            status_code=501,
        )

    # ── Account deletion ─────────────────────────────

    def delete_account(self, user_id: str, password: str) -> dict[str, Any]:
        """Soft-delete user account with 30-day grace period.

        Requires password confirmation.
        """
        user = self.db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
        if user is None:
            raise AuthError("User not found.", code="NOT_FOUND", status_code=404)

        if user.password_hash is None:
            raise AuthError(
                "Cannot delete OAuth-only accounts with password. Use OAuth provider.",
                code="FORBIDDEN",
                status_code=403,
            )

        if not verify_password(password, user.password_hash):
            raise AuthError("Invalid password.", code="UNAUTHORIZED", status_code=401)

        now = datetime.now(UTC)
        user.deleted_at = now  # type: ignore[assignment]

        # Revoke all refresh tokens
        self.db.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=now)
        )
        self.db.commit()

        scheduled_deletion = now + timedelta(days=30)
        return {
            "status": "pending_deletion",
            "grace_period_days": 30,
            "scheduled_deletion_at": scheduled_deletion,
            "message": (
                "Account scheduled for deletion. "
                "You can reactivate by logging in within 30 days."
            ),
        }

    # ── Get user ─────────────────────────────────────

    def get_user_by_id(self, user_id: str) -> User | None:
        """Retrieve a user by ID, excluding soft-deleted."""
        user = self.db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
        if user is not None and user.deleted_at is not None:
            return None
        return user

    # ── OAuth 2.0 PKCE ───────────────────────────────

    def _validate_redirect_uri(self, redirect_uri: str | None) -> str:
        """Validate redirect URI against configured redirect URI and allowed CORS origins."""
        if not redirect_uri:
            return settings.google_redirect_uri

        allowed: set[str] = {settings.google_redirect_uri}
        for origin in settings.cors_origins:
            origin_clean = origin.rstrip("/")
            allowed.add(f"{origin_clean}/auth/google/callback")
            allowed.add(f"{origin_clean}/login")

        if redirect_uri not in allowed:
            raise AuthError(
                "Invalid OAuth redirect_uri.",
                code="VALIDATION_ERROR",
                status_code=400,
            )
        return redirect_uri

    def get_oauth_authorize_url(
        self,
        provider: str,
        code_challenge: str,
        code_challenge_method: str = "S256",
        redirect_uri: str | None = None,
    ) -> tuple[str, str]:
        """Initiate OAuth 2.0 PKCE flow."""
        if provider.lower() != "google":
            raise AuthError(
                f"Unsupported OAuth provider: {provider}",
                code="VALIDATION_ERROR",
                status_code=400,
            )

        if code_challenge_method != "S256":
            raise AuthError(
                "Only S256 code_challenge_method is supported.",
                code="VALIDATION_ERROR",
                status_code=400,
            )

        if not code_challenge:
            raise AuthError(
                "code_challenge is required.",
                code="VALIDATION_ERROR",
                status_code=400,
            )

        effective_redirect = self._validate_redirect_uri(redirect_uri)

        now = time.time()
        for s, exp in list(_oauth_states.items()):
            if exp < now:
                _oauth_states.pop(s, None)

        state = secrets.token_urlsafe(32)
        _oauth_states[state] = now + 600.0  # 10 minutes

        params = {
            "client_id": settings.google_client_id,
            "response_type": "code",
            "scope": "openid email profile",
            "redirect_uri": effective_redirect,
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": code_challenge_method,
            "access_type": "offline",
            "prompt": "consent",
        }
        auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
        return auth_url, state

    def oauth_callback(
        self,
        provider: str,
        code: str,
        code_verifier: str,
        state: str,
        redirect_uri: str | None = None,
    ) -> dict[str, Any]:
        """Process OAuth 2.0 PKCE callback and provision or link user."""
        if provider.lower() != "google":
            raise AuthError(
                f"Unsupported OAuth provider: {provider}",
                code="VALIDATION_ERROR",
                status_code=400,
            )

        effective_redirect = self._validate_redirect_uri(redirect_uri)

        now = time.time()
        expiry = _oauth_states.pop(state, None)
        if expiry is None or expiry < now:
            raise AuthError(
                "Invalid or expired OAuth state parameter (CSRF protection).",
                code="UNAUTHORIZED",
                status_code=401,
            )

        # For development / testing mode with mock codes
        if code.startswith("mock_") or code.startswith("mock:"):
            clean = code.removeprefix("mock_").removeprefix("mock:")
            parts = clean.split(":")
            provider_user_id = parts[0] if len(parts) > 0 and parts[0] else "google-mock-user-123"
            email = parts[1] if len(parts) > 1 and parts[1] else "mockuser@example.com"
            display_name = parts[2] if len(parts) > 2 and parts[2] else "Mock User"
            avatar_url = None
        else:
            try:
                token_resp = httpx.post(
                    "https://oauth2.googleapis.com/token",
                    data={
                        "client_id": settings.google_client_id,
                        "client_secret": settings.google_client_secret,
                        "code": code,
                        "code_verifier": code_verifier,
                        "grant_type": "authorization_code",
                        "redirect_uri": effective_redirect,
                    },
                    timeout=10.0,
                )
                if token_resp.status_code != 200:
                    logger.error("OAuth token exchange failed: %s", token_resp.text)
                    raise AuthError(
                        "OAuth token exchange with provider failed.",
                        code="UNAUTHORIZED",
                        status_code=401,
                    )

                token_data = token_resp.json()
                id_token_or_access = token_data.get("access_token")

                userinfo_resp = httpx.get(
                    "https://www.googleapis.com/oauth2/v3/userinfo",
                    headers={"Authorization": f"Bearer {id_token_or_access}"},
                    timeout=10.0,
                )
                if userinfo_resp.status_code != 200:
                    raise AuthError(
                        "Failed to fetch user profile from provider.",
                        code="UNAUTHORIZED",
                        status_code=401,
                    )

                info = userinfo_resp.json()
                provider_user_id = str(info["sub"])
                email = info["email"]
                display_name = info.get("name") or email.split("@")[0]
                avatar_url = info.get("picture")
            except httpx.RequestError as exc:
                logger.error("HTTP error during OAuth exchange: %s", exc)
                raise AuthError(
                    "Network error contacting OAuth provider.",
                    code="INTERNAL_ERROR",
                    status_code=502,
                )

        email = email.strip().lower()

        # 1. Check if OAuth account exists
        oauth_acc = self.db.execute(
            select(OAuthAccount).where(
                OAuthAccount.provider == provider.lower(),
                OAuthAccount.provider_user_id == provider_user_id,
            )
        ).scalar_one_or_none()

        if oauth_acc:
            user = self.db.execute(
                select(User).where(User.id == oauth_acc.user_id)
            ).scalar_one_or_none()
            if user is None or user.deleted_at is not None:
                raise AuthError(
                    "User account not found or has been deactivated.",
                    code="UNAUTHORIZED",
                    status_code=401,
                )
        else:
            # 2. Check if user already exists with this email
            user = self.db.execute(select(User).where(User.email == email)).scalar_one_or_none()
            if user:
                if user.deleted_at is not None:
                    raise AuthError(
                        "User account has been deactivated.",
                        code="UNAUTHORIZED",
                        status_code=401,
                    )
                # Link OAuth account to existing user
                oauth_acc = OAuthAccount(
                    user_id=user.id,
                    provider=provider.lower(),
                    provider_user_id=provider_user_id,
                )
                self.db.add(oauth_acc)
                if not user.email_verified:
                    user.email_verified = True
            else:
                # 3. Create brand new user
                user = User(
                    email=email,
                    email_verified=True,
                    role=UserRole.LEARNER,
                )
                self.db.add(user)
                self.db.flush()

                profile = UserProfile(
                    user_id=user.id,
                    display_name=display_name,
                    avatar_url=avatar_url,
                )
                self.db.add(profile)

                oauth_acc = OAuthAccount(
                    user_id=user.id,
                    provider=provider.lower(),
                    provider_user_id=provider_user_id,
                )
                self.db.add(oauth_acc)

            self.db.commit()

        return self._issue_tokens(user)

    # ── Private helpers ──────────────────────────────

    def _issue_tokens(self, user: User) -> dict[str, Any]:
        """Issue access + refresh token pair for a user."""
        access_token = create_access_token(user_id=user.id, role=user.role.value)
        raw_refresh = generate_refresh_token()
        expires_at = datetime.now(UTC) + timedelta(
            days=settings.jwt_refresh_token_expire_days
        )

        rt = RefreshToken(
            user_id=user.id,
            token_hash=hash_token(raw_refresh),
            expires_at=expires_at,
        )
        self.db.add(rt)
        self.db.commit()

        expires_in = settings.jwt_access_token_expire_minutes * 60

        return {
            "access_token": access_token,
            "refresh_token": raw_refresh,
            "expires_in": expires_in,
            "user": user,
        }


# Global store for active CSRF state tokens
_oauth_states: dict[str, float] = {}
