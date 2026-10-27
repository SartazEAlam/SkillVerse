"""Course catalog, draft lifecycle, and version publishing service."""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, or_, select, update
from sqlalchemy.orm import Session, joinedload, selectinload

from app.modules.activities.models import Activity, GradingConfig
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

    def __init__(
        self,
        message: str,
        code: str = "COURSE_ERROR",
        status_code: int = 400,
        details: Any = None,
    ) -> None:
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details
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
                joinedload(Course.current_version)
                .selectinload(CourseVersion.modules)
                .selectinload(Module.lessons)
                .selectinload(Lesson.activities)
                .joinedload(Activity.grading_config),
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
        """Get course by UUID with discipline and skill associations eagerly loaded."""
        stmt = (
            select(Course)
            .options(
                joinedload(Course.discipline),
                selectinload(Course.skill_associations).joinedload(CourseSkill.skill),
            )
            .where(Course.id == course_id)
        )
        return self.db.scalars(stmt).first()

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
                .selectinload(Lesson.blocks),
                selectinload(CourseVersion.modules)
                .selectinload(Module.lessons)
                .selectinload(Lesson.activities)
                .joinedload(Activity.grading_config),
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
                    .selectinload(Lesson.blocks),
                    selectinload(CourseVersion.modules)
                    .selectinload(Module.lessons)
                    .selectinload(Lesson.activities)
                    .joinedload(Activity.grading_config),
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

                # Clone modules, lessons, blocks, and activities
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

                        # Clone activities linked to this lesson
                        activity_id_map: dict[str, str] = {}
                        for act in getattr(les, "activities", []):
                            new_act = Activity(
                                lesson_id=new_les.id,
                                activity_type=act.activity_type,
                                title=act.title,
                                instructions=act.instructions,
                                configuration=dict(act.configuration)
                                if isinstance(act.configuration, dict)
                                else {},
                                max_attempts=act.max_attempts,
                                sort_order=act.sort_order,
                                is_active=act.is_active,
                            )
                            self.db.add(new_act)
                            self.db.flush()
                            activity_id_map[act.id] = new_act.id

                            if act.grading_config:
                                new_gc = GradingConfig(
                                    activity_id=new_act.id,
                                    grading_type=act.grading_config.grading_type,
                                    passing_score=act.grading_config.passing_score,
                                    answer_key=dict(act.grading_config.answer_key)
                                    if isinstance(act.grading_config.answer_key, dict)
                                    else {},
                                    rubric=dict(act.grading_config.rubric)
                                    if isinstance(act.grading_config.rubric, dict)
                                    else None,
                                    test_cases=list(act.grading_config.test_cases)
                                    if isinstance(act.grading_config.test_cases, list)
                                    else None,
                                    feedback_config=dict(act.grading_config.feedback_config)
                                    if isinstance(act.grading_config.feedback_config, dict)
                                    else None,
                                )
                                self.db.add(new_gc)

                        for blk in les.blocks:
                            content = dict(blk.content) if isinstance(blk.content, dict) else {}
                            if blk.block_type == "activity" and "activity_id" in content:
                                old_act_id = content["activity_id"]
                                if old_act_id in activity_id_map:
                                    content["activity_id"] = activity_id_map[old_act_id]

                            new_blk = LessonBlockModel(
                                lesson_id=new_les.id,
                                block_type=blk.block_type,
                                content=content,
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

        # Find open draft with modules, lessons, blocks, and activities eagerly loaded
        stmt = (
            select(CourseVersion)
            .options(
                selectinload(CourseVersion.modules)
                .selectinload(Module.lessons)
                .selectinload(Lesson.blocks),
                selectinload(CourseVersion.modules)
                .selectinload(Module.lessons)
                .selectinload(Lesson.activities)
                .joinedload(Activity.grading_config),
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
        # Enforce all mandatory validations reported by draft validation
        validation = self._validate_course_and_draft(course, draft)
        if not validation["valid"]:
            first_error = validation["errors"][0]["message"]
            raise CourseServiceError(
                first_error,
                code="PUBLISH_VALIDATION_ERROR",
                status_code=400,
                details=validation["errors"],
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
                activities = [
                    {
                        "id": act.id,
                        "lesson_id": act.lesson_id,
                        "activity_type": act.activity_type,
                        "title": act.title,
                        "instructions": act.instructions,
                        "sort_order": act.sort_order,
                        "max_attempts": act.max_attempts,
                        "passing_score": act.grading_config.passing_score
                        if act.grading_config
                        else 70.0,
                        "configuration": act.configuration
                        if isinstance(act.configuration, dict)
                        else {},
                        "skill_id": (act.configuration or {}).get("skill_id")
                        if isinstance(act.configuration, dict)
                        else None,
                        "skill_slug": (act.configuration or {}).get("skill_slug")
                        if isinstance(act.configuration, dict)
                        else None,
                    }
                    for act in sorted(
                        getattr(les, "activities", []) or [], key=lambda a: a.sort_order
                    )
                    if act.is_active
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
                        "activities": activities,
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

    # ── Phase 7: Creator Studio & Course Authoring Operations ──────────────

    def list_managed_courses(
        self,
        user_id: str,
        is_admin: bool = False,
        status: CourseStatus | None = None,
    ) -> dict[str, Any]:
        """List all courses managed by the creator or admin, with rich authoring metadata."""
        stmt = (
            select(Course)
            .options(
                joinedload(Course.discipline),
                joinedload(Course.current_version),
                selectinload(Course.versions),
            )
            .order_by(Course.updated_at.desc(), Course.id.desc())
        )
        if not is_admin:
            stmt = stmt.where(Course.creator_id == user_id)
        if status:
            stmt = stmt.where(Course.status == status)

        courses = list(self.db.scalars(stmt).all())

        items = []
        for c in courses:
            draft_v = next((v for v in c.versions if v.published_at is None), None)
            pub_v = c.current_version

            target_v = draft_v or pub_v
            modules_count = 0
            lessons_count = 0
            activities_count = 0
            if target_v:
                m_ids = self.db.scalars(
                    select(Module.id).where(Module.course_version_id == target_v.id)
                ).all()
                modules_count = len(m_ids)
                if m_ids:
                    les_ids = self.db.scalars(
                        select(Lesson.id).where(Lesson.module_id.in_(m_ids))
                    ).all()
                    lessons_count = len(les_ids)
                    if les_ids:
                        activities_count = (
                            self.db.scalar(
                                select(func.count(Activity.id)).where(
                                    Activity.lesson_id.in_(les_ids), Activity.is_active.is_(True)
                                )
                            )
                            or 0
                        )

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
                    "creator_id": c.creator_id,
                    "published_version_number": pub_v.version_number if pub_v else None,
                    "has_draft": draft_v is not None,
                    "draft_version_id": draft_v.id if draft_v else None,
                    "modules_count": modules_count,
                    "lessons_count": lessons_count,
                    "activities_count": activities_count,
                    "created_at": c.created_at,
                    "updated_at": c.updated_at,
                }
            )

        return {"items": items, "total": len(items)}

    def delete_course(self, course_id: str, user_id: str, is_admin: bool = False) -> bool:
        """Delete an unpublished draft course (published courses must be archived)."""
        course = self.get_course_by_id(course_id)
        if not course:
            raise CourseServiceError("Course not found.", code="COURSE_NOT_FOUND", status_code=404)
        if not is_admin and course.creator_id != user_id:
            raise CourseServiceError("Forbidden.", code="FORBIDDEN", status_code=403)

        has_published = any(v.published_at is not None for v in course.versions)
        if course.status == CourseStatus.PUBLISHED or has_published:
            raise CourseServiceError(
                "Cannot delete a published course. Use archive instead to preserve enrollment and progress records.",
                code="COURSE_PUBLISHED_CANNOT_DELETE",
                status_code=400,
            )

        self.db.delete(course)
        self.db.commit()
        return True

    def delete_lesson_from_draft(
        self, course_id: str, lesson_id: str, user_id: str, is_admin: bool = False
    ) -> bool:
        """Delete a lesson and its blocks/activities from the working draft."""
        lesson = self.db.get(Lesson, lesson_id)
        if not lesson or lesson.module.course_version.course_id != course_id:
            raise CourseServiceError("Lesson not found.", code="LESSON_NOT_FOUND", status_code=404)

        course = lesson.module.course_version.course
        if not is_admin and course.creator_id != user_id:
            raise CourseServiceError("Forbidden.", code="FORBIDDEN", status_code=403)

        self._assert_version_is_mutable(lesson.module.course_version)
        self.db.delete(lesson)
        self.db.commit()
        return True

    def reorder_draft_curriculum(
        self,
        course_id: str,
        user_id: str,
        modules_order: list[dict[str, Any]],
        lessons_order: list[dict[str, Any]],
        is_admin: bool = False,
    ) -> bool:
        """Batch update sort_order for modules and lessons in a draft."""
        course = self.get_course_by_id(course_id)
        if not course:
            raise CourseServiceError("Course not found.", code="COURSE_NOT_FOUND", status_code=404)
        if not is_admin and course.creator_id != user_id:
            raise CourseServiceError("Forbidden.", code="FORBIDDEN", status_code=403)

        draft = self.get_or_create_draft(course_id)
        self._assert_version_is_mutable(draft)

        for m_item in modules_order:
            mod = self.db.get(Module, m_item["id"])
            if mod and mod.course_version_id == draft.id:
                mod.sort_order = m_item["sort_order"]

        for l_item in lessons_order:
            les = self.db.get(Lesson, l_item["id"])
            if les and les.module.course_version_id == draft.id:
                les.sort_order = l_item["sort_order"]
                if l_item.get("module_id"):
                    target_mod = self.db.get(Module, l_item["module_id"])
                    if target_mod and target_mod.course_version_id == draft.id:
                        les.module_id = target_mod.id

        self.db.commit()
        return True

    def _validate_course_and_draft(self, course: Course, draft: CourseVersion) -> dict[str, Any]:
        """Perform comprehensive validation of a course draft prior to publishing.

        Shared by validate_draft() and publish_course() to enforce consistent mandatory rules.
        """
        errors: list[dict[str, Any]] = []
        warnings: list[dict[str, Any]] = []

        # 1. Course metadata
        if not course.title or len(course.title.strip()) < 3:
            errors.append(
                {
                    "scope": "course",
                    "id": course.id,
                    "title": course.title,
                    "message": "Course title must be at least 3 characters long.",
                }
            )
        if not course.short_description or len(course.short_description.strip()) < 10:
            errors.append(
                {
                    "scope": "course",
                    "id": course.id,
                    "title": course.title,
                    "message": "Course short description must be at least 10 characters long.",
                }
            )
        if not course.discipline or not course.discipline.is_active:
            errors.append(
                {
                    "scope": "course",
                    "id": course.id,
                    "title": course.title,
                    "message": "Course must be assigned to an active discipline.",
                }
            )
        if not course.skill_associations:
            warnings.append(
                {
                    "scope": "course",
                    "id": course.id,
                    "title": course.title,
                    "message": "Course has no associated skills. Learners will not earn skill mastery from this course.",
                }
            )

        # 2. Modules
        if not draft.modules:
            errors.append(
                {
                    "scope": "course",
                    "id": course.id,
                    "title": course.title,
                    "message": "Cannot publish course without any modules.",
                }
            )

        course_skill_ids = {cs.skill_id for cs in (course.skill_associations or [])}

        # Reliably load activities for all lessons in this draft
        lesson_ids = [
            les.id for mod in (draft.modules or []) for les in (mod.lessons or []) if les.id
        ]
        activities_by_lesson: dict[str, list[Activity]] = defaultdict(list)
        if lesson_ids:
            acts_stmt = (
                select(Activity)
                .options(joinedload(Activity.grading_config))
                .where(Activity.lesson_id.in_(lesson_ids))
                .order_by(Activity.sort_order)
            )
            for act in self.db.scalars(acts_stmt).unique():
                if act.lesson_id:
                    activities_by_lesson[act.lesson_id].append(act)

        for mod in draft.modules or []:
            if not mod.title or len(mod.title.strip()) < 2:
                errors.append(
                    {
                        "scope": "module",
                        "id": mod.id,
                        "title": mod.title,
                        "message": f"Module '{mod.title}' title must be at least 2 characters long.",
                    }
                )
            if not mod.lessons:
                errors.append(
                    {
                        "scope": "module",
                        "id": mod.id,
                        "title": mod.title,
                        "message": f"Cannot publish course: module '{mod.title}' has no lessons.",
                    }
                )

            for les in mod.lessons or []:
                if not les.title or len(les.title.strip()) < 2:
                    errors.append(
                        {
                            "scope": "lesson",
                            "id": les.id,
                            "title": les.title,
                            "message": f"Lesson '{les.title}' title must be at least 2 characters long.",
                        }
                    )
                if not les.slug or not les.slug.strip():
                    errors.append(
                        {
                            "scope": "lesson",
                            "id": les.id,
                            "title": les.title,
                            "message": f"Lesson '{les.title}' is missing a URL slug.",
                        }
                    )
                if not les.blocks:
                    errors.append(
                        {
                            "scope": "lesson",
                            "id": les.id,
                            "title": les.title,
                            "message": f"Cannot publish course: lesson '{les.title}' in module '{mod.title}' has no content blocks.",
                        }
                    )
                else:
                    for blk in les.blocks:
                        try:
                            LessonBlock(id=blk.id, type=blk.block_type, data=blk.content)
                        except Exception as e:
                            errors.append(
                                {
                                    "scope": "lesson",
                                    "id": les.id,
                                    "title": les.title,
                                    "message": f"Block validation error in lesson '{les.title}': {e}",
                                }
                            )

                lesson_acts = (
                    activities_by_lesson[les.id]
                    if les.id in activities_by_lesson
                    else (getattr(les, "activities", []) or [])
                )

                for act in lesson_acts:
                    if not act.is_active:
                        continue
                    if not act.title or not act.title.strip():
                        errors.append(
                            {
                                "scope": "activity",
                                "id": act.id,
                                "title": act.title,
                                "message": f"Activity in lesson '{les.title}' is missing a title.",
                            }
                        )
                    if not act.instructions or not act.instructions.strip():
                        errors.append(
                            {
                                "scope": "activity",
                                "id": act.id,
                                "title": act.title,
                                "message": f"Activity '{act.title}' is missing instructions.",
                            }
                        )
                    if not act.grading_config:
                        errors.append(
                            {
                                "scope": "activity",
                                "id": act.id,
                                "title": act.title,
                                "message": f"Activity '{act.title}' is missing grading configuration.",
                            }
                        )
                    else:
                        if act.grading_config.passing_score is not None and not (
                            0 <= act.grading_config.passing_score <= 100
                        ):
                            errors.append(
                                {
                                    "scope": "activity",
                                    "id": act.id,
                                    "title": act.title,
                                    "message": f"Activity '{act.title}' has an invalid passing score (must be between 0 and 100).",
                                }
                            )
                    # Verify skill tag if present
                    act_cfg = act.configuration if isinstance(act.configuration, dict) else {}
                    act_skill_id = act_cfg.get("skill_id")
                    if act_skill_id and act_skill_id not in course_skill_ids:
                        errors.append(
                            {
                                "scope": "activity",
                                "id": act.id,
                                "title": act.title,
                                "message": f"Activity '{act.title}' references skill '{act_skill_id}' which is not associated with this course.",
                            }
                        )

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
        }

    def validate_draft(
        self, course_id: str, user_id: str, is_admin: bool = False
    ) -> dict[str, Any]:
        """Perform comprehensive validation of a course draft prior to publishing."""
        course = self.get_course_by_id(course_id)
        if not course:
            raise CourseServiceError("Course not found.", code="COURSE_NOT_FOUND", status_code=404)
        if not is_admin and course.creator_id != user_id:
            raise CourseServiceError("Forbidden.", code="FORBIDDEN", status_code=403)

        draft = self.get_or_create_draft(course_id)
        return self._validate_course_and_draft(course, draft)

    def get_draft_preview(
        self, course_id: str, user_id: str, is_admin: bool = False
    ) -> dict[str, Any]:
        """Fetch draft curriculum structured for the learner-facing workspace preview."""
        return self.get_draft_detail(course_id=course_id, user_id=user_id, is_admin=is_admin)

    def get_draft_preview_lesson(
        self, course_id: str, lesson_slug: str, user_id: str, is_admin: bool = False
    ) -> dict[str, Any]:
        """Fetch draft lesson structured for learner-facing preview."""
        draft_course = self.get_draft_detail(
            course_id=course_id, user_id=user_id, is_admin=is_admin
        )
        for mod in draft_course["modules"]:
            for les in mod["lessons"]:
                if les["slug"] == lesson_slug:
                    return les
        raise CourseServiceError(
            f"Lesson '{lesson_slug}' not found in draft.", code="LESSON_NOT_FOUND", status_code=404
        )
