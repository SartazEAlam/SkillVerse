"""Pydantic schemas for disciplines, skills, and prerequisites."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.modules.skills.models import SkillDifficulty


class DisciplineBase(BaseModel):
    """Base fields for a discipline."""

    slug: str = Field(min_length=2, max_length=100)
    name: str = Field(min_length=2, max_length=200)
    description: str | None = None
    icon: str | None = None
    sort_order: int = 0
    is_active: bool = True


class DisciplineResponse(DisciplineBase):
    """Public representation of a discipline."""

    id: str
    created_at: datetime
    skills_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class SkillSummary(BaseModel):
    """Compact summary of a skill."""

    id: str
    slug: str
    name: str
    difficulty_level: SkillDifficulty
    icon: str | None = None
    sort_order: int = 0

    model_config = ConfigDict(from_attributes=True)


class DisciplineDetailResponse(DisciplineResponse):
    """Detailed discipline representation including contained skills."""

    skills: list[SkillSummary] = []


class SkillCreateRequest(BaseModel):
    """Payload to create a new skill."""

    slug: str = Field(min_length=2, max_length=100, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    name: str = Field(min_length=2, max_length=200)
    description: str | None = None
    discipline_id: str
    parent_skill_id: str | None = None
    difficulty_level: SkillDifficulty = SkillDifficulty.FOUNDATIONAL
    icon: str | None = None
    sort_order: int = 0
    is_active: bool = True


class SkillUpdateRequest(BaseModel):
    """Payload to update an existing skill."""

    name: str | None = None
    description: str | None = None
    difficulty_level: SkillDifficulty | None = None
    icon: str | None = None
    sort_order: int | None = None
    is_active: bool | None = None


class SkillResponse(BaseModel):
    """Public representation of a skill."""

    id: str
    slug: str
    name: str
    description: str | None = None
    discipline_id: str
    discipline_slug: str | None = None
    discipline_name: str | None = None
    parent_skill_id: str | None = None
    difficulty_level: SkillDifficulty
    icon: str | None = None
    sort_order: int = 0
    is_active: bool = True
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SkillDetailResponse(SkillResponse):
    """Detailed skill view with prerequisites and dependent unlocked skills."""

    prerequisites: list[SkillSummary] = []
    unlocked_skills: list[SkillSummary] = []
    courses_count: int = 0


class PrerequisiteAddRequest(BaseModel):
    """Request to establish a directed prerequisite dependency."""

    prerequisite_skill_id: str = Field(description="UUID of the skill that must be completed first")


class PrerequisiteEdge(BaseModel):
    """Edge representation in the skill graph."""

    source: str = Field(description="Prerequisite skill ID (must be completed first)")
    target: str = Field(description="Dependent skill ID (unlocked by source)")


class SkillMapNode(BaseModel):
    """Skill Map node with taxonomy presentation coordinates and metadata."""

    id: str
    slug: str
    name: str
    discipline_slug: str
    difficulty_level: SkillDifficulty
    description: str | None = None
    icon: str | None = None


class SkillTaxonomyMapResponse(BaseModel):
    """Complete graph structure of all active skills and prerequisite links."""

    nodes: list[SkillMapNode] = []
    edges: list[PrerequisiteEdge] = []
    disciplines: list[DisciplineResponse] = []
