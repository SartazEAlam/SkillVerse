"""API tests for learner project submission lifecycle, revision trees, and rubric evaluations."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.modules.auth.models import User, UserRole
from app.modules.skills.models import Discipline, Skill, SkillDifficulty


@pytest.fixture
def published_project(
    client: TestClient,
    creator_headers: dict[str, str],
    db: Session,
) -> str:
    """Fixture creating a published project ready for learner submissions."""
    discipline = Discipline(
        slug="frontend-disc",
        name="Frontend Engineering",
        description="Client-side engineering",
    )
    db.add(discipline)
    db.commit()

    skill = Skill(
        slug="react-architecture",
        name="React Architecture",
        discipline_id=discipline.id,
        difficulty_level=SkillDifficulty.INTERMEDIATE,
    )
    db.add(skill)
    db.commit()

    payload = {
        "title": "Interactive Dashboard Project",
        "short_description": "Build an analytics dashboard with interactive charts and themes.",
        "full_description": "A comprehensive frontend project integrating data fetching, state management, and accessible UI.",
        "discipline_id": discipline.id,
        "difficulty_level": "INTERMEDIATE",
        "requirements": {
            "milestones": [
                {"id": "m1", "title": "Chart Components"},
                {"id": "m2", "title": "Theme Toggle"},
            ],
            "deliverables": ["GitHub repository URL", "Deployed demo URL"],
        },
        "evaluation_criteria": {
            "passing_score": 70.0,
            "rubric": [
                {"id": "crit_code", "title": "Code Quality", "max_score": 50.0, "weight": 1.0},
                {"id": "crit_ux", "title": "UI / UX Polish", "max_score": 50.0, "weight": 1.0},
            ],
        },
        "skills": [{"skill_id": skill.id, "is_primary": True}],
    }
    create_res = client.post("/api/v1/projects", json=payload, headers=creator_headers)
    assert create_res.status_code == 201
    proj_id = create_res.json()["id"]

    pub_res = client.post(f"/api/v1/projects/{proj_id}/publish", headers=creator_headers)
    assert pub_res.status_code == 200
    return proj_id


@pytest.fixture
def second_evaluator_headers(client: TestClient, db: Session) -> dict[str, str]:
    """Provide authentication headers for a second evaluator user."""
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "reviewer2@example.com",
            "password": "SecureP@ss1",
            "display_name": "Reviewer Two",
        },
    )
    user = db.query(User).filter(User.email == "reviewer2@example.com").first()
    user.role = UserRole.CREATOR
    db.commit()
    res = client.post(
        "/api/v1/auth/login",
        json={"email": "reviewer2@example.com", "password": "SecureP@ss1"},
    )
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def test_start_submission_and_duplicate_draft_prevention(
    client: TestClient,
    auth_headers: dict[str, str],
    published_project: str,
) -> None:
    """Starting a project creates a draft, and re-invoking returns the existing draft."""
    res1 = client.post(
        f"/api/v1/projects/{published_project}/submissions",
        json={"title": "My Dashboard Attempt"},
        headers=auth_headers,
    )
    assert res1.status_code == 201
    data1 = res1.json()
    sub_id = data1["id"]
    assert data1["status"] == "DRAFT"
    assert data1["version_number"] == 1

    # Call again: must return the existing draft without creating a new record
    res2 = client.post(
        f"/api/v1/projects/{published_project}/submissions",
        headers=auth_headers,
    )
    assert res2.status_code in (200, 201)
    data2 = res2.json()
    assert data2["id"] == sub_id
    assert data2["version_number"] == 1


def test_update_draft_and_submit_lifecycle(
    client: TestClient,
    auth_headers: dict[str, str],
    published_project: str,
) -> None:
    """Learner can update milestones and deliverables before submitting."""
    res_start = client.post(
        f"/api/v1/projects/{published_project}/submissions",
        headers=auth_headers,
    )
    sub_id = res_start.json()["id"]

    # Update draft
    patch_payload = {
        "title": "Interactive Analytics Hub",
        "summary": "Completed dashboard featuring real-time charts and dark mode.",
        "content": {
            "repo_url": "https://github.com/learner/dashboard",
            "demo_url": "https://dashboard-demo.skillverse.dev",
        },
        "milestones_completed": ["m1", "m2"],
    }
    patch_res = client.patch(f"/api/v1/submissions/{sub_id}", json=patch_payload, headers=auth_headers)
    assert patch_res.status_code == 200
    updated = patch_res.json()
    assert updated["title"] == "Interactive Analytics Hub"
    assert updated["milestones_completed"] == ["m1", "m2"]
    assert updated["content"]["repo_url"] == "https://github.com/learner/dashboard"

    # Submit project
    submit_res = client.post(f"/api/v1/submissions/{sub_id}/submit", headers=auth_headers)
    assert submit_res.status_code == 200
    assert submit_res.json()["status"] == "SUBMITTED"
    assert submit_res.json()["submitted_at"] is not None

    # Editing submitted project must fail
    fail_patch = client.patch(
        f"/api/v1/submissions/{sub_id}",
        json={"title": "Attempt to edit submitted project"},
        headers=auth_headers,
    )
    assert fail_patch.status_code in (400, 422)


def test_self_evaluation_prevention(
    client: TestClient,
    creator_headers: dict[str, str],
    published_project: str,
) -> None:
    """A creator cannot evaluate or claim their own submission."""
    # Creator starts and submits their own project
    start_res = client.post(
        f"/api/v1/projects/{published_project}/submissions",
        headers=creator_headers,
    )
    sub_id = start_res.json()["id"]

    client.patch(
        f"/api/v1/submissions/{sub_id}",
        json={"summary": "Deliverables provided by creator test."},
        headers=creator_headers,
    )
    client.post(f"/api/v1/submissions/{sub_id}/submit", headers=creator_headers)

    # Attempt to claim own submission
    claim_res = client.post(f"/api/v1/submissions/{sub_id}/review", headers=creator_headers)
    assert claim_res.status_code == 403
    assert "own submission" in claim_res.json()["error"]["message"]

    # Attempt to evaluate own submission
    eval_res = client.post(
        f"/api/v1/submissions/{sub_id}/evaluation",
        json={"feedback": "Self-evaluation attempt", "action": "APPROVE"},
        headers=creator_headers,
    )
    assert eval_res.status_code == 403
    assert "own submission" in eval_res.json()["error"]["message"]


def test_evaluation_pass_flow(
    client: TestClient,
    auth_headers: dict[str, str],
    creator_headers: dict[str, str],
    published_project: str,
) -> None:
    """Evaluator claims and grades submission with passing score -> COMPLETED status."""
    start_res = client.post(
        f"/api/v1/projects/{published_project}/submissions",
        headers=auth_headers,
    )
    sub_id = start_res.json()["id"]

    client.patch(
        f"/api/v1/submissions/{sub_id}",
        json={"summary": "Comprehensive solution with clean architecture."},
        headers=auth_headers,
    )
    client.post(f"/api/v1/submissions/{sub_id}/submit", headers=auth_headers)

    # Evaluator claims submission
    claim_res = client.post(f"/api/v1/submissions/{sub_id}/review", headers=creator_headers)
    assert claim_res.status_code == 200
    assert claim_res.json()["status"] == "UNDER_REVIEW"

    # Evaluator scores rubric: 45/50 on code (90%), 40/50 on UX (80%) -> average = 85.0% >= 70.0%
    eval_payload = {
        "criteria_scores": [
            {"criterion_id": "crit_code", "score": 45.0, "feedback": "Excellent modular patterns."},
            {"criterion_id": "crit_ux", "score": 40.0, "feedback": "Responsive and accessible."},
        ],
        "feedback": "Outstanding work overall! Clean implementation of charts and state.",
    }
    eval_res = client.post(f"/api/v1/submissions/{sub_id}/evaluation", json=eval_payload, headers=creator_headers)
    assert eval_res.status_code == 200
    eval_data = eval_res.json()
    assert eval_data["passed"] is True
    assert eval_data["status"] == "COMPLETED"
    assert eval_data["score"] == 85.0


def test_changes_requested_and_revision_chain(
    client: TestClient,
    auth_headers: dict[str, str],
    second_evaluator_headers: dict[str, str],
    published_project: str,
) -> None:
    """Failing or changes-requested review triggers immutable revision workflow."""
    start_res = client.post(
        f"/api/v1/projects/{published_project}/submissions",
        headers=auth_headers,
    )
    sub_v1_id = start_res.json()["id"]

    client.patch(
        f"/api/v1/submissions/{sub_v1_id}",
        json={"summary": "Initial draft submission."},
        headers=auth_headers,
    )
    client.post(f"/api/v1/submissions/{sub_v1_id}/submit", headers=auth_headers)

    # Reviewer requests changes
    eval_payload = {
        "criteria_scores": [
            {"criterion_id": "crit_code", "score": 20.0, "feedback": "Missing error handling."},
            {"criterion_id": "crit_ux", "score": 20.0, "feedback": "Mobile layout is broken."},
        ],
        "feedback": "Please fix mobile layout and add error boundaries before resubmission.",
        "action": "REQUEST_CHANGES",
    }
    eval_res = client.post(
        f"/api/v1/submissions/{sub_v1_id}/evaluation",
        json=eval_payload,
        headers=second_evaluator_headers,
    )
    assert eval_res.status_code == 200
    assert eval_res.json()["status"] == "CHANGES_REQUESTED"
    assert eval_res.json()["passed"] is False

    # Learner initiates a revision
    rev_res = client.post(
        f"/api/v1/submissions/{sub_v1_id}/revisions",
        json={"title": "Dashboard v2 (Mobile Fixed)"},
        headers=auth_headers,
    )
    assert rev_res.status_code == 201
    rev_data = rev_res.json()
    assert rev_data["version_number"] == 2
    assert rev_data["revision_of_id"] == sub_v1_id
    assert rev_data["status"] == "DRAFT"

    # Verify original v1 submission remains unchanged in CHANGES_REQUESTED status
    v1_check = client.get(f"/api/v1/submissions/{sub_v1_id}", headers=auth_headers)
    assert v1_check.status_code == 200
    assert v1_check.json()["status"] == "CHANGES_REQUESTED"

    # Inspect full revision history
    history_res = client.get(f"/api/v1/submissions/{sub_v1_id}/history", headers=auth_headers)
    assert history_res.status_code == 200
    history = history_res.json()
    assert len(history["submissions"]) == 2
    assert history["submissions"][0]["version_number"] == 1
    assert history["submissions"][1]["version_number"] == 2


def test_list_my_submissions(
    client: TestClient,
    auth_headers: dict[str, str],
    published_project: str,
) -> None:
    """Learner can list their authored submissions."""
    client.post(
        f"/api/v1/projects/{published_project}/submissions",
        headers=auth_headers,
    )
    res = client.get("/api/v1/submissions/mine", headers=auth_headers)
    assert res.status_code == 200
    items = res.json()
    assert isinstance(items, list)
    assert len(items) >= 1
    assert items[0]["project_id"] == published_project


def test_submission_lifecycle_transition_history(
    client: TestClient,
    auth_headers: dict[str, str],
    creator_headers: dict[str, str],
    published_project: str,
) -> None:
    """Validate full state machine transitions and audit history: DRAFT -> SUBMITTED -> UNDER_REVIEW -> EVALUATED -> COMPLETED."""
    # 1. Start draft (None -> DRAFT)
    res_start = client.post(
        f"/api/v1/projects/{published_project}/submissions",
        headers=auth_headers,
    )
    assert res_start.status_code == 201
    sub_id = res_start.json()["id"]

    # 2. Update and Submit (DRAFT -> SUBMITTED)
    client.patch(
        f"/api/v1/submissions/{sub_id}",
        json={"summary": "Deliverable notes for lifecycle testing."},
        headers=auth_headers,
    )
    res_sub = client.post(f"/api/v1/submissions/{sub_id}/submit", headers=auth_headers)
    assert res_sub.status_code == 200
    assert res_sub.json()["status"] == "SUBMITTED"

    # 3. Evaluator claims (SUBMITTED -> UNDER_REVIEW)
    res_claim = client.post(f"/api/v1/submissions/{sub_id}/review", headers=creator_headers)
    assert res_claim.status_code == 200
    assert res_claim.json()["status"] == "UNDER_REVIEW"

    # 4. Evaluator scores and approves (UNDER_REVIEW -> EVALUATED -> COMPLETED)
    eval_payload = {
        "criteria_scores": [
            {"criterion_id": "crit_code", "score": 48.0, "feedback": "Superb work."},
            {"criterion_id": "crit_ux", "score": 46.0, "feedback": "Polished UI."},
        ],
        "feedback": "Outstanding implementation satisfying all criteria.",
        "action": "APPROVE",
    }
    eval_res = client.post(f"/api/v1/submissions/{sub_id}/evaluation", json=eval_payload, headers=creator_headers)
    assert eval_res.status_code == 200
    eval_data = eval_res.json()
    assert eval_data["status"] == "COMPLETED"
    assert eval_data["passed"] is True

    # Check transition history in evaluation response
    history = eval_data.get("transition_history", [])
    assert len(history) >= 4
    to_statuses = [t["to_status"] for t in history]
    assert "DRAFT" in to_statuses
    assert "SUBMITTED" in to_statuses
    assert "UNDER_REVIEW" in to_statuses
    assert "EVALUATED" in to_statuses
    assert "COMPLETED" in to_statuses

    # Ensure EVALUATED intermediate state is present before COMPLETED
    evaluated_idx = to_statuses.index("EVALUATED")
    completed_idx = to_statuses.index("COMPLETED")
    assert evaluated_idx < completed_idx
    assert history[evaluated_idx]["from_status"] == "UNDER_REVIEW"
    assert history[completed_idx]["from_status"] == "EVALUATED"

    # Check submission details endpoint returns the transition history
    sub_detail_res = client.get(f"/api/v1/submissions/{sub_id}", headers=auth_headers)
    assert sub_detail_res.status_code == 200
    detail = sub_detail_res.json()
    assert detail["status"] == "COMPLETED"
    detail_to_statuses = [t["to_status"] for t in detail["transition_history"]]
    assert detail_to_statuses == to_statuses


def test_cross_user_revision_rejection(
    client: TestClient,
    auth_headers: dict[str, str],
    creator_headers: dict[str, str],
    published_project: str,
) -> None:
    """Learner B cannot initiate a revision on Learner A's submission."""
    # Learner A creates, submits, and reviewer requests changes
    start_res = client.post(
        f"/api/v1/projects/{published_project}/submissions",
        headers=auth_headers,
    )
    sub_id = start_res.json()["id"]

    client.patch(
        f"/api/v1/submissions/{sub_id}",
        json={"summary": "Learner A submission requiring changes."},
        headers=auth_headers,
    )
    client.post(f"/api/v1/submissions/{sub_id}/submit", headers=auth_headers)

    client.post(
        f"/api/v1/submissions/{sub_id}/evaluation",
        json={"feedback": "Changes required.", "action": "REQUEST_CHANGES"},
        headers=creator_headers,
    )

    # Register Learner B
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "learner_b@example.com",
            "password": "SecureP@ss1",
            "display_name": "Learner B",
        },
    )
    b_login = client.post(
        "/api/v1/auth/login",
        json={"email": "learner_b@example.com", "password": "SecureP@ss1"},
    )
    b_headers = {"Authorization": f"Bearer {b_login.json()['access_token']}"}

    # Learner B attempts to initiate revision on Learner A's submission -> 403 Forbidden
    cross_rev_res = client.post(
        f"/api/v1/submissions/{sub_id}/revisions",
        json={"title": "Learner B unauthorized revision hijack"},
        headers=b_headers,
    )
    assert cross_rev_res.status_code == 403
    assert "another learner's submission" in cross_rev_res.json()["error"]["message"]


