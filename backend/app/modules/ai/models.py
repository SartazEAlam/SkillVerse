"""Database models for AI interaction telemetry and audit logging."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database import Base, generate_uuid

if TYPE_CHECKING:
    from app.modules.auth.models import User


class AIInteraction(Base):
    """Operational telemetry record for AI tutor and assessment hint requests.

    Privacy standard: In compliance with data minimization principles, full learner
    prompts and assistant responses are NOT persisted by default. Only operational
    metadata (token counts, latency, status, timestamps, and target references) is
    retained for rate limiting, usage accounting, and service reliability auditing.
    """

    __tablename__ = "ai_interactions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    interaction_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # 'tutor_query', 'activity_hint', 'feedback'
    lesson_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    activity_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)  # 'mock', 'gemini'
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default="success", nullable=False
    )  # 'success', 'rate_limited', 'filtered', 'error'
    error_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    # Relationship
    user: Mapped[User] = relationship("User", backref="ai_interactions")

    __table_args__ = (
        Index("ix_ai_interactions_user_created", "user_id", "created_at"),
        Index("ix_ai_interactions_type_created", "interaction_type", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<AIInteraction id={self.id} user={self.user_id} type={self.interaction_type} "
            f"provider={self.provider} tokens={self.total_tokens}>"
        )

