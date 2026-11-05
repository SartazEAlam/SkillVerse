"""Pydantic schemas for projects, submissions, evaluations, and artifacts."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.modules.projects.models import PortfolioItemType, PortfolioItemVisibility


def _validate_slug(value: str | None) -> str | None:
    if value is None:
        return None
    slug = value.strip().lower()
    if not re.match(r"^[a-z0-9]+(?:-[a-z0-9]+)*$", slug):
        raise ValueError("Slug must consist of lowercase letters, numbers, and hyphens.")
    return slug


# ── Project Skill Schemas ───────────────────────────────────────────────────


class ProjectSkillInput(BaseModel):
    """Skill association payload for a project."""

    skill_id: str = Field(..., description="UUID of the skill")
    is_primary: bool = Field(default=False, description="Whether this is a primary focus skill")


class ProjectSkillResponse(BaseModel):
    """Skill representation associated with a project."""

    skill_id: str
    skill_slug: str
    skill_name: str
    difficulty_level: str
    is_primary: bool

    model_config = ConfigDict(from_attributes=True)


# ── Project Authoring and Discovery Schemas ─────────────────────────────────


class ProjectCreateRequest(BaseModel):
    """Payload to create a new practical project specification."""

    title: str = Field(..., min_length=3, max_length=300)
    slug: str | None = Field(default=None, max_length=200)
    short_description: str = Field(..., min_length=10, max_length=1000)
    full_description: str = Field(..., min_length=20)
    discipline_id: str = Field(..., min_length=1, max_length=36)
    difficulty_level: str = Field(
        default="BEGINNER",
        description="BEGINNER, INTERMEDIATE, ADVANCED, or EXPERT",
    )
    estimated_duration_hours: int | None = Field(default=None, ge=1, le=1000)
    course_version_id: str | None = Field(default=None, max_length=36)
    requirements: dict[str, Any] = Field(
        default_factory=dict,
        description="Structured milestones, deliverables, and guidelines",
    )
    evaluation_criteria: dict[str, Any] = Field(
        default_factory=dict,
        description="Rubric with criteria weights, max scores, and passing_score",
    )
    starter_resources: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Reference templates, boilerplates, and guidelines",
    )
    skills: list[ProjectSkillInput] = Field(
        ...,
        min_length=1,
        description="At least one demonstrated skill required",
    )

    @field_validator("slug")
    @classmethod
    def validate_slug_format(cls, v: str | None) -> str | None:
        return _validate_slug(v)

    @field_validator("difficulty_level")
    @classmethod
    def validate_difficulty(cls, v: str) -> str:
        upper = v.strip().upper()
        allowed = {"BEGINNER", "INTERMEDIATE", "ADVANCED", "EXPERT"}
        if upper not in allowed:
            raise ValueError(f"difficulty_level must be one of {sorted(allowed)}")
        return upper


class ProjectUpdateRequest(BaseModel):
    """Payload to update an existing project draft or published project."""

    title: str | None = Field(default=None, min_length=3, max_length=300)
    slug: str | None = Field(default=None, max_length=200)
    short_description: str | None = Field(default=None, min_length=10, max_length=1000)
    full_description: str | None = Field(default=None, min_length=20)
    discipline_id: str | None = Field(default=None, min_length=1, max_length=36)
    difficulty_level: str | None = None
    estimated_duration_hours: int | None = Field(default=None, ge=1, le=1000)
    course_version_id: str | None = None
    requirements: dict[str, Any] | None = None
    evaluation_criteria: dict[str, Any] | None = None
    starter_resources: list[dict[str, Any]] | None = None
    skills: list[ProjectSkillInput] | None = None

    @field_validator("slug")
    @classmethod
    def validate_slug_format(cls, v: str | None) -> str | None:
        return _validate_slug(v)

    @field_validator("difficulty_level")
    @classmethod
    def validate_difficulty(cls, v: str | None) -> str | None:
        if v is None:
            return None
        upper = v.strip().upper()
        allowed = {"BEGINNER", "INTERMEDIATE", "ADVANCED", "EXPERT"}
        if upper not in allowed:
            raise ValueError(f"difficulty_level must be one of {sorted(allowed)}")
        return upper


class ProjectSummaryResponse(BaseModel):
    """Summary item representation for project catalog discovery."""

    id: str
    slug: str
    title: str
    short_description: str
    discipline_id: str
    discipline_name: str | None = None
    discipline_slug: str | None = None
    difficulty_level: str
    estimated_duration_hours: int | None = None
    status: str
    creator_id: str
    created_at: datetime
    updated_at: datetime
    skills: list[ProjectSkillResponse] = []
    submissions_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class ProjectDetailResponse(ProjectSummaryResponse):
    """Full detailed project view including rubric, milestones, and starter resources."""

    full_description: str
    course_version_id: str | None = None
    requirements: dict[str, Any]
    evaluation_criteria: dict[str, Any]
    starter_resources: list[dict[str, Any]] = []
    creator_name: str | None = None
    my_submission: SubmissionSummaryResponse | None = None


class ProjectPaginatedResponse(BaseModel):
    """Paginated collection response for project discovery."""

    items: list[ProjectSummaryResponse]
    total: int
    page: int
    limit: int
    pages: int


# ── Artifact Schemas ────────────────────────────────────────────────────────


class ArtifactResponse(BaseModel):
    """Metadata response for an uploaded submission deliverable artifact."""

    id: str
    submission_id: str
    user_id: str
    storage_key: str
    original_filename: str
    mime_type: str
    file_size_bytes: int
    checksum_sha256: str
    is_public: bool
    created_at: datetime
    download_url: str

    model_config = ConfigDict(from_attributes=True)


class ArtifactListResponse(BaseModel):
    """Collection of deliverable artifacts for a submission."""

    submission_id: str
    total_count: int
    total_size_bytes: int
    artifacts: list[ArtifactResponse]


# ── Submission Schemas ──────────────────────────────────────────────────────


class SubmissionCreateRequest(BaseModel):
    """Initial payload to begin working on a project."""

    title: str | None = Field(default=None, max_length=300)
    summary: str | None = Field(default=None, max_length=5000)
    content: dict[str, Any] = Field(default_factory=dict)


class SubmissionUpdateRequest(BaseModel):
    """Draft update payload for an in-progress project submission."""

    title: str | None = Field(default=None, max_length=300)
    summary: str | None = Field(default=None, max_length=5000)
    content: dict[str, Any] | None = None
    milestones_completed: list[str] | None = None


class SubmissionRevisionRequest(BaseModel):
    """Payload to initiate a new revision after changes were requested."""

    title: str | None = Field(default=None, max_length=300)
    summary: str | None = Field(default=None, max_length=5000)
    content: dict[str, Any] | None = None


class SubmissionSummaryResponse(BaseModel):
    """Compact summary of a learner submission."""

    id: str
    project_id: str
    user_id: str
    version_number: int
    revision_of_id: str | None = None
    status: str
    title: str | None = None
    score: float | None = None
    passed: bool | None = None
    submitted_at: datetime | None = None
    evaluated_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SubmissionDetailResponse(SubmissionSummaryResponse):
    """Comprehensive submission view including deliverables, artifacts, and evaluation."""

    summary: str | None = None
    content: dict[str, Any]
    milestones_completed: list[str] = []
    evaluation: dict[str, Any] | None = None
    evaluator_id: str | None = None
    evaluator_name: str | None = None
    artifacts: list[ArtifactResponse] = []
    revisions_count: int = 0
    transition_history: list[dict[str, Any]] = Field(default_factory=list)


class SubmissionHistoryResponse(BaseModel):
    """Historical timeline of all submission revisions for a project and learner."""

    project_id: str
    user_id: str
    current_version: int
    submissions: list[SubmissionSummaryResponse]


# ── Review and Evaluation Schemas ───────────────────────────────────────────


class SubmissionReviewClaimResponse(BaseModel):
    """Response returned when an evaluator claims a submission for review."""

    submission_id: str
    status: str
    evaluator_id: str
    claimed_at: datetime


class CriteriaScoreInput(BaseModel):
    """Evaluator score and feedback on a specific rubric criterion."""

    criterion_id: str = Field(..., min_length=1)
    score: float = Field(..., ge=0)
    feedback: str | None = None


class SubmissionEvaluationRequest(BaseModel):
    """Evaluation decision and rubric scores submitted by an evaluator."""

    criteria_scores: list[CriteriaScoreInput] = Field(default_factory=list)
    feedback: str = Field(..., min_length=1, max_length=10000)
    action: str | None = Field(
        default=None,
        description="Optional explicit override: 'APPROVE' or 'REQUEST_CHANGES'",
    )


class EvaluationResponse(BaseModel):
    """Outcome of a completed submission evaluation."""

    submission_id: str
    status: str
    score: float
    passed: bool
    evaluation: dict[str, Any]
    evaluated_at: datetime
    evaluator_id: str
    transition_history: list[dict[str, Any]] = Field(default_factory=list)


# ── Portfolio & Portfolio Items Schemas ─────────────────────────────────────


class PortfolioUpdateRequest(BaseModel):
    """Payload to update portfolio profile, bio, custom slug, visibility, and display settings."""

    title: str | None = Field(default=None, max_length=200)
    headline: str | None = Field(default=None, max_length=300)
    bio_override: str | None = Field(default=None, max_length=5000)
    description: str | None = Field(default=None, max_length=5000, description="Alias for bio_override")
    custom_slug: str | None = Field(
        default=None,
        min_length=3,
        max_length=100,
        pattern=r"^[a-zA-Z0-9_-]+$",
        description="Unique custom URL slug (alphanumeric, dashes, underscores)",
    )
    visibility: PortfolioItemVisibility | None = None
    is_public: bool | None = None
    contact_links: dict[str, Any] | None = None
    settings: dict[str, Any] | None = None

    @field_validator("visibility", mode="before")
    @classmethod
    def normalize_visibility(cls, v: Any) -> Any:
        if isinstance(v, str):
            v_upper = v.strip().upper()
            if v_upper in PortfolioItemVisibility.__members__:
                return PortfolioItemVisibility[v_upper]
        return v


class PortfolioItemCreateRequest(BaseModel):
    """Payload to add a new showcase item to the learner's portfolio."""

    item_type: PortfolioItemType = PortfolioItemType.PROJECT_SUBMISSION
    reference_id: str | None = Field(
        default=None,
        description="ID of referenced entity (e.g. completed project submission ID)",
    )
    title: str | None = Field(default=None, max_length=300)
    summary: str | None = Field(default=None, max_length=5000)
    description: str | None = Field(default=None, max_length=5000, description="Alias for summary")
    visibility: PortfolioItemVisibility = PortfolioItemVisibility.PUBLIC
    external_url: str | None = Field(default=None, max_length=500)
    skills_demonstrated: list[str] = Field(default_factory=list)
    artifacts: list[dict[str, Any]] = Field(default_factory=list)

    @field_validator("item_type", mode="before")
    @classmethod
    def normalize_item_type(cls, v: Any) -> Any:
        if isinstance(v, str):
            v_upper = v.strip().upper()
            if v_upper in PortfolioItemType.__members__:
                return PortfolioItemType[v_upper]
        return v

    @field_validator("visibility", mode="before")
    @classmethod
    def normalize_visibility(cls, v: Any) -> Any:
        if isinstance(v, str):
            v_upper = v.strip().upper()
            if v_upper in PortfolioItemVisibility.__members__:
                return PortfolioItemVisibility[v_upper]
        return v


