"""Pydantic schemas for AI tutoring, progressive hints, and user preferences."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class ChatMessageTurn(BaseModel):
    """Previous exchange turn for conversational context."""

    role: Literal["user", "assistant"]
    content: str = Field(..., max_length=1000)


class TutorChatRequest(BaseModel):
    """Learner question for the AI tutor."""

    lesson_id: str
    message: str = Field(..., min_length=1, max_length=1000)
    history: list[ChatMessageTurn] = Field(default_factory=list, max_length=6)


class TutorChatResponse(BaseModel):
    """Pedagogical response returned by the AI tutor."""

    reply: str
    response: str = ""
    suggestions: list[str] = Field(default_factory=list)
    provider: str
    model: str
    tokens_used: int = 0

    @model_validator(mode="before")
    @classmethod
    def sync_reply_and_response(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "reply" in data and not data.get("response"):
                data["response"] = data["reply"]
            elif "response" in data and not data.get("reply"):
                data["reply"] = data["response"]
        return data


class ActivityHintRequest(BaseModel):
    """Request for progressive assessment hint."""

    activity_id: str
    lesson_id: str | None = None
    hint_level: int = Field(default=1, ge=1, le=3)


class ActivityHintResponse(BaseModel):
    """Progressive hint without answer key disclosure."""

    hint: str
    hint_level: int
    max_level: int = 3
    provider: str


class AIStatusResponse(BaseModel):
    """Service status and learner AI preference indicators."""

    enabled: bool
    provider: str
    model: str
    user_opted_out: bool
    opted_out: bool = False
    rate_limit_hourly: int
    remaining_tutor_requests: int

    @model_validator(mode="before")
    @classmethod
    def sync_opted_out(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "user_opted_out" in data and not data.get("opted_out"):
                data["opted_out"] = data["user_opted_out"]
            elif "opted_out" in data and not data.get("user_opted_out"):
                data["user_opted_out"] = data["opted_out"]
        return data


class AIPeriodicPreferenceRequest(BaseModel):
    """Update AI tutor opt-out preference."""

    ai_opt_out: bool = False

    @model_validator(mode="before")
    @classmethod
    def sync_opt_out(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "opt_out" in data and "ai_opt_out" not in data:
                data["ai_opt_out"] = data["opt_out"]
            elif "ai_opt_out" in data and "opt_out" not in data:
                data["opt_out"] = data["ai_opt_out"]
        return data
