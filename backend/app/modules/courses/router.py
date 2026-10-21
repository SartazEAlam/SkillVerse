"""API endpoints for course catalog discovery, draft authoring, and version publishing."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.dependencies import require_creator_or_admin
from app.infrastructure.database import get_db
from app.modules.auth.models import User, UserRole
from app.modules.courses.models import CourseDifficulty
from app.modules.courses.schemas import (
    CourseCreateRequest,
    CourseDetailResponse,
    CoursePaginatedResponse,
    CoursePublishRequest,
    CoursePublishResponse,
    CourseUpdateRequest,
    LessonContentUpdateRequest,
    LessonCreateRequest,
    LessonDetailResponse,
    LessonUpdateRequest,
    ModuleCreateRequest,
    ModuleUpdateRequest,
)
from app.modules.courses.service import CourseService, CourseServiceError

router = APIRouter(tags=["Courses & Catalog"])


def _get_course_service(db: Session = Depends(get_db)) -> CourseService:
    return CourseService(db)


# ── Public Catalog Endpoints ───────────────────────────────────────────────


@router.get("/courses", response_model=CoursePaginatedResponse)
def list_courses(
    discipline: str | None = Query(None, description="Discipline slug filter"),
    difficulty: CourseDifficulty | None = Query(None, description="Course difficulty level"),
    search: str | None = Query(None, description="Search query across title and description"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=50, description="Items per page"),
    service: CourseService = Depends(_get_course_service),
) -> dict[str, Any]:
    """Search and filter published courses in the public catalog.

    Only courses in PUBLISHED status with an active published version are returned.
    Drafts and archived courses are strictly excluded.
    """
    return service.list_published_courses(
        discipline_slug=discipline,
        difficulty=difficulty,
        search=search,
        page=page,
        limit=limit,
    )


@router.get("/courses/{slug}", response_model=CourseDetailResponse)
def get_course_by_slug(
    slug: str,
    service: CourseService = Depends(_get_course_service),
) -> dict[str, Any]:
    """Retrieve full curriculum and lesson outlines from the current published course version.

    Returns 404 for unpublished draft or archived courses.
    """
    course = service.get_published_course_by_slug(slug)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "COURSE_NOT_FOUND",
                    "message": f"Published course '{slug}' not found.",
                }
            },
        )
    return course


@router.get("/courses/{course_slug}/lessons/{lesson_slug}", response_model=LessonDetailResponse)
def get_published_lesson(
    course_slug: str,
    lesson_slug: str,
    service: CourseService = Depends(_get_course_service),
) -> dict[str, Any]:
    """Retrieve individual lesson details and content blocks from the published course version."""
    lesson = service.get_published_lesson(course_slug=course_slug, lesson_slug=lesson_slug)
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "LESSON_NOT_FOUND",
                    "message": f"Lesson '{lesson_slug}' not found in published course.",
                }
            },
        )
    return lesson


# ── Protected Authoring & Draft Endpoints ──────────────────────────────────


@router.post("/courses", response_model=CourseDetailResponse, status_code=status.HTTP_201_CREATED)
def create_course(
    body: CourseCreateRequest,
    current_user: User = Depends(require_creator_or_admin),
    service: CourseService = Depends(_get_course_service),
) -> dict[str, Any]:
    """Create a new course aggregate and initialize its draft (creator or admin privilege required)."""
    try:
        course = service.create_course(
            creator_id=current_user.id,
            slug=body.slug,
            title=body.title,
            short_description=body.short_description,
            full_description=body.full_description,
            discipline_id=body.discipline_id,
            difficulty_level=body.difficulty_level,
            estimated_duration_minutes=body.estimated_duration_minutes,
            cover_image_url=body.cover_image_url,
            learning_objectives=body.learning_objectives,
            skill_ids=body.skill_ids,
        )
        return service.get_draft_detail(
            course_id=course.id,
            user_id=current_user.id,
            is_admin=current_user.role == UserRole.ADMIN,
        )
    except CourseServiceError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"error": {"code": e.code, "message": e.message}},
        )


@router.get("/courses/{course_id}/draft", response_model=CourseDetailResponse)
def get_course_draft(
    course_id: str,
    current_user: User = Depends(require_creator_or_admin),
    service: CourseService = Depends(_get_course_service),
) -> dict[str, Any]:
    """Retrieve the working draft of a course (only accessible by creator or admin)."""
    try:
        return service.get_draft_detail(
            course_id=course_id,
            user_id=current_user.id,
            is_admin=current_user.role == UserRole.ADMIN,
        )
    except CourseServiceError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"error": {"code": e.code, "message": e.message}},
        )


@router.patch("/courses/{course_id}", response_model=CourseDetailResponse)
def update_course(
    course_id: str,
    body: CourseUpdateRequest,
    current_user: User = Depends(require_creator_or_admin),
    service: CourseService = Depends(_get_course_service),
) -> dict[str, Any]:
    """Update top-level course aggregate metadata and draft objectives."""
    try:
        service.update_course_metadata(
            course_id=course_id,
            user_id=current_user.id,
            is_admin=current_user.role == UserRole.ADMIN,
            title=body.title,
            short_description=body.short_description,
            full_description=body.full_description,
            difficulty_level=body.difficulty_level,
            estimated_duration_minutes=body.estimated_duration_minutes,
            cover_image_url=body.cover_image_url,
            learning_objectives=body.learning_objectives,
            skill_ids=body.skill_ids,
        )
        return service.get_draft_detail(
            course_id=course_id,
            user_id=current_user.id,
            is_admin=current_user.role == UserRole.ADMIN,
        )
    except CourseServiceError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"error": {"code": e.code, "message": e.message}},
        )


# ── Draft Modules & Lessons Management ─────────────────────────────────────


@router.post("/courses/{course_id}/draft/modules", status_code=status.HTTP_201_CREATED)
def add_draft_module(
    course_id: str,
    body: ModuleCreateRequest,
    current_user: User = Depends(require_creator_or_admin),
    service: CourseService = Depends(_get_course_service),
) -> dict[str, Any]:
    """Add a module to the course's working draft."""
    try:
        mod = service.add_module_to_draft(
            course_id=course_id,
            user_id=current_user.id,
            title=body.title,
            description=body.description,
            sort_order=body.sort_order,
            is_admin=current_user.role == UserRole.ADMIN,
        )
        return {
            "id": mod.id,
            "title": mod.title,
            "description": mod.description,
            "sort_order": mod.sort_order,
            "lessons": [],
        }
    except CourseServiceError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"error": {"code": e.code, "message": e.message}},
        )


