"""Tests for AI tutoring, progressive hints, telemetry audit, and user opt-out."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.infrastructure.rate_limiter import limiter
from app.modules.activities.models import Activity, ActivityType
from app.modules.ai.models import AIInteraction
from app.modules.auth.models import User, UserRole
from app.modules.auth.security import hash_password
from app.modules.courses.models import (
    Course,
    CourseDifficulty,
    CourseStatus,
    CourseVersion,
    Lesson,
    LessonBlock,
    Module,
)
from app.modules.skills.models import Discipline


@pytest.fixture
def sample_lesson_with_activity(db: Session) -> tuple[str, str]:
    """Create a test course, module, lesson with content blocks, and an activity."""
    # 1. Creator user
    creator = User(
        email="ai_course_creator@example.com",
        password_hash=hash_password("SecureP@ss1"),
        role=UserRole.CREATOR,
    )
    db.add(creator)
    db.flush()

    # 2. Discipline
    disc = Discipline(slug="tech-ai", name="Technology", sort_order=1)
    db.add(disc)
    db.flush()

    # 3. Course
    course = Course(
        slug="ai-test-course",
        title="AI Test Course",
        short_description="Testing AI tutor integration",
        discipline_id=disc.id,
        creator_id=creator.id,
        difficulty_level=CourseDifficulty.BEGINNER,
        status=CourseStatus.PUBLISHED,
    )
    db.add(course)
    db.flush()

    cv = CourseVersion(
        course_id=course.id,
        version_number=1,
        title="AI Test Course v1",
        is_active=True,
    )
    db.add(cv)
    db.flush()

    mod = Module(
        course_version_id=cv.id,
        title="Module 1: Foundations",
        sort_order=1,
    )
    db.add(mod)
    db.flush()

    lesson = Lesson(
        module_id=mod.id,
        slug="foundations-lesson",
        title="Understanding Semantic HTML",
        description="Learn why semantic HTML is essential for accessible web apps.",
        learning_objectives=["Explain the accessibility tree", "Use header, main, and nav tags"],
        sort_order=1,
    )
    db.add(lesson)
    db.flush()

    block1 = LessonBlock(
        lesson_id=lesson.id,
        block_type="heading",
        content={"text": "Semantic Elements vs Generic Divs", "level": 2},
        sort_order=1,
    )
    block2 = LessonBlock(
        lesson_id=lesson.id,
        block_type="text",
        content={
            "text": "Semantic elements like <main> and <nav> allow assistive tools to understand page structure.",
            "format": "markdown",
        },
        sort_order=2,
    )
    db.add_all([block1, block2])
    db.flush()

    activity = Activity(
        lesson_id=lesson.id,
        activity_type=ActivityType.SINGLE_CHOICE,
        title="Identify Primary Landmark",
        instructions="Select the correct primary landmark element for page content.",
        configuration={
            "options": [
                {"id": "opt-main", "text": "<main> element"},
                {"id": "opt-div", "text": "<div id='main'>"},
            ]
        },
        max_attempts=3,
        sort_order=1,
    )
    db.add(activity)
    db.commit()

    return lesson.id, activity.id


class TestAITutor:
    """Test suite for AI tutor question answering, context assembly, and safeguards."""

    def test_ask_tutor_success(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        sample_lesson_with_activity: tuple[str, str],
        db: Session,
    ) -> None:
        lesson_id, _ = sample_lesson_with_activity

        resp = client.post(
            "/api/v1/ai/tutor",
            headers=auth_headers,
            json={
                "lesson_id": lesson_id,
                "message": "Can you explain why semantic HTML matters?",
            },
        )
        assert resp.status_code == 200
        data = resp.json()

        assert "reply" in data
        assert "suggestions" in data
        assert len(data["suggestions"]) > 0
        assert data["provider"] == "mock"
        assert data["tokens_used"] > 0
        # Check pedagogical grounding in lesson title
        assert "Understanding Semantic HTML" in data["reply"]

        # Verify operational telemetry in database without storing prompt content
        interactions = db.scalars(select(AIInteraction).where(AIInteraction.lesson_id == lesson_id)).all()
        assert len(interactions) == 1
        record = interactions[0]
        assert record.interaction_type == "tutor_query"
        assert record.status == "success"
        assert record.total_tokens > 0
        assert record.latency_ms >= 0

    def test_ask_tutor_unauthenticated(
        self, client: TestClient, sample_lesson_with_activity: tuple[str, str]
    ) -> None:
        lesson_id, _ = sample_lesson_with_activity
        resp = client.post(
            "/api/v1/ai/tutor",
            json={"lesson_id": lesson_id, "message": "Help me understand"},
        )
        assert resp.status_code == 401

    def test_ask_tutor_lesson_not_found(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        resp = client.post(
            "/api/v1/ai/tutor",
            headers=auth_headers,
            json={"lesson_id": "non-existent-lesson-uuid", "message": "Explain this"},
        )
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "LESSON_NOT_FOUND"

    def test_ask_tutor_rate_limiting(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        sample_lesson_with_activity: tuple[str, str],
    ) -> None:
        lesson_id, _ = sample_lesson_with_activity
        limiter.reset()

        # Execute requests up to the rate limit
        for _ in range(settings.ai_tutor_rate_limit):
            r = client.post(
                "/api/v1/ai/tutor",
                headers=auth_headers,
                json={"lesson_id": lesson_id, "message": "Quick question"},
            )
            assert r.status_code == 200

        # Request exceeding limit must be rejected with 429
        exceeded = client.post(
            "/api/v1/ai/tutor",
            headers=auth_headers,
            json={"lesson_id": lesson_id, "message": "One too many"},
        )
        assert exceeded.status_code == 429
        assert exceeded.json()["error"]["code"] == "RATE_LIMITED"
        assert "Retry-After" in exceeded.headers

        limiter.reset()

    def test_ask_tutor_opt_out_enforcement(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        sample_lesson_with_activity: tuple[str, str],
    ) -> None:
        lesson_id, _ = sample_lesson_with_activity

        # Enable AI opt-out for this learner
        pref_resp = client.post(
            "/api/v1/ai/preferences",
            headers=auth_headers,
            json={"ai_opt_out": True},
        )
        assert pref_resp.status_code == 200

        # Server must reject tutor request with 403 AI_FEATURE_OPTED_OUT
        resp = client.post(
            "/api/v1/ai/tutor",
            headers=auth_headers,
            json={"lesson_id": lesson_id, "message": "Should fail"},
        )
        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "AI_FEATURE_OPTED_OUT"

        # Re-enable and verify it works again
        client.post(
            "/api/v1/ai/preferences",
            headers=auth_headers,
            json={"ai_opt_out": False},
        )
        resp2 = client.post(
            "/api/v1/ai/tutor",
            headers=auth_headers,
            json={"lesson_id": lesson_id, "message": "Now should pass"},
        )
        assert resp2.status_code == 200


class TestActivityHints:
    """Test suite for progressive assessment hints without answer disclosure."""

    def test_progressive_hint_levels(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        sample_lesson_with_activity: tuple[str, str],
    ) -> None:
        lesson_id, activity_id = sample_lesson_with_activity

        # Level 1 hint
        h1 = client.post(
            "/api/v1/ai/hint",
            headers=auth_headers,
            json={"activity_id": activity_id, "lesson_id": lesson_id, "hint_level": 1},
        )
        assert h1.status_code == 200
        assert "Level 1 Hint" in h1.json()["hint"]
        assert h1.json()["hint_level"] == 1

        # Level 2 hint
        h2 = client.post(
            "/api/v1/ai/hint",
            headers=auth_headers,
            json={"activity_id": activity_id, "lesson_id": lesson_id, "hint_level": 2},
        )
        assert h2.status_code == 200
        assert "Level 2 Hint" in h2.json()["hint"]
        assert h2.json()["hint_level"] == 2

        # Level 3 hint
        h3 = client.post(
            "/api/v1/ai/hint",
            headers=auth_headers,
            json={"activity_id": activity_id, "lesson_id": lesson_id, "hint_level": 3},
        )
        assert h3.status_code == 200
        assert "Level 3 Hint" in h3.json()["hint"]
        assert h3.json()["hint_level"] == 3

    def test_hint_activity_not_found(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        resp = client.post(
            "/api/v1/ai/hint",
            headers=auth_headers,
            json={"activity_id": "non-existent-activity", "hint_level": 1},
        )
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "ACTIVITY_NOT_FOUND"


class TestAIStatusAndPreferences:
    """Test suite for status reporting and preference synchronization."""

    def test_ai_status_reporting(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        resp = client.get("/api/v1/ai/status", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["enabled"] is True
        assert data["provider"] == "mock"
        assert data["user_opted_out"] is False
        assert data["rate_limit_hourly"] == settings.ai_tutor_rate_limit
        assert data["remaining_tutor_requests"] >= 0
