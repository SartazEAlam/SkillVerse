"""Phase 5 — activities, grading configs, and attempts

Revision ID: 003_activities_and_assessments
Revises: 002_skill_taxonomy_and_courses
Create Date: 2026-10-23
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "003_activities_and_assessments"
down_revision: str | None = "002_skill_taxonomy_and_courses"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── activities table ────────────────────────────
    op.create_table(
        "activities",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "lesson_id",
            sa.String(length=36),
            sa.ForeignKey("lessons.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("activity_type", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("instructions", sa.Text(), nullable=False),
        sa.Column(
            "configuration",
            sa.JSON().with_variant(JSONB, "postgresql"),
            server_default="{}",
            nullable=False,
        ),
        sa.Column("max_attempts", sa.Integer(), nullable=True),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
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
    op.create_index("ix_activities_lesson_id", "activities", ["lesson_id"])
    op.create_index("ix_activities_activity_type", "activities", ["activity_type"])

    # ── grading_configs table ───────────────────────
    op.create_table(
        "grading_configs",
        sa.Column(
            "activity_id",
            sa.String(length=36),
            sa.ForeignKey("activities.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("grading_type", sa.String(length=50), nullable=False),
        sa.Column("passing_score", sa.Float(), server_default="70.0", nullable=False),
        sa.Column(
            "answer_key",
            sa.JSON().with_variant(JSONB, "postgresql"),
            server_default="{}",
            nullable=False,
        ),
        sa.Column("rubric", sa.JSON().with_variant(JSONB, "postgresql"), nullable=True),
        sa.Column("test_cases", sa.JSON().with_variant(JSONB, "postgresql"), nullable=True),
        sa.Column("feedback_config", sa.JSON().with_variant(JSONB, "postgresql"), nullable=True),
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

    # ── attempts table ──────────────────────────────
    op.create_table(
        "attempts",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(length=36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "activity_id",
            sa.String(length=36),
            sa.ForeignKey("activities.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column(
            "submission",
            sa.JSON().with_variant(JSONB, "postgresql"),
            server_default="{}",
            nullable=False,
        ),
        sa.Column("result", sa.JSON().with_variant(JSONB, "postgresql"), nullable=True),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("max_score", sa.Float(), server_default="100.0", nullable=False),
        sa.Column("passed", sa.Boolean(), nullable=True),
        sa.Column("feedback", sa.JSON().with_variant(JSONB, "postgresql"), nullable=True),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
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
            "user_id", "activity_id", "attempt_number", name="uq_user_activity_attempt"
        ),
    )
    op.create_index("ix_attempts_user_id", "attempts", ["user_id"])
    op.create_index("ix_attempts_activity_id", "attempts", ["activity_id"])
    op.create_index("ix_attempts_user_activity", "attempts", ["user_id", "activity_id"])


def downgrade() -> None:
    op.drop_table("attempts")
    op.drop_table("grading_configs")
    op.drop_table("activities")
