"""Provider-neutral AI interface and context data contracts."""

from __future__ import annotations

from abc import ABC, abstractmethod

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """Chat message turn for conversation history."""

    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str = Field(..., max_length=2000)


class LessonContext(BaseModel):
    """Trusted lesson context extracted strictly from backend models."""

    course_title: str
    course_slug: str
    module_title: str
    lesson_title: str
    lesson_slug: str
    learning_objectives: list[str] = Field(default_factory=list)
    content_summary: str = ""


class ActivityHintContext(BaseModel):
    """Context for generating hints without revealing secret answer keys."""

    activity_type: str
    title: str
    instructions: str
    options: list[str] | None = None
    starter_code: str | None = None


class AITutorResponse(BaseModel):
    """Validated response from AI tutor."""

    reply: str
    suggestions: list[str] = Field(default_factory=list)
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    provider: str
    model: str


class AIHintResponse(BaseModel):
    """Validated progressive hint response."""

    hint: str
    hint_level: int
    max_level: int = 3
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    provider: str
    model: str


class AIProviderError(Exception):
    """Raised when an AI provider encounter an operational or timeout error."""

    def __init__(self, message: str, code: str = "AI_PROVIDER_ERROR", status_code: int = 502) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code


class BaseAIProvider(ABC):
    """Abstract provider interface decoupling business logic from external AI services."""

    @abstractmethod
    def ask_tutor(
        self,
        user_message: str,
        lesson_context: LessonContext,
        history: list[ChatMessage] | None = None,
    ) -> AITutorResponse:
        """Generate a pedagogical response to a learner question within lesson context."""

    @abstractmethod
    def generate_hint(
        self,
        activity_context: ActivityHintContext,
        hint_level: int,
    ) -> AIHintResponse:
        """Generate a progressive hint for an interactive assessment."""
