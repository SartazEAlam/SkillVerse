"""Business logic service for AI tutoring, progressive hints, and operational audit."""

from __future__ import annotations

import logging
import time
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.config import settings
from app.infrastructure.ai.base import (
    ActivityHintContext,
    AIProviderError,
    BaseAIProvider,
    ChatMessage,
    LessonContext,
)
from app.infrastructure.ai.factory import get_ai_provider
from app.modules.activities.models import Activity
from app.modules.ai.models import AIInteraction
from app.modules.ai.schemas import (
    ActivityHintResponse,
    AIStatusResponse,
    ChatMessageTurn,
    TutorChatResponse,
)
from app.modules.auth.models import User, UserProfile
from app.modules.courses.models import CourseVersion, Lesson, Module

logger = logging.getLogger("skillverse.ai.service")


class AIService:
    """Orchestrates trusted context extraction, AI provider calls, and audit logging."""

    def __init__(self, db: Session, provider: BaseAIProvider | None = None) -> None:
        self.db = db
        self.provider = provider or get_ai_provider()

    def _check_opt_out(self, user: User) -> None:
        """Verify the user has not disabled AI features."""
        if user.profile and user.profile.preferences and user.profile.preferences.get("ai_opt_out"):
            raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error": {
                            "code": "AI_FEATURE_OPTED_OUT",
                            "message": "AI tutoring and hints are disabled in your user preferences.",
                        }
                    },
                )

    def _build_lesson_context(self, lesson_id: str) -> LessonContext:
        """Assemble trusted lesson context strictly from backend models.

        Ensures arbitrary client input cannot override verified lesson facts.
        """
        lesson = self.db.scalars(
            select(Lesson)
            .options(
                joinedload(Lesson.module)
                .joinedload(Module.course_version)
                .joinedload(CourseVersion.course),
                joinedload(Lesson.blocks),
            )
            .where(Lesson.id == lesson_id)
        ).unique().first()

        if not lesson:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": {"code": "LESSON_NOT_FOUND", "message": "Lesson not found."}},
            )

        module = lesson.module
        course_ver = module.course_version if module else None
        course = course_ver.course if course_ver else None

        # Extract textual content from structured lesson blocks
        content_snippets: list[str] = []
        if lesson.description:
            content_snippets.append(lesson.description)

        for blk in sorted(lesson.blocks, key=lambda b: b.sort_order):
            c = blk.content if isinstance(blk.content, dict) else {}
            if blk.block_type in ("heading", "text", "callout"):
                txt = c.get("text") or c.get("title") or ""
                if txt:
                    content_snippets.append(str(txt))
            elif blk.block_type == "list":
                items = c.get("items", [])
                if items and isinstance(items, list):
                    content_snippets.append("; ".join(str(i) for i in items))
            elif blk.block_type == "code_example":
                code = c.get("code", "")
                if code:
                    content_snippets.append(f"Code example:\n{code[:300]}")

        # Limit total content summary to prevent prompt token blowout
        summary = "\n\n".join(content_snippets)
        if len(summary) > 2500:
            summary = summary[:2500] + "..."

        return LessonContext(
            course_title=course.title if course else "Course",
            course_slug=course.slug if course else "",
            module_title=module.title if module else "Module",
            lesson_title=lesson.title,
            lesson_slug=lesson.slug,
            learning_objectives=lesson.learning_objectives or [],
            content_summary=summary,
        )

    def _log_interaction(
        self,
        user_id: str,
        interaction_type: str,
        lesson_id: str | None,
        activity_id: str | None,
        provider: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int,
        latency_ms: int,
        status_str: str = "success",
        error_code: str | None = None,
    ) -> None:
        """Record operational telemetry without storing learner prompt content."""
        interaction = AIInteraction(
            user_id=user_id,
            interaction_type=interaction_type,
            lesson_id=lesson_id,
            activity_id=activity_id,
            provider=provider,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            latency_ms=latency_ms,
            status=status_str,
            error_code=error_code,
        )
        self.db.add(interaction)
        try:
            self.db.commit()
        except Exception as e:
            logger.warning("Failed to commit AI interaction telemetry: %s", e)
            self.db.rollback()

    def ask_tutor(
        self,
        user: User,
        lesson_id: str,
        message: str,
        history: list[ChatMessageTurn] | None = None,
    ) -> TutorChatResponse:
        """Process a pedagogical tutor request from an authenticated learner."""
        self._check_opt_out(user)
        lesson_ctx = self._build_lesson_context(lesson_id)

        chat_history = [
            ChatMessage(role=turn.role, content=turn.content) for turn in (history or [])
        ]

        t0 = time.perf_counter()
        try:
            resp = self.provider.ask_tutor(
                user_message=message,
                lesson_context=lesson_ctx,
                history=chat_history,
            )
            latency_ms = int((time.perf_counter() - t0) * 1000)

            self._log_interaction(
                user_id=user.id,
                interaction_type="tutor_query",
                lesson_id=lesson_id,
                activity_id=None,
                provider=resp.provider,
                model=resp.model,
                prompt_tokens=resp.prompt_tokens,
                completion_tokens=resp.completion_tokens,
                total_tokens=resp.total_tokens,
                latency_ms=latency_ms,
                status_str="success",
            )

            return TutorChatResponse(
                reply=resp.reply,
                suggestions=resp.suggestions,
                provider=resp.provider,
                model=resp.model,
                tokens_used=resp.total_tokens,
            )
        except AIProviderError as ape:
            latency_ms = int((time.perf_counter() - t0) * 1000)
            self._log_interaction(
                user_id=user.id,
                interaction_type="tutor_query",
                lesson_id=lesson_id,
                activity_id=None,
                provider="unknown",
                model="unknown",
                prompt_tokens=0,
                completion_tokens=0,
                total_tokens=0,
                latency_ms=latency_ms,
                status_str="error",
                error_code=ape.code,
            )
            raise HTTPException(
                status_code=ape.status_code,
                detail={"error": {"code": ape.code, "message": ape.message}},
            )

    def generate_hint(
        self,
        user: User,
        activity_id: str,
        lesson_id: str | None = None,
        hint_level: int = 1,
    ) -> ActivityHintResponse:
        """Generate a progressive hint for an interactive assessment."""
        self._check_opt_out(user)

        activity = self.db.get(Activity, activity_id)
        if not activity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": {"code": "ACTIVITY_NOT_FOUND", "message": "Activity not found."}},
            )

        # Context assembly: extract public options/instructions; strictly exclude answer_key!
        cfg = activity.configuration if isinstance(activity.configuration, dict) else {}
        options_list: list[str] = []
        for opt in cfg.get("options", []):
            if isinstance(opt, dict) and "text" in opt:
                options_list.append(str(opt["text"]))
            elif isinstance(opt, str):
                options_list.append(opt)

        hint_ctx = ActivityHintContext(
            activity_type=activity.activity_type,
            title=activity.title,
            instructions=activity.instructions or "",
            options=options_list if options_list else None,
            starter_code=str(cfg.get("starter_code")) if cfg.get("starter_code") else None,
        )

        t0 = time.perf_counter()
        try:
            resp = self.provider.generate_hint(
                activity_context=hint_ctx,
                hint_level=hint_level,
            )
            latency_ms = int((time.perf_counter() - t0) * 1000)

            self._log_interaction(
                user_id=user.id,
                interaction_type="activity_hint",
                lesson_id=lesson_id or activity.lesson_id,
                activity_id=activity.id,
                provider=resp.provider,
                model=resp.model,
                prompt_tokens=resp.prompt_tokens,
                completion_tokens=resp.completion_tokens,
                total_tokens=resp.total_tokens,
                latency_ms=latency_ms,
                status_str="success",
            )

            return ActivityHintResponse(
                hint=resp.hint,
                hint_level=resp.hint_level,
                max_level=resp.max_level,
                provider=resp.provider,
            )
        except AIProviderError as ape:
            latency_ms = int((time.perf_counter() - t0) * 1000)
            self._log_interaction(
                user_id=user.id,
                interaction_type="activity_hint",
                lesson_id=lesson_id or activity.lesson_id,
                activity_id=activity.id,
                provider="unknown",
                model="unknown",
                prompt_tokens=0,
                completion_tokens=0,
                total_tokens=0,
                latency_ms=latency_ms,
                status_str="error",
                error_code=ape.code,
            )
            raise HTTPException(
                status_code=ape.status_code,
                detail={"error": {"code": ape.code, "message": ape.message}},
            )

    def get_status(self, user: User, remaining_requests: int) -> AIStatusResponse:
        """Inspect AI provider availability and user opt-out status."""
        user_opted_out = False
        if user.profile and user.profile.preferences:
            user_opted_out = bool(user.profile.preferences.get("ai_opt_out", False))

        is_enabled = settings.ai_provider != "disabled" and not user_opted_out

        return AIStatusResponse(
            enabled=is_enabled,
            provider=settings.ai_provider,
            model=settings.gemini_model if settings.ai_provider == "gemini" else "mock-tutor-v1",
            user_opted_out=user_opted_out,
            rate_limit_hourly=settings.ai_tutor_rate_limit,
            remaining_tutor_requests=remaining_requests,
        )

    def set_opt_out(self, user: User, opt_out: bool) -> dict[str, Any]:
        """Update learner AI opt-out preference in UserProfile."""
        if user.profile is None:
            user.profile = UserProfile(user_id=user.id, display_name=user.email)
            self.db.add(user.profile)

        prefs = dict(user.profile.preferences) if user.profile.preferences else {}
        prefs["ai_opt_out"] = opt_out
        user.profile.preferences = prefs

        self.db.commit()
        self.db.refresh(user)

        return {
            "ai_opt_out": opt_out,
            "opt_out": opt_out,
            "message": "AI preferences updated successfully.",
        }
