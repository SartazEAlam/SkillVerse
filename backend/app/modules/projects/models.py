"""SQLAlchemy database models for projects, submissions, artifacts, and portfolios."""

from __future__ import annotations

import enum
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database import Base, TimestampMixin, generate_uuid

if TYPE_CHECKING:
    from app.modules.auth.models import User
    from app.modules.courses.models import CourseVersion
    from app.modules.skills.models import Discipline, Skill


class ProjectStatus(enum.StrEnum):
    """Lifecycle status for project specifications."""

    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class SubmissionStatus(enum.StrEnum):
    """Lifecycle status for learner project submissions."""

    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    CHANGES_REQUESTED = "CHANGES_REQUESTED"
    EVALUATED = "EVALUATED"
    COMPLETED = "COMPLETED"


class PortfolioItemType(enum.StrEnum):
    """Classification of showcase entries within a learner's portfolio."""

    PROJECT_SUBMISSION = "PROJECT_SUBMISSION"
    SKILL_MASTERY = "SKILL_MASTERY"
    ACHIEVEMENT = "ACHIEVEMENT"
    CUSTOM = "CUSTOM"


class PortfolioItemVisibility(enum.StrEnum):
    """Privacy and exposure level for individual portfolio showcase items."""

    PRIVATE = "PRIVATE"
    UNLISTED = "UNLISTED"
    PUBLIC = "PUBLIC"


class Project(TimestampMixin, Base):
    """Structured practical project or capstone definition."""

    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    slug: Mapped[str] = mapped_column(String(200), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    short_description: Mapped[str] = mapped_column(Text, nullable=False)
    full_description: Mapped[str] = mapped_column(Text, nullable=False)

    course_version_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("course_versions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    discipline_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("disciplines.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    difficulty_level: Mapped[str] = mapped_column(String(50), default="BEGINNER", nullable=False)
    estimated_duration_hours: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Structured requirements (milestones, deliverables, checklist)
    requirements: Mapped[dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        default=dict,
        server_default="{}",
        nullable=False,
    )

    # Evaluation rubric (criteria, score weights, passing thresholds)
    evaluation_criteria: Mapped[dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        default=dict,
        server_default="{}",
        nullable=False,
    )

    # Starter materials (templates, repos, boilerplates, documentation)
    starter_resources: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        default=list,
        server_default="[]",
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        default=ProjectStatus.DRAFT.value,
        server_default="DRAFT",
        nullable=False,
        index=True,
    )
    creator_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # Relationships
    discipline: Mapped[Discipline] = relationship("Discipline")
    course_version: Mapped[CourseVersion | None] = relationship("CourseVersion")
    creator: Mapped[User] = relationship("User")
    project_skills: Mapped[list[ProjectSkill]] = relationship(
        "ProjectSkill",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    submissions: Mapped[list[ProjectSubmission]] = relationship(
        "ProjectSubmission",
        back_populates="project",
        cascade="all, delete-orphan",
    )


class ProjectSkill(Base):
    """Many-to-many relationship connecting projects to demonstrated skills."""

    __tablename__ = "project_skills"

    project_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("projects.id", ondelete="CASCADE"),
        primary_key=True,
    )
    skill_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("skills.id", ondelete="CASCADE"),
        primary_key=True,
    )
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    project: Mapped[Project] = relationship("Project", back_populates="project_skills")
    skill: Mapped[Skill] = relationship("Skill")