@router.patch("/courses/{course_id}/draft/modules/{module_id}")
def update_draft_module(
    course_id: str,
    module_id: str,
    body: ModuleUpdateRequest,
    current_user: User = Depends(require_creator_or_admin),
    service: CourseService = Depends(_get_course_service),
) -> dict[str, Any]:
    """Update a module in the course's working draft."""
    try:
        mod = service.update_module_in_draft(
            course_id=course_id,
            module_id=module_id,
            user_id=current_user.id,
            title=body.title,
            description=body.description,
            sort_order=body.sort_order,
            is_admin=current_user.role == UserRole.ADMIN,
        )
        return {
            "id": mod.id,
            "title": mod.title,
            "description": mod.description,
            "sort_order": mod.sort_order,
        }
    except CourseServiceError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"error": {"code": e.code, "message": e.message}},
        )


@router.delete(
    "/courses/{course_id}/draft/modules/{module_id}", status_code=status.HTTP_204_NO_CONTENT
)
def delete_draft_module(
    course_id: str,
    module_id: str,
    current_user: User = Depends(require_creator_or_admin),
    service: CourseService = Depends(_get_course_service),
) -> None:
    """Delete a module and its lessons from the working draft."""
    try:
        service.delete_module_from_draft(
            course_id=course_id,
            module_id=module_id,
            user_id=current_user.id,
            is_admin=current_user.role == UserRole.ADMIN,
        )
    except CourseServiceError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"error": {"code": e.code, "message": e.message}},
        )


@router.post(
    "/courses/{course_id}/draft/modules/{module_id}/lessons", status_code=status.HTTP_201_CREATED
)
def add_draft_lesson(
    course_id: str,
    module_id: str,
    body: LessonCreateRequest,
    current_user: User = Depends(require_creator_or_admin),
    service: CourseService = Depends(_get_course_service),
) -> dict[str, Any]:
    """Add a lesson unit to a module in the working draft."""
    try:
        lesson = service.add_lesson_to_draft(
            course_id=course_id,
            module_id=module_id,
            user_id=current_user.id,
            slug=body.slug,
            title=body.title,
            description=body.description,
            learning_objectives=body.learning_objectives,
            estimated_minutes=body.estimated_minutes,
            sort_order=body.sort_order,
            is_admin=current_user.role == UserRole.ADMIN,
        )
        return {
            "id": lesson.id,
            "slug": lesson.slug,
            "title": lesson.title,
            "description": lesson.description,
            "learning_objectives": lesson.learning_objectives or [],
            "estimated_minutes": lesson.estimated_minutes,
            "sort_order": lesson.sort_order,
            "content_version": lesson.content_version,
            "blocks": [],
        }
    except CourseServiceError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"error": {"code": e.code, "message": e.message}},
        )


