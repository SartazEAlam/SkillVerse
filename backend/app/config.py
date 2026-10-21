"""SkillVerse backend application configuration.

Loads settings from environment variables with Pydantic Settings.
"""

from __future__ import annotations

from typing import Literal, Self

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Server ──────────────────────────────────────
    environment: Literal["development", "staging", "production"] = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = True
    log_level: str = "info"

    # ── Database ────────────────────────────────────
    database_url: str = "postgresql://skillverse:skillverse_dev@localhost:5432/skillverse"
    database_echo: bool = False

    # ── JWT ──────────────────────────────────────────
    jwt_secret_key: str = "change-me-to-a-random-64-char-string-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_days: int = 30

    # ── OAuth (Google) ───────────────────────────────
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:5173/auth/google/callback"

    # ── CORS ─────────────────────────────────────────
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # ── Redis ────────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"

    # ── Email ────────────────────────────────────────
    email_backend: Literal["console", "smtp"] = "console"
    smtp_host: str = "localhost"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    email_from: str = "noreply@skillverse.dev"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: object) -> list[str]:
        if isinstance(v, str):
            import json

            return list(json.loads(v))
        return list(v)  # type: ignore[arg-type]

    @model_validator(mode="after")
    def validate_production_environment(self) -> Self:
        """Enforce strict production security invariants."""
        if self.environment == "production":
            if self.database_url.startswith("sqlite"):
                msg = (
                    "Production environment cannot use SQLite. "
                    "A valid PostgreSQL database_url is required."
                )
                raise ValueError(msg)
            insecure_keys = {
                "change-me-to-a-random-64-char-string-in-production",
                "development-secret-key-for-skillverse-local-testing-purposes-only",
            }
            if (
                not self.jwt_secret_key
                or self.jwt_secret_key in insecure_keys
                or len(self.jwt_secret_key) < 32
            ):
                msg = (
                    "Production environment requires a secure, non-default JWT_SECRET_KEY "
                    "of at least 32 characters."
                )
                raise ValueError(msg)
        return self

    @property
    def is_development(self) -> bool:
        return self.environment == "development"


# Singleton settings instance
settings = Settings()
