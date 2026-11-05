"""Mock AI provider for development, testing, and offline execution."""

from __future__ import annotations

from app.infrastructure.ai.base import (
    ActivityHintContext,
    AICommunicationFeedbackResponse,
    AIHintResponse,
    AITutorResponse,
    BaseAIProvider,
    ChatMessage,
    CommunicationFeedbackContext,
    LessonContext,
)


class MockAIProvider(BaseAIProvider):
    """Deterministic, pedagogical mock AI tutor provider.

    Used when no external AI credentials exist or when running automated test suites.
    Clearly marks all responses with provider='mock'.
    """

    def __init__(self, model_name: str = "mock-tutor-v1") -> None:
        self.model_name = model_name

    def ask_tutor(
        self,
        user_message: str,
        lesson_context: LessonContext,
        history: list[ChatMessage] | None = None,
    ) -> AITutorResponse:
        """Provide pedagogical guidance grounded in the current lesson context."""
        msg_lower = user_message.lower()

        # Tailored pedagogical responses based on keywords
        if any(w in msg_lower for w in ["what", "explain", "how", "why", "help"]):
            reply = (
                f"Great question! In **{lesson_context.lesson_title}**, the focus is on "
                f"understanding foundational principles. Specifically: "
                f"{lesson_context.learning_objectives[0] if lesson_context.learning_objectives else 'breaking down the problem step by step.'} "
                f"\n\nTo think about your question ('{user_message.strip()}'), consider: "
                f"how does this relate to the concepts outlined in {lesson_context.module_title}?"
            )
            suggestions = [
                f"Can you explain the main goal of {lesson_context.lesson_title}?",
                "Give me a practical example",
                "How do I prepare for the checkpoint assessment?",
            ]
        elif "hint" in msg_lower or "stuck" in msg_lower:
            reply = (
                f"When working through {lesson_context.lesson_title}, review the key concepts "
                f"introduced in the structured reading. Pay close attention to definitions and "
                f"how components connect together before attempting the checkpoint activity."
            )
            suggestions = [
                "What are the common pitfalls?",
                "Break this down step by step",
            ]
        else:
            reply = (
                f"I'm here to help you master **{lesson_context.lesson_title}**! "
                f"Based on this lesson, we are covering: "
                f"{'; '.join(lesson_context.learning_objectives[:2]) if lesson_context.learning_objectives else 'core concepts'}. "
                f"\n\nWhat specific part of '{user_message.strip()}' would you like to explore together?"
            )
            suggestions = [
                "Summarize the key takeaways",
                "Test my understanding with a question",
            ]

        # Calculate mock token usage
        prompt_tokens = len(user_message.split()) + len(lesson_context.content_summary.split()) + 40
        completion_tokens = len(reply.split()) + 10

        return AITutorResponse(
            reply=reply,
            suggestions=suggestions,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            provider="mock",
            model=self.model_name,
        )

    def generate_hint(
        self,
        activity_context: ActivityHintContext,
        hint_level: int,
    ) -> AIHintResponse:
        """Provide progressive hints without revealing the answer key."""
        clamped_level = max(1, min(3, hint_level))

        if clamped_level == 1:
            hint = (
                f"**Level 1 Hint (Gentle Nudge):** Carefully re-read the prompt for '{activity_context.title}'. "
                f"Identify the central term or condition being asked about."
            )
        elif clamped_level == 2:
            hint = (
                f"**Level 2 Hint (Conceptual Principle):** Remember the core rule from the lesson: "
                f"{activity_context.instructions.split('.')[0] if activity_context.instructions else 'apply the foundational definition'}. "
                f"Think about which options directly contradict this rule."
            )
        else:
            hint = (
                "**Level 3 Hint (Structural Guidance):** Eliminate choices that violate standards or edge-case constraints. "
                "Focus on the option that provides the most specific and accurate solution without side effects."
            )

        prompt_tokens = len(activity_context.instructions.split()) + 30
        completion_tokens = len(hint.split())

        return AIHintResponse(
            hint=hint,
            hint_level=clamped_level,
            max_level=3,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            provider="mock",
            model=self.model_name,
        )

    def review_communication(
        self,
        context: CommunicationFeedbackContext,
    ) -> AICommunicationFeedbackResponse:
        """Provide constructive qualitative writing guidance on BLUF or STAR submissions."""
        fmt = context.format.lower()
        if fmt == "bluf":
            summary = (
                f"Your BLUF communication demonstrates good intent for '{context.title}'. "
                f"Placing the key outcome directly up front ensures the reader immediately grasps the priority."
            )
            strengths = [
                "Clear statement of the primary conclusion or request.",
                "Organized structural separation between summary and context.",
            ]
            improvements = [
                "Consider refining the bottom line to be even more action-oriented.",
                "Ensure timelines or deadlines in next steps are explicit rather than implicit.",
            ]
            actionable_tips = [
                f"Start with a strong active verb: 'Requesting approval for...' or 'Notifying team of...' for audience '{context.audience or 'stakeholders'}'.",
                "Keep sentences under 25 words to maximize executive readability.",
            ]
        else:
            # STAR
            summary = (
                f"Structured STAR interview response for '{context.title}' covering "
                f"the {context.competency or 'target'} competency."
            )
            strengths = [
                "Followed the sequential four-part STAR framework.",
                "Described concrete actions taken rather than generic team efforts.",
            ]
            improvements = [
                "Quantify the Result section with specific metrics or percentage improvements if available.",
                "Clarify the initial challenge in Situation to contrast the positive outcome.",
            ]
            actionable_tips = [
                "Use the 'So that...' phrasing in Task to clarify the business stakes.",
                "Frame Results around long-term impact on team velocity or system reliability.",
            ]

        total_words = sum(len(txt.split()) for txt in context.learner_sections.values())
        prompt_tokens = total_words + 40
        completion_tokens = 90

        return AICommunicationFeedbackResponse(
            summary=summary,
            strengths=strengths,
            improvements=improvements,
            actionable_tips=actionable_tips,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            provider="mock",
            model=self.model_name,
        )
