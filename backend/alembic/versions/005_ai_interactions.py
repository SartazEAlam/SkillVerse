"""Phase 8 — AI interaction telemetry and audit logging

Revision ID: 005_ai_interactions
Revises: 004_progress_mastery
Create Date: 2026-10-29
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "005_ai_interactions"
down_revision: str | None = "004_progress_mastery"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "ai_interactions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(length=36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("interaction_type", sa.String(length=50), nullable=False),
        sa.Column("lesson_id", sa.String(length=36), nullable=True),
        sa.Column("activity_id", sa.String(length=36), nullable=True),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("model", sa.String(length=100), nullable=False),
        sa.Column("prompt_tokens", sa.Integer(), server_default="0", nullable=False),
        sa.Column("completion_tokens", sa.Integer(), server_default="0", nullable=False),
        sa.Column("total_tokens", sa.Integer(), server_default="0", nullable=False),
        sa.Column("latency_ms", sa.Integer(), server_default="0", nullable=False),
        sa.Column("status", sa.String(length=20), server_default="success", nullable=False),
        sa.Column("error_code", sa.String(length=50), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_ai_interactions_user_id", "ai_interactions", ["user_id"])
    op.create_index(
        "ix_ai_interactions_user_created", "ai_interactions", ["user_id", "created_at"]
    )
    op.create_index(
        "ix_ai_interactions_type_created", "ai_interactions", ["interaction_type", "created_at"]
    )


def downgrade() -> None:
    op.drop_index("ix_ai_interactions_type_created", table_name="ai_interactions")
    op.drop_index("ix_ai_interactions_user_created", table_name="ai_interactions")
    op.drop_index("ix_ai_interactions_user_id", table_name="ai_interactions")
    op.drop_table("ai_interactions")

