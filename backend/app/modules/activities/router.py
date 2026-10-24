"""FastAPI router for interactive activities, learner submissions, and attempt history."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_optional_current_user, require_creator_or_admin
from app.infrastructure.database import get_db
from app.modules.activities.schemas import (
    ActivityCreate,
    ActivityDetailResponse,
    ActivitySummaryResponse,
    AttemptListResponse,
    AttemptResponse,
    AttemptSubmissionRequest,
)
from app.modules.activities.service import ActivityService, ActivityServiceError
from app.modules.auth.models import User, UserRole

router = APIRouter(tags=["Activities & Assessments"])


def _get_activity_service(db: Session = Depends(get_db)) -> ActivityService:
    return ActivityService(db)


# ── Authoring Endpoints (Creator / Admin) ───────────────────────────────────


@router.post(
    "/activities",
    response_model=ActivityDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new activity (Creator/Admin)",
)
def create_activity(
    payload: ActivityCreate,
    service: ActivityService = Depends(_get_activity_service),
    current_user: User = Depends(require_creator_or_admin),
) -> ActivityDetailResponse:
    """Create a new interactive activity along with its confidential grading configuration.

    The grading configuration and answer key are stored securely on the server
    and never exposed to learners.
    """
    try:
        activity = service.create_activity(payload)
        public_activity = service.get_public_activity(activity.id)
        if not public_activity:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"error": {"code": "ACTIVITY_CREATE_FAILED", "message": "Failed to retrieve created activity."}},
            )
        return public_activity
    except ActivityServiceError as err:
        raise HTTPException(
            status_code=err.status_code,
            detail={"error": {"code": err.code, "message": err.message}},
        ) from err


# ── Public / Learner Activity Endpoints ─────────────────────────────────────


@router.get(
    "/activities/{activity_id}",
    response_model=ActivityDetailResponse,
    summary="Get sanitized activity definition",
)
def get_activity(
    activity_id: str,
    service: ActivityService = Depends(_get_activity_service),
) -> ActivityDetailResponse:
    """Retrieve public activity definition.

    SECURITY INVARIANT: The answer key, hidden test cases, and grading secrets
    are stripped before delivery.
    """
    activity = service.get_public_activity(activity_id)
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "ACTIVITY_NOT_FOUND", "message": f"Activity '{activity_id}' not found."}},
        )
    return activity


@router.get(
    "/lessons/{lesson_id}/activities",
    response_model=list[ActivitySummaryResponse],
    summary="List activities for a lesson",
)
def list_lesson_activities(
    lesson_id: str,
    service: ActivityService = Depends(_get_activity_service),
    current_user: User | None = Depends(get_optional_current_user),
) -> list[ActivitySummaryResponse]:
    """Retrieve all activities configured for a lesson.

    If authenticated, returns the learner's best score and attempt counts.
    """
    user_id = current_user.id if current_user else None
    try:
        return service.list_lesson_activities(lesson_id=lesson_id, user_id=user_id)
    except ActivityServiceError as err:
        raise HTTPException(
            status_code=err.status_code,
            detail={"error": {"code": err.code, "message": err.message}},
        ) from err


# ── Submission & Attempts Endpoints (Learner Authenticated) ────────────────


@router.post(
    "/activities/{activity_id}/attempts",
    response_model=AttemptResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit an answer attempt for an activity",
)
def submit_attempt(
    activity_id: str,
    payload: AttemptSubmissionRequest,
    current_user: User = Depends(get_current_user),
    service: ActivityService = Depends(_get_activity_service),
) -> AttemptResponse:
    """Submit learner response for server-authoritative grading and recording.

    Scores, feedback, and pass/fail states are evaluated exclusively on the server.
    Retry limits are enforced.
    """
    try:
        return service.submit_attempt(
            activity_id=activity_id,
            user_id=current_user.id,
            submission=payload.submission,
        )
    except ActivityServiceError as err:
        raise HTTPException(
            status_code=err.status_code,
            detail={"error": {"code": err.code, "message": err.message}},
        ) from err


@router.get(
    "/activities/{activity_id}/attempts",
    response_model=AttemptListResponse,
    summary="List authenticated user's attempt history for an activity",
)
def list_attempts(
    activity_id: str,
    current_user: User = Depends(get_current_user),
    service: ActivityService = Depends(_get_activity_service),
) -> AttemptListResponse:
    """Retrieve the current user's past attempts for an activity, ordered latest first."""
    try:
        return service.get_user_attempts(activity_id=activity_id, user_id=current_user.id)
    except ActivityServiceError as err:
        raise HTTPException(
            status_code=err.status_code,
            detail={"error": {"code": err.code, "message": err.message}},
        ) from err


@router.get(
    "/activities/{activity_id}/attempts/{attempt_id}",
    response_model=AttemptResponse,
    summary="Get details of a specific attempt",
)
def get_attempt(
    activity_id: str,
    attempt_id: str,
    current_user: User = Depends(get_current_user),
    service: ActivityService = Depends(_get_activity_service),
) -> AttemptResponse:
    """Retrieve details for a specific attempt.

    SECURITY INVARIANT: Enforces cross-user authorization. Learners can only view
    their own attempts. Admins can view any attempt.
    """
    try:
        is_admin = current_user.role == UserRole.ADMIN
        return service.get_attempt_by_id(attempt_id=attempt_id, user_id=current_user.id, is_admin=is_admin)
    except ActivityServiceError as err:
        raise HTTPException(
            status_code=err.status_code,
            detail={"error": {"code": err.code, "message": err.message}},
        ) from err
