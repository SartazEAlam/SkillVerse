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

    # ── CORS & Security (Phase 10 Stage 2) ───────────
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    cors_allow_credentials: bool = False
    cors_max_age: int = 600

    # ── Content Security Policy & HSTS (Phase 10 Stage 2) ──
    csp_enabled: bool = True
    csp_report_only: bool = True  # Rollout default: Report-Only mode
    csp_report_uri: str = ""
    hsts_enabled: bool = False  # Enabled in production when HTTPS is confirmed
    hsts_max_age: int = 31536000
    hsts_include_subdomains: bool = False
    hsts_preload: bool = False

    # ── Redis ────────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"

    # ── Email ────────────────────────────────────────
    email_backend: Literal["console", "smtp"] = "console"
    smtp_host: str = "localhost"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    email_from: str = "noreply@skillverse.dev"

    # ── AI Integration (Phase 8) ─────────────────────
    ai_provider: Literal["mock", "gemini", "disabled"] = "mock"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"
    ai_timeout_seconds: int = 15
    ai_tutor_rate_limit: int = 30  # Max tutor requests per hour per user
    ai_hint_rate_limit: int = 10  # Max activity hint requests per hour per user
    ai_store_content: bool = False  # Privacy default: do not persist raw learner prompt/response text
    ai_max_input_length: int = 1000  # Cap learner questions to 1000 characters

    # ── Storage Configuration (Phase 9) ─────────────
    storage_provider: Literal["local", "s3", "disabled"] = "local"
    storage_local_root: str = "uploads/artifacts"
    storage_max_file_size_mb: int = 20  # Max artifact size: 20MB
    storage_allowed_extensions: list[str] = [
        ".zip",
        ".tar.gz",
        ".tgz",
        ".pdf",
        ".png",
        ".jpg",
        ".jpeg",
        ".webp",
        ".txt",
        ".md",
        ".json",
        ".csv",
    ]

    # ── Security & Proxy Configuration (Phase 10) ─────
    trusted_proxies: list[str] = []

    @field_validator("trusted_proxies", mode="before")
    @classmethod
    def parse_trusted_proxies(cls, v: object) -> list[str]:
        if isinstance(v, str):
            import json

            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return [str(item).strip() for item in parsed if str(item).strip()]
            except Exception:
                pass
            return [p.strip() for p in v.split(",") if p.strip()]
        if isinstance(v, (list, tuple, set)):
            return [str(item).strip() for item in v if str(item).strip()]
        return []

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: object) -> list[str]:
        raw_list: list[str] = []
        if isinstance(v, str):
            v_str = v.strip()
            if not v_str:
                return []
            import json

            try:
                parsed = json.loads(v_str)
                if isinstance(parsed, list):
                    raw_list = [str(x).strip() for x in parsed if str(x).strip()]
                else:
                    raw_list = [str(parsed).strip()]
            except Exception:
                raw_list = [x.strip() for x in v_str.split(",") if x.strip()]
        elif isinstance(v, (list, tuple, set)):
            raw_list = [str(x).strip() for x in v if str(x).strip()]
        else:
            return []

        cleaned: list[str] = []
        from urllib.parse import urlparse

        for orig in raw_list:
            orig = orig.strip()
            if not orig:
                continue
            if orig == "*":
                cleaned.append("*")
                continue
            orig_no_slash = orig.rstrip("/")
            parsed_url = urlparse(orig_no_slash)
            if parsed_url.scheme not in ("http", "https") or not parsed_url.netloc:
                raise ValueError(f"Invalid CORS origin format: '{orig}'")
            if parsed_url.path:
                raise ValueError(f"CORS origin must not contain a path component: '{orig}'")
            cleaned.append(f"{parsed_url.scheme}://{parsed_url.netloc}")
        return cleaned

    @model_validator(mode="after")
    def validate_production_environment(self) -> Self:
        """Enforce strict production security invariants."""
        if self.cors_allow_credentials and "*" in self.cors_origins:
            raise ValueError("CORS credentials cannot be enabled with wildcard origin.")

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

            if not self.cors_origins:
                msg = "Production environment requires explicit, valid HTTPS cors_origins."
                raise ValueError(msg)

            from urllib.parse import urlparse

            for origin in self.cors_origins:
                if origin == "*":
                    msg = "Wildcard CORS origin '*' is strictly forbidden in production."
                    raise ValueError(msg)
                if origin.startswith("http://"):
                    msg = f"Insecure HTTP CORS origin '{origin}' is forbidden in production."
                    raise ValueError(msg)
                p = urlparse(origin)
                host = (p.hostname or "").lower()
                if host in ("localhost", "127.0.0.1", "::1"):
                    msg = f"Localhost CORS origin '{origin}' is forbidden in production."
                    raise ValueError(msg)
        return self

    @property
    def is_development(self) -> bool:
        return self.environment == "development"


# Singleton settings instance
settings = Settings()
