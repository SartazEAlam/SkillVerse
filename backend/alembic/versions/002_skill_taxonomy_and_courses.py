"""Phase 3 — skills, disciplines, prerequisites, courses, modules, lessons, blocks, versions

Revision ID: 002_skill_taxonomy_and_courses
Revises: 001_initial_identity
Create Date: 2026-10-21
"""

import contextlib
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "002_skill_taxonomy_and_courses"
down_revision: str | None = "001_initial_identity"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Enums are created automatically during op.create_table
    skill_difficulty_enum = sa.Enum("FOUNDATIONAL", "INTERMEDIATE", "ADVANCED", name="skill_difficulty")
    course_difficulty_enum = sa.Enum(
        "BEGINNER", "INTERMEDIATE", "ADVANCED", name="course_difficulty"
    )
    course_status_enum = sa.Enum("DRAFT", "PUBLISHED", "ARCHIVED", name="course_status")

    # ── disciplines table ────────────────────────────
    op.create_table(
        "disciplines",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("slug", sa.String(100), unique=True, nullable=False, index=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("icon", sa.String(100), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    # ── skills table ─────────────────────────────────
    op.create_table(
        "skills",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("slug", sa.String(100), unique=True, nullable=False, index=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "discipline_id",
            sa.String(36),
            sa.ForeignKey("disciplines.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "parent_skill_id",
            sa.String(36),
            sa.ForeignKey("skills.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column("difficulty_level", skill_difficulty_enum, nullable=False, server_default="FOUNDATIONAL"),
        sa.Column("icon", sa.String(100), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    # ── skill_prerequisites table ────────────────────
    op.create_table(
        "skill_prerequisites",
        sa.Column(
            "skill_id",
            sa.String(36),
            sa.ForeignKey("skills.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "prerequisite_skill_id",
            sa.String(36),
            sa.ForeignKey("skills.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint("skill_id != prerequisite_skill_id", name="ck_no_self_prerequisite"),
    )

    # ── courses table ────────────────────────────────
    op.create_table(
        "courses",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("slug", sa.String(200), unique=True, nullable=False, index=True),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("short_description", sa.Text(), nullable=False),
        sa.Column("full_description", sa.Text(), nullable=True),
        sa.Column(
            "discipline_id",
            sa.String(36),
            sa.ForeignKey("disciplines.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column("difficulty_level", course_difficulty_enum, nullable=False, server_default="BEGINNER"),
        sa.Column("estimated_duration_minutes", sa.Integer(), nullable=True),
        sa.Column("cover_image_url", sa.Text(), nullable=True),
        sa.Column("status", course_status_enum, nullable=False, server_default="DRAFT", index=True),
        sa.Column(
            "creator_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column("current_version_id", sa.String(36), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    # ── course_skills table ──────────────────────────
    op.create_table(
        "course_skills",
        sa.Column(
            "course_id",
            sa.String(36),
            sa.ForeignKey("courses.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "skill_id",
            sa.String(36),
            sa.ForeignKey("skills.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    # ── course_versions table ────────────────────────
    op.create_table(
        "course_versions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "course_id",
            sa.String(36),
            sa.ForeignKey("courses.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "learning_objectives",
            sa.JSON().with_variant(JSONB(), "postgresql"),
            nullable=False,
            server_default="[]",
        ),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "publisher_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("changelog", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("course_id", "version_number", name="uq_course_version_number"),
    )

    # Add foreign key from courses.current_version_id -> course_versions.id
    op.create_foreign_key(
        "fk_courses_current_version_id",
        "courses",
        "course_versions",
        ["current_version_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # ── modules table ────────────────────────────────
    op.create_table(
        "modules",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "course_version_id",
            sa.String(36),
            sa.ForeignKey("course_versions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    # ── lessons table ────────────────────────────────
    op.create_table(
        "lessons",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "module_id",
            sa.String(36),
            sa.ForeignKey("modules.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("slug", sa.String(200), nullable=False),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "learning_objectives",
            sa.JSON().with_variant(JSONB(), "postgresql"),
            nullable=False,
            server_default="[]",
        ),
        sa.Column("estimated_minutes", sa.Integer(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("content_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("module_id", "slug", name="uq_module_lesson_slug"),
    )

    # ── lesson_blocks table ──────────────────────────
    op.create_table(
        "lesson_blocks",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "lesson_id",
            sa.String(36),
            sa.ForeignKey("lessons.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("block_type", sa.String(50), nullable=False),
        sa.Column(
            "content",
            sa.JSON().with_variant(JSONB(), "postgresql"),
            nullable=False,
        ),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )


def downgrade() -> None:
    bind = op.get_bind()

    op.drop_table("lesson_blocks")
    op.drop_table("lessons")
    op.drop_table("modules")

    # Drop circular foreign key before dropping tables
    with contextlib.suppress(Exception):
        op.drop_constraint("fk_courses_current_version_id", "courses", type_="foreignkey")

    op.drop_table("course_versions")
    op.drop_table("course_skills")
    op.drop_table("courses")
    op.drop_table("skill_prerequisites")
    op.drop_table("skills")
    op.drop_table("disciplines")

    sa.Enum(name="course_status").drop(bind, checkfirst=True)
    sa.Enum(name="course_difficulty").drop(bind, checkfirst=True)
    sa.Enum(name="skill_difficulty").drop(bind, checkfirst=True)
