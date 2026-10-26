"""Tests for interactive activities, deterministic grading engine, attempts, and security."""

from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.modules.activities.grading import (
    CodingGrader,
    FillBlankGrader,
    GradingError,
    MatchingGrader,
    MultipleSelectGrader,
    OrderingGrader,
    ScenarioGrader,
    ShortAnswerGrader,
    SingleChoiceGrader,
    TrueFalseGrader,
)
from app.modules.activities.models import AttemptStatus
from app.modules.activities.service import ActivityServiceError
from app.modules.auth.models import User
from app.modules.courses.models import (
    Course,
    CourseSkill,
    CourseStatus,
    CourseVersion,
    Lesson,
    Module,
)
from app.modules.skills.models import Discipline, Skill, SkillDifficulty

# ══════════════════════════════════════════════════════════════════════════════
# UNIT TESTS: DETERMINISTIC GRADING STRATEGIES
# ══════════════════════════════════════════════════════════════════════════════


class TestGradingStrategies:
    """Unit tests for each deterministic activity grader."""

    def test_single_choice_grading(self) -> None:
        grader = SingleChoiceGrader()
        config = {
            "options": [
                {"id": "opt-1", "text": "Semantic <header>"},
                {"id": "opt-2", "text": "Non-semantic <div class='header'>"},
            ]
        }
        answer_key = {"correct_option_id": "opt-1"}

        # Correct
        res = grader.grade(config, answer_key, {"selected_option_id": "opt-1"}, 70.0)
        assert res.score == 100.0
        assert res.passed is True
        assert res.status == AttemptStatus.GRADED

        # Incorrect
        res_wrong = grader.grade(config, answer_key, {"selected_option_id": "opt-2"}, 70.0)
        assert res_wrong.score == 0.0
        assert res_wrong.passed is False

        # Invalid option ID rejected
        with pytest.raises(GradingError) as exc_info:
            grader.grade(config, answer_key, {"selected_option_id": "invalid-opt"}, 70.0)
        assert exc_info.value.code == "UNKNOWN_OPTION_ID"

    def test_multiple_select_grading_and_partial_credit(self) -> None:
        grader = MultipleSelectGrader()
        config = {
            "options": [
                {"id": "a", "text": "<header>"},
                {"id": "b", "text": "<main>"},
                {"id": "c", "text": "<div>"},
            ]
        }
        answer_key = {"correct_option_ids": ["a", "b"]}

        # All correct
        res = grader.grade(config, answer_key, {"selected_option_ids": ["a", "b"]}, 70.0)
        assert res.score == 100.0
        assert res.passed is True

        # Partial correct (1 correct, 0 incorrect: 1/2 = 50%)
        res_part = grader.grade(config, answer_key, {"selected_option_ids": ["a"]}, 70.0)
        assert res_part.score == 50.0
        assert res_part.passed is False

        # With incorrect penalty (1 correct, 1 incorrect: 1/2 - 1/2 = 0%)
        res_pen = grader.grade(config, answer_key, {"selected_option_ids": ["a", "c"]}, 70.0)
        assert res_pen.score == 0.0

        # Non-list selection rejected
        with pytest.raises(GradingError) as exc_info:
            grader.grade(config, answer_key, {"selected_option_ids": "not-a-list"}, 70.0)
        assert exc_info.value.code == "INVALID_SUBMISSION"

    def test_true_false_grading(self) -> None:
        grader = TrueFalseGrader()
        config = {"statement": "<main> can appear multiple times per page without hidden attribute."}
        answer_key = {"correct_boolean": False}

        res_correct = grader.grade(config, answer_key, {"selected_boolean": False}, 70.0)
        assert res_correct.score == 100.0
        assert res_correct.passed is True

        res_incorrect = grader.grade(config, answer_key, {"selected_boolean": True}, 70.0)
        assert res_incorrect.score == 0.0
        assert res_incorrect.passed is False

    def test_short_answer_normalization(self) -> None:
        grader = ShortAnswerGrader()
        config = {"prompt": "What HTML attribute connects a label to an input?"}
        answer_key = {"accepted_answers": ["for", "htmlFor"], "case_sensitive": False}

        # Case-insensitive whitespace normalized
        res = grader.grade(config, answer_key, {"text": "   FOR   "}, 70.0)
        assert res.score == 100.0
        assert res.passed is True

        # Incorrect answer
        res_wrong = grader.grade(config, answer_key, {"text": "name"}, 70.0)
        assert res_wrong.score == 0.0
        assert res_wrong.passed is False

        # Empty string rejected
        with pytest.raises(GradingError):
            grader.grade(config, answer_key, {"text": "   "}, 70.0)

    def test_short_answer_manual_review_mode(self) -> None:
        grader = ShortAnswerGrader()
        config = {"prompt": "Explain why accessibility improves SEO."}
        answer_key = {"review_required": True}

        res = grader.grade(
            config,
            answer_key,
            {"text": "Semantic markup helps search engine crawlers understand structure."},
            70.0,
        )
        assert res.status == AttemptStatus.REVIEW_REQUIRED
        assert res.score is None
        assert res.passed is None

    def test_fill_in_the_blank_grading(self) -> None:
        grader = FillBlankGrader()
        config = {
            "template": "A [blank1] element defines navigation, while [blank2] defines the main content.",
            "blanks": [{"id": "blank1"}, {"id": "blank2"}],
        }
        answer_key = {
            "blanks": {
                "blank1": {"accepted_answers": ["nav", "<nav>"], "case_sensitive": False},
                "blank2": {"accepted_answers": ["main", "<main>"], "case_sensitive": False},
            }
        }

        # Both correct
        res = grader.grade(config, answer_key, {"answers": {"blank1": "NAV", "blank2": "main"}}, 70.0)
        assert res.score == 100.0
        assert res.passed is True

        # One correct (50%)
        res_half = grader.grade(config, answer_key, {"answers": {"blank1": "NAV", "blank2": "article"}}, 70.0)
        assert res_half.score == 50.0
        assert res_half.passed is False

    def test_ordering_grading(self) -> None:
        grader = OrderingGrader()
        config = {
            "items": [
                {"id": "step-1", "text": "Plan structure"},
                {"id": "step-2", "text": "Draft semantic markup"},
                {"id": "step-3", "text": "Run axe accessibility audit"},
            ]
        }
        answer_key = {"correct_order": ["step-1", "step-2", "step-3"]}

        # Correct
        res = grader.grade(config, answer_key, {"ordered_item_ids": ["step-1", "step-2", "step-3"]}, 70.0)
        assert res.score == 100.0
        assert res.passed is True

        # Incomplete items rejected
        with pytest.raises(GradingError) as exc_info:
            grader.grade(config, answer_key, {"ordered_item_ids": ["step-1", "step-2"]}, 70.0)
        assert exc_info.value.code == "INVALID_ITEM_SET"

    def test_matching_grading(self) -> None:
        grader = MatchingGrader()
        config = {
            "left_items": [{"id": "s1", "text": "<header>"}, {"id": "s2", "text": "<footer>"}],
            "right_items": [{"id": "t1", "text": "Introductory content"}, {"id": "t2", "text": "Copyright and links"}],
        }
        answer_key = {"pairs": {"s1": "t1", "s2": "t2"}}

        # All match
        res = grader.grade(config, answer_key, {"pairs": {"s1": "t1", "s2": "t2"}}, 70.0)
        assert res.score == 100.0
        assert res.passed is True

        # 1 match (50%)
        res_part = grader.grade(config, answer_key, {"pairs": {"s1": "t1", "s2": "t1"}}, 70.0)
        assert res_part.score == 50.0

    def test_scenario_grading(self) -> None:
        grader = ScenarioGrader()
        config = {
            "decisions": [
                {"id": "dec-best", "title": "Acknowledge and summarize the client's concern."},
                {"id": "dec-bad", "title": "Interrupt and defend the initial specification."},
            ]
        }
        answer_key = {
            "best_decision_id": "dec-best",
            "acceptable_decision_ids": [],
        }

        res = grader.grade(config, answer_key, {"selected_decision_id": "dec-best"}, 70.0)
        assert res.score == 100.0
        assert res.passed is True
        assert "Optimal decision" in res.feedback["message"]

    def test_coding_grader_sandbox_boundary(self) -> None:
        grader = CodingGrader()
        config = {"language": "python", "starter_code": "def solve():\n    pass"}
        answer_key = {"test_cases": [{"input": "2", "expected_output": "4"}]}

        # When sandbox service is not connected, fails safely without executing in host process
        res = grader.grade(config, answer_key, {"code": "def solve(): return 4"}, 70.0)
        assert res.status == AttemptStatus.SUBMITTED
        assert res.score is None
        assert "containerized sandbox runner" in res.feedback["message"]


