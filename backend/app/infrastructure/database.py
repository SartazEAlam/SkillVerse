"""Database session management and base model.

Uses synchronous SQLAlchemy for simplicity in the initial foundation.
Async can be introduced later if profiling shows it's needed.
"""

from __future__ import annotations

import uuid
from collections.abc import Generator
from datetime import UTC, datetime

from sqlalchemy import DateTime, create_engine, func
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    sessionmaker,
)

from app.config import settings

if settings.database_url.startswith("sqlite"):
    engine = create_engine(
        settings.database_url,
        echo=settings.database_echo,
        connect_args={"check_same_thread": False},
    )
else:
    engine = create_engine(
        settings.database_url,
        echo=settings.database_echo,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
    )

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class Base(DeclarativeBase):
    """Declarative base with common columns."""

    pass


class TimestampMixin:
    """Mixin providing created_at and updated_at columns."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )


def generate_uuid() -> str:
    """Generate a UUID4 string for use as a primary key."""
    return str(uuid.uuid4())


def check_database_connection() -> bool:
    """Check if the database is reachable. Used by health check."""
    try:
        with engine.connect() as conn:
            conn.execute(func.now())  # type: ignore[arg-type]
        return True
    except Exception:
        return False
