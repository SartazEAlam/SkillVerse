"""Business logic service for activities, attempts, and assessment workflows."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.modules.activities.grading import GradingError, grading_engine
from app.modules.activities.models import (
    Activity,
    ActivityType,
    Attempt,
    AttemptStatus,
    GradingConfig,
    GradingType,
)
from app.modules.activities.schemas import (
    ActivityAuthoringResponse,
    ActivityCreate,
    ActivityDetailResponse,
    ActivitySummaryResponse,
    ActivityUpdateRequest,
    AttemptListResponse,
    AttemptResponse,
)
from app.modules.courses.models import (
    Course,
    CourseSkill,
    CourseVersion,
    Lesson,
    LessonBlock,
    Module,
)
from app.modules.skills.models import Skill

logger = logging.getLogger("skillverse.activities")


class ActivityServiceError(Exception):
    """Business logic error raised by ActivityService."""

    def __init__(self, message: str, code: str = "ACTIVITY_ERROR", status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code


class ActivityService:
    """Manages activity definitions, learner submissions, and attempt history."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # ── Activity Retrieval ─────────────────────────────────────────────────

    def get_activity_by_id(self, activity_id: str) -> Activity | None:
        """Fetch raw activity entity with its grading config."""
        stmt = (
            select(Activity)
            .options(joinedload(Activity.grading_config))
            .where(Activity.id == activity_id, Activity.is_active.is_(True))
        )
        return self.db.scalars(stmt).first()

    def get_public_activity(self, activity_id: str) -> ActivityDetailResponse | None:
        """Retrieve public activity payload with confidential answer keys stripped."""
        activity = self.get_activity_by_id(activity_id)
        if not activity:
            return None

        passing_score = activity.grading_config.passing_score if activity.grading_config else 70.0
        cfg = activity.configuration if isinstance(activity.configuration, dict) else {}
        skill_id = cfg.get("skill_id")
        skill_slug = cfg.get("skill_slug") or cfg.get("skill")

        return ActivityDetailResponse(
            id=activity.id,
            lesson_id=activity.lesson_id,
            activity_type=ActivityType(activity.activity_type),
            title=activity.title,
            instructions=activity.instructions,
            configuration=activity.configuration,
            skill_id=skill_id,
            skill_slug=skill_slug,
            max_attempts=activity.max_attempts,
            sort_order=activity.sort_order,
            passing_score=passing_score,
            created_at=activity.created_at,
            updated_at=activity.updated_at,
        )

    def list_lesson_activities(
        self, lesson_id: str, user_id: str | None = None
    ) -> list[ActivitySummaryResponse]:
        """List active activities for a lesson, with optional user attempt summary."""
        lesson = self.db.get(Lesson, lesson_id)
        if not lesson:
            raise ActivityServiceError(
                f"Lesson '{lesson_id}' not found.",
                code="LESSON_NOT_FOUND",
                status_code=404,
            )

        stmt = (
            select(Activity)
            .options(joinedload(Activity.grading_config))
            .where(Activity.lesson_id == lesson_id, Activity.is_active.is_(True))
            .order_by(Activity.sort_order)
        )
        activities = self.db.scalars(stmt).all()

        results: list[ActivitySummaryResponse] = []
        for act in activities:
            best_score: float | None = None
            passed: bool | None = None
            attempts_count = 0

            if user_id:
                user_attempts = (
                    self.db.scalars(
                        select(Attempt).where(
                            Attempt.activity_id == act.id, Attempt.user_id == user_id
                        )
                    ).all()
                )
                attempts_count = len(user_attempts)
                graded_scores = [a.score for a in user_attempts if a.score is not None]
                if graded_scores:
                    best_score = max(graded_scores)
                if any(a.passed for a in user_attempts):
                    passed = True
                elif user_attempts and all(a.passed is False for a in user_attempts):
                    passed = False

            can_retry = act.max_attempts is None or attempts_count < act.max_attempts
            passing_score = act.grading_config.passing_score if act.grading_config else 70.0

            results.append(
                ActivitySummaryResponse(
                    id=act.id,
                    lesson_id=act.lesson_id,
                    activity_type=ActivityType(act.activity_type),
                    title=act.title,
                    instructions=act.instructions,
                    sort_order=act.sort_order,
                    max_attempts=act.max_attempts,
                    passing_score=passing_score,
                    best_score=best_score,
                    passed=passed,
                    attempts_count=attempts_count,
                    can_retry=can_retry,
                )
            )

        return results

    def _validate_and_resolve_skill_tag(
        self,
        course: Course,
        raw_skill_id: str | None,
        raw_skill_slug: str | None,
    ) -> tuple[str, str]:
        """Validate that skill tags resolve to an active skill associated with the course."""
        skill_by_id: Skill | None = None
        if raw_skill_id is not None:
            clean_id = str(raw_skill_id).strip()
            if clean_id:
                skill_by_id = self.db.scalars(
                    select(Skill).where(Skill.id == clean_id, Skill.is_active.is_(True))
                ).first()
                if not skill_by_id:
                    inactive = self.db.scalars(select(Skill).where(Skill.id == clean_id)).first()
                    if inactive and not inactive.is_active:
                        raise ActivityServiceError(
                            f"Skill with ID '{clean_id}' is inactive.",
                            code="INACTIVE_SKILL",
                            status_code=400,
                        )
                    raise ActivityServiceError(
                        f"Skill with ID '{clean_id}' not found.",
                        code="SKILL_NOT_FOUND",
                        status_code=404,
                    )

        skill_by_slug: Skill | None = None
        if raw_skill_slug is not None:
            clean_slug = str(raw_skill_slug).strip().lower()
            if clean_slug:
                skill_by_slug = self.db.scalars(
                    select(Skill).where(Skill.slug == clean_slug, Skill.is_active.is_(True))
                ).first()
                if not skill_by_slug:
                    inactive = self.db.scalars(
                        select(Skill).where(Skill.slug == clean_slug)
                    ).first()
                    if inactive and not inactive.is_active:
                        raise ActivityServiceError(
                            f"Skill with slug '{clean_slug}' is inactive.",
                            code="INACTIVE_SKILL",
                            status_code=400,
                        )
                    raise ActivityServiceError(
                        f"Skill with slug '{clean_slug}' not found.",
                        code="SKILL_NOT_FOUND",
                        status_code=404,
                    )

        if skill_by_id and skill_by_slug and skill_by_id.id != skill_by_slug.id:
            raise ActivityServiceError(
                f"Conflicting skill references: skill_id '{raw_skill_id}' ({skill_by_id.slug}) does not match skill_slug '{raw_skill_slug}'.",
                code="CONFLICTING_SKILL_TAGS",
                status_code=400,
            )

        target_skill = skill_by_id or skill_by_slug
        if not target_skill:
            raise ActivityServiceError("No valid skill tag specified.", code="SKILL_NOT_FOUND", status_code=404)

        # Verify target_skill is associated with the course
        is_course_skill = self.db.scalar(
            select(func.count(CourseSkill.skill_id)).where(
                CourseSkill.course_id == course.id,
                CourseSkill.skill_id == target_skill.id,
            )
        )
        if not is_course_skill or is_course_skill == 0:
            raise ActivityServiceError(
                f"Skill '{target_skill.name}' ({target_skill.slug}) is not associated with course '{course.title}'.",
                code="UNRELATED_SKILL",
                status_code=400,
            )

        return target_skill.id, target_skill.slug

    def _check_activity_access(
        self,
        activity: Activity,
        user_id: str,
        is_admin: bool = False,
        require_draft: bool = False,
    ) -> tuple[Course | None, CourseVersion | None]:
        """Verify creator ownership or admin rights, and optionally enforce draft mutability."""
        if not activity.lesson_id:
            return None, None

        stmt = (
            select(Course, CourseVersion)
            .join(CourseVersion, Course.id == CourseVersion.course_id)
            .join(Module, CourseVersion.id == Module.course_version_id)
            .join(Lesson, Module.id == Lesson.module_id)
            .where(Lesson.id == activity.lesson_id)
        )
        row = self.db.execute(stmt).first()
        if not row:
            raise ActivityServiceError(
                "Course curriculum for this activity could not be found.",
                code="COURSE_NOT_FOUND",
                status_code=404,
            )
        course, version = row[0], row[1]
        if course.creator_id != user_id and not is_admin:
            raise ActivityServiceError(
                "You are not authorized to view or edit activities in this course.",
                code="FORBIDDEN",
                status_code=403,
            )

        if require_draft and version.published_at is not None:
            raise ActivityServiceError(
                "Cannot modify an activity in a published course version. Edit within a working draft instead.",
                code="CANNOT_MODIFY_PUBLISHED_VERSION",
                status_code=400,
            )

        return course, version

    # ── Activity Authoring ─────────────────────────────────────────────────

    def create_activity(self, data: ActivityCreate) -> Activity:
        """Create an activity aggregate with its confidential grading config."""
        lesson: Lesson | None = None
        if data.lesson_id is not None:
            lesson = self.db.get(Lesson, data.lesson_id)
            if not lesson:
                raise ActivityServiceError(
                    f"Lesson '{data.lesson_id}' not found.",
                    code="LESSON_NOT_FOUND",
                    status_code=404,
                )

        config = dict(data.configuration)
        raw_skill_id = data.skill_id if data.skill_id is not None else config.get("skill_id")
        if isinstance(raw_skill_id, str):
            raw_skill_id = raw_skill_id.strip() or None

        raw_skill_slug = (
            data.skill_slug
            if data.skill_slug is not None
            else (config.get("skill_slug") or config.get("skill"))
        )
        if isinstance(raw_skill_slug, str):
            raw_skill_slug = raw_skill_slug.strip().lower() or None

        if raw_skill_id is not None or raw_skill_slug is not None:
            if not lesson:
                raise ActivityServiceError(
                    "Cannot assign a skill tag to an activity without a valid lesson.",
                    code="LESSON_REQUIRED_FOR_SKILL",
                    status_code=400,
                )

            # Find course containing this lesson
            stmt = (
                select(Course)
                .join(CourseVersion, Course.id == CourseVersion.course_id)
                .join(Module, CourseVersion.id == Module.course_version_id)
                .join(Lesson, Module.id == Lesson.module_id)
                .where(Lesson.id == lesson.id)
            )
            course = self.db.scalars(stmt).first()
            if not course:
                raise ActivityServiceError(
                    f"Lesson '{lesson.id}' is not linked to any active course.",
                    code="COURSE_NOT_FOUND",
                    status_code=400,
                )

            s_id, s_slug = self._validate_and_resolve_skill_tag(course, raw_skill_id, raw_skill_slug)
            config["skill_id"] = s_id
            config["skill_slug"] = s_slug

        activity = Activity(
            lesson_id=data.lesson_id,
            activity_type=data.activity_type.value,
            title=data.title,
            instructions=data.instructions,
            configuration=config,
            max_attempts=data.max_attempts,
            sort_order=data.sort_order,
        )
        self.db.add(activity)
        self.db.flush()

        grading_config = GradingConfig(
            activity_id=activity.id,
            grading_type=data.grading_type.value,
            passing_score=data.passing_score,
            answer_key=data.answer_key,
            rubric=data.rubric,
            test_cases=data.test_cases,
            feedback_config=data.feedback_config,
        )
        self.db.add(grading_config)
        self.db.commit()
        self.db.refresh(activity)
        return activity

    def get_authoring_activity(
        self, activity_id: str, user_id: str, is_admin: bool = False
    ) -> ActivityAuthoringResponse:
        """Fetch full activity definition including answer key for an authorized creator."""
        activity = self.get_activity_by_id(activity_id)
        if not activity:
            raise ActivityServiceError(
                f"Activity '{activity_id}' not found.",
                code="ACTIVITY_NOT_FOUND",
                status_code=404,
            )
        self._check_activity_access(activity, user_id, is_admin, require_draft=False)

        cfg = activity.configuration if isinstance(activity.configuration, dict) else {}
        g_cfg = activity.grading_config
        return ActivityAuthoringResponse(
            id=activity.id,
            lesson_id=activity.lesson_id,
            activity_type=ActivityType(activity.activity_type),
            title=activity.title,
            instructions=activity.instructions,
            configuration=cfg,
            skill_id=cfg.get("skill_id"),
            skill_slug=cfg.get("skill_slug") or cfg.get("skill"),
            max_attempts=activity.max_attempts,
            sort_order=activity.sort_order,
            grading_type=GradingType(g_cfg.grading_type) if g_cfg else GradingType.AUTOMATED,
            passing_score=g_cfg.passing_score if g_cfg else 70.0,
            answer_key=g_cfg.answer_key if g_cfg and g_cfg.answer_key else {},
            rubric=g_cfg.rubric if g_cfg else None,
            test_cases=g_cfg.test_cases if g_cfg else None,
            feedback_config=g_cfg.feedback_config if g_cfg else None,
            created_at=activity.created_at,
            updated_at=activity.updated_at,
        )

    def update_activity(
        self,
        activity_id: str,
        data: ActivityUpdateRequest,
        user_id: str,
        is_admin: bool = False,
    ) -> ActivityAuthoringResponse:
        """Update an activity definition and its grading configuration in a draft."""
        activity = self.get_activity_by_id(activity_id)
        if not activity:
            raise ActivityServiceError(
                f"Activity '{activity_id}' not found.",
                code="ACTIVITY_NOT_FOUND",
                status_code=404,
            )
        course, _ = self._check_activity_access(activity, user_id, is_admin, require_draft=True)

        if data.title is not None:
            activity.title = data.title.strip()
        if data.instructions is not None:
            activity.instructions = data.instructions
        if data.max_attempts is not None:
            activity.max_attempts = data.max_attempts
        if data.sort_order is not None:
            activity.sort_order = data.sort_order

        # Configuration and skill tags
        config = dict(activity.configuration) if isinstance(activity.configuration, dict) else {}
        if data.configuration is not None:
            config = dict(data.configuration)

        raw_skill_id = data.skill_id if data.skill_id is not None else config.get("skill_id")
        raw_skill_slug = (
            data.skill_slug
            if data.skill_slug is not None
            else (config.get("skill_slug") or config.get("skill"))
        )

        if course and (raw_skill_id or raw_skill_slug):
            s_id, s_slug = self._validate_and_resolve_skill_tag(course, raw_skill_id, raw_skill_slug)
            config["skill_id"] = s_id
            config["skill_slug"] = s_slug
        elif data.skill_id == "" or data.skill_slug == "":
            config.pop("skill_id", None)
            config.pop("skill_slug", None)

        activity.configuration = config

        # Grading config updates
        g_cfg = activity.grading_config
        if not g_cfg:
            g_cfg = GradingConfig(
                activity_id=activity.id,
                grading_type=data.grading_type.value if data.grading_type else GradingType.AUTOMATED.value,
                passing_score=data.passing_score if data.passing_score is not None else 70.0,
                answer_key=data.answer_key or {},
                rubric=data.rubric,
                test_cases=data.test_cases,
                feedback_config=data.feedback_config,
            )
            self.db.add(g_cfg)
        else:
            if data.grading_type is not None:
                g_cfg.grading_type = data.grading_type.value
            if data.passing_score is not None:
                g_cfg.passing_score = data.passing_score
            if data.answer_key is not None:
                g_cfg.answer_key = data.answer_key
            if data.rubric is not None:
                g_cfg.rubric = data.rubric
            if data.test_cases is not None:
                g_cfg.test_cases = data.test_cases
            if data.feedback_config is not None:
                g_cfg.feedback_config = data.feedback_config

        self.db.commit()
        self.db.refresh(activity)
        return self.get_authoring_activity(activity.id, user_id, is_admin)

    def delete_activity(self, activity_id: str, user_id: str, is_admin: bool = False) -> None:
        """Delete an activity and its grading configuration from a draft lesson."""
        activity = self.get_activity_by_id(activity_id)
        if not activity:
            raise ActivityServiceError(
                f"Activity '{activity_id}' not found.",
                code="ACTIVITY_NOT_FOUND",
                status_code=404,
            )
        self._check_activity_access(activity, user_id, is_admin, require_draft=True)

        # Remove referencing lesson blocks if any
        if activity.lesson_id:
            blocks = self.db.scalars(
                select(LessonBlock).where(
                    LessonBlock.lesson_id == activity.lesson_id,
                    LessonBlock.block_type == "activity",
                )
            ).all()
            for blk in blocks:
                if isinstance(blk.content, dict) and blk.content.get("activity_id") == activity.id:
                    self.db.delete(blk)

        if activity.grading_config:
            self.db.delete(activity.grading_config)
        self.db.delete(activity)
        self.db.commit()

    # ── Submission & Attempt Lifecycle ─────────────────────────────────────

    def submit_attempt(
        self, activity_id: str, user_id: str, submission: dict[str, Any]
    ) -> AttemptResponse:
        """Process, grade, and record a learner submission attempt."""
        activity = self.get_activity_by_id(activity_id)
        if not activity:
            raise ActivityServiceError(
                f"Activity '{activity_id}' not found.", code="ACTIVITY_NOT_FOUND", status_code=404
            )

        if not activity.grading_config:
            raise ActivityServiceError(
                "Activity grading configuration is missing.", code="GRADING_CONFIG_MISSING", status_code=500
            )

        # 1. Enforce retry limits
        existing_count = (
            self.db.scalar(
                select(func.count(Attempt.id)).where(
                    Attempt.activity_id == activity_id, Attempt.user_id == user_id
                )
            )
            or 0
        )

        if activity.max_attempts is not None and existing_count >= activity.max_attempts:
            raise ActivityServiceError(
                f"Maximum attempt limit ({activity.max_attempts}) reached for this activity.",
                code="RETRY_LIMIT_EXCEEDED",
                status_code=400,
            )

        attempt_number = existing_count + 1

        # 2. Server-side authoritative grading
        try:
            grading_result = grading_engine.grade(
                activity_type=activity.activity_type,
                configuration=activity.configuration,
                answer_key=activity.grading_config.answer_key,
                submission=submission,
                passing_score=activity.grading_config.passing_score,
                feedback_config=activity.grading_config.feedback_config,
            )
        except GradingError as err:
            raise ActivityServiceError(err.message, code=err.code, status_code=err.status_code) from err

        now = datetime.now(UTC)

        # 3. Persist attempt with concurrency protection
        attempt = Attempt(
            user_id=user_id,
            activity_id=activity.id,
            attempt_number=attempt_number,
            status=grading_result.status.value,
            submission=submission,
            result=grading_result.result,
            score=grading_result.score,
            max_score=grading_result.max_score,
            passed=grading_result.passed,
            feedback=grading_result.feedback,
            started_at=now,
            completed_at=now if grading_result.status != AttemptStatus.IN_PROGRESS else None,
        )
        self.db.add(attempt)
        try:
            self.db.commit()
            self.db.refresh(attempt)
        except IntegrityError as err:
            self.db.rollback()
            raise ActivityServiceError(
                "A concurrent submission for this attempt is already being processed. Please refresh and try again.",
                code="CONCURRENT_SUBMISSION",
                status_code=409,
            ) from err

        # Trigger progression, skill mastery, and achievement evaluations
        try:
            from app.modules.progress.service import ProgressionService

            ProgressionService(self.db).handle_activity_completed(attempt)
        except Exception:
            self.db.rollback()
            logger.warning("Progression cascade initial attempt failed for attempt '%s', retrying once...", attempt.id)
            try:
                ProgressionService(self.db).handle_activity_completed(attempt)
            except Exception:
                self.db.rollback()
                logger.exception("Failed to update progression cascade for attempt '%s'", attempt.id)

        # 4. Compute retry status
        total_now = existing_count + 1
        can_retry = activity.max_attempts is None or total_now < activity.max_attempts
        remaining = (
            max(0, activity.max_attempts - total_now)
            if activity.max_attempts is not None
            else None
        )

        return AttemptResponse(
            id=attempt.id,
            user_id=attempt.user_id,
            activity_id=attempt.activity_id,
            attempt_number=attempt.attempt_number,
            status=AttemptStatus(attempt.status),
            submission=attempt.submission,
            result=attempt.result,
            score=attempt.score,
            max_score=attempt.max_score,
            passed=attempt.passed,
            feedback=attempt.feedback,
            started_at=attempt.started_at,
            completed_at=attempt.completed_at,
            can_retry=can_retry,
            attempts_remaining=remaining,
        )

    def get_user_attempts(self, activity_id: str, user_id: str) -> AttemptListResponse:
        """Retrieve attempt history for an activity and authenticated user."""
        activity = self.get_activity_by_id(activity_id)
        if not activity:
            raise ActivityServiceError(
                f"Activity '{activity_id}' not found.", code="ACTIVITY_NOT_FOUND", status_code=404
            )

        attempts = (
            self.db.scalars(
                select(Attempt)
                .where(Attempt.activity_id == activity_id, Attempt.user_id == user_id)
                .order_by(Attempt.attempt_number.desc())
            ).all()
        )

        total = len(attempts)
        can_retry = activity.max_attempts is None or total < activity.max_attempts

        items: list[AttemptResponse] = []
        for att in attempts:
            rem = (
                max(0, activity.max_attempts - att.attempt_number)
                if activity.max_attempts is not None
                else None
            )
            items.append(
                AttemptResponse(
                    id=att.id,
                    user_id=att.user_id,
                    activity_id=att.activity_id,
                    attempt_number=att.attempt_number,
                    status=AttemptStatus(att.status),
                    submission=att.submission,
                    result=att.result,
                    score=att.score,
                    max_score=att.max_score,
                    passed=att.passed,
                    feedback=att.feedback,
                    started_at=att.started_at,
                    completed_at=att.completed_at,
                    can_retry=can_retry,
                    attempts_remaining=rem,
                )
            )

        return AttemptListResponse(
            activity_id=activity_id,
            total_attempts=total,
            max_attempts=activity.max_attempts,
            can_retry=can_retry,
            attempts=items,
        )

    def get_attempt_by_id(
        self, attempt_id: str, user_id: str, is_admin: bool = False
    ) -> AttemptResponse:
        """Retrieve specific attempt detail ensuring strict cross-user authorization."""
        attempt = self.db.get(Attempt, attempt_id)
        if not attempt:
            raise ActivityServiceError(
                f"Attempt '{attempt_id}' not found.", code="ATTEMPT_NOT_FOUND", status_code=404
            )

        if not is_admin and attempt.user_id != user_id:
            raise ActivityServiceError(
                "Forbidden: you do not have permission to view another learner's attempt.",
                code="FORBIDDEN",
                status_code=403,
            )

        activity = self.get_activity_by_id(attempt.activity_id)
        max_attempts = activity.max_attempts if activity else None
        can_retry = max_attempts is None or attempt.attempt_number < max_attempts
        remaining = (
            max(0, max_attempts - attempt.attempt_number)
            if max_attempts is not None
            else None
        )

        return AttemptResponse(
            id=attempt.id,
            user_id=attempt.user_id,
            activity_id=attempt.activity_id,
            attempt_number=attempt.attempt_number,
            status=AttemptStatus(attempt.status),
            submission=attempt.submission,
            result=attempt.result,
            score=attempt.score,
            max_score=attempt.max_score,
            passed=attempt.passed,
            feedback=attempt.feedback,
            started_at=attempt.started_at,
            completed_at=attempt.completed_at,
            can_retry=can_retry,
            attempts_remaining=remaining,
        )
