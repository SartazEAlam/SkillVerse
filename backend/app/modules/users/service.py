"""Users service — profile retrieval and updates."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.modules.auth.models import User, UserProfile


class UserService:
    """Profile management business logic."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_profile(self, user: User) -> dict[str, Any]:
        """Return the user's profile data."""
        profile = user.profile
        return {
            "id": user.id,
            "email": user.email,
            "role": user.role.value,
            "email_verified": user.email_verified,
            "display_name": profile.display_name if profile else None,
            "avatar_url": profile.avatar_url if profile else None,
            "bio": profile.bio if profile else None,
            "timezone": profile.timezone if profile else None,
            "preferences": profile.preferences if profile else {},
            "created_at": user.created_at,
        }

    def update_profile(
        self,
        user: User,
        display_name: str | None = None,
        bio: str | None = None,
        timezone: str | None = None,
        avatar_url: str | None = None,
    ) -> User:
        """Update user profile fields. Only provided (non-None) fields are changed."""
        if user.profile is None:
            user.profile = UserProfile(user_id=user.id, display_name=display_name or user.email)
            self.db.add(user.profile)

        if display_name is not None:
            user.profile.display_name = display_name
        if bio is not None:
            user.profile.bio = bio
        if timezone is not None:
            user.profile.timezone = timezone
        if avatar_url is not None:
            user.profile.avatar_url = avatar_url

        self.db.commit()
        self.db.refresh(user)
        return user

    def update_preferences(self, user: User, preferences: dict[str, Any]) -> User:
        """Merge new preference keys into existing preferences JSONB."""
        if user.profile is None:
            user.profile = UserProfile(user_id=user.id, display_name=user.email)
            self.db.add(user.profile)

        current = dict(user.profile.preferences) if user.profile.preferences else {}
        # Only update keys that are provided and not None
        for key, value in preferences.items():
            if value is not None:
                current[key] = value
        user.profile.preferences = current  # type: ignore[assignment]

        self.db.commit()
        self.db.refresh(user)
        return user

    def export_data(self, user: User) -> dict[str, Any]:
        """Export all user data for GDPR compliance.

        In Phase 2, exports user + profile. Later phases add enrollments, progress, etc.
        """
        profile = user.profile
        return {
            "manifest": {
                "generated_at": user.created_at.isoformat(),
                "user_id": user.id,
                "format_version": "1.0",
                "included_sections": ["user", "profile"],
            },
            "user": {
                "id": user.id,
                "email": user.email,
                "role": user.role.value,
                "email_verified": user.email_verified,
                "created_at": user.created_at.isoformat(),
            },
            "profile": {
                "display_name": profile.display_name if profile else None,
                "bio": profile.bio if profile else None,
                "timezone": profile.timezone if profile else None,
                "avatar_url": profile.avatar_url if profile else None,
                "preferences": profile.preferences if profile else {},
            },
        }
