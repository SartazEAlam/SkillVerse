"""Auth router — registration, login, token refresh, logout, password reset, email verification."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_auth_service, get_current_user
from app.infrastructure.rate_limiter import rate_limit
from app.modules.auth.models import User
from app.modules.auth.schemas import (
    ForgotPasswordRequest,
    LoginRequest,
    LoginResponse,
    MessageResponse,
    OAuthAuthorizeResponse,
    OAuthCallbackRequest,
    RefreshRequest,
    RegisterRequest,
    RegisterResponse,
    ResetPasswordRequest,
    UserResponse,
    VerifyEmailRequest,
)
from app.modules.auth.service import AuthError, AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


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
        created_at=user.created_at,
    )


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit(max_requests=5, window_seconds=3600))],
)
def register(body: RegisterRequest, auth: AuthService = Depends(get_auth_service)) -> dict:
    """Register a new user account."""
    try:
        user, _verification_token = auth.register(
            email=body.email,
            password=body.password,
            display_name=body.display_name,
        )
    except AuthError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"error": {"code": e.code, "message": e.message}},
        )

    return {"user": _user_to_response(user)}


@router.post(
    "/login",
    response_model=LoginResponse,
    dependencies=[Depends(rate_limit(max_requests=10, window_seconds=900))],
)
def login(body: LoginRequest, auth: AuthService = Depends(get_auth_service)) -> dict:
    """Authenticate and receive tokens."""
    try:
        result = auth.login(email=body.email, password=body.password)
    except AuthError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"error": {"code": e.code, "message": e.message}},
        )

    return {
        "access_token": result["access_token"],
        "refresh_token": result["refresh_token"],
        "expires_in": result["expires_in"],
        "user": _user_to_response(result["user"]),
    }


@router.post("/refresh", response_model=LoginResponse)
def refresh(body: RefreshRequest, auth: AuthService = Depends(get_auth_service)) -> dict:
    """Refresh access token using a valid refresh token."""
    try:
        result = auth.refresh(raw_refresh_token=body.refresh_token)
    except AuthError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"error": {"code": e.code, "message": e.message}},
        )

    return {
        "access_token": result["access_token"],
        "refresh_token": result["refresh_token"],
        "expires_in": result["expires_in"],
        "user": _user_to_response(result["user"]),
    }


@router.post("/logout", response_model=MessageResponse)
def logout(
    current_user: User = Depends(get_current_user),
    auth: AuthService = Depends(get_auth_service),
) -> dict:
    """Revoke all refresh tokens for the authenticated user."""
    auth.logout(user_id=current_user.id)
    return {"message": "Successfully logged out."}


@router.post("/verify-email", response_model=MessageResponse)
def verify_email(body: VerifyEmailRequest, auth: AuthService = Depends(get_auth_service)) -> dict:
    """Verify user email with token."""
    try:
        auth.verify_email(token=body.token)
    except AuthError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"error": {"code": e.code, "message": e.message}},
        )
    return {"message": "Email verified successfully."}


@router.post(
    "/forgot-password",
    response_model=MessageResponse,
    dependencies=[Depends(rate_limit(max_requests=3, window_seconds=3600))],
)
def forgot_password(
    body: ForgotPasswordRequest, auth: AuthService = Depends(get_auth_service)
) -> dict:
    """Initiate password reset. Always returns 200 to prevent email enumeration."""
    auth.forgot_password(email=body.email)
    return {"message": "If an account exists with that email, a reset link has been sent."}


@router.post("/reset-password", response_model=MessageResponse)
def reset_password(
    body: ResetPasswordRequest, auth: AuthService = Depends(get_auth_service)
) -> dict:
    """Complete password reset with token."""
    try:
        auth.reset_password(token=body.token, new_password=body.new_password)
    except AuthError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"error": {"code": e.code, "message": e.message}},
        )
    return {"message": "Password reset successfully."}


@router.get(
    "/oauth/{provider}/authorize",
    response_model=OAuthAuthorizeResponse,
    dependencies=[Depends(rate_limit(max_requests=10, window_seconds=900))],
)
def oauth_authorize(
    provider: str,
    code_challenge: str,
    code_challenge_method: str = "S256",
    redirect_uri: str | None = None,
    auth: AuthService = Depends(get_auth_service),
) -> dict:
    """Initiates OAuth 2.0 authorization with PKCE flow."""
    try:
        url, state = auth.get_oauth_authorize_url(
            provider=provider,
            code_challenge=code_challenge,
            code_challenge_method=code_challenge_method,
            redirect_uri=redirect_uri,
        )
    except AuthError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"error": {"code": e.code, "message": e.message}},
        )
    return {"authorization_url": url, "state": state}


@router.post(
    "/oauth/{provider}/callback",
    response_model=LoginResponse,
    dependencies=[Depends(rate_limit(max_requests=10, window_seconds=900))],
)
def oauth_callback(
    provider: str,
    body: OAuthCallbackRequest,
    redirect_uri: str | None = None,
    auth: AuthService = Depends(get_auth_service),
) -> dict:
    """Exchange authorization code and PKCE code_verifier for session tokens."""
    try:
        result = auth.oauth_callback(
            provider=provider,
            code=body.code,
            code_verifier=body.code_verifier,
            state=body.state,
            redirect_uri=redirect_uri,
        )
    except AuthError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"error": {"code": e.code, "message": e.message}},
        )
    return {
        "access_token": result["access_token"],
        "refresh_token": result["refresh_token"],
        "expires_in": result["expires_in"],
        "user": _user_to_response(result["user"]),
    }
