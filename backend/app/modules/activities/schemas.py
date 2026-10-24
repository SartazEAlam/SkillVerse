"""Pydantic schemas for activities, submissions, grading configs, and attempts."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.modules.activities.models import ActivityType, AttemptStatus, GradingType

# ── Activity Configuration Schemas (Strict Types & Validation) ─────────────


class OptionItem(BaseModel):
    """An option item for choice questions."""

    id: str = Field(min_length=1, max_length=100)
    text: str = Field(min_length=1, max_length=1000)


class MatchingItem(BaseModel):
    """Item for matching activities."""

    id: str = Field(min_length=1, max_length=100)
    text: str = Field(min_length=1, max_length=500)


class BlankItem(BaseModel):
    """Blank definition for fill-in-the-blank activities."""

    id: str = Field(min_length=1, max_length=100)
    hint: str | None = Field(default=None, max_length=300)


class ScenarioDecision(BaseModel):
    """Decision option in a scenario-based activity."""

    id: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=300)
    description: str = Field(min_length=1, max_length=2000)


class CodingTestCasePublic(BaseModel):
    """Publicly visible test case definition (no secret tests leaked)."""

    id: str
    description: str
    is_public: bool = True


# ── Authoring / Internal Activity Creation Schema ───────────────────────────


class ActivityCreate(BaseModel):
    """Payload to create an activity along with its confidential grading config."""

    lesson_id: str | None = None
    activity_type: ActivityType
    title: str = Field(min_length=1, max_length=300)
    instructions: str = Field(min_length=1)
    configuration: dict[str, Any] = Field(default_factory=dict)
    max_attempts: int | None = Field(default=None, ge=1)
    sort_order: int = Field(default=0, ge=0)
    grading_type: GradingType = GradingType.AUTOMATED
    passing_score: float = Field(default=70.0, ge=0.0, le=100.0)
    answer_key: dict[str, Any] = Field(default_factory=dict)
    rubric: dict[str, Any] | None = None
    test_cases: list[dict[str, Any]] | None = None
    feedback_config: dict[str, Any] | None = None


# ── Public / Learner-Facing Activity Schemas ─────────────────────────────────


class ActivityDetailResponse(BaseModel):
    """Public activity payload.

    SECURITY INVARIANT: The answer_key, secret rubric solutions, and private
    feedback templates are NEVER included in this model.
    """

    id: str
    lesson_id: str | None
    activity_type: ActivityType
    title: str
    instructions: str
    configuration: dict[str, Any]
    max_attempts: int | None
    sort_order: int
    passing_score: float = 70.0
    created_at: datetime
    updated_at: datetime


class ActivitySummaryResponse(BaseModel):
    """Activity summary with the learner's best attempt status if authenticated."""

    id: str
    lesson_id: str | None
    activity_type: ActivityType
    title: str
    instructions: str
    sort_order: int
    max_attempts: int | None
    passing_score: float = 70.0
    best_score: float | None = None
    passed: bool | None = None
    attempts_count: int = 0
    can_retry: bool = True


# ── Submission & Attempt Schemas ───────────────────────────────────────────


class AttemptSubmissionRequest(BaseModel):
    """Untrusted learner submission payload."""

    submission: dict[str, Any] = Field(
        ...,
        description="The submitted answers (e.g. selected_option_id, ordered_item_ids, pairs, code)",
    )


class AttemptResponse(BaseModel):
    """Attempt detail with server-authoritative score and feedback."""

    id: str
    user_id: str
    activity_id: str
    attempt_number: int
    status: AttemptStatus
    submission: dict[str, Any]
    result: dict[str, Any] | None = None
    score: float | None = None
    max_score: float = 100.0
    passed: bool | None = None
    feedback: dict[str, Any] | None = None
    started_at: datetime
    completed_at: datetime | None = None
    can_retry: bool = True
    attempts_remaining: int | None = None


class AttemptListResponse(BaseModel):
    """Paginated or complete list of learner attempts for an activity."""

    activity_id: str
    total_attempts: int
    max_attempts: int | None
    can_retry: bool
    attempts: list[AttemptResponse]
