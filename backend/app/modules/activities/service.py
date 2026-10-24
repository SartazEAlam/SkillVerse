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
)
from app.modules.activities.schemas import (
    ActivityCreate,
    ActivityDetailResponse,
    ActivitySummaryResponse,
    AttemptListResponse,
    AttemptResponse,
)
from app.modules.courses.models import Lesson

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

        return ActivityDetailResponse(
            id=activity.id,
            lesson_id=activity.lesson_id,
            activity_type=ActivityType(activity.activity_type),
            title=activity.title,
            instructions=activity.instructions,
            configuration=activity.configuration,
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

    # ── Activity Authoring ─────────────────────────────────────────────────

    def create_activity(self, data: ActivityCreate) -> Activity:
        """Create an activity aggregate with its confidential grading config."""
        if data.lesson_id is not None:
            lesson = self.db.get(Lesson, data.lesson_id)
            if not lesson:
                raise ActivityServiceError(
                    f"Lesson '{data.lesson_id}' not found.",
                    code="LESSON_NOT_FOUND",
                    status_code=404,
                )

        activity = Activity(
            lesson_id=data.lesson_id,
            activity_type=data.activity_type.value,
            title=data.title,
            instructions=data.instructions,
            configuration=data.configuration,
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
