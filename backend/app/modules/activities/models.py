"""Database models for interactive learning activities, grading configs, and attempts."""

from __future__ import annotations

import enum
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

import app.modules.auth.models  # noqa: F401
from app.infrastructure.database import Base, TimestampMixin, generate_uuid

if TYPE_CHECKING:
    from app.modules.auth.models import User
    from app.modules.courses.models import Lesson


class ActivityType(enum.StrEnum):
    """Supported interactive activity types."""

    SINGLE_CHOICE = "single_choice"
    MULTIPLE_SELECT = "multiple_select"
    SHORT_ANSWER = "short_answer"
    TRUE_FALSE = "true_false"
    FILL_IN_THE_BLANK = "fill_in_the_blank"
    ORDERING = "ordering"
    MATCHING = "matching"
    CODE_EXERCISE = "code_exercise"
    SCENARIO = "scenario"


class GradingType(enum.StrEnum):
    """Supported grading methodologies."""

    AUTOMATED = "automated"
    AI_ASSISTED = "ai_assisted"
    RUBRIC = "rubric"
    COMPLETION = "completion"


class AttemptStatus(enum.StrEnum):
    """Lifecycle statuses for learner activity attempts."""

    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"
    GRADED = "graded"
    REVIEW_REQUIRED = "review_required"


class Activity(TimestampMixin, Base):
    """Interactive learning activity entity."""

    __tablename__ = "activities"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    lesson_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("lessons.id", ondelete="CASCADE"), nullable=True, index=True
    )
    activity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    instructions: Mapped[str] = mapped_column(Text, nullable=False)
    configuration: Mapped[dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), default=dict, server_default="{}", nullable=False
    )
    max_attempts: Mapped[int | None] = mapped_column(Integer, nullable=True)  # NULL = unlimited
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true", nullable=False
    )

    # Relationships
    lesson: Mapped[Lesson | None] = relationship(
        "Lesson", back_populates="activities", foreign_keys=[lesson_id]
    )
    grading_config: Mapped[GradingConfig | None] = relationship(
        "GradingConfig",
        back_populates="activity",
        uselist=False,
        cascade="all, delete-orphan",
    )
    attempts: Mapped[list[Attempt]] = relationship(
        "Attempt",
        back_populates="activity",
        cascade="all, delete-orphan",
        order_by="Attempt.attempt_number",
    )

    def __repr__(self) -> str:
        return f"<Activity id={self.id} type={self.activity_type} title={self.title}>"


class GradingConfig(TimestampMixin, Base):
    """Server-authoritative evaluation configuration and answer keys."""

    __tablename__ = "grading_configs"

    activity_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("activities.id", ondelete="CASCADE"), primary_key=True
    )
    grading_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default=GradingType.AUTOMATED
    )
    passing_score: Mapped[float] = mapped_column(
        Float, nullable=False, default=70.0, server_default="70.0"
    )
    # Server-only confidential answer key: never exposed in public activity responses
    answer_key: Mapped[dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), default=dict, server_default="{}", nullable=False
    )
    rubric: Mapped[dict[str, Any] | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=True
    )
    test_cases: Mapped[list[dict[str, Any]] | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=True
    )
    feedback_config: Mapped[dict[str, Any] | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=True
    )

    # Relationships
    activity: Mapped[Activity] = relationship("Activity", back_populates="grading_config")

    def __repr__(self) -> str:
        return (
            f"<GradingConfig activity_id={self.activity_id} type={self.grading_type} pass={self.passing_score}>"
        )


class Attempt(TimestampMixin, Base):
    """Individual learner submission attempt with persistent outcome."""

    __tablename__ = "attempts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    activity_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("activities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default=AttemptStatus.GRADED
    )
    submission: Mapped[dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), default=dict, server_default="{}", nullable=False
    )
    result: Mapped[dict[str, Any] | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=True
    )
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_score: Mapped[float] = mapped_column(
        Float, nullable=False, default=100.0, server_default="100.0"
    )
    passed: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    feedback: Mapped[dict[str, Any] | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=True
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        UniqueConstraint("user_id", "activity_id", "attempt_number", name="uq_user_activity_attempt"),
        Index("ix_attempts_user_activity", "user_id", "activity_id"),
    )

    # Relationships
    user: Mapped[User] = relationship("User")
    activity: Mapped[Activity] = relationship("Activity", back_populates="attempts")

    def __repr__(self) -> str:
        return f"<Attempt id={self.id} user={self.user_id} activity={self.activity_id} #{self.attempt_number} score={self.score}>"
