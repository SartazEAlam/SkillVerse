"""Pydantic schemas for courses, catalog discovery, draft authoring, and version publishing."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.modules.courses.content_schemas import LessonContentDocument
from app.modules.courses.models import CourseDifficulty, CourseStatus
from app.modules.skills.schemas import SkillSummary


class CourseSummary(BaseModel):
    """Compact course representation for catalog listing."""

    id: str
    slug: str
    title: str
    short_description: str
    discipline_id: str
    discipline_slug: str | None = None
    discipline_name: str | None = None
    difficulty_level: CourseDifficulty
    estimated_duration_minutes: int | None = None
    cover_image_url: str | None = None
    status: CourseStatus
    version_number: int | None = None
    skills: list[SkillSummary] = []

    model_config = ConfigDict(from_attributes=True)


class CoursePaginatedResponse(BaseModel):
    """Paginated catalog list response."""

    items: list[CourseSummary]
    total: int
    page: int
    limit: int
    pages: int


class LessonBlockResponse(BaseModel):
    """Structured content block representation."""

    id: str
    block_type: str
    content: dict[str, Any]
    sort_order: int

    model_config = ConfigDict(from_attributes=True)


class LessonDetailResponse(BaseModel):
    """Detailed lesson view including structured content blocks."""

    id: str
    slug: str
    title: str
    description: str | None = None
    learning_objectives: list[str] = []
    estimated_minutes: int | None = None
    sort_order: int
    content_version: int = 1
    blocks: list[LessonBlockResponse] = []

    model_config = ConfigDict(from_attributes=True)


class ModuleDetailResponse(BaseModel):
    """Module container with contained lessons."""

    id: str
    title: str
    description: str | None = None
    sort_order: int
    lessons: list[LessonDetailResponse] = []

    model_config = ConfigDict(from_attributes=True)


class CourseDetailResponse(BaseModel):
    """Complete published or draft course detail with modules, lessons, and content."""

    id: str
    slug: str
    title: str
    short_description: str
    full_description: str | None = None
    discipline_id: str
    discipline_slug: str | None = None
    discipline_name: str | None = None
    difficulty_level: CourseDifficulty
    estimated_duration_minutes: int | None = None
    cover_image_url: str | None = None
    status: CourseStatus
    creator_id: str
    version_id: str | None = None
    version_number: int | None = None
    published_at: datetime | None = None
    learning_objectives: list[str] = []
    skills: list[SkillSummary] = []
    modules: list[ModuleDetailResponse] = []

    model_config = ConfigDict(from_attributes=True)


# ── Authoring & Draft Request Schemas ──────────────────────────────────────


class CourseCreateRequest(BaseModel):
    """Payload to create a new course and initial working draft."""

    slug: str = Field(min_length=3, max_length=150, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    title: str = Field(min_length=3, max_length=300)
    short_description: str = Field(min_length=10, max_length=1000)
    full_description: str | None = None
    discipline_id: str
    difficulty_level: CourseDifficulty = CourseDifficulty.BEGINNER
    estimated_duration_minutes: int | None = Field(None, ge=1, le=10000)
    cover_image_url: str | None = None
    learning_objectives: list[str] = Field(default_factory=list)
    skill_ids: list[str] = Field(default_factory=list)


class CourseUpdateRequest(BaseModel):
    """Payload to update course aggregate metadata."""

    title: str | None = Field(None, min_length=3, max_length=300)
    short_description: str | None = Field(None, min_length=10, max_length=1000)
    full_description: str | None = None
    difficulty_level: CourseDifficulty | None = None
    estimated_duration_minutes: int | None = Field(None, ge=1, le=10000)
    cover_image_url: str | None = None
    learning_objectives: list[str] | None = None
    skill_ids: list[str] | None = None


class ModuleCreateRequest(BaseModel):
    """Payload to add a module to a working draft."""

    title: str = Field(min_length=2, max_length=300)
    description: str | None = None
    sort_order: int = 0


class ModuleUpdateRequest(BaseModel):
    """Payload to update an existing draft module."""

    title: str | None = Field(None, min_length=2, max_length=300)
    description: str | None = None
    sort_order: int | None = None


class LessonCreateRequest(BaseModel):
    """Payload to add a lesson to a draft module."""

    slug: str = Field(min_length=2, max_length=150, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    title: str = Field(min_length=2, max_length=300)
    description: str | None = None
    learning_objectives: list[str] = Field(default_factory=list)
    estimated_minutes: int | None = Field(None, ge=1, le=300)
    sort_order: int = 0


class LessonUpdateRequest(BaseModel):
    """Payload to update an existing draft lesson outline."""

    title: str | None = Field(None, min_length=2, max_length=300)
    description: str | None = None
    learning_objectives: list[str] | None = None
    estimated_minutes: int | None = Field(None, ge=1, le=300)
    sort_order: int | None = None


class LessonContentUpdateRequest(BaseModel):
    """Payload containing a validated lesson content document with structured blocks."""

    document: LessonContentDocument


class CoursePublishRequest(BaseModel):
    """Payload to publish a working draft."""

    changelog: str | None = Field(None, max_length=2000)


class CoursePublishResponse(BaseModel):
    """Confirmation of successful course version publication."""

    course_id: str
    version_id: str
    version_number: int
    published_at: datetime
    publisher_id: str
    changelog: str | None = None