@router.patch("/courses/{course_id}/draft/lessons/{lesson_id}")
def update_draft_lesson(
    course_id: str,
    lesson_id: str,
    body: LessonUpdateRequest,
    current_user: User = Depends(require_creator_or_admin),
    service: CourseService = Depends(_get_course_service),
) -> dict[str, Any]:
    """Update lesson outline in the working draft."""
    try:
        lesson = service.update_lesson_in_draft(
            course_id=course_id,
            lesson_id=lesson_id,
            user_id=current_user.id,
            title=body.title,
            description=body.description,
            learning_objectives=body.learning_objectives,
            estimated_minutes=body.estimated_minutes,
            sort_order=body.sort_order,
            is_admin=current_user.role == UserRole.ADMIN,
        )
        return {
            "id": lesson.id,
            "slug": lesson.slug,
            "title": lesson.title,
            "description": lesson.description,
            "learning_objectives": lesson.learning_objectives or [],
            "estimated_minutes": lesson.estimated_minutes,
            "sort_order": lesson.sort_order,
            "content_version": lesson.content_version,
        }
    except CourseServiceError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"error": {"code": e.code, "message": e.message}},
        )


@router.put("/courses/{course_id}/draft/lessons/{lesson_id}/content")
def update_draft_lesson_content(
    course_id: str,
    lesson_id: str,
    body: LessonContentUpdateRequest,
    current_user: User = Depends(require_creator_or_admin),
    service: CourseService = Depends(_get_course_service),
) -> dict[str, Any]:
    """Atomically replace structured content blocks for a draft lesson.

    Validates block schema, rich-text tags, and media host security.
    """
    try:
        lesson = service.update_lesson_content(
            course_id=course_id,
            lesson_id=lesson_id,
            user_id=current_user.id,
            document=body.document,
            is_admin=current_user.role == UserRole.ADMIN,
        )
        blocks = [
            {
                "id": b.id,
                "block_type": b.block_type,
                "content": b.content,
                "sort_order": b.sort_order,
            }
            for b in sorted(lesson.blocks, key=lambda x: x.sort_order)
        ]
        return {
            "id": lesson.id,
            "slug": lesson.slug,
            "title": lesson.title,
            "description": lesson.description,
            "learning_objectives": lesson.learning_objectives or [],
            "estimated_minutes": lesson.estimated_minutes,
            "sort_order": lesson.sort_order,
            "content_version": lesson.content_version,
            "blocks": blocks,
        }
    except CourseServiceError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"error": {"code": e.code, "message": e.message}},
        )


# ── Publishing & Status Lifecycle Endpoints ────────────────────────────────


@router.post("/courses/{course_id}/publish", response_model=CoursePublishResponse)
def publish_course(
    course_id: str,
    body: CoursePublishRequest | None = None,
    current_user: User = Depends(require_creator_or_admin),
    service: CourseService = Depends(_get_course_service),
) -> dict[str, Any]:
    """Atomically publish the course working draft into an immutable snapshot.

    Validates full curriculum structure, stamps version, and activates in public catalog.
    """
    try:
        version = service.publish_course(
            course_id=course_id,
            publisher_id=current_user.id,
            changelog=body.changelog if body else None,
            is_admin=current_user.role == UserRole.ADMIN,
        )
        return {
            "course_id": version.course_id,
            "version_id": version.id,
            "version_number": version.version_number,
            "published_at": version.published_at,
            "publisher_id": version.publisher_id,
            "changelog": version.changelog,
        }
    except CourseServiceError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"error": {"code": e.code, "message": e.message}},
        )


@router.post("/courses/{course_id}/unpublish")
def unpublish_course(
    course_id: str,
    current_user: User = Depends(require_creator_or_admin),
    service: CourseService = Depends(_get_course_service),
) -> dict[str, Any]:
    """Unpublish a course, removing it from public catalog discovery."""
    try:
        course = service.unpublish_course(
            course_id=course_id,
            user_id=current_user.id,
            is_admin=current_user.role == UserRole.ADMIN,
        )
        return {"id": course.id, "status": course.status}
    except CourseServiceError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"error": {"code": e.code, "message": e.message}},
        )


@router.post("/courses/{course_id}/archive")
def archive_course(
    course_id: str,
    current_user: User = Depends(require_creator_or_admin),
    service: CourseService = Depends(_get_course_service),
) -> dict[str, Any]:
    """Archive a course, preventing further updates and hiding from catalog."""
    try:
        course = service.archive_course(
            course_id=course_id,
            user_id=current_user.id,
            is_admin=current_user.role == UserRole.ADMIN,
        )
        return {"id": course.id, "status": course.status}
    except CourseServiceError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"error": {"code": e.code, "message": e.message}},
        )
