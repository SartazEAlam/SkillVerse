"""Tests for specialized practice activity upgrades: web development, communication (BLUF/STAR),
and productivity simulations (multi-order and multi-pair workflows).
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.modules.activities.grading import (
    CommunicationGrader,
    GradingError,
    MatchingGrader,
    OrderingGrader,
    WebPracticeGrader,
    grading_engine,
)
from app.modules.activities.models import ActivityType

# ── 1. Web Development Practice Grader Unit Tests ────────────────────────────


def test_web_practice_valid_submission() -> None:
    """Valid repository, live demo, completed milestones, and reflection pass with 100%."""
    grader = WebPracticeGrader()
    config = {
        "require_repo_url": True,
        "require_live_url": True,
        "require_reflection": True,
        "milestones": [
            {"id": "m1", "title": "Create responsive HTML layout", "required": True},
            {"id": "m2", "title": "Style with CSS grid/flexbox", "required": True},
        ],
    }
    submission = {
        "repo_url": "https://github.com/learner/responsive-landing-page",
        "live_url": "https://landing-page-demo.vercel.app",
        "implementation_notes": "Built using semantic HTML5 and CSS Flexbox for mobile responsiveness.",
        "completed_milestone_ids": ["m1", "m2"],
        "reflection": "I learned how media queries ensure accessibility on narrow screens and touch devices.",
    }

    result = grader.grade(config, {}, submission, passing_score=70.0)
    assert result.passed is True
    assert result.score == 100.0
    assert result.result["url_validation"]["repo_url"] == "valid"
    assert result.result["url_validation"]["live_url"] == "valid"
    assert "not executed" in result.feedback["security_notice"]


def test_web_practice_rejects_unsafe_url_schemes() -> None:
    """Unsafe or executable URL schemes (javascript:, file:, data:) are strictly rejected."""
    grader = WebPracticeGrader()
    config = {"require_repo_url": True}

    for unsafe_url in [
        "javascript:alert('xss')",
        "file:///etc/passwd",
        "data:text/html,<script>evil()</script>",
        "ftp://example.com/repo",
        "https://",
    ]:
        with pytest.raises(GradingError) as exc_info:
            grader.grade(config, {}, {"repo_url": unsafe_url}, passing_score=70.0)
        assert exc_info.value.code in ("UNSAFE_URL_SCHEME", "INVALID_DOMAIN")


def test_web_practice_missing_required_repo_url() -> None:
    """Missing required repo URL raises GradingError."""
    grader = WebPracticeGrader()
    config = {"require_repo_url": True}

    with pytest.raises(GradingError) as exc_info:
        grader.grade(config, {}, {"repo_url": ""}, passing_score=70.0)
    assert exc_info.value.code == "MISSING_REPO_URL"


def test_web_practice_insufficient_reflection() -> None:
    """Short or empty reflection when required is rejected."""
    grader = WebPracticeGrader()
    config = {
        "require_repo_url": True,
        "require_reflection": True,
    }
    submission = {
        "repo_url": "https://github.com/learner/my-project",
        "reflection": "Good project.",  # Only 2 words, less than required 10
    }

    with pytest.raises(GradingError) as exc_info:
        grader.grade(config, {}, submission, passing_score=70.0)
    assert exc_info.value.code == "INSUFFICIENT_REFLECTION"


def test_web_practice_partial_milestone_scoring() -> None:
    """Completing only half of required milestones yields proportional partial credit."""
    grader = WebPracticeGrader()
    config = {
        "require_repo_url": True,
        "require_live_url": False,
        "require_reflection": False,
        "milestones": [
            {"id": "m1", "title": "Milestone 1", "required": True},
            {"id": "m2", "title": "Milestone 2", "required": True},
        ],
    }
    submission = {
        "repo_url": "https://github.com/learner/partial-project",
        "completed_milestone_ids": ["m1"],  # 1 of 2
    }

    result = grader.grade(config, {}, submission, passing_score=70.0)
    # Deliverables: 25 (repo) + 10 (not require live) = 35. Milestones: (1/2)*45 = 22.5. Reflection: 20. Total = 77.5
    assert result.score == 77.5
    assert result.passed is True


# ── 2. Communication Practice (BLUF and STAR) Unit Tests ────────────────────


def test_communication_bluf_valid_submission() -> None:
    """Valid BLUF response with concise bottom line and detailed context passes with 100%."""
    grader = CommunicationGrader()
    config = {
        "format": "bluf",
        "scenario": "Server outage during deployment cycle.",
        "audience": "VP of Engineering",
        "objective": "Status update and rollback approval",
    }
    submission = {
        "format": "bluf",
        "sections": {
            "bottom_line": "Requesting immediate approval to roll back release 2.4 to restore production stability.",
            "context_details": "At 14:15 UTC, latency spiked by 300% due to connection pool exhaustion in the new caching tier. Customer checkouts are currently degraded.",
            "next_steps": "Upon your sign-off, DevOps will execute the automated rollback script, with expected full recovery within 4 minutes.",
        },
        "reflection": "Leading with the bottom line eliminates uncertainty during urgent operational incidents.",
    }

    result = grader.grade(config, {}, submission, passing_score=70.0)
    assert result.passed is True
    assert result.score == 100.0
    assert result.result["format"] == "bluf"
    assert result.result["section_breakdown"]["bottom_line"]["meets_requirements"] is True
    assert "AI Writing Review" in result.feedback["qualitative_notice"]


def test_communication_bluf_missing_bottom_line() -> None:
    """BLUF submission missing bottom line is rejected."""
    grader = CommunicationGrader()
    config = {"format": "bluf"}
    submission = {
        "format": "bluf",
        "sections": {
            "context_details": "We had an issue with database indexes.",
            "next_steps": "Fixing it soon.",
        },
    }

    with pytest.raises(GradingError) as exc_info:
        grader.grade(config, {}, submission, passing_score=70.0)
    assert exc_info.value.code == "MISSING_BLUF"


def test_communication_bluf_too_short() -> None:
    """BLUF under 5 words is rejected for lack of substance."""
    grader = CommunicationGrader()
    config = {"format": "bluf"}
    submission = {
        "format": "bluf",
        "sections": {
            "bottom_line": "Servers down.",  # Only 2 words
            "context_details": "Detailed context here explaining the outage thoroughly.",
            "next_steps": "We will restart servers now.",
        },
    }

    with pytest.raises(GradingError) as exc_info:
        grader.grade(config, {}, submission, passing_score=70.0)
    assert exc_info.value.code == "BLUF_TOO_SHORT"


def test_communication_star_valid_submission() -> None:
    """Valid STAR interview response covering Situation, Task, Action, Result passes with 100%."""
    grader = CommunicationGrader()
    config = {
        "format": "star",
        "competency": "Conflict Resolution",
    }
    submission = {
        "format": "star",
        "sections": {
            "situation": "During our quarterly migration sprint, our frontend and backend teams disagreed on API contracts, creating an integration bottleneck.",
            "task": "As technical lead, I needed to align both teams on a unified OpenAPI specification within 48 hours without slipping sprint velocity.",
            "action": "I convened a focused contract-first design workshop where we defined schemas collaboratively, generated mock endpoints immediately, and unblocked frontend developers.",
            "result": "Both teams integrated seamlessly two days ahead of schedule, with zero runtime payload contract regressions in QA.",
        },
    }

    result = grader.grade(config, {}, submission, passing_score=70.0)
    assert result.passed is True
    assert result.score == 100.0
    assert result.result["format"] == "star"
    for sec in ["situation", "task", "action", "result"]:
        assert result.result["section_breakdown"][sec]["meets_requirements"] is True


def test_communication_star_incomplete_penalized() -> None:
    """STAR response with missing or brief sections receives reduced score."""
    grader = CommunicationGrader()
    config = {"format": "star"}
    submission = {
        "format": "star",
        "sections": {
            "situation": "Our legacy servers were running low on disk space frequently.",
            "task": "Clean up logs.",  # Too short (< 5 words)
            "action": "I wrote a cron job to rotate files.",  # Short
            # 'result' missing!
        },
    }

    result = grader.grade(config, {}, submission, passing_score=70.0)
    assert result.score < 70.0
    assert result.passed is False


# ── 3. Productivity Simulations (Ordering & Matching) Unit Tests ─────────────


def test_ordering_grader_multiple_acceptable_orders() -> None:
    """Ordering grader accepts multiple valid workflows / topological sorts."""
    grader = OrderingGrader()
    config = {
        "items": [
            {"id": "task_a", "text": "Set up database schema"},
            {"id": "task_b", "text": "Write API endpoints"},
            {"id": "task_c", "text": "Build UI components"},
            {"id": "task_d", "text": "End-to-end testing"},
        ]
    }
    # Both [A, B, C, D] (backend-first) and [A, C, B, D] (UI-first) are valid workflows!
    answer_key = {
        "acceptable_orders": [
            ["task_a", "task_b", "task_c", "task_d"],
            ["task_a", "task_c", "task_b", "task_d"],
        ]
    }

    # Order 1 matches
    res1 = grader.grade(config, answer_key, {"ordered_item_ids": ["task_a", "task_b", "task_c", "task_d"]}, 70.0)
    assert res1.passed is True
    assert res1.score == 100.0
    assert res1.result["is_exact_match"] is True

    # Order 2 also matches!
    res2 = grader.grade(config, answer_key, {"ordered_item_ids": ["task_a", "task_c", "task_b", "task_d"]}, 70.0)
    assert res2.passed is True
    assert res2.score == 100.0
    assert res2.result["is_exact_match"] is True


def test_matching_grader_multi_target_acceptable_pairs() -> None:
    """Matching grader supports multi-target acceptable pairs when tasks map to multiple tools."""
    grader = MatchingGrader()
    config = {
        "left_items": [
            {"id": "task_containerize", "text": "Containerize microservice"},
            {"id": "task_version_control", "text": "Version control source code"},
        ],
        "right_items": [
            {"id": "tool_docker", "text": "Docker"},
            {"id": "tool_podman", "text": "Podman"},
            {"id": "tool_git", "text": "Git"},
        ],
    }
    answer_key = {
        "acceptable_pairs": {
            "task_containerize": ["tool_docker", "tool_podman"],  # Either Docker or Podman is correct!
            "task_version_control": ["tool_git"],
        }
    }

    # Match with Docker
    res_docker = grader.grade(
        config,
        answer_key,
        {"pairs": {"task_containerize": "tool_docker", "task_version_control": "tool_git"}},
        70.0,
    )
    assert res_docker.score == 100.0
    assert res_docker.passed is True

    # Match with Podman
    res_podman = grader.grade(
        config,
        answer_key,
        {"pairs": {"task_containerize": "tool_podman", "task_version_control": "tool_git"}},
        70.0,
    )
    assert res_podman.score == 100.0
    assert res_podman.passed is True


# ── 4. Unified GradingEngine Dispatcher ──────────────────────────────────────


def test_grading_engine_dispatches_new_activity_types() -> None:
    """GradingEngine correctly dispatches to WebPracticeGrader and CommunicationGrader."""
    # Web practice dispatch
    web_res = grading_engine.grade(
        ActivityType.WEB_PRACTICE,
        {"require_repo_url": True, "require_live_url": False, "require_reflection": False},
        {},
        {"repo_url": "https://github.com/example/repo"},
        70.0,
    )
    assert web_res.status.value == "graded"

    # Communication dispatch
    comm_res = grading_engine.grade(
        ActivityType.COMMUNICATION,
        {"format": "bluf"},
        {},
        {
            "format": "bluf",
            "sections": {
                "bottom_line": "Action requested: Approve project proposal.",
                "context_details": "Detailed context provided for the proposal.",
                "next_steps": "Schedule review meeting on Thursday.",
            },
        },
        70.0,
    )
    assert comm_res.status.value == "graded"


# ── 5. End-to-End API Integration & AI Review Tests ─────────────────────────


@pytest.fixture
def test_activity_course_setup(client: TestClient, creator_headers: dict[str, str]) -> dict[str, str]:
    """Create web practice and communication practice activities via authoring API."""
    res_web = client.post(
        "/api/v1/activities",
        json={
            "activity_type": "web_practice",
            "title": "Build a Portfolio Showcase Component",
            "instructions": "Implement a responsive component and share the repository.",
            "configuration": {
                "require_repo_url": True,
                "require_live_url": False,
                "require_reflection": True,
                "milestones": [{"id": "m1", "title": "Component Design", "required": True}],
            },
            "passing_score": 70.0,
            "answer_key": {},
        },
        headers=creator_headers,
    )
    assert res_web.status_code == 201, res_web.text
    web_act_id = res_web.json()["id"]

    res_comm = client.post(
        "/api/v1/activities",
        json={
            "activity_type": "communication",
            "title": "Urgent Incident Executive Summary",
            "instructions": "Provide a concise BLUF executive communication.",
            "configuration": {
                "format": "bluf",
                "scenario": "Payment gateway latency elevated.",
                "audience": "VP of Engineering",
                "objective": "Rollback sign-off",
            },
            "passing_score": 70.0,
            "answer_key": {},
        },
        headers=creator_headers,
    )
    assert res_comm.status_code == 201, res_comm.text
    comm_act_id = res_comm.json()["id"]

    return {
        "web_activity_id": web_act_id,
        "comm_activity_id": comm_act_id,
    }


def test_submit_web_practice_activity_api(
    client: TestClient,
    auth_headers: dict[str, str],
    test_activity_course_setup: dict[str, str],
) -> None:
    """Submit attempt on web development practice via API."""
    act_id = test_activity_course_setup["web_activity_id"]

    sub_payload = {
        "submission": {
            "repo_url": "https://github.com/my-user/portfolio-component",
            "implementation_notes": "Implemented with Tailwind CSS and React hooks.",
            "completed_milestone_ids": ["m1"],
            "reflection": "Structuring modular components improved reusability across pages and simplified state management for future extensions.",
        }
    }
    res = client.post(f"/api/v1/activities/{act_id}/attempts", json=sub_payload, headers=auth_headers)
    assert res.status_code == 201
    data = res.json()
    assert data["passed"] is True
    assert data["score"] >= 70.0
    assert "not executed" in data["feedback"]["security_notice"]


def test_submit_communication_practice_api(
    client: TestClient,
    auth_headers: dict[str, str],
    test_activity_course_setup: dict[str, str],
) -> None:
    """Submit attempt on communication practice via API."""
    act_id = test_activity_course_setup["comm_activity_id"]

    sub_payload = {
        "submission": {
            "format": "bluf",
            "sections": {
                "bottom_line": "Requesting immediate sign-off to switch traffic to backup payment gateway.",
                "context_details": "Primary provider is returning 504 Gateway Timeouts on 45% of transactions since 10:00 UTC.",
                "next_steps": "Failover takes 90 seconds once approved, restoring transaction flow.",
            },
            "reflection": "Using BLUF ensured executive stakeholders didn't have to wade through technical logs to make a decision.",
        }
    }
    res = client.post(f"/api/v1/activities/{act_id}/attempts", json=sub_payload, headers=auth_headers)
    assert res.status_code == 201
    data = res.json()
    assert data["passed"] is True
    assert data["result"]["format"] == "bluf"
    assert "AI Writing Review" in data["feedback"]["qualitative_notice"]


def test_ai_communication_feedback_api(
    client: TestClient,
    auth_headers: dict[str, str],
    test_activity_course_setup: dict[str, str],
) -> None:
    """Request qualitative AI review for communication submission."""
    act_id = test_activity_course_setup["comm_activity_id"]

    ai_payload = {
        "activity_id": act_id,
        "sections": {
            "bottom_line": "Requesting approval to migrate services to new cluster.",
            "context_details": "Old cluster is approaching resource limits.",
            "next_steps": "Will schedule migration for 02:00 UTC.",
        },
        "reflection": "Clear and concise.",
    }
    res = client.post("/api/v1/ai/communication-feedback", json=ai_payload, headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "summary" in data
    assert len(data["strengths"]) > 0
    assert len(data["improvements"]) > 0
    assert len(data["actionable_tips"]) > 0
    assert data["provider"] == "mock"


def test_ai_communication_feedback_respects_opt_out(
    client: TestClient,
    auth_headers: dict[str, str],
    test_activity_course_setup: dict[str, str],
) -> None:
    """Opted-out users receive 403 Forbidden when requesting communication feedback."""
    act_id = test_activity_course_setup["comm_activity_id"]

    # Opt out
    client.post("/api/v1/ai/preferences", json={"ai_opt_out": True}, headers=auth_headers)

    ai_payload = {
        "activity_id": act_id,
        "sections": {"bottom_line": "Requesting sign-off."},
    }
    res = client.post("/api/v1/ai/communication-feedback", json=ai_payload, headers=auth_headers)
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "AI_FEATURE_OPTED_OUT"

    # Reset opt-out
    client.post("/api/v1/ai/preferences", json={"ai_opt_out": False}, headers=auth_headers)
