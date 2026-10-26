"""SQLAlchemy database models for enrollments, lesson progress, skill mastery, and achievements."""

from __future__ import annotations

import enum
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    JSON,
    DateTime,
    Float,
    ForeignKey,
    Index,
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
    from app.modules.courses.models import Course, CourseVersion, Lesson
    from app.modules.skills.models import Skill


class EnrollmentStatus(enum.StrEnum):
    """Lifecycle status for a learner's course enrollment."""

    ENROLLED = "ENROLLED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


class LessonProgressStatus(enum.StrEnum):
    """Progress status for an individual lesson within an enrollment."""

    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


class SkillMasteryStatus(enum.StrEnum):
    """Transparent proficiency tier reflecting evidence-backed capability."""

    NOT_STARTED = "NOT_STARTED"
    LEARNING = "LEARNING"
    PRACTICING = "PRACTICING"
    PROVISIONAL = "PROVISIONAL"
    MASTERED = "MASTERED"
    NEEDS_REVIEW = "NEEDS_REVIEW"


class Enrollment(TimestampMixin, Base):
    """Learner enrollment in a specific immutable course version."""

    __tablename__ = "enrollments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    course_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    course_version_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("course_versions.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default=EnrollmentStatus.ENROLLED.value
    )
    enrolled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), server_default=func.now(), nullable=False
    )
    last_accessed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("user_id", "course_id", name="uq_user_course_enrollment"),
        Index("ix_enrollments_user_status", "user_id", "status"),
    )

    # Relationships
    user: Mapped[User] = relationship("User")
    course: Mapped[Course] = relationship("Course")
    course_version: Mapped[CourseVersion] = relationship("CourseVersion")
    lesson_progresses: Mapped[list[LessonProgress]] = relationship(
        "LessonProgress",
        back_populates="enrollment",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Enrollment id={self.id} user={self.user_id} course={self.course_id} status={self.status}>"


class LessonProgress(TimestampMixin, Base):
    """Learner progress record for an individual lesson within an enrollment."""

    __tablename__ = "lesson_progress"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    enrollment_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("enrollments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    lesson_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default=LessonProgressStatus.NOT_STARTED.value
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_accessed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("enrollment_id", "lesson_id", name="uq_enrollment_lesson"),
        Index("ix_lesson_progress_user_lesson", "user_id", "lesson_id"),
    )

    # Relationships
    enrollment: Mapped[Enrollment] = relationship("Enrollment", back_populates="lesson_progresses")
    user: Mapped[User] = relationship("User")
    lesson: Mapped[Lesson] = relationship("Lesson")

    def __repr__(self) -> str:
        return f"<LessonProgress enrollment={self.enrollment_id} lesson={self.lesson_id} status={self.status}>"


class SkillMastery(TimestampMixin, Base):
    """Transparent proficiency and evidence tracking per learner and skill."""

    __tablename__ = "skill_mastery"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    skill_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("skills.id", ondelete="CASCADE"), nullable=False, index=True
    )
    mastery_level: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)  # 0.0 to 100.0
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default=SkillMasteryStatus.NOT_STARTED.value
    )
    evidence: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), default=list, server_default="[]", nullable=False
    )
    last_assessed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("user_id", "skill_id", name="uq_user_skill_mastery"),
        Index("ix_skill_mastery_user_status", "user_id", "status"),
    )

    # Relationships
    user: Mapped[User] = relationship("User")
    skill: Mapped[Skill] = relationship("Skill")

    def __repr__(self) -> str:
        return f"<SkillMastery user={self.user_id} skill={self.skill_id} status={self.status} level={self.mastery_level}>"


class Achievement(TimestampMixin, Base):
    """Specification of an earnable platform recognition or milestone."""

    __tablename__ = "achievements"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    icon: Mapped[str | None] = mapped_column(String(100), nullable=True)
    criteria: Mapped[dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), default=dict, server_default="{}", nullable=False
    )

    # Relationships
    user_achievements: Mapped[list[UserAchievement]] = relationship(
        "UserAchievement", back_populates="achievement", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Achievement slug={self.slug} name={self.name}>"


class UserAchievement(TimestampMixin, Base):
    """Awarded achievement record for a learner."""

    __tablename__ = "user_achievements"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    achievement_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("achievements.id", ondelete="CASCADE"), nullable=False, index=True
    )
    earned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("user_id", "achievement_id", name="uq_user_achievement"),
    )

    # Relationships
    user: Mapped[User] = relationship("User")
    achievement: Mapped[Achievement] = relationship("Achievement", back_populates="user_achievements")

    def __repr__(self) -> str:
        return f"<UserAchievement user={self.user_id} achievement={self.achievement_id}>"