class PortfolioItemUpdateRequest(BaseModel):
    """Payload to update an existing portfolio item."""

    title: str | None = Field(default=None, max_length=300)
    summary: str | None = Field(default=None, max_length=5000)
    description: str | None = Field(default=None, max_length=5000, description="Alias for summary")
    visibility: PortfolioItemVisibility | None = None
    external_url: str | None = Field(default=None, max_length=500)
    sort_order: int | None = Field(default=None, ge=0)

    @field_validator("visibility", mode="before")
    @classmethod
    def normalize_visibility(cls, v: Any) -> Any:
        if isinstance(v, str):
            v_upper = v.strip().upper()
            if v_upper in PortfolioItemVisibility.__members__:
                return PortfolioItemVisibility[v_upper]
        return v


class PortfolioItemReorderRequest(BaseModel):
    """Payload to reorder portfolio items by sequential IDs."""

    item_ids: list[str] = Field(..., min_length=1)


class PortfolioItemResponse(BaseModel):
    """Representation of an individual portfolio showcase item."""

    id: str
    portfolio_user_id: str
    item_type: str
    reference_id: str | None = None
    title: str
    summary: str | None = None
    skills_demonstrated: list[str] = Field(default_factory=list)
    artifacts: list[dict[str, Any]] = Field(default_factory=list)
    external_url: str | None = None
    sort_order: int
    visibility: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PortfolioDetailResponse(BaseModel):
    """Comprehensive portfolio profile returned to the authenticated owner."""

    user_id: str
    title: str | None = None
    headline: str | None = None
    bio_override: str | None = None
    custom_slug: str | None = None
    visibility: str
    is_public: bool
    contact_links: dict[str, Any] = Field(default_factory=dict)
    settings: dict[str, Any] = Field(default_factory=dict)
    items: list[PortfolioItemResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PortfolioPublicResponse(BaseModel):
    """Sanitized public portfolio representation for anonymous exploration."""

    user_id: str
    display_name: str
    avatar_url: str | None = None
    title: str | None = None
    headline: str | None = None
    bio_override: str | None = None
    custom_slug: str | None = None
    visibility: str
    contact_links: dict[str, Any] = Field(default_factory=dict)
    settings: dict[str, Any] = Field(default_factory=dict)
    items: list[PortfolioItemResponse] = Field(default_factory=list)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


