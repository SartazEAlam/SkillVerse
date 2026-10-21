"""SQLAlchemy models for cross-disciplinary skills, disciplines, and prerequisites."""

from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database import Base, TimestampMixin, generate_uuid


class SkillDifficulty(enum.StrEnum):
    """Proficiency level / depth classification for a skill."""

    FOUNDATIONAL = "FOUNDATIONAL"
    INTERMEDIATE = "INTERMEDIATE"
    ADVANCED = "ADVANCED"


class Discipline(TimestampMixin, Base):
    """Broad domain organizing related skills and courses (e.g. Technology, Communication)."""

    __tablename__ = "disciplines"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    icon: Mapped[str | None] = mapped_column(String(100), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    skills: Mapped[list[Skill]] = relationship(
        "Skill",
        back_populates="discipline",
        cascade="all, delete-orphan",
        order_by="Skill.sort_order",
    )
    courses: Mapped[list[Course]] = relationship(  # noqa: F821
        "Course",
        back_populates="discipline",
    )

    def __repr__(self) -> str:
        return f"<Discipline slug={self.slug} name={self.name}>"


class Skill(TimestampMixin, Base):
    """Specific ability a learner can develop within a discipline."""

    __tablename__ = "skills"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    discipline_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("disciplines.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    parent_skill_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("skills.id", ondelete="SET NULL"), nullable=True, index=True
    )
    difficulty_level: Mapped[SkillDifficulty] = mapped_column(
        Enum(SkillDifficulty, name="skill_difficulty", create_constraint=True),
        default=SkillDifficulty.FOUNDATIONAL,
        nullable=False,
    )
    icon: Mapped[str | None] = mapped_column(String(100), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Hierarchy Relationships
    discipline: Mapped[Discipline] = relationship("Discipline", back_populates="skills")
    parent: Mapped[Skill | None] = relationship(
        "Skill", remote_side=[id], back_populates="children"
    )
    children: Mapped[list[Skill]] = relationship("Skill", back_populates="parent")

    # Prerequisite Relationships
    prerequisite_edges: Mapped[list[SkillPrerequisite]] = relationship(
        "SkillPrerequisite",
        foreign_keys="SkillPrerequisite.skill_id",
        back_populates="skill",
        cascade="all, delete-orphan",
    )
    dependent_edges: Mapped[list[SkillPrerequisite]] = relationship(
        "SkillPrerequisite",
        foreign_keys="SkillPrerequisite.prerequisite_skill_id",
        back_populates="prerequisite_skill",
        cascade="all, delete-orphan",
    )

    # Course association
    course_associations: Mapped[list[CourseSkill]] = relationship(  # noqa: F821
        "CourseSkill",
        back_populates="skill",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Skill slug={self.slug} name={self.name} difficulty={self.difficulty_level}>"


class SkillPrerequisite(Base):
    """Directed prerequisite relationship between two skills (skill requires prerequisite_skill)."""

    __tablename__ = "skill_prerequisites"

    skill_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True
    )
    prerequisite_skill_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        CheckConstraint(
            "skill_id != prerequisite_skill_id",
            name="ck_no_self_prerequisite",
        ),
    )

    # Relationships
    skill: Mapped[Skill] = relationship(
        "Skill", foreign_keys=[skill_id], back_populates="prerequisite_edges"
    )
    prerequisite_skill: Mapped[Skill] = relationship(
        "Skill", foreign_keys=[prerequisite_skill_id], back_populates="dependent_edges"
    )

    def __repr__(self) -> str:
        return f"<SkillPrerequisite skill_id={self.skill_id} requires={self.prerequisite_skill_id}>"