def test_cross_project_revision_rejection(
    client: TestClient,
    auth_headers: dict[str, str],
    creator_headers: dict[str, str],
    published_project: str,
) -> None:
    """A revision strictly inherits the project_id from its source submission and cannot cross project boundaries."""
    # Learner starts and submits on published_project
    start_res = client.post(
        f"/api/v1/projects/{published_project}/submissions",
        headers=auth_headers,
    )
    sub_id = start_res.json()["id"]

    client.patch(
        f"/api/v1/submissions/{sub_id}",
        json={"summary": "Submission to be revised."},
        headers=auth_headers,
    )
    client.post(f"/api/v1/submissions/{sub_id}/submit", headers=auth_headers)

    client.post(
        f"/api/v1/submissions/{sub_id}/evaluation",
        json={"feedback": "Please revise.", "action": "REQUEST_CHANGES"},
        headers=creator_headers,
    )

    # Create revision
    rev_res = client.post(
        f"/api/v1/submissions/{sub_id}/revisions",
        json={"title": "Dashboard v2 Revision"},
        headers=auth_headers,
    )
    assert rev_res.status_code == 201
    rev_data = rev_res.json()
    assert rev_data["project_id"] == published_project
    assert rev_data["revision_of_id"] == sub_id
    assert rev_data["version_number"] == 2