# ══════════════════════════════════════════════════════════════════════════════
# INTEGRATION TESTS: FASTAPI ENDPOINTS & AUTHORIZATION
# ══════════════════════════════════════════════════════════════════════════════


class TestActivityAPI:
    """Integration tests for activity creation, viewing, submission, and security."""

    def test_create_and_get_public_activity(
        self, client: TestClient, creator_headers: dict[str, str]
    ) -> None:
        """Confidential answer keys must never be returned in public endpoints."""
        payload = {
            "activity_type": "single_choice",
            "title": "Accessible Form Labels",
            "instructions": "Select the correct landmark element for primary page content.",
            "configuration": {
                "options": [
                    {"id": "opt-main", "text": "<main>"},
                    {"id": "opt-div", "text": "<div id='content'>"},
                ]
            },
            "max_attempts": 3,
            "sort_order": 1,
            "passing_score": 70.0,
            "answer_key": {"correct_option_id": "opt-main"},
        }

        # 1. Creator creates activity
        create_res = client.post("/api/v1/activities", json=payload, headers=creator_headers)
        assert create_res.status_code == 201
        data = create_res.json()
        activity_id = data["id"]
        assert data["title"] == "Accessible Form Labels"
        assert "answer_key" not in data  # Never leaked

        # 2. Public unauthenticated learner fetches activity
        get_res = client.get(f"/api/v1/activities/{activity_id}")
        assert get_res.status_code == 200
        pub_data = get_res.json()
        assert pub_data["id"] == activity_id
        assert pub_data["configuration"]["options"][0]["id"] == "opt-main"
        assert "answer_key" not in pub_data  # Confidential key stripped!

    def test_submit_attempt_and_enforce_retry_limit(
        self, client: TestClient, creator_headers: dict[str, str], auth_headers: dict[str, str]
    ) -> None:
        """Learner can submit attempts until max_attempts limit is reached."""
        # Create activity with max_attempts = 2
        act_res = client.post(
            "/api/v1/activities",
            json={
                "activity_type": "single_choice",
                "title": "HTML Landmark Test",
                "instructions": "Pick the element.",
                "configuration": {
                    "options": [
                        {"id": "a", "text": "Option A"},
                        {"id": "b", "text": "Option B"},
                    ]
                },
                "max_attempts": 2,
                "passing_score": 70.0,
                "answer_key": {"correct_option_id": "a"},
            },
            headers=creator_headers,
        )
        activity_id = act_res.json()["id"]

        # Attempt 1 (wrong answer)
        att1_res = client.post(
            f"/api/v1/activities/{activity_id}/attempts",
            json={"submission": {"selected_option_id": "b"}},
            headers=auth_headers,
        )
        assert att1_res.status_code == 201
        att1_data = att1_res.json()
        assert att1_data["attempt_number"] == 1
        assert att1_data["score"] == 0.0
        assert att1_data["passed"] is False
        assert att1_data["can_retry"] is True
        assert att1_data["attempts_remaining"] == 1

        # Attempt 2 (correct answer)
        att2_res = client.post(
            f"/api/v1/activities/{activity_id}/attempts",
            json={"submission": {"selected_option_id": "a"}},
            headers=auth_headers,
        )
        assert att2_res.status_code == 201
        att2_data = att2_res.json()
        assert att2_data["attempt_number"] == 2
        assert att2_data["score"] == 100.0
        assert att2_data["passed"] is True
        assert att2_data["can_retry"] is False
        assert att2_data["attempts_remaining"] == 0

        # Attempt 3 (exceeds max_attempts)
        att3_res = client.post(
            f"/api/v1/activities/{activity_id}/attempts",
            json={"submission": {"selected_option_id": "a"}},
            headers=auth_headers,
        )
        assert att3_res.status_code == 400
        err = att3_res.json()["error"]
        assert err["code"] == "RETRY_LIMIT_EXCEEDED"

    def test_unauthenticated_submission_rejected(self, client: TestClient) -> None:
        """Unauthenticated submissions must return 401."""
        res = client.post(
            "/api/v1/activities/any-uuid/attempts",
            json={"submission": {"selected_option_id": "opt-1"}},
        )
        assert res.status_code == 401

    def test_cross_user_attempt_authorization(
        self, client: TestClient, creator_headers: dict[str, str], auth_headers: dict[str, str]
    ) -> None:
        """A learner cannot view another learner's private attempt details."""
        # Create activity
        act_res = client.post(
            "/api/v1/activities",
            json={
                "activity_type": "true_false",
                "title": "TF Quiz",
                "instructions": "Answer true or false.",
                "configuration": {"statement": "CSS is for styling."},
                "answer_key": {"correct_boolean": True},
            },
            headers=creator_headers,
        )
        activity_id = act_res.json()["id"]

        # User A submits attempt
        att_res = client.post(
            f"/api/v1/activities/{activity_id}/attempts",
            json={"submission": {"selected_boolean": True}},
            headers=auth_headers,
        )
        assert att_res.status_code == 201
        attempt_id = att_res.json()["id"]

        # Register User B
        client.post(
            "/api/v1/auth/register",
            json={"email": "user_b@example.com", "password": "SecureP@ss1", "display_name": "User B"},
        )
        login_b = client.post(
            "/api/v1/auth/login",
            json={"email": "user_b@example.com", "password": "SecureP@ss1"},
        )
        user_b_headers = {"Authorization": f"Bearer {login_b.json()['access_token']}"}

        # User B attempts to access User A's attempt
        res_b = client.get(
            f"/api/v1/activities/{activity_id}/attempts/{attempt_id}",
            headers=user_b_headers,
        )
        assert res_b.status_code == 403
        assert res_b.json()["error"]["code"] == "FORBIDDEN"

    def test_create_activity_with_invalid_lesson_id_fails(
        self, client: TestClient, creator_headers: dict[str, str], db: Session
    ) -> None:
        """Creating an activity with a nonexistent lesson ID must return 404 and persist nothing."""
        from sqlalchemy import select

        from app.modules.activities.models import Activity

        res = client.post(
            "/api/v1/activities",
            json={
                "lesson_id": "00000000-0000-0000-0000-000000000000",
                "activity_type": "single_choice",
                "title": "Orphan Activity Attempt",
                "instructions": "Should fail validation.",
                "configuration": {
                    "options": [
                        {"id": "a", "text": "Option A"},
                        {"id": "b", "text": "Option B"},
                    ]
                },
                "answer_key": {"correct_option_id": "a"},
            },
            headers=creator_headers,
        )
        assert res.status_code == 404
        assert res.json()["error"]["code"] == "LESSON_NOT_FOUND"

        # Verify no activity was persisted in the database
        saved = db.scalars(
            select(Activity).where(Activity.title == "Orphan Activity Attempt")
        ).first()
        assert saved is None

    def test_list_lesson_activities_with_invalid_lesson_id_fails(
        self, client: TestClient
    ) -> None:
        """Listing activities for a nonexistent lesson ID must return 404."""
        res = client.get("/api/v1/lessons/nonexistent-lesson-uuid/activities")
        assert res.status_code == 404
        assert res.json()["error"]["code"] == "LESSON_NOT_FOUND"

    def test_submit_attempt_with_invalid_activity_id_fails(
        self, client: TestClient, auth_headers: dict[str, str], db: Session
    ) -> None:
        """Submitting an attempt for a nonexistent activity must return 404 and persist no attempt."""
        from sqlalchemy import select

        from app.modules.activities.models import Attempt

        res = client.post(
            "/api/v1/activities/00000000-0000-0000-0000-000000000000/attempts",
            json={"submission": {"selected_option_id": "a"}},
            headers=auth_headers,
        )
        assert res.status_code == 404
        assert res.json()["error"]["code"] == "ACTIVITY_NOT_FOUND"

        # Verify no attempt was persisted
        attempts = db.scalars(
            select(Attempt).where(Attempt.activity_id == "00000000-0000-0000-0000-000000000000")
        ).all()
        assert len(attempts) == 0

    def test_concurrent_submission_integrity_handling(
        self, client: TestClient, creator_headers: dict[str, str], auth_headers: dict[str, str]
    ) -> None:
        """Concurrent submissions that trigger IntegrityError must return HTTP 409 Conflict."""
        from unittest.mock import patch


        # Create valid activity
        act_res = client.post(
            "/api/v1/activities",
            json={
                "activity_type": "true_false",
                "title": "Concurrency Protection Check",
                "instructions": "Test concurrent attempt race conditions.",
                "configuration": {"statement": "Concurrency is handled properly."},
                "answer_key": {"correct_boolean": True},
            },
            headers=creator_headers,
        )
        activity_id = act_res.json()["id"]

        # Simulate IntegrityError on db.commit() during submit_attempt
        with patch(
            "app.modules.activities.service.ActivityService.submit_attempt",
            side_effect=ActivityServiceError(
                "A concurrent submission for this attempt is already being processed. Please refresh and try again.",
                code="CONCURRENT_SUBMISSION",
                status_code=409,
            ),
        ):
            res = client.post(
                f"/api/v1/activities/{activity_id}/attempts",
                json={"submission": {"selected_boolean": True}},
                headers=auth_headers,
            )
            assert res.status_code == 409
            assert res.json()["error"]["code"] == "CONCURRENT_SUBMISSION"

    def test_service_submit_attempt_rollback_on_integrity_error(
        self, db: Session, client: TestClient, creator_headers: dict[str, str]
    ) -> None:
        """ActivityService must catch IntegrityError, rollback transaction, and raise 409 CONCURRENT_SUBMISSION."""
        from unittest.mock import patch

        from sqlalchemy.exc import IntegrityError

        from app.modules.activities.service import ActivityService, ActivityServiceError

        act_res = client.post(
            "/api/v1/activities",
            json={
                "activity_type": "true_false",
                "title": "Service Concurrency Rollback Check",
                "instructions": "Test direct service rollback.",
                "configuration": {"statement": "Transactional rollback works."},
                "answer_key": {"correct_boolean": True},
            },
            headers=creator_headers,
        )
        activity_id = act_res.json()["id"]

        service = ActivityService(db)
        with patch.object(
            db,
            "commit",
            side_effect=IntegrityError("duplicate key", params=None, orig=Exception("UNIQUE constraint failed: uq_user_activity_attempt")),
        ):
            with pytest.raises(ActivityServiceError) as exc_info:
                service.submit_attempt(
                    activity_id=activity_id,
                    user_id="test-user-id",
                    submission={"selected_boolean": True},
                )
            assert exc_info.value.status_code == 409
            assert exc_info.value.code == "CONCURRENT_SUBMISSION"


