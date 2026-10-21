"""Pydantic schemas for users module (profile management)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class UpdateProfileRequest(BaseModel):
    """Profile update request — all fields optional."""

    display_name: str | None = Field(None, min_length=1, max_length=100)
    bio: str | None = Field(None, max_length=500)
    timezone: str | None = Field(None, max_length=50)
    avatar_url: str | None = None


class UpdatePreferencesRequest(BaseModel):
    """Preferences update request."""

    theme: str | None = None
    reduced_motion: bool | None = None
    language: str | None = None
