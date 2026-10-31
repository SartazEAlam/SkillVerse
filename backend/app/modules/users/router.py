"""Users router — profile management endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_auth_service, get_current_user
from app.infrastructure.database import get_db
from app.modules.auth.models import User
from app.modules.auth.schemas import DeleteAccountRequest, DeleteAccountResponse, UserResponse
from app.modules.auth.service import AuthError, AuthService
from app.modules.users.schemas import UpdatePreferencesRequest, UpdateProfileRequest
from app.modules.users.service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


def _get_user_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(db)


def _user_to_response(user: User) -> UserResponse:
    """Convert a User ORM object to a UserResponse schema."""
    return UserResponse(
        id=user.id,
        email=user.email,
        role=user.role,
        email_verified=user.email_verified,
        display_name=user.profile.display_name if user.profile else None,
        avatar_url=user.profile.avatar_url if user.profile else None,
        bio=user.profile.bio if user.profile else None,
        timezone=user.profile.timezone if user.profile else None,
        preferences=user.profile.preferences if user.profile else {},
        created_at=user.created_at,
    )


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)) -> UserResponse:
    """Get the authenticated user's profile."""
    return _user_to_response(current_user)


@router.patch("/me", response_model=UserResponse)
def update_me(
    body: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(_get_user_service),
) -> UserResponse:
    """Update the authenticated user's profile."""
    updated = user_service.update_profile(
        user=current_user,
        display_name=body.display_name,
        bio=body.bio,
        timezone=body.timezone,
        avatar_url=body.avatar_url,
    )
    return _user_to_response(updated)


@router.patch("/me/preferences", response_model=UserResponse)
def update_preferences(
    body: UpdatePreferencesRequest,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(_get_user_service),
) -> UserResponse:
    """Update the authenticated user's UI preferences."""
    prefs = body.model_dump(exclude_none=True)
    updated = user_service.update_preferences(user=current_user, preferences=prefs)
    return _user_to_response(updated)


@router.get("/me/export")
def export_data(
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(_get_user_service),
) -> dict[str, Any]:
    """Export all personal data (GDPR portability)."""
    return user_service.export_data(user=current_user)


@router.delete("/me", response_model=DeleteAccountResponse)
def delete_account(
    body: DeleteAccountRequest,
    current_user: User = Depends(get_current_user),
    auth: AuthService = Depends(get_auth_service),
) -> dict[str, Any]:
    """Soft-delete user account with 30-day grace period."""
    try:
        result = auth.delete_account(user_id=current_user.id, password=body.password)
    except AuthError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"error": {"code": e.code, "message": e.message}},
        )
    return result
