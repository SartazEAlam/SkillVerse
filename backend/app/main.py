"""SkillVerse FastAPI application factory."""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.infrastructure.database import check_database_connection

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("skillverse")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: startup and shutdown events."""
    logger.info("SkillVerse API starting up (env=%s)", settings.environment)
    if settings.is_development and settings.database_url.startswith("sqlite"):
        import app.modules.activities.models
        import app.modules.auth.models
        import app.modules.courses.models
        import app.modules.skills.models  # noqa: F401
        from app.infrastructure.database import Base, engine

        Base.metadata.create_all(bind=engine)
    yield
    logger.info("SkillVerse API shutting down")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="SkillVerse API",
        description="Cross-disciplinary interactive skill-learning platform",
        version="0.1.0",
        docs_url="/api/docs" if settings.is_development else None,
        redoc_url="/api/redoc" if settings.is_development else None,
        lifespan=lifespan,
    )

    # ── CORS ─────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Error handlers ───────────────────────────────
    from fastapi.exceptions import RequestValidationError
    from starlette.exceptions import HTTPException as StarletteHTTPException

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Any, exc: RequestValidationError
    ) -> JSONResponse:
        details = []
        for err in exc.errors():
            field = ".".join(str(x) for x in err.get("loc", []) if x != "body")
            details.append({"field": field or "body", "message": err.get("msg", "Invalid value")})

        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Request validation failed.",
                    "details": details,
                }
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Any, exc: StarletteHTTPException) -> JSONResponse:
        status_code_map = {
            400: "VALIDATION_ERROR",
            401: "UNAUTHORIZED",
            403: "FORBIDDEN",
            404: "NOT_FOUND",
            409: "CONFLICT",
            422: "UNPROCESSABLE_ENTITY",
            429: "RATE_LIMITED",
            500: "INTERNAL_ERROR",
        }

        if isinstance(exc.detail, dict) and "error" in exc.detail:
            content = exc.detail
        else:
            code = status_code_map.get(exc.status_code, "HTTP_ERROR")
            content = {
                "error": {
                    "code": code,
                    "message": str(exc.detail),
                    "details": {},
                }
            }

        return JSONResponse(
            status_code=exc.status_code,
            content=content,
            headers=dict(exc.headers) if exc.headers else None,
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Any, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled server exception: %s", exc)
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected server error occurred.",
                    "details": {},
                }
            },
        )

    # ── Root & Health check ──────────────────────────
    @app.get("/", include_in_schema=False)
    def root() -> dict[str, Any]:
        """Root endpoint returning API metadata and helpful links."""
        return {
            "name": "SkillVerse API",
            "version": "0.1.0",
            "status": "online",
            "docs": "/api/docs" if settings.is_development else None,
            "health": "/api/v1/health",
            "message": "SkillVerse API is running. The web application runs on http://localhost:5173",
        }

    @app.get("/api/v1/health", tags=["System"])
    def health_check() -> JSONResponse:
        """System liveness and dependency readiness check."""
        db_ok = check_database_connection()

        services: dict[str, str] = {
            "database": "connected" if db_ok else "disconnected",
            "redis": "not_configured",  # Redis check will be added when integrated
            "storage": "not_configured",  # Object storage check will be added when integrated
        }

        all_critical_ok = db_ok
        status_str = "healthy" if all_critical_ok else "degraded"
        http_status = 200 if all_critical_ok else 503

        result: dict[str, Any] = {
            "status": status_str,
            "version": "0.1.0",
            "timestamp": datetime.now(UTC).isoformat(),
            "services": services,
        }
        return JSONResponse(content=result, status_code=http_status)

    # ── Register routers ─────────────────────────────
    from app.modules.activities.router import router as activities_router
    from app.modules.auth.router import router as auth_router
    from app.modules.courses.router import router as courses_router
    from app.modules.skills.router import router as skills_router
    from app.modules.users.router import router as users_router

    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(users_router, prefix="/api/v1")
    app.include_router(skills_router, prefix="/api/v1")
    app.include_router(courses_router, prefix="/api/v1")
    app.include_router(activities_router, prefix="/api/v1")

    return app


app = create_app()