# ══════════════════════════════════════════════════════════════════════════════
# REGRESSION TESTS: ACTIVITY-TO-SKILL ATTRIBUTION VALIDATION
# ══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def course_skills_setup(db: Session, creator_headers: dict[str, str]) -> dict[str, Any]:
    creator = db.query(User).filter(User.email == "creator@example.com").first()

    disc = Discipline(slug="web-dev-discipline", name="Web Development", sort_order=1)
    db.add(disc)
    db.flush()

    skill_html = Skill(
        slug="html-basics",
        name="HTML Basics",
        discipline_id=disc.id,
        difficulty_level=SkillDifficulty.FOUNDATIONAL,
        is_active=True,
    )
    skill_css = Skill(
        slug="css-styling",
        name="CSS Styling",
        discipline_id=disc.id,
        difficulty_level=SkillDifficulty.INTERMEDIATE,
        is_active=True,
    )
    skill_python = Skill(
        slug="python-core",
        name="Python Core",
        discipline_id=disc.id,
        difficulty_level=SkillDifficulty.FOUNDATIONAL,
        is_active=True,
    )
    skill_inactive = Skill(
        slug="deprecated-tech",
        name="Deprecated Tech",
        discipline_id=disc.id,
        difficulty_level=SkillDifficulty.FOUNDATIONAL,
        is_active=False,
    )
    db.add_all([skill_html, skill_css, skill_python, skill_inactive])
    db.flush()

    # Course A teaches html-basics and css-styling
    course_a = Course(
        slug="intro-web-course",
        title="Intro to Web",
        short_description="Learn HTML and CSS",
        discipline_id=disc.id,
        status=CourseStatus.PUBLISHED,
        creator_id=creator.id,
    )
    db.add(course_a)
    db.flush()

    cs_html = CourseSkill(course_id=course_a.id, skill_id=skill_html.id, is_primary=True)
    cs_css = CourseSkill(course_id=course_a.id, skill_id=skill_css.id, is_primary=False)
    db.add_all([cs_html, cs_css])

    ver_a = CourseVersion(
        course_id=course_a.id,
        version_number=1,
        title="Intro to Web v1",
        is_active=True,
    )
    db.add(ver_a)
    db.flush()
    course_a.current_version_id = ver_a.id

    mod_a = Module(course_version_id=ver_a.id, title="Web Module 1", sort_order=1)
    db.add(mod_a)
    db.flush()

    lesson_a = Lesson(module_id=mod_a.id, slug="html-lesson", title="HTML Lesson", sort_order=1)
    db.add(lesson_a)
    db.flush()

    # Course B teaches python-core
    course_b = Course(
        slug="intro-python-course",
        title="Intro to Python",
        short_description="Learn Python",
        discipline_id=disc.id,
        status=CourseStatus.PUBLISHED,
        creator_id=creator.id,
    )
    db.add(course_b)
    db.flush()

    cs_py = CourseSkill(course_id=course_b.id, skill_id=skill_python.id, is_primary=True)
    db.add(cs_py)

    ver_b = CourseVersion(
        course_id=course_b.id,
        version_number=1,
        title="Intro to Python v1",
        is_active=True,
    )
    db.add(ver_b)
    db.flush()
    course_b.current_version_id = ver_b.id

    mod_b = Module(course_version_id=ver_b.id, title="Python Module 1", sort_order=1)
    db.add(mod_b)
    db.flush()

    lesson_b = Lesson(module_id=mod_b.id, slug="python-lesson", title="Python Lesson", sort_order=1)
    db.add(lesson_b)
    db.commit()

    return {
        "discipline": disc,
        "skill_html": skill_html,
        "skill_css": skill_css,
        "skill_python": skill_python,
        "skill_inactive": skill_inactive,
        "course_a": course_a,
        "course_b": course_b,
        "lesson_a": lesson_a,
        "lesson_b": lesson_b,
    }


