"""Integration tests for SkillMastery progression calculation with completed project capstones."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.modules.progress.service import ProgressionService
from app.modules.projects.models import (
    ProjectSubmission,
    SubmissionStatus,
)
from app.modules.skills.models import Discipline, Skill, SkillDifficulty


@pytest.fixture
def progression_test_data(db: Session, client: TestClient, creator_headers: dict[str, str]) -> dict[str, str]:
    """Seed discipline, skill, courses, and project for progression testing."""
    discipline = Discipline(
        slug="cloud-computing",
        name="Cloud Computing",
        description="Distributed infrastructure and cloud systems",
    )
    db.add(discipline)
    db.commit()

    skill = Skill(
        slug="k8s-orchestration",
        name="Kubernetes Orchestration",
        discipline_id=discipline.id,
        difficulty_level=SkillDifficulty.ADVANCED,
    )
    db.add(skill)
    db.commit()

    # Project 1 assessing this skill
    p1_payload = {
        "title": "Kubernetes Cluster Deployment",
        "short_description": "Deploy a high-availability microservices cluster.",
        "full_description": "Comprehensive orchestration project.",
        "discipline_id": discipline.id,
        "difficulty_level": "ADVANCED",
        "requirements": {
            "milestones": [{"id": "m1", "title": "Helm chart deployment"}],
            "deliverables": ["K8s manifests repo"],
        },
        "evaluation_criteria": {
            "passing_score": 75.0,
            "rubric": [{"id": "r1", "title": "Cluster Config", "max_score": 100.0, "weight": 1.0}],
        },
        "skills": [{"skill_id": skill.id, "is_primary": True}],
    }
    p1_res = client.post("/api/v1/projects", json=p1_payload, headers=creator_headers)
    assert p1_res.status_code == 201
    p1_id = p1_res.json()["id"]
    client.post(f"/api/v1/projects/{p1_id}/publish", headers=creator_headers)

    # Project 2 also assessing this skill (for multi-project mastery test)
    p2_payload = {
        "title": "Service Mesh & Observability",
        "short_description": "Implement Istio service mesh and Prometheus monitoring.",
        "full_description": "Advanced networking project.",
        "discipline_id": discipline.id,
        "difficulty_level": "ADVANCED",
        "requirements": {
            "milestones": [{"id": "m1", "title": "Mesh configuration"}],
            "deliverables": ["Istio configuration repo"],
        },
        "evaluation_criteria": {
            "passing_score": 70.0,
            "rubric": [{"id": "r1", "title": "Mesh Config", "max_score": 100.0, "weight": 1.0}],
        },
        "skills": [{"skill_id": skill.id, "is_primary": True}],
    }
    p2_res = client.post("/api/v1/projects", json=p2_payload, headers=creator_headers)
    assert p2_res.status_code == 201
    p2_id = p2_res.json()["id"]
    client.post(f"/api/v1/projects/{p2_id}/publish", headers=creator_headers)

    return {
        "discipline_id": discipline.id,
        "skill_id": skill.id,
        "project1_id": p1_id,
        "project2_id": p2_id,
    }


def test_completed_project_awards_skill_mastery_evidence(
    client: TestClient,
    auth_headers: dict[str, str],
    creator_headers: dict[str, str],
    progression_test_data: dict[str, str],
    db: Session,
) -> None:
    """Completing a project automatically awards verifiable skill mastery evidence."""
    skill_id = progression_test_data["skill_id"]
    proj_id = progression_test_data["project1_id"]

    # 1. Initially user has no mastery
    my_mastery_before = client.get("/api/v1/progress/skills", headers=auth_headers).json()
    skill_before = next(s for s in my_mastery_before if s["skill_id"] == skill_id)
    assert skill_before["status"] == "NOT_STARTED"
    assert skill_before["mastery_level"] == 0.0
    assert skill_before["evidence"] == []

    # 2. Start project, submit deliverables, and evaluate with 90% score
    draft_res = client.post(f"/api/v1/projects/{proj_id}/submissions", headers=auth_headers)
    sub_id = draft_res.json()["id"]

    client.post(
        f"/api/v1/submissions/{sub_id}/submit",
        json={"summary": "Deployed multi-node cluster."},
        headers=auth_headers,
    )

    eval_res = client.post(
        f"/api/v1/submissions/{sub_id}/evaluation",
        json={
            "criteria_scores": [{"criterion_id": "r1", "score": 90.0, "feedback": "Well configured"}],
            "feedback": "Great production setup.",
            "action": "APPROVE",
        },
        headers=creator_headers,
    )
    assert eval_res.status_code == 200
    assert eval_res.json()["status"] == "COMPLETED"

    # 3. Verify SkillMastery is automatically recalculated
    my_mastery_after = client.get("/api/v1/progress/skills", headers=auth_headers).json()
    skill_after = next(s for s in my_mastery_after if s["skill_id"] == skill_id)

    # 1 completed task results in PROVISIONAL status
    assert skill_after["status"] == "PROVISIONAL"
    assert skill_after["mastery_level"] == 90.0
    assert len(skill_after["evidence"]) == 1

    ev = skill_after["evidence"][0]
    assert ev["project_id"] == proj_id
    assert ev["submission_id"] == sub_id
    assert ev["rule"] == "capstone_project_completed"
    assert ev["score"] == 90.0
    assert ev["passed"] is True


def test_incomplete_or_failed_project_does_not_award_mastery(
    client: TestClient,
    auth_headers: dict[str, str],
    creator_headers: dict[str, str],
    progression_test_data: dict[str, str],
) -> None:
    """Draft, submitted, or failed project submissions do not award passing competency evidence."""
    skill_id = progression_test_data["skill_id"]
    proj_id = progression_test_data["project1_id"]

    # 1. Start draft
    draft_res = client.post(f"/api/v1/projects/{proj_id}/submissions", headers=auth_headers)
    sub_id = draft_res.json()["id"]

    # In draft, no evidence
    s_draft = next(
        s for s in client.get("/api/v1/progress/skills", headers=auth_headers).json()
        if s["skill_id"] == skill_id
    )
    assert s_draft["evidence"] == []

    # 2. Submit
    client.post(f"/api/v1/submissions/{sub_id}/submit", headers=auth_headers)

    # Under review: status is PRACTICING (level 30.0), no passed evidence
    s_sub = next(
        s for s in client.get("/api/v1/progress/skills", headers=auth_headers).json()
        if s["skill_id"] == skill_id
    )
    assert s_sub["status"] == "PRACTICING"
    assert s_sub["mastery_level"] == 30.0
    assert s_sub["evidence"] == []

    # 3. Evaluator requests changes with failing score (50%)
    client.post(
        f"/api/v1/submissions/{sub_id}/evaluation",
        json={
            "criteria_scores": [{"criterion_id": "r1", "score": 50.0, "feedback": "Needs improvement"}],
            "feedback": "Needs revision before approval.",
            "action": "REQUEST_CHANGES",
        },
        headers=creator_headers,
    )

    s_failed = next(
        s for s in client.get("/api/v1/progress/skills", headers=auth_headers).json()
        if s["skill_id"] == skill_id
    )
    assert s_failed["status"] == "PRACTICING"
    assert s_failed["evidence"] == []


def test_multiple_revisions_deduplicated_by_project(
    client: TestClient,
    auth_headers: dict[str, str],
    creator_headers: dict[str, str],
    progression_test_data: dict[str, str],
    db: Session,
) -> None:
    """Multiple passing revisions of the same project count as 1 task and retain highest score."""
    skill_id = progression_test_data["skill_id"]
    proj_id = progression_test_data["project1_id"]

    # Revision 1: initial submission receives revisions requested
    d1 = client.post(f"/api/v1/projects/{proj_id}/submissions", headers=auth_headers).json()
    sub1_id = d1["id"]
    client.post(f"/api/v1/submissions/{sub1_id}/submit", headers=auth_headers)
    client.post(
        f"/api/v1/submissions/{sub1_id}/evaluation",
        json={
            "criteria_scores": [{"criterion_id": "r1", "score": 70.0}],
            "feedback": "Needs polish on ingress configuration.",
            "action": "REQUEST_CHANGES",
        },
        headers=creator_headers,
    )

    # Revision 2: learner creates revision and completes with 96%
    d2 = client.post(
        f"/api/v1/submissions/{sub1_id}/revisions",
        json={"reason": "Adding high-availability ingresses."},
        headers=auth_headers,
    ).json()
    sub2_id = d2["id"]
    client.post(f"/api/v1/submissions/{sub2_id}/submit", headers=auth_headers)
    client.post(
        f"/api/v1/submissions/{sub2_id}/evaluation",
        json={
            "criteria_scores": [{"criterion_id": "r1", "score": 96.0}],
            "feedback": "Excellent high-availability update.",
            "action": "APPROVE",
        },
        headers=creator_headers,
    )

    # Also mark revision 1 as COMPLETED with 78% in database to test deduplication of multiple passing revisions
    sub1_db = db.query(ProjectSubmission).filter(ProjectSubmission.id == sub1_id).first()
    sub1_db.status = SubmissionStatus.COMPLETED.value
    sub1_db.passed = True
    sub1_db.score = 78.0
    db.commit()

    # Recalculate skill mastery
    ProgressionService(db).recalculate_skill_mastery(sub1_db.user_id, skill_id)

    s_rev2 = next(
        s for s in client.get("/api/v1/progress/skills", headers=auth_headers).json()
        if s["skill_id"] == skill_id
    )

    # CRITICAL: Both revisions are passed and completed, but deduplicate by project_id!
    # Still counts as 1 task (not 2), so status remains PROVISIONAL!
    assert s_rev2["status"] == "PROVISIONAL"
    # Mastery score is updated to the higher revision score (96.0)
    assert s_rev2["mastery_level"] == 96.0
    assert len(s_rev2["evidence"]) == 1
    assert s_rev2["evidence"][0]["submission_id"] == sub2_id
    assert s_rev2["evidence"][0]["score"] == 96.0


def test_two_distinct_tasks_achieve_mastered_status(
    client: TestClient,
    auth_headers: dict[str, str],
    creator_headers: dict[str, str],
    progression_test_data: dict[str, str],
) -> None:
    """Completing 2 distinct qualifying tasks with >= 80% average promotes learner to MASTERED."""
    skill_id = progression_test_data["skill_id"]
    p1_id = progression_test_data["project1_id"]
    p2_id = progression_test_data["project2_id"]

    # 1. Complete Project 1 with 82%
    d1 = client.post(f"/api/v1/projects/{p1_id}/submissions", headers=auth_headers).json()
    client.post(f"/api/v1/submissions/{d1['id']}/submit", headers=auth_headers)
    client.post(
        f"/api/v1/submissions/{d1['id']}/evaluation",
        json={
            "criteria_scores": [{"criterion_id": "r1", "score": 82.0}],
            "feedback": "Good project 1 execution.",
            "action": "APPROVE",
        },
        headers=creator_headers,
    )

    s_after_p1 = next(
        s for s in client.get("/api/v1/progress/skills", headers=auth_headers).json()
        if s["skill_id"] == skill_id
    )
    assert s_after_p1["status"] == "PROVISIONAL"
    assert s_after_p1["mastery_level"] == 82.0

    # 2. Complete Project 2 with 94%
    d2 = client.post(f"/api/v1/projects/{p2_id}/submissions", headers=auth_headers).json()
    client.post(f"/api/v1/submissions/{d2['id']}/submit", headers=auth_headers)
    client.post(
        f"/api/v1/submissions/{d2['id']}/evaluation",
        json={
            "criteria_scores": [{"criterion_id": "r1", "score": 94.0}],
            "feedback": "Outstanding project 2 execution.",
            "action": "APPROVE",
        },
        headers=creator_headers,
    )

    s_after_p2 = next(
        s for s in client.get("/api/v1/progress/skills", headers=auth_headers).json()
        if s["skill_id"] == skill_id
    )

    # 2 distinct projects completed: average is (82 + 94) / 2 = 88.0 >= 80.0 -> MASTERED!
    assert s_after_p2["status"] == "MASTERED"
    assert s_after_p2["mastery_level"] == 88.0
    assert len(s_after_p2["evidence"]) == 2
