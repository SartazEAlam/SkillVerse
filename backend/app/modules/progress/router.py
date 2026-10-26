"""FastAPI router for course enrollments, lesson progress, skill mastery, and progress dashboard."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_optional_current_user
from app.infrastructure.database import get_db
from app.modules.auth.models import User
from app.modules.progress.schemas import (
    AchievementResponse,
    CoursePrerequisitesResponse,
    DashboardSummaryResponse,
    EnrollmentCreate,
    EnrollmentResponse,
    LessonCompleteResponse,
    LessonProgressResponse,
    RecommendationItem,
    SkillMasteryResponse,
)
from app.modules.progress.service import ProgressionService, ProgressionServiceError

router = APIRouter(tags=["Progression & Enrollments"])


def _get_progression_service(db: Session = Depends(get_db)) -> ProgressionService:
    return ProgressionService(db)


# ── 1. Course Enrollment Endpoints ──────────────────────────────────────────


@router.post(
    "/courses/{course_slug}/enroll",
    response_model=EnrollmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Enroll in a published course",
)
def enroll_in_course(
    course_slug: str,
    payload: EnrollmentCreate | None = None,
    current_user: User = Depends(get_current_user),
    service: ProgressionService = Depends(_get_progression_service),
) -> EnrollmentResponse:
    """Enroll the authenticated learner in the active immutable version of a course."""
    target_slug = payload.course_slug if payload and payload.course_slug else course_slug
    try:
        return service.enroll_user(user_id=current_user.id, course_slug=target_slug)
    except ProgressionServiceError as err:
        raise HTTPException(
            status_code=err.status_code,
            detail={"error": {"code": err.code, "message": err.message, "details": err.details}},
        ) from err


@router.get(
    "/courses/{course_slug}/prerequisites",
    response_model=CoursePrerequisitesResponse,
    summary="Evaluate course prerequisite eligibility",
)
def check_course_prerequisites(
    course_slug: str,
    current_user: User | None = Depends(get_optional_current_user),
    service: ProgressionService = Depends(_get_progression_service),
) -> CoursePrerequisitesResponse:
    """Check if all prerequisite skills for a course are satisfied by the learner."""
    user_id = current_user.id if current_user else None
    try:
        return service.check_course_prerequisites(user_id=user_id, course_slug=course_slug)
    except ProgressionServiceError as err:
        raise HTTPException(
            status_code=err.status_code,
            detail={"error": {"code": err.code, "message": err.message, "details": err.details}},
        ) from err


@router.get(
    "/enrollments",
    response_model=list[EnrollmentResponse],
    summary="List authenticated user's course enrollments",
)
def list_enrollments(
    current_user: User = Depends(get_current_user),
    service: ProgressionService = Depends(_get_progression_service),
) -> list[EnrollmentResponse]:
    """Retrieve all active course enrollments with computed progress percentages for the learner."""
    return service.get_user_enrollments(user_id=current_user.id)


@router.get(
    "/enrollments/{enrollment_id}",
    response_model=EnrollmentResponse,
    summary="Get details of a specific enrollment",
)
def get_enrollment(
    enrollment_id: str,
    current_user: User = Depends(get_current_user),
    service: ProgressionService = Depends(_get_progression_service),
) -> EnrollmentResponse:
    """Retrieve details and progress metrics for a single enrollment."""
    try:
        return service.get_enrollment_by_id(enrollment_id=enrollment_id, user_id=current_user.id)
    except ProgressionServiceError as err:
        raise HTTPException(
            status_code=err.status_code,
            detail={"error": {"code": err.code, "message": err.message, "details": err.details}},
        ) from err


# ── 2. Lesson Progress Lifecycle Endpoints ──────────────────────────────────


@router.post(
    "/enrollments/{enrollment_id}/lessons/{lesson_id}/start",
    response_model=LessonProgressResponse,
    summary="Mark lesson as started",
)
def start_lesson(
    enrollment_id: str,
    lesson_id: str,
    current_user: User = Depends(get_current_user),
    service: ProgressionService = Depends(_get_progression_service),
) -> LessonProgressResponse:
    """Record that the learner has opened a lesson, updating activity and enrollment timestamps."""
    try:
        return service.start_lesson(
            user_id=current_user.id, enrollment_id=enrollment_id, lesson_id=lesson_id
        )
    except ProgressionServiceError as err:
        raise HTTPException(
            status_code=err.status_code,
            detail={"error": {"code": err.code, "message": err.message, "details": err.details}},
        ) from err


@router.post(
    "/enrollments/{enrollment_id}/lessons/{lesson_id}/complete",
    response_model=LessonCompleteResponse,
    summary="Complete a lesson",
)
def complete_lesson(
    enrollment_id: str,
    lesson_id: str,
    current_user: User = Depends(get_current_user),
    service: ProgressionService = Depends(_get_progression_service),
) -> LessonCompleteResponse:
    """Complete a lesson. Enforces that all required interactive activities in the lesson are passed."""
    try:
        return service.complete_lesson(
            user_id=current_user.id, enrollment_id=enrollment_id, lesson_id=lesson_id
        )
    except ProgressionServiceError as err:
        raise HTTPException(
            status_code=err.status_code,
            detail={"error": {"code": err.code, "message": err.message, "details": err.details}},
        ) from err


# ── 3. Dashboard, Mastery, and Achievements Endpoints ───────────────────────


@router.get(
    "/progress/dashboard",
    response_model=DashboardSummaryResponse,
    summary="Consolidated learner dashboard overview",
)
def get_dashboard_summary(
    current_user: User = Depends(get_current_user),
    service: ProgressionService = Depends(_get_progression_service),
) -> DashboardSummaryResponse:
    """Retrieve consolidated overview of enrolled courses, resume learning item, skill mastery, and achievements."""
    return service.get_dashboard_summary(user_id=current_user.id)


@router.get(
    "/progress/skills",
    response_model=list[SkillMasteryResponse],
    summary="Skill mastery overview with verified evidence",
)
def get_skills_mastery(
    current_user: User = Depends(get_current_user),
    service: ProgressionService = Depends(_get_progression_service),
) -> list[SkillMasteryResponse]:
    """Retrieve learner's transparent skill mastery status, evidence history, and prerequisite lock states."""
    return service.get_user_skills_mastery(user_id=current_user.id)


@router.get(
    "/progress/achievements",
    response_model=list[AchievementResponse],
    summary="List platform achievements and earned status",
)
def get_achievements(
    current_user: User = Depends(get_current_user),
    service: ProgressionService = Depends(_get_progression_service),
) -> list[AchievementResponse]:
    """Retrieve all platform achievements and whether the authenticated learner has earned them."""
    return service.get_user_achievements(user_id=current_user.id)


@router.get(
    "/progress/recommendations",
    response_model=list[RecommendationItem],
    summary="Personalized learning recommendations",
)
def get_recommendations(
    current_user: User = Depends(get_current_user),
    service: ProgressionService = Depends(_get_progression_service),
) -> list[RecommendationItem]:
    """Retrieve deterministic, explainable next learning action suggestions."""
    return service.get_recommendations(user_id=current_user.id)