class TestActivitySkillTagValidation:
    """Regression tests for activity-to-skill attribution validation."""

    def test_valid_skill_tag_belonging_to_course(
        self,
        client: TestClient,
        creator_headers: dict[str, str],
        course_skills_setup: dict[str, Any],
    ) -> None:
        """Creating an activity with a valid skill belonging to the course succeeds and canonicalizes tags."""
        lesson_id = course_skills_setup["lesson_a"].id
        skill_html = course_skills_setup["skill_html"]
        skill_css = course_skills_setup["skill_css"]

        # 1. With explicit skill_id and skill_slug matching
        res1 = client.post(
            "/api/v1/activities",
            json={
                "lesson_id": lesson_id,
                "activity_type": "true_false",
                "title": "HTML Semantics Check",
                "instructions": "Identify valid semantic elements.",
                "configuration": {"statement": "<article> is a semantic element."},
                "answer_key": {"correct_boolean": True},
                "skill_id": skill_html.id,
                "skill_slug": skill_html.slug,
            },
            headers=creator_headers,
        )
        assert res1.status_code == 201
        data1 = res1.json()
        assert data1["skill_id"] == skill_html.id
        assert data1["skill_slug"] == "html-basics"
        assert data1["configuration"]["skill_id"] == skill_html.id
        assert data1["configuration"]["skill_slug"] == "html-basics"

        # 2. With skill_id only -> resolves and canonicalizes skill_slug
        res2 = client.post(
            "/api/v1/activities",
            json={
                "lesson_id": lesson_id,
                "activity_type": "true_false",
                "title": "CSS Styling Check",
                "instructions": "Identify CSS concepts.",
                "configuration": {"statement": "CSS grid is two-dimensional."},
                "answer_key": {"correct_boolean": True},
                "skill_id": skill_css.id,
            },
            headers=creator_headers,
        )
        assert res2.status_code == 201
        data2 = res2.json()
        assert data2["skill_id"] == skill_css.id
        assert data2["skill_slug"] == "css-styling"

        # 3. With skill_slug only -> resolves and canonicalizes skill_id
        res3 = client.post(
            "/api/v1/activities",
            json={
                "lesson_id": lesson_id,
                "activity_type": "true_false",
                "title": "CSS Styling Check 2",
                "instructions": "Identify CSS concepts.",
                "configuration": {"statement": "Flexbox is one-dimensional."},
                "answer_key": {"correct_boolean": True},
                "skill_slug": "css-styling",
            },
            headers=creator_headers,
        )
        assert res3.status_code == 201
        data3 = res3.json()
        assert data3["skill_id"] == skill_css.id
        assert data3["skill_slug"] == "css-styling"

    def test_nonexistent_skill_reference(
        self,
        client: TestClient,
        creator_headers: dict[str, str],
        course_skills_setup: dict[str, Any],
    ) -> None:
        """Nonexistent skill ID or slug returns 404 SKILL_NOT_FOUND."""
        lesson_id = course_skills_setup["lesson_a"].id

        # Nonexistent ID
        res_id = client.post(
            "/api/v1/activities",
            json={
                "lesson_id": lesson_id,
                "activity_type": "true_false",
                "title": "Bogus Skill ID Activity",
                "instructions": "Test.",
                "configuration": {"statement": "Test."},
                "answer_key": {"correct_boolean": True},
                "skill_id": "00000000-0000-0000-0000-000000000000",
            },
            headers=creator_headers,
        )
        assert res_id.status_code == 404
        assert res_id.json()["error"]["code"] == "SKILL_NOT_FOUND"

        # Nonexistent slug
        res_slug = client.post(
            "/api/v1/activities",
            json={
                "lesson_id": lesson_id,
                "activity_type": "true_false",
                "title": "Bogus Skill Slug Activity",
                "instructions": "Test.",
                "configuration": {"statement": "Test."},
                "answer_key": {"correct_boolean": True},
                "skill_slug": "nonexistent-quantum-skill",
            },
            headers=creator_headers,
        )
        assert res_slug.status_code == 404
        assert res_slug.json()["error"]["code"] == "SKILL_NOT_FOUND"

    def test_inactive_skill_reference(
        self,
        client: TestClient,
        creator_headers: dict[str, str],
        course_skills_setup: dict[str, Any],
    ) -> None:
        """Inactive skill reference returns 400 INACTIVE_SKILL."""
        lesson_id = course_skills_setup["lesson_a"].id
        skill_inactive = course_skills_setup["skill_inactive"]

        res = client.post(
            "/api/v1/activities",
            json={
                "lesson_id": lesson_id,
                "activity_type": "true_false",
                "title": "Deprecated Tech Activity",
                "instructions": "Test.",
                "configuration": {"statement": "Test."},
                "answer_key": {"correct_boolean": True},
                "skill_slug": skill_inactive.slug,
            },
            headers=creator_headers,
        )
        assert res.status_code == 400
        assert res.json()["error"]["code"] == "INACTIVE_SKILL"

    def test_skill_belonging_to_another_course(
        self,
        client: TestClient,
        creator_headers: dict[str, str],
        course_skills_setup: dict[str, Any],
    ) -> None:
        """Referencing an active skill from another course returns 400 UNRELATED_SKILL."""
        lesson_a_id = course_skills_setup["lesson_a"].id
        skill_python = course_skills_setup["skill_python"]

        # Pass python-core slug to an HTML lesson in Course A
        res = client.post(
            "/api/v1/activities",
            json={
                "lesson_id": lesson_a_id,
                "activity_type": "true_false",
                "title": "Misattributed Skill Activity",
                "instructions": "Test.",
                "configuration": {"statement": "Test."},
                "answer_key": {"correct_boolean": True},
                "skill_slug": skill_python.slug,
            },
            headers=creator_headers,
        )
        assert res.status_code == 400
        assert res.json()["error"]["code"] == "UNRELATED_SKILL"
        assert "not associated with course" in res.json()["error"]["message"]

        # Pass python-core ID to an HTML lesson in Course A
        res_by_id = client.post(
            "/api/v1/activities",
            json={
                "lesson_id": lesson_a_id,
                "activity_type": "true_false",
                "title": "Misattributed Skill Activity by ID",
                "instructions": "Test.",
                "configuration": {"statement": "Test."},
                "answer_key": {"correct_boolean": True},
                "skill_id": skill_python.id,
            },
            headers=creator_headers,
        )
        assert res_by_id.status_code == 400
        assert res_by_id.json()["error"]["code"] == "UNRELATED_SKILL"

    def test_conflicting_skill_id_and_skill_slug(
        self,
        client: TestClient,
        creator_headers: dict[str, str],
        course_skills_setup: dict[str, Any],
    ) -> None:
        """Supplying skill_id and skill_slug that point to different skills returns 400 CONFLICTING_SKILL_TAGS."""
        lesson_id = course_skills_setup["lesson_a"].id
        skill_html = course_skills_setup["skill_html"]
        skill_css = course_skills_setup["skill_css"]

        res = client.post(
            "/api/v1/activities",
            json={
                "lesson_id": lesson_id,
                "activity_type": "true_false",
                "title": "Conflicting Skills Activity",
                "instructions": "Test.",
                "configuration": {"statement": "Test."},
                "answer_key": {"correct_boolean": True},
                "skill_id": skill_html.id,
                "skill_slug": skill_css.slug,
            },
            headers=creator_headers,
        )
        assert res.status_code == 400
        assert res.json()["error"]["code"] == "CONFLICTING_SKILL_TAGS"

    def test_activity_without_skill_tags(
        self,
        client: TestClient,
        creator_headers: dict[str, str],
        course_skills_setup: dict[str, Any],
    ) -> None:
        """Creating an activity without skill tags succeeds, preserving optionality and backwards compatibility."""
        lesson_id = course_skills_setup["lesson_a"].id

        res = client.post(
            "/api/v1/activities",
            json={
                "lesson_id": lesson_id,
                "activity_type": "true_false",
                "title": "Untagged Activity",
                "instructions": "General practice question.",
                "configuration": {"statement": "This is a general question."},
                "answer_key": {"correct_boolean": True},
            },
            headers=creator_headers,
        )
        assert res.status_code == 201
        data = res.json()
        assert data["skill_id"] is None
        assert data["skill_slug"] is None

    def test_skill_tag_without_lesson_rejected(
        self,
        client: TestClient,
        creator_headers: dict[str, str],
        course_skills_setup: dict[str, Any],
    ) -> None:
        """Supplying a skill tag without an associated lesson returns 400 LESSON_REQUIRED_FOR_SKILL."""
        skill_html = course_skills_setup["skill_html"]

        res = client.post(
            "/api/v1/activities",
            json={
                "lesson_id": None,
                "activity_type": "true_false",
                "title": "Orphan Activity with Skill Tag",
                "instructions": "Cannot attribute without lesson and course context.",
                "configuration": {"statement": "Test."},
                "answer_key": {"correct_boolean": True},
                "skill_slug": skill_html.slug,
            },
            headers=creator_headers,
        )
        assert res.status_code == 400
        assert res.json()["error"]["code"] == "LESSON_REQUIRED_FOR_SKILL"
