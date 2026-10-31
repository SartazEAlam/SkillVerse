"""REST API routes for AI tutoring, progressive hints, and learner preferences."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.dependencies import get_current_user
from app.infrastructure.database import get_db
from app.infrastructure.rate_limiter import limiter
from app.modules.ai.schemas import (
    ActivityHintRequest,
    ActivityHintResponse,
    AIPeriodicPreferenceRequest,
    AIStatusResponse,
    TutorChatRequest,
    TutorChatResponse,
)
from app.modules.ai.service import AIService
from app.modules.auth.models import User

router = APIRouter(prefix="/ai", tags=["AI Tutoring"])


def _get_ai_service(db: Session = Depends(get_db)) -> AIService:
    return AIService(db)


def _check_tutor_rate_limit(user: User) -> int:
    """Enforce user-scoped hourly rate limits on tutor interactions."""
    key = f"user:{user.id}:ai_tutor"
    allowed, remaining, retry_after = limiter.check(
        key=key,
        max_requests=settings.ai_tutor_rate_limit,
        window_seconds=3600,
    )
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": {
                    "code": "RATE_LIMITED",
                    "message": f"Tutor request limit reached ({settings.ai_tutor_rate_limit}/hr). Please try again in {retry_after} seconds.",
                    "details": {"retry_after": retry_after},
                }
            },
            headers={"Retry-After": str(retry_after)},
        )
    return remaining


def _check_hint_rate_limit(user: User) -> int:
    """Enforce user-scoped hourly rate limits on assessment hints."""
    key = f"user:{user.id}:ai_hint"
    allowed, remaining, retry_after = limiter.check(
        key=key,
        max_requests=settings.ai_hint_rate_limit,
        window_seconds=3600,
    )
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": {
                    "code": "RATE_LIMITED",
                    "message": f"Hint request limit reached ({settings.ai_hint_rate_limit}/hr). Please try again in {retry_after} seconds.",
                    "details": {"retry_after": retry_after},
                }
            },
            headers={"Retry-After": str(retry_after)},
        )
    return remaining


@router.post("/tutor", response_model=TutorChatResponse)
def ask_tutor(
    body: TutorChatRequest,
    current_user: User = Depends(get_current_user),
    service: AIService = Depends(_get_ai_service),
) -> TutorChatResponse:
    """Ask the AI tutor a question within lesson context.

    Enforces server-side authentication, trusted context assembly, input length limits,
    and user-scoped hourly rate limits.
    """
    _check_tutor_rate_limit(current_user)

    return service.ask_tutor(
        user=current_user,
        lesson_id=body.lesson_id,
        message=body.message,
        history=body.history,
    )


@router.post("/hint", response_model=ActivityHintResponse)
def get_activity_hint(
    body: ActivityHintRequest,
    current_user: User = Depends(get_current_user),
    service: AIService = Depends(_get_ai_service),
) -> ActivityHintResponse:
    """Request a progressive hint for an interactive assessment activity.

    Confidential answer keys and rubric solutions are strictly segregated from AI prompts.
    """
    _check_hint_rate_limit(current_user)

    return service.generate_hint(
        user=current_user,
        activity_id=body.activity_id,
        lesson_id=body.lesson_id,
        hint_level=body.hint_level,
    )


@router.get("/status", response_model=AIStatusResponse)
def get_ai_status(
    current_user: User = Depends(get_current_user),
    service: AIService = Depends(_get_ai_service),
) -> AIStatusResponse:
    """Inspect AI provider status, model name, and remaining hourly tutor quota."""
    key = f"user:{current_user.id}:ai_tutor"
    _, remaining, _ = limiter.check(
        key=key,
        max_requests=settings.ai_tutor_rate_limit,
        window_seconds=3600,
    )
    return service.get_status(user=current_user, remaining_requests=remaining)


@router.api_route("/preferences", methods=["PUT", "POST"])
def update_ai_preferences(
    body: AIPeriodicPreferenceRequest,
    current_user: User = Depends(get_current_user),
    service: AIService = Depends(_get_ai_service),
) -> dict[str, Any]:
    """Toggle user opt-out preference for AI tutoring."""
    return service.set_opt_out(user=current_user, opt_out=body.ai_opt_out)
