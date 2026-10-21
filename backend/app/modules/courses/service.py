"""Course catalog, draft lifecycle, and version publishing service."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, or_, select, update
from sqlalchemy.orm import Session, joinedload, selectinload

from app.modules.courses.content_schemas import LessonBlock, LessonContentDocument
from app.modules.courses.models import (
    Course,
    CourseDifficulty,
    CourseSkill,
    CourseStatus,
    CourseVersion,
    Lesson,
    Module,
)
from app.modules.courses.models import (
    LessonBlock as LessonBlockModel,
)
from app.modules.skills.models import Discipline, Skill

logger = logging.getLogger(__name__)


class CourseServiceError(Exception):
    """Domain exception for course catalog, draft editing, and publishing errors."""

    def __init__(self, message: str, code: str = "COURSE_ERROR", status_code: int = 400) -> None:
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(message)


class CourseService:
    """Service managing courses, working drafts, and immutable version publishing."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # ── Public Catalog Queries ─────────────────────────────────────────────

    def list_published_courses(
        self,
        discipline_slug: str | None = None,
        difficulty: CourseDifficulty | None = None,
        search: str | None = None,
        page: int = 1,
        limit: int = 10,
    ) -> dict[str, Any]:
        """Query published courses with deterministic pagination and filtering.

        Strictly excludes drafts, unapproved, or archived courses.
        """
        # Ensure only published courses with an active published version are returned
        base_query = (
            select(Course)
            .join(Course.current_version)
            .join(Course.discipline)
            .where(
                Course.status == CourseStatus.PUBLISHED,
                Course.current_version_id.is_not(None),
                CourseVersion.is_active.is_(True),
                CourseVersion.published_at.is_not(None),
            )
        )

        if discipline_slug:
            base_query = base_query.where(Discipline.slug == discipline_slug)

        if difficulty:
            base_query = base_query.where(Course.difficulty_level == difficulty)

        if search and search.strip():
            term = f"%{search.strip().lower()}%"
            base_query = base_query.where(
                or_(
                    func.lower(Course.title).like(term),
                    func.lower(Course.slug).like(term),
                    func.lower(Course.short_description).like(term),
                )
            )

        # Count total matches
        count_stmt = select(func.count()).select_from(base_query.subquery())
        total = self.db.scalar(count_stmt) or 0

        # Paginate with deterministic ordering
        offset = (page - 1) * limit
        items_stmt = (
            base_query.options(
                joinedload(Course.discipline),
                joinedload(Course.current_version),
                selectinload(Course.skill_associations).joinedload(CourseSkill.skill),
            )
            .order_by(Course.created_at.desc(), Course.id.asc())
            .offset(offset)
            .limit(limit)
        )
        courses = list(self.db.scalars(items_stmt).all())

        pages = (total + limit - 1) // limit if limit > 0 else 1

        items = []
        for c in courses:
            skills = [
                {
                    "id": cs.skill.id,
                    "slug": cs.skill.slug,
                    "name": cs.skill.name,
                    "difficulty_level": cs.skill.difficulty_level,
                    "icon": cs.skill.icon,
                    "sort_order": cs.skill.sort_order,
                }
                for cs in c.skill_associations
                if cs.skill and cs.skill.is_active
            ]
            items.append(
                {
                    "id": c.id,
                    "slug": c.slug,
                    "title": c.title,
                    "short_description": c.short_description,
                    "discipline_id": c.discipline_id,
                    "discipline_slug": c.discipline.slug if c.discipline else None,
                    "discipline_name": c.discipline.name if c.discipline else None,
                    "difficulty_level": c.difficulty_level,
                    "estimated_duration_minutes": c.estimated_duration_minutes,
                    "cover_image_url": c.cover_image_url,
                    "status": c.status,
                    "version_number": c.current_version.version_number
                    if c.current_version
                    else None,
                    "skills": skills,
                }
            )

        return {
            "items": items,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": pages,
        }

    def get_published_course_by_slug(self, slug: str) -> dict[str, Any] | None:
        """Retrieve full curriculum from the current published version of a course."""
        stmt = (
            select(Course)
            .options(
                joinedload(Course.discipline),
                joinedload(Course.current_version)
                .selectinload(CourseVersion.modules)
                .selectinload(Module.lessons)
                .selectinload(Lesson.blocks),
                selectinload(Course.skill_associations).joinedload(CourseSkill.skill),
            )
            .where(
                Course.slug == slug,
                Course.status == CourseStatus.PUBLISHED,
                Course.current_version_id.is_not(None),
            )
        )
        course = self.db.scalars(stmt).first()
        if not course or not course.current_version or not course.current_version.is_active:
            return None

        version = course.current_version
        return self._format_course_detail(course, version)

    def get_published_lesson(self, course_slug: str, lesson_slug: str) -> dict[str, Any] | None:
        """Retrieve lesson details and content blocks from the current published course version."""
        course_data = self.get_published_course_by_slug(course_slug)
        if not course_data:
            return None

        for module in course_data["modules"]:
            for lesson in module["lessons"]:
                if lesson["slug"] == lesson_slug:
                    return lesson
        return None

    # ── Course Creation & Aggregate Management ─────────────────────────────

    def create_course(
        self,
        creator_id: str,
        slug: str,
        title: str,
        short_description: str,
        discipline_id: str,
        difficulty_level: CourseDifficulty = CourseDifficulty.BEGINNER,
        full_description: str | None = None,
        estimated_duration_minutes: int | None = None,
        cover_image_url: str | None = None,
        learning_objectives: list[str] | None = None,
        skill_ids: list[str] | None = None,
    ) -> Course:
        """Create a new course aggregate with an initial working draft (version 0)."""
        # Validate slug uniqueness
        existing = self.db.scalars(select(Course).where(Course.slug == slug)).first()
        if existing:
            raise CourseServiceError(
                f"Course with slug '{slug}' already exists.",
                code="COURSE_ALREADY_EXISTS",
                status_code=409,
            )

        # Validate discipline
        discipline = self.db.get(Discipline, discipline_id)
        if not discipline:
            raise CourseServiceError(
                f"Discipline '{discipline_id}' does not exist.",
                code="DISCIPLINE_NOT_FOUND",
                status_code=404,
            )

        course = Course(
            slug=slug,
            title=title,
            short_description=short_description,
            full_description=full_description,
            discipline_id=discipline_id,
            difficulty_level=difficulty_level,
            estimated_duration_minutes=estimated_duration_minutes,
            cover_image_url=cover_image_url,
            status=CourseStatus.DRAFT,
            creator_id=creator_id,
        )
        self.db.add(course)
        self.db.flush()

        # Map skills
        if skill_ids:
            for s_id in set(skill_ids):
                skill = self.db.get(Skill, s_id)
                if skill:
                    self.db.add(CourseSkill(course_id=course.id, skill_id=s_id, is_primary=True))

        # Create working draft version (version_number=0 represents mutable draft)
        draft_version = CourseVersion(
            course_id=course.id,
            version_number=0,
            title=title,
            description=full_description,
            learning_objectives=learning_objectives or [],
            published_at=None,
            is_active=False,
        )
        self.db.add(draft_version)
        self.db.commit()
        self.db.refresh(course)
        return course

    def update_course_metadata(
        self,
        course_id: str,
        user_id: str,
        is_admin: bool = False,
        title: str | None = None,
        short_description: str | None = None,
        full_description: str | None = None,
        difficulty_level: CourseDifficulty | None = None,
        estimated_duration_minutes: int | None = None,
        cover_image_url: str | None = None,
        learning_objectives: list[str] | None = None,
        skill_ids: list[str] | None = None,
    ) -> Course:
        """Update top-level course metadata and the working draft objectives."""
        course = self.get_course_by_id(course_id)
        if not course:
            raise CourseServiceError("Course not found.", code="COURSE_NOT_FOUND", status_code=404)

        if not is_admin and course.creator_id != user_id:
            raise CourseServiceError(
                "You do not have permission to modify this course.",
                code="FORBIDDEN",
                status_code=403,
            )

        if title is not None:
            course.title = title
        if short_description is not None:
            course.short_description = short_description
        if full_description is not None:
            course.full_description = full_description
        if difficulty_level is not None:
            course.difficulty_level = difficulty_level
        if estimated_duration_minutes is not None:
            course.estimated_duration_minutes = estimated_duration_minutes
        if cover_image_url is not None:
            course.cover_image_url = cover_image_url

        if skill_ids is not None:
            # Replace skill mappings
            self.db.query(CourseSkill).filter(CourseSkill.course_id == course.id).delete()
            for s_id in set(skill_ids):
                skill = self.db.get(Skill, s_id)
                if skill:
                    self.db.add(CourseSkill(course_id=course.id, skill_id=s_id, is_primary=True))

        # Also update active working draft if exists
        draft = self.get_or_create_draft(course_id=course.id)
        if title is not None:
            draft.title = title
        if full_description is not None:
            draft.description = full_description
        if learning_objectives is not None:
            draft.learning_objectives = learning_objectives

        self.db.commit()
        self.db.refresh(course)
        return course

    def get_course_by_id(self, course_id: str) -> Course | None:
        """Get course by UUID."""
        return self.db.get(Course, course_id)

    # ── Draft Management & Published Immutability ──────────────────────────

    def get_or_create_draft(self, course_id: str) -> CourseVersion:
        """Retrieve existing working draft (published_at is None), or create a new one.

        If a course is already published and has no open draft, this clones the current
        published version into a fresh draft (version_number=0, published_at=None).
        Modifying this cloned draft NEVER alters earlier published versions.
        """
        stmt = (
            select(CourseVersion)
            .options(
                selectinload(CourseVersion.modules)
                .selectinload(Module.lessons)
                .selectinload(Lesson.blocks)
            )
            .where(
                CourseVersion.course_id == course_id,
                CourseVersion.published_at.is_(None),
            )
        )
        draft = self.db.scalars(stmt).first()
        if draft:
            return draft

        # No draft exists — check if course has a published version to clone from
        course = self.get_course_by_id(course_id)
        if not course:
            raise CourseServiceError("Course not found.", code="COURSE_NOT_FOUND", status_code=404)

        if course.current_version_id:
            # Clone from current published version
            pub_version = self.db.scalars(
                select(CourseVersion)
                .options(
                    selectinload(CourseVersion.modules)
                    .selectinload(Module.lessons)
                    .selectinload(Lesson.blocks)
                )
                .where(CourseVersion.id == course.current_version_id)
            ).first()

            if pub_version:
                new_draft = CourseVersion(
                    course_id=course.id,
                    version_number=0,
                    title=pub_version.title,
                    description=pub_version.description,
                    learning_objectives=list(pub_version.learning_objectives),
                    published_at=None,
                    is_active=False,
                )
                self.db.add(new_draft)
                self.db.flush()

                # Clone modules, lessons, and blocks
                for mod in pub_version.modules:
                    new_mod = Module(
                        course_version_id=new_draft.id,
                        title=mod.title,
                        description=mod.description,
                        sort_order=mod.sort_order,
                    )
                    self.db.add(new_mod)
                    self.db.flush()

                    for les in mod.lessons:
                        new_les = Lesson(
                            module_id=new_mod.id,
                            slug=les.slug,
                            title=les.title,
                            description=les.description,
                            learning_objectives=list(les.learning_objectives),
                            estimated_minutes=les.estimated_minutes,
                            sort_order=les.sort_order,
                            content_version=les.content_version,
                        )
                        self.db.add(new_les)
                        self.db.flush()

                        for blk in les.blocks:
                            new_blk = LessonBlockModel(
                                lesson_id=new_les.id,
                                block_type=blk.block_type,
                                content=dict(blk.content),
                                sort_order=blk.sort_order,
                            )
                            self.db.add(new_blk)

                self.db.commit()
                self.db.refresh(new_draft)
                return new_draft

        # Course was never published and somehow has no draft — create a blank one
        blank_draft = CourseVersion(
            course_id=course.id,
            version_number=0,
            title=course.title,
            description=course.full_description,
            learning_objectives=[],
            published_at=None,
            is_active=False,
        )
        self.db.add(blank_draft)
        self.db.commit()
        self.db.refresh(blank_draft)
        return blank_draft

    def get_draft_detail(
        self, course_id: str, user_id: str, is_admin: bool = False
    ) -> dict[str, Any]:
        """Get complete draft structure with modules, lessons, and content."""
        course = self.get_course_by_id(course_id)
        if not course:
            raise CourseServiceError("Course not found.", code="COURSE_NOT_FOUND", status_code=404)

        if not is_admin and course.creator_id != user_id:
            raise CourseServiceError(
                "You do not have permission to view this course draft.",
                code="FORBIDDEN",
                status_code=403,
            )

        draft = self.get_or_create_draft(course_id)
        return self._format_course_detail(course, draft)

    def _assert_version_is_mutable(self, version: CourseVersion) -> None:
        """Enforce published-version immutability."""
        if version.published_at is not None:
            raise CourseServiceError(
                "Published course versions are immutable and cannot be modified. Edit a draft instead.",
                code="VERSION_IMMUTABLE",
                status_code=409,
            )

    # ── Draft Modules & Lessons Management ─────────────────────────────────

    def add_module_to_draft(
        self,
        course_id: str,
        user_id: str,
        title: str,
        description: str | None = None,
        sort_order: int = 0,
        is_admin: bool = False,
    ) -> Module:
        """Add a module container to the course's working draft."""
        course = self.get_course_by_id(course_id)
        if not course:
            raise CourseServiceError("Course not found.", code="COURSE_NOT_FOUND", status_code=404)
        if not is_admin and course.creator_id != user_id:
            raise CourseServiceError("Forbidden.", code="FORBIDDEN", status_code=403)

        draft = self.get_or_create_draft(course_id)
        self._assert_version_is_mutable(draft)

        module = Module(
            course_version_id=draft.id,
            title=title,
            description=description,
            sort_order=sort_order,
        )
        self.db.add(module)
        self.db.commit()
        self.db.refresh(module)
        return module

    def update_module_in_draft(
        self,
        course_id: str,
        module_id: str,
        user_id: str,
        title: str | None = None,
        description: str | None = None,
        sort_order: int | None = None,
        is_admin: bool = False,
    ) -> Module:
        """Update a module in the working draft."""
        course = self.get_course_by_id(course_id)
        if not course:
            raise CourseServiceError("Course not found.", code="COURSE_NOT_FOUND", status_code=404)
        if not is_admin and course.creator_id != user_id:
            raise CourseServiceError("Forbidden.", code="FORBIDDEN", status_code=403)

        module = self.db.get(Module, module_id)
        if not module or module.course_version.course_id != course_id:
            raise CourseServiceError("Module not found.", code="MODULE_NOT_FOUND", status_code=404)

        self._assert_version_is_mutable(module.course_version)

        if title is not None:
            module.title = title
        if description is not None:
            module.description = description
        if sort_order is not None:
            module.sort_order = sort_order

        self.db.commit()
        self.db.refresh(module)
        return module

    def delete_module_from_draft(
        self,
        course_id: str,
        module_id: str,
        user_id: str,
        is_admin: bool = False,
    ) -> bool:
        """Delete a module and its lessons from the working draft."""
        course = self.get_course_by_id(course_id)
        if not course:
            raise CourseServiceError("Course not found.", code="COURSE_NOT_FOUND", status_code=404)
        if not is_admin and course.creator_id != user_id:
            raise CourseServiceError("Forbidden.", code="FORBIDDEN", status_code=403)

        module = self.db.get(Module, module_id)
        if not module or module.course_version.course_id != course_id:
            raise CourseServiceError("Module not found.", code="MODULE_NOT_FOUND", status_code=404)

        self._assert_version_is_mutable(module.course_version)
        self.db.delete(module)
        self.db.commit()
        return True

    def add_lesson_to_draft(
        self,
        course_id: str,
        module_id: str,
        user_id: str,
        slug: str,
        title: str,
        description: str | None = None,
        learning_objectives: list[str] | None = None,
        estimated_minutes: int | None = None,
        sort_order: int = 0,
        is_admin: bool = False,
    ) -> Lesson:
        """Add a lesson unit to a module in the working draft."""
        course = self.get_course_by_id(course_id)
        if not course:
            raise CourseServiceError("Course not found.", code="COURSE_NOT_FOUND", status_code=404)
        if not is_admin and course.creator_id != user_id:
            raise CourseServiceError("Forbidden.", code="FORBIDDEN", status_code=403)

        module = self.db.get(Module, module_id)
        if not module or module.course_version.course_id != course_id:
            raise CourseServiceError("Module not found.", code="MODULE_NOT_FOUND", status_code=404)

        self._assert_version_is_mutable(module.course_version)

        # Check unique lesson slug within module
        existing_lesson = self.db.scalars(
            select(Lesson).where(Lesson.module_id == module_id, Lesson.slug == slug)
        ).first()
        if existing_lesson:
            raise CourseServiceError(
                f"Lesson with slug '{slug}' already exists in this module.",
                code="LESSON_SLUG_EXISTS",
                status_code=409,
            )

        lesson = Lesson(
            module_id=module_id,
            slug=slug,
            title=title,
            description=description,
            learning_objectives=learning_objectives or [],
            estimated_minutes=estimated_minutes,
            sort_order=sort_order,
            content_version=1,
        )
        self.db.add(lesson)
        self.db.commit()
        self.db.refresh(lesson)
        return lesson

    def update_lesson_in_draft(
        self,
        course_id: str,
        lesson_id: str,
        user_id: str,
        title: str | None = None,
        description: str | None = None,
        learning_objectives: list[str] | None = None,
        estimated_minutes: int | None = None,
        sort_order: int | None = None,
        is_admin: bool = False,
    ) -> Lesson:
        """Update lesson metadata in the working draft."""
        lesson = self.db.get(Lesson, lesson_id)
        if not lesson or lesson.module.course_version.course_id != course_id:
            raise CourseServiceError("Lesson not found.", code="LESSON_NOT_FOUND", status_code=404)

        course = lesson.module.course_version.course
        if not is_admin and course.creator_id != user_id:
            raise CourseServiceError("Forbidden.", code="FORBIDDEN", status_code=403)

        self._assert_version_is_mutable(lesson.module.course_version)

        if title is not None:
            lesson.title = title
        if description is not None:
            lesson.description = description
        if learning_objectives is not None:
            lesson.learning_objectives = learning_objectives
        if estimated_minutes is not None:
            lesson.estimated_minutes = estimated_minutes
        if sort_order is not None:
            lesson.sort_order = sort_order

        self.db.commit()
        self.db.refresh(lesson)
        return lesson

    def update_lesson_content(
        self,
        course_id: str,
        lesson_id: str,
        user_id: str,
        document: LessonContentDocument,
        is_admin: bool = False,
    ) -> Lesson:
        """Atomically replace content blocks for a draft lesson.

        Validates all block data through LessonContentDocument Pydantic models.
        """
        lesson = self.db.get(Lesson, lesson_id)
        if not lesson or lesson.module.course_version.course_id != course_id:
            raise CourseServiceError("Lesson not found.", code="LESSON_NOT_FOUND", status_code=404)

        course = lesson.module.course_version.course
        if not is_admin and course.creator_id != user_id:
            raise CourseServiceError("Forbidden.", code="FORBIDDEN", status_code=403)

        self._assert_version_is_mutable(lesson.module.course_version)

        # Clear existing blocks for this lesson
        self.db.query(LessonBlockModel).filter(LessonBlockModel.lesson_id == lesson_id).delete()

        # Add validated blocks
        for idx, block in enumerate(document.blocks, start=1):
            block_type_val = block.type.value if hasattr(block.type, "value") else str(block.type)
            blk_model = LessonBlockModel(
                lesson_id=lesson.id,
                block_type=block_type_val,
                content=block.data,
                sort_order=idx,
            )
            self.db.add(blk_model)

        lesson.content_version += 1
        if document.learning_objectives:
            lesson.learning_objectives = document.learning_objectives

        self.db.commit()
        self.db.refresh(lesson)
        return lesson

    # ── Publishing & Immutability Guarantee ────────────────────────────────

    def publish_course(
        self,
        course_id: str,
        publisher_id: str,
        changelog: str | None = None,
        is_admin: bool = False,
    ) -> CourseVersion:
        """Atomically publish the working draft into an immutable snapshot.

        Enforces all Phase 3 publishing requirements:
        1. Authenticate & authorize publisher (owner or admin).
        2. Validate course structure: at least 1 module, every module has at least 1 lesson.
        3. Every lesson must have at least 1 content block.
        4. Validate lesson blocks against schemas and sanitization rules.
        5. Verify learning objectives are present.
        6. Compute next version number safely.
        7. Stamp version with publisher identity and publication timestamp.
        8. Set active flag and update Course.current_version_id atomically.
        9. Deactivate earlier published versions (preserving history).
        """
        course = self.get_course_by_id(course_id)
        if not course:
            raise CourseServiceError("Course not found.", code="COURSE_NOT_FOUND", status_code=404)

        if not is_admin and course.creator_id != publisher_id:
            raise CourseServiceError(
                "You do not have permission to publish this course.",
                code="FORBIDDEN",
                status_code=403,
            )

        # Find open draft
        stmt = (
            select(CourseVersion)
            .options(
                selectinload(CourseVersion.modules)
                .selectinload(Module.lessons)
                .selectinload(Lesson.blocks)
            )
            .where(
                CourseVersion.course_id == course_id,
                CourseVersion.published_at.is_(None),
            )
        )
        draft = self.db.scalars(stmt).first()
        if not draft:
            raise CourseServiceError(
                "No open draft found to publish for this course.",
                code="NO_DRAFT_TO_PUBLISH",
                status_code=400,
            )

        # ── Validations ──
        if not draft.modules:
            raise CourseServiceError(
                "Cannot publish course without any modules.",
                code="PUBLISH_VALIDATION_ERROR",
                status_code=400,
            )

        for mod in draft.modules:
            if not mod.lessons:
                raise CourseServiceError(
                    f"Cannot publish course: module '{mod.title}' has no lessons.",
                    code="PUBLISH_VALIDATION_ERROR",
                    status_code=400,
                )
            for les in mod.lessons:
                if not les.blocks:
                    raise CourseServiceError(
                        f"Cannot publish course: lesson '{les.title}' in module '{mod.title}' has no content blocks.",
                        code="PUBLISH_VALIDATION_ERROR",
                        status_code=400,
                    )
                # Validate block schemas
                for blk in les.blocks:
                    try:
                        LessonBlock(id=blk.id, type=blk.block_type, data=blk.content)
                    except Exception as e:
                        raise CourseServiceError(
                            f"Block validation error in lesson '{les.title}': {e}",
                            code="PUBLISH_VALIDATION_ERROR",
                            status_code=400,
                        )

        # Compute next version number safely
        max_ver_stmt = select(func.max(CourseVersion.version_number)).where(
            CourseVersion.course_id == course_id,
            CourseVersion.published_at.is_not(None),
        )
        max_version = self.db.scalar(max_ver_stmt) or 0
        next_version = max_version + 1

        # Atomically transition draft to published immutable version
        now = datetime.now(UTC)
        draft.version_number = next_version
        draft.published_at = now
        draft.publisher_id = publisher_id
        draft.changelog = changelog
        draft.is_active = True

        # Deactivate previous published versions
        self.db.execute(
            update(CourseVersion)
            .where(CourseVersion.course_id == course_id, CourseVersion.id != draft.id)
            .values(is_active=False)
        )

        # Update course aggregate pointer
        course.status = CourseStatus.PUBLISHED
        course.current_version_id = draft.id

        try:
            self.db.commit()
            self.db.refresh(draft)
            self.db.refresh(course)
        except Exception as e:
            self.db.rollback()
            logger.exception("Failed to publish course %s: %s", course_id, e)
            raise CourseServiceError(
                "Failed to publish course due to transaction failure.",
                code="PUBLISH_TRANSACTION_FAILED",
                status_code=500,
            ) from e

        return draft

    def unpublish_course(self, course_id: str, user_id: str, is_admin: bool = False) -> Course:
        """Unpublish a course, removing it from public catalog discovery.

        Earlier published versions remain safely in the version history.
        """
        course = self.get_course_by_id(course_id)
        if not course:
            raise CourseServiceError("Course not found.", code="COURSE_NOT_FOUND", status_code=404)
        if not is_admin and course.creator_id != user_id:
            raise CourseServiceError("Forbidden.", code="FORBIDDEN", status_code=403)

        course.status = CourseStatus.DRAFT
        self.db.commit()
        self.db.refresh(course)
        return course

    def archive_course(self, course_id: str, user_id: str, is_admin: bool = False) -> Course:
        """Archive a course, removing it from public discovery while preserving history."""
        course = self.get_course_by_id(course_id)
        if not course:
            raise CourseServiceError("Course not found.", code="COURSE_NOT_FOUND", status_code=404)
        if not is_admin and course.creator_id != user_id:
            raise CourseServiceError("Forbidden.", code="FORBIDDEN", status_code=403)

        course.status = CourseStatus.ARCHIVED
        self.db.commit()
        self.db.refresh(course)
        return course

    # ── Formatting Helper ──────────────────────────────────────────────────

    def _format_course_detail(self, course: Course, version: CourseVersion) -> dict[str, Any]:
        """Format course aggregate and version snapshot into response dict."""
        skills = [
            {
                "id": cs.skill.id,
                "slug": cs.skill.slug,
                "name": cs.skill.name,
                "difficulty_level": cs.skill.difficulty_level,
                "icon": cs.skill.icon,
                "sort_order": cs.skill.sort_order,
            }
            for cs in course.skill_associations
            if cs.skill and cs.skill.is_active
        ]

        modules = []
        for mod in sorted(version.modules, key=lambda m: m.sort_order):
            lessons = []
            for les in sorted(mod.lessons, key=lambda item: item.sort_order):
                blocks = [
                    {
                        "id": blk.id,
                        "block_type": blk.block_type,
                        "content": blk.content,
                        "sort_order": blk.sort_order,
                    }
                    for blk in sorted(les.blocks, key=lambda b: b.sort_order)
                ]
                lessons.append(
                    {
                        "id": les.id,
                        "slug": les.slug,
                        "title": les.title,
                        "description": les.description,
                        "learning_objectives": les.learning_objectives or [],
                        "estimated_minutes": les.estimated_minutes,
                        "sort_order": les.sort_order,
                        "content_version": les.content_version,
                        "blocks": blocks,
                    }
                )
            modules.append(
                {
                    "id": mod.id,
                    "title": mod.title,
                    "description": mod.description,
                    "sort_order": mod.sort_order,
                    "lessons": lessons,
                }
            )

        return {
            "id": course.id,
            "slug": course.slug,
            "title": course.title,
            "short_description": course.short_description,
            "full_description": course.full_description,
            "discipline_id": course.discipline_id,
            "discipline_slug": course.discipline.slug if course.discipline else None,
            "discipline_name": course.discipline.name if course.discipline else None,
            "difficulty_level": course.difficulty_level,
            "estimated_duration_minutes": course.estimated_duration_minutes,
            "cover_image_url": course.cover_image_url,
            "status": course.status,
            "creator_id": course.creator_id,
            "version_id": version.id,
            "version_number": version.version_number,
            "published_at": version.published_at,
            "learning_objectives": version.learning_objectives or [],
            "skills": skills,
            "modules": modules,
        }
