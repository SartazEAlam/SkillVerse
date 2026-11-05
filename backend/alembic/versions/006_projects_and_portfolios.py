"""Phase 9 — projects, project submissions, artifacts, and portfolios

Revision ID: 006_projects_and_portfolios
Revises: 005_ai_interactions
Create Date: 2026-10-31
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "006_projects_and_portfolios"
down_revision: str | None = "005_ai_interactions"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── 1. projects table ────────────────────────────────────────────────────────
    op.create_table(
        "projects",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("slug", sa.String(length=200), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("short_description", sa.Text(), nullable=False),
        sa.Column("full_description", sa.Text(), nullable=False),
        sa.Column(
            "course_version_id",
            sa.String(length=36),
            sa.ForeignKey("course_versions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "discipline_id",
            sa.String(length=36),
            sa.ForeignKey("disciplines.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("difficulty_level", sa.String(length=50), server_default="BEGINNER", nullable=False),
        sa.Column("estimated_duration_hours", sa.Integer(), nullable=True),
        sa.Column(
            "requirements",
            sa.JSON().with_variant(JSONB, "postgresql"),
            server_default="{}",
            nullable=False,
        ),
        sa.Column(
            "evaluation_criteria",
            sa.JSON().with_variant(JSONB, "postgresql"),
            server_default="{}",
            nullable=False,
        ),
        sa.Column(
            "starter_resources",
            sa.JSON().with_variant(JSONB, "postgresql"),
            server_default="[]",
            nullable=False,
        ),
        sa.Column("status", sa.String(length=50), server_default="DRAFT", nullable=False),
        sa.Column(
            "creator_id",
            sa.String(length=36),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_projects_slug", "projects", ["slug"], unique=True)
    op.create_index("ix_projects_discipline_id", "projects", ["discipline_id"])
    op.create_index("ix_projects_course_version_id", "projects", ["course_version_id"])
    op.create_index("ix_projects_creator_id", "projects", ["creator_id"])
    op.create_index("ix_projects_status", "projects", ["status"])

    # ── 2. project_skills association table ──────────────────────────────────────
    op.create_table(
        "project_skills",
        sa.Column(
            "project_id",
            sa.String(length=36),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "skill_id",
            sa.String(length=36),
            sa.ForeignKey("skills.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("is_primary", sa.Boolean(), server_default="0", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # ── 3. project_submissions table ─────────────────────────────────────────────
    op.create_table(
        "project_submissions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "project_id",
            sa.String(length=36),
            sa.ForeignKey("projects.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.String(length=36),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("version_number", sa.Integer(), server_default="1", nullable=False),
        sa.Column(
            "revision_of_id",
            sa.String(length=36),
            sa.ForeignKey("project_submissions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("status", sa.String(length=50), server_default="DRAFT", nullable=False),
        sa.Column("title", sa.String(length=300), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column(
            "content",
            sa.JSON().with_variant(JSONB, "postgresql"),
            server_default="{}",
            nullable=False,
        ),
        sa.Column(
            "milestones_completed",
            sa.JSON().with_variant(JSONB, "postgresql"),
            server_default="[]",
            nullable=False,
        ),
        sa.Column(
            "evaluation",
            sa.JSON().with_variant(JSONB, "postgresql"),
            nullable=True,
        ),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("passed", sa.Boolean(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("evaluated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "evaluator_id",
            sa.String(length=36),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "user_id",
            "project_id",
            "version_number",
            name="uq_user_project_submission_version",
        ),
    )
    op.create_index("ix_project_submissions_project_id", "project_submissions", ["project_id"])
    op.create_index("ix_project_submissions_user_id", "project_submissions", ["user_id"])
    op.create_index("ix_project_submissions_status", "project_submissions", ["status"])
    op.create_index("ix_project_submissions_revision_of_id", "project_submissions", ["revision_of_id"])
    op.create_index(
        "ix_project_submissions_project_status", "project_submissions", ["project_id", "status"]
    )

    # ── 4. project_artifacts table ───────────────────────────────────────────────
    op.create_table(
        "project_artifacts",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "submission_id",
            sa.String(length=36),
            sa.ForeignKey("project_submissions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.String(length=36),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("storage_key", sa.String(length=500), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("mime_type", sa.String(length=100), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=False),
        sa.Column("checksum_sha256", sa.String(length=64), nullable=False),
        sa.Column("is_public", sa.Boolean(), server_default="0", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_project_artifacts_submission_id", "project_artifacts", ["submission_id"])
    op.create_index("ix_project_artifacts_user_id", "project_artifacts", ["user_id"])
    op.create_index("ix_project_artifacts_storage_key", "project_artifacts", ["storage_key"], unique=True)

    # ── 5. portfolios table ──────────────────────────────────────────────────────
    op.create_table(
        "portfolios",
        sa.Column(
            "user_id",
            sa.String(length=36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("is_public", sa.Boolean(), server_default="0", nullable=False),
        sa.Column("custom_slug", sa.String(length=100), nullable=True),
        sa.Column("title", sa.String(length=200), nullable=True),
        sa.Column("headline", sa.String(length=300), nullable=True),
        sa.Column("bio_override", sa.Text(), nullable=True),
        sa.Column(
            "contact_links",
            sa.JSON().with_variant(JSONB, "postgresql"),
            server_default="{}",
            nullable=False,
        ),
        sa.Column(
            "settings",
            sa.JSON().with_variant(JSONB, "postgresql"),
            server_default="{}",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_portfolios_is_public", "portfolios", ["is_public"])
    op.create_index("ix_portfolios_custom_slug", "portfolios", ["custom_slug"], unique=True)

    # ── 6. portfolio_items table ─────────────────────────────────────────────────
    op.create_table(
        "portfolio_items",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "portfolio_user_id",
            sa.String(length=36),
            sa.ForeignKey("portfolios.user_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("item_type", sa.String(length=50), server_default="PROJECT_SUBMISSION", nullable=False),
        sa.Column("reference_id", sa.String(length=36), nullable=True),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column(
            "skills_demonstrated",
            sa.JSON().with_variant(JSONB, "postgresql"),
            server_default="[]",
            nullable=False,
        ),
        sa.Column(
            "artifacts",
            sa.JSON().with_variant(JSONB, "postgresql"),
            server_default="[]",
            nullable=False,
        ),
        sa.Column("external_url", sa.String(length=500), nullable=True),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("visibility", sa.String(length=50), server_default="PUBLIC", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_portfolio_items_portfolio_user_id", "portfolio_items", ["portfolio_user_id"])
    op.create_index("ix_portfolio_items_reference_id", "portfolio_items", ["reference_id"])
    op.create_index(
        "ix_portfolio_items_user_order", "portfolio_items", ["portfolio_user_id", "sort_order"]
    )


def downgrade() -> None:
    # Drop in reverse dependency order
    op.drop_index("ix_portfolio_items_user_order", table_name="portfolio_items")
    op.drop_index("ix_portfolio_items_reference_id", table_name="portfolio_items")
    op.drop_index("ix_portfolio_items_portfolio_user_id", table_name="portfolio_items")
    op.drop_table("portfolio_items")

    op.drop_index("ix_portfolios_custom_slug", table_name="portfolios")
    op.drop_index("ix_portfolios_is_public", table_name="portfolios")
    op.drop_table("portfolios")

    op.drop_index("ix_project_artifacts_storage_key", table_name="project_artifacts")
    op.drop_index("ix_project_artifacts_user_id", table_name="project_artifacts")
    op.drop_index("ix_project_artifacts_submission_id", table_name="project_artifacts")
    op.drop_table("project_artifacts")

    op.drop_index("ix_project_submissions_project_status", table_name="project_submissions")
    op.drop_index("ix_project_submissions_revision_of_id", table_name="project_submissions")
    op.drop_index("ix_project_submissions_status", table_name="project_submissions")
    op.drop_index("ix_project_submissions_user_id", table_name="project_submissions")
    op.drop_index("ix_project_submissions_project_id", table_name="project_submissions")
    op.drop_table("project_submissions")

    op.drop_table("project_skills")

    op.drop_index("ix_projects_status", table_name="projects")
    op.drop_index("ix_projects_creator_id", table_name="projects")
    op.drop_index("ix_projects_course_version_id", table_name="projects")
    op.drop_index("ix_projects_discipline_id", table_name="projects")
    op.drop_index("ix_projects_slug", table_name="projects")
    op.drop_table("projects")
