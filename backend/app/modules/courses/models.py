"""SQLAlchemy models for courses, modules, lessons, content blocks, and versions."""

from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database import Base, TimestampMixin, generate_uuid
from app.modules.skills.models import Discipline, Skill


class CourseDifficulty(enum.StrEnum):
    """Target learner experience / difficulty level."""

    BEGINNER = "BEGINNER"
    INTERMEDIATE = "INTERMEDIATE"
    ADVANCED = "ADVANCED"


class CourseStatus(enum.StrEnum):
    """Lifecycle status of a course aggregate."""

    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class Course(TimestampMixin, Base):
    """Primary course record and aggregate root."""

    __tablename__ = "courses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    slug: Mapped[str] = mapped_column(String(200), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    short_description: Mapped[str] = mapped_column(Text, nullable=False)
    full_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    discipline_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("disciplines.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    difficulty_level: Mapped[CourseDifficulty] = mapped_column(
        Enum(CourseDifficulty, name="course_difficulty", create_constraint=True),
        default=CourseDifficulty.BEGINNER,
        nullable=False,
    )
    estimated_duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cover_image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[CourseStatus] = mapped_column(
        Enum(CourseStatus, name="course_status", create_constraint=True),
        default=CourseStatus.DRAFT,
        nullable=False,
        index=True,
    )
    creator_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    current_version_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey(
            "course_versions.id",
            ondelete="SET NULL",
            use_alter=True,
            name="fk_courses_current_version_id",
        ),
        nullable=True,
    )

    # Relationships
    discipline: Mapped[Discipline] = relationship("Discipline", back_populates="courses")
    creator: Mapped[User] = relationship("User", foreign_keys=[creator_id])  # noqa: F821
    current_version: Mapped[CourseVersion | None] = relationship(
        "CourseVersion",
        foreign_keys=[current_version_id],
        post_update=True,
    )
    versions: Mapped[list[CourseVersion]] = relationship(
        "CourseVersion",
        foreign_keys="CourseVersion.course_id",
        back_populates="course",
        cascade="all, delete-orphan",
        order_by="CourseVersion.version_number.desc()",
    )
    skill_associations: Mapped[list[CourseSkill]] = relationship(
        "CourseSkill",
        back_populates="course",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Course slug={self.slug} title={self.title} status={self.status}>"


class CourseSkill(Base):
    """Many-to-many relationship mapping courses to skills taught."""

    __tablename__ = "course_skills"

    course_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("courses.id", ondelete="CASCADE"), primary_key=True
    )
    skill_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True
    )
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), server_default=func.now(), nullable=False
    )

    # Relationships
    course: Mapped[Course] = relationship("Course", back_populates="skill_associations")
    skill: Mapped[Skill] = relationship("Skill", back_populates="course_associations")

    def __repr__(self) -> str:
        return f"<CourseSkill course_id={self.course_id} skill_id={self.skill_id}>"


class CourseVersion(TimestampMixin, Base):
    """Immutable version snapshot (or working draft) of course curriculum."""

    __tablename__ = "course_versions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    course_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    learning_objectives: Mapped[list[str]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), default=list, server_default="[]", nullable=False
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    publisher_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    changelog: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    __table_args__ = (
        UniqueConstraint("course_id", "version_number", name="uq_course_version_number"),
    )

    # Relationships
    course: Mapped[Course] = relationship(
        "Course", foreign_keys=[course_id], back_populates="versions"
    )
    publisher: Mapped[User | None] = relationship("User", foreign_keys=[publisher_id])  # noqa: F821
    modules: Mapped[list[Module]] = relationship(
        "Module",
        back_populates="course_version",
        cascade="all, delete-orphan",
        order_by="Module.sort_order",
    )

    @property
    def is_published(self) -> bool:
        """True if this version has been formally published."""
        return self.published_at is not None

    def __repr__(self) -> str:
        return f"<CourseVersion course_id={self.course_id} v={self.version_number} active={self.is_active}>"


class Module(TimestampMixin, Base):
    """Ordered module container within a course version."""

    __tablename__ = "modules"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    course_version_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("course_versions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)

    # Relationships
    course_version: Mapped[CourseVersion] = relationship("CourseVersion", back_populates="modules")
    lessons: Mapped[list[Lesson]] = relationship(
        "Lesson",
        back_populates="module",
        cascade="all, delete-orphan",
        order_by="Lesson.sort_order",
    )

    def __repr__(self) -> str:
        return f"<Module id={self.id} title={self.title} sort_order={self.sort_order}>"


class Lesson(TimestampMixin, Base):
    """Individual learning unit within a module."""

    __tablename__ = "lessons"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    module_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("modules.id", ondelete="CASCADE"), nullable=False, index=True
    )
    slug: Mapped[str] = mapped_column(String(200), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    learning_objectives: Mapped[list[str]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), default=list, server_default="[]", nullable=False
    )
    estimated_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)
    content_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    __table_args__ = (UniqueConstraint("module_id", "slug", name="uq_module_lesson_slug"),)

    # Relationships
    module: Mapped[Module] = relationship("Module", back_populates="lessons")
    blocks: Mapped[list[LessonBlock]] = relationship(
        "LessonBlock",
        back_populates="lesson",
        cascade="all, delete-orphan",
        order_by="LessonBlock.sort_order",
    )

    def __repr__(self) -> str:
        return f"<Lesson id={self.id} slug={self.slug} title={self.title}>"


class LessonBlock(TimestampMixin, Base):
    """Ordered content block (heading, text, code, callout, image, video) in a lesson."""

    __tablename__ = "lesson_blocks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    lesson_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False, index=True
    )
    block_type: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), default=dict, nullable=False
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)

    # Relationships
    lesson: Mapped[Lesson] = relationship("Lesson", back_populates="blocks")

    def __repr__(self) -> str:
        return f"<LessonBlock id={self.id} type={self.block_type} sort={self.sort_order}>"
