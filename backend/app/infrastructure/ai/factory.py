"""Factory for initializing configured AI provider."""

from __future__ import annotations

import logging

from app.config import settings
from app.infrastructure.ai.base import BaseAIProvider
from app.infrastructure.ai.gemini_provider import GeminiAIProvider
from app.infrastructure.ai.mock_provider import MockAIProvider

logger = logging.getLogger("skillverse.ai.factory")


def get_ai_provider() -> BaseAIProvider:
    """Return the configured AI provider based on application settings.

    Defaults to MockAIProvider if 'mock' or if 'gemini' is requested without an API key.
    """
    provider_type = (settings.ai_provider or "mock").lower()

    if provider_type == "gemini":
        if settings.gemini_api_key:
            logger.info("Initializing live Gemini AI provider (model=%s)", settings.gemini_model)
            return GeminiAIProvider(
                api_key=settings.gemini_api_key,
                model=settings.gemini_model,
                timeout_seconds=settings.ai_timeout_seconds,
            )
        else:
            logger.warning(
                "AI_PROVIDER='gemini' requested but GEMINI_API_KEY is empty. "
                "Falling back safely to MockAIProvider."
            )
            return MockAIProvider(model_name="mock-fallback-v1")

    # Default to deterministic mock provider
    return MockAIProvider(model_name="mock-tutor-v1")
