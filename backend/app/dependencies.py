"""FastAPI dependency injection — database sessions and current user extraction."""

from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.infrastructure.database import get_db
from app.modules.auth.models import User
from app.modules.auth.security import decode_access_token
from app.modules.auth.service import AuthService

_bearer_scheme = HTTPBearer(auto_error=False)


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    """Provide an AuthService instance with a database session."""
    return AuthService(db)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Extract and validate the current user from the Authorization header.

    Returns the User ORM instance. Raises 401 if token is missing/invalid.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "UNAUTHORIZED", "message": "Authentication required."}},
        )

    try:
        payload = decode_access_token(credentials.credentials)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "UNAUTHORIZED", "message": "Invalid or expired token."}},
        )

    user_id: str | None = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "UNAUTHORIZED", "message": "Invalid token payload."}},
        )

    auth_service = AuthService(db)
    user = auth_service.get_user_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "UNAUTHORIZED", "message": "User not found or deactivated."}},
        )

    return user


def get_optional_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> User | None:
    """Extract current user if valid bearer token is present, else None."""
    if credentials is None:
        return None
    try:
        payload = decode_access_token(credentials.credentials)
        user_id: str | None = payload.get("sub")
        if not user_id:
            return None
        auth_service = AuthService(db)
        return auth_service.get_user_by_id(user_id)
    except Exception:
        return None


def require_creator_or_admin(current_user: User = Depends(get_current_user)) -> User:
    """Enforce that the authenticated user has creator or admin privileges."""
    from app.modules.auth.models import UserRole

    if current_user.role not in (UserRole.CREATOR, UserRole.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": {"code": "FORBIDDEN", "message": "Creator or Admin privileges required."}
            },
        )
    return current_user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Enforce that the authenticated user has admin privileges."""
    from app.modules.auth.models import UserRole

    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": {"code": "FORBIDDEN", "message": "Admin privileges required."}},
        )
    return current_user