class ProjectSubmission(TimestampMixin, Base):
    """Learner project submission with revision tracking, milestones, and evaluation."""

    __tablename__ = "project_submissions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    project_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("projects.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    version_number: Mapped[int] = mapped_column(Integer, default=1, server_default="1", nullable=False)
    revision_of_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("project_submissions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        default=SubmissionStatus.DRAFT.value,
        server_default="DRAFT",
        nullable=False,
        index=True,
    )

    title: Mapped[str | None] = mapped_column(String(300), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Learner deliverables: repository URL, live preview link, answers, text responses
    content: Mapped[dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        default=dict,
        server_default="{}",
        nullable=False,
    )

    # Completed milestone IDs
    milestones_completed: Mapped[list[str]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        default=list,
        server_default="[]",
        nullable=False,
    )

    # Structured evaluation outcome and rubric scores
    evaluation: Mapped[dict[str, Any] | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=True,
    )
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    passed: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    evaluated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    evaluator_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "project_id",
            "version_number",
            name="uq_user_project_submission_version",
        ),
        Index("ix_project_submissions_project_status", "project_id", "status"),
    )

    # Relationships
    project: Mapped[Project] = relationship("Project", back_populates="submissions")
    user: Mapped[User] = relationship("User", foreign_keys=[user_id])
    evaluator: Mapped[User | None] = relationship("User", foreign_keys=[evaluator_id])
    revision_of: Mapped[ProjectSubmission | None] = relationship(
        "ProjectSubmission",
        remote_side=[id],
        back_populates="revisions",
    )
    revisions: Mapped[list[ProjectSubmission]] = relationship(
        "ProjectSubmission",
        back_populates="revision_of",
    )
    artifacts: Mapped[list[ProjectArtifact]] = relationship(
        "ProjectArtifact",
        back_populates="submission",
        cascade="all, delete-orphan",
    )


class ProjectArtifact(TimestampMixin, Base):
    """Uploaded deliverable artifact with storage key reference and validation checksum."""

    __tablename__ = "project_artifacts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    submission_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("project_submissions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    storage_key: Mapped[str] = mapped_column(String(500), unique=True, nullable=False, index=True)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    checksum_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    submission: Mapped[ProjectSubmission] = relationship("ProjectSubmission", back_populates="artifacts")
    user: Mapped[User] = relationship("User")


class Portfolio(TimestampMixin, Base):
    """Learner-owned public or private showcase profile."""

    __tablename__ = "portfolios"

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    custom_slug: Mapped[str | None] = mapped_column(
        String(100), unique=True, nullable=True, index=True
    )

    title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    headline: Mapped[str | None] = mapped_column(String(300), nullable=True)
    bio_override: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Public contact and social links (GitHub, LinkedIn, personal site)
    contact_links: Mapped[dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        default=dict,
        server_default="{}",
        nullable=False,
    )

    # Display settings (show_skills, show_achievements, layout_mode)
    settings: Mapped[dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        default=dict,
        server_default="{}",
        nullable=False,
    )

    # Relationships
    user: Mapped[User] = relationship("User")
    items: Mapped[list[PortfolioItem]] = relationship(
        "PortfolioItem",
        back_populates="portfolio",
        cascade="all, delete-orphan",
        order_by="PortfolioItem.sort_order",
    )

    @property
    def visibility(self) -> str:
        """Derive visibility string ('PRIVATE', 'UNLISTED', 'PUBLIC') from settings and is_public."""
        if self.settings and "visibility" in self.settings:
            return str(self.settings["visibility"])
        return PortfolioItemVisibility.PUBLIC.value if self.is_public else PortfolioItemVisibility.PRIVATE.value



class PortfolioItem(TimestampMixin, Base):
    """Curated showcase item featured on a learner's portfolio."""

    __tablename__ = "portfolio_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    portfolio_user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("portfolios.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    item_type: Mapped[str] = mapped_column(
        String(50),
        default=PortfolioItemType.PROJECT_SUBMISSION.value,
        nullable=False,
    )
    reference_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)

    title: Mapped[str] = mapped_column(String(300), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    skills_demonstrated: Mapped[list[str]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        default=list,
        server_default="[]",
        nullable=False,
    )
    artifacts: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        default=list,
        server_default="[]",
        nullable=False,
    )
    external_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    sort_order: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    visibility: Mapped[str] = mapped_column(
        String(50),
        default=PortfolioItemVisibility.PUBLIC.value,
        server_default="PUBLIC",
        nullable=False,
    )

    __table_args__ = (
        Index("ix_portfolio_items_user_order", "portfolio_user_id", "sort_order"),
    )

    # Relationships
    portfolio: Mapped[Portfolio] = relationship("Portfolio", back_populates="items")

