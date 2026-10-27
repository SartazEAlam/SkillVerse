"""FastAPI router for interactive activities, learner submissions, and attempt history."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_optional_current_user, require_creator_or_admin
from app.infrastructure.database import get_db
from app.modules.activities.schemas import (
    ActivityAuthoringResponse,
    ActivityCreate,
    ActivityDetailResponse,
    ActivitySummaryResponse,
    ActivityUpdateRequest,
    AttemptListResponse,
    AttemptResponse,
    AttemptSubmissionRequest,
)
from app.modules.activities.service import ActivityService, ActivityServiceError
from app.modules.auth.models import User, UserRole
from app.modules.courses.models import Course, CourseVersion, Lesson, Module

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
    if payload.lesson_id:
        stmt = (
            select(Course, CourseVersion)
            .join(CourseVersion, Course.id == CourseVersion.course_id)
            .join(Module, CourseVersion.id == Module.course_version_id)
            .join(Lesson, Module.id == Lesson.module_id)
            .where(Lesson.id == payload.lesson_id)
        )
        row = service.db.execute(stmt).first()
        if row:
            course, version = row[0], row[1]
            if course.creator_id != current_user.id and current_user.role != UserRole.ADMIN:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error": {
                            "code": "FORBIDDEN",
                            "message": "You are not authorized to add activities to this course.",
                        }
                    },
                )
            if version.published_at is not None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": {
                            "code": "CANNOT_MODIFY_PUBLISHED_VERSION",
                            "message": "Cannot add activities to a published course version.",
                        }
                    },
                )
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


@router.get(
    "/activities/{activity_id}/authoring",
    response_model=ActivityAuthoringResponse,
    summary="Get full activity with answer key for creator authoring",
)
def get_authoring_activity(
    activity_id: str,
    service: ActivityService = Depends(_get_activity_service),
    current_user: User = Depends(require_creator_or_admin),
) -> ActivityAuthoringResponse:
    """Retrieve full activity details including confidential answer key for authorized creators."""
    try:
        return service.get_authoring_activity(
            activity_id=activity_id,
            user_id=current_user.id,
            is_admin=current_user.role == UserRole.ADMIN,
        )
    except ActivityServiceError as err:
        raise HTTPException(
            status_code=err.status_code,
            detail={"error": {"code": err.code, "message": err.message}},
        ) from err


@router.patch(
    "/activities/{activity_id}",
    response_model=ActivityAuthoringResponse,
    summary="Update activity and grading criteria in draft",
)
def update_activity(
    activity_id: str,
    payload: ActivityUpdateRequest,
    service: ActivityService = Depends(_get_activity_service),
    current_user: User = Depends(require_creator_or_admin),
) -> ActivityAuthoringResponse:
    """Update activity content, settings, and grading keys in a working draft."""
    try:
        return service.update_activity(
            activity_id=activity_id,
            data=payload,
            user_id=current_user.id,
            is_admin=current_user.role == UserRole.ADMIN,
        )
    except ActivityServiceError as err:
        raise HTTPException(
            status_code=err.status_code,
            detail={"error": {"code": err.code, "message": err.message}},
        ) from err


@router.delete(
    "/activities/{activity_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete activity from draft",
)
def delete_activity(
    activity_id: str,
    service: ActivityService = Depends(_get_activity_service),
    current_user: User = Depends(require_creator_or_admin),
) -> None:
    """Delete an activity and its grading configuration from a working draft."""
    try:
        service.delete_activity(
            activity_id=activity_id,
            user_id=current_user.id,
            is_admin=current_user.role == UserRole.ADMIN,
        )
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
