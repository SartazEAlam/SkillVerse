"""Integration tests for learner portfolio configuration, item curation, and privacy filtering."""

from __future__ import annotations

import io

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.infrastructure.rate_limiter import limiter
from app.infrastructure.storage.factory import get_storage_service
from app.modules.projects.models import (
    ProjectArtifact,
    ProjectSubmission,
    SubmissionStatus,
)
from app.modules.skills.models import Discipline, Skill, SkillDifficulty


@pytest.fixture
def test_setup_project_and_skills(db: Session, creator_headers: dict[str, str], client: TestClient) -> dict[str, str]:
    """Seed discipline, skill, and published project for portfolio testing."""
    discipline = Discipline(
        slug="portfolio-disc",
        name="Showcase Discipline",
        description="Testing portfolio items",
    )
    db.add(discipline)
    db.commit()

    skill = Skill(
        slug="fullstack-dev",
        name="Fullstack Engineering",
        discipline_id=discipline.id,
        difficulty_level=SkillDifficulty.INTERMEDIATE,
    )
    db.add(skill)
    db.commit()

    payload = {
        "title": "Fullstack Portfolio Project",
        "short_description": "A capstone project demonstrating end-to-end engineering.",
        "full_description": "Comprehensive project deliverable showcase.",
        "discipline_id": discipline.id,
        "difficulty_level": "INTERMEDIATE",
        "requirements": {
            "milestones": [{"id": "m1", "title": "Implementation"}],
            "deliverables": ["Source code repository"],
        },
        "evaluation_criteria": {
            "passing_score": 70.0,
            "rubric": [{"id": "crit1", "title": "Execution", "max_score": 100.0, "weight": 1.0}],
        },
        "skills": [{"skill_id": skill.id, "is_primary": True}],
    }
    create_res = client.post("/api/v1/projects", json=payload, headers=creator_headers)
    assert create_res.status_code == 201
    proj_id = create_res.json()["id"]

    pub_res = client.post(f"/api/v1/projects/{proj_id}/publish", headers=creator_headers)
    assert pub_res.status_code == 200

    return {
        "discipline_id": discipline.id,
        "skill_id": skill.id,
        "project_id": proj_id,
    }


@pytest.fixture
def second_user_headers(client: TestClient, db: Session) -> dict[str, str]:
    """Provide authentication headers for a second learner."""
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "learner2@example.com",
            "password": "SecureP@ss1",
            "display_name": "Second Learner",
        },
    )
    res = client.post(
        "/api/v1/auth/login",
        json={"email": "learner2@example.com", "password": "SecureP@ss1"},
    )
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


# ── Portfolio Profile & Settings Tests ──────────────────────────────────────


def test_get_my_portfolio_auto_creates_default(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    """Accessing /portfolios/me for the first time auto-creates a private showcase profile."""
    res = client.get("/api/v1/portfolios/me", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()

    assert data["visibility"] == "PRIVATE"
    assert data["is_public"] is False
    assert "Portfolio" in data["title"]
    assert data["items"] == []
    assert data["custom_slug"] is None

    # Idempotent second call returns the same portfolio
    res2 = client.get("/api/v1/portfolios/me", headers=auth_headers)
    assert res2.status_code == 200
    assert res2.json()["user_id"] == data["user_id"]


def test_update_my_portfolio_metadata_and_visibility(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    """Learners can update title, headline, bio, contact links, and visibility settings."""
    patch_payload = {
        "title": "Alex Rivers | Full Stack Developer",
        "headline": "Building distributed systems and reactive frontends",
        "bio_override": "Senior software engineer specializing in Python and TypeScript.",
        "visibility": "PUBLIC",
        "contact_links": {
            "github": "https://github.com/alexrivers",
            "linkedin": "https://linkedin.com/in/alexrivers",
        },
    }
    res = client.patch("/api/v1/portfolios/me", json=patch_payload, headers=auth_headers)
    assert res.status_code == 200
    data = res.json()

    assert data["title"] == "Alex Rivers | Full Stack Developer"
    assert data["headline"] == "Building distributed systems and reactive frontends"
    assert data["bio_override"] == "Senior software engineer specializing in Python and TypeScript."
    assert data["visibility"] == "PUBLIC"
    assert data["is_public"] is True
    assert data["contact_links"]["github"] == "https://github.com/alexrivers"

    # Switch to UNLISTED
    res_unlisted = client.patch(
        "/api/v1/portfolios/me",
        json={"visibility": "UNLISTED"},
        headers=auth_headers,
    )
    assert res_unlisted.status_code == 200
    assert res_unlisted.json()["visibility"] == "UNLISTED"
    assert res_unlisted.json()["is_public"] is True

    # Switch to PRIVATE
    res_private = client.patch(
        "/api/v1/portfolios/me",
        json={"visibility": "PRIVATE"},
        headers=auth_headers,
    )
    assert res_private.status_code == 200
    assert res_private.json()["visibility"] == "PRIVATE"
    assert res_private.json()["is_public"] is False


def test_portfolio_custom_slug_validation_and_uniqueness(
    client: TestClient,
    auth_headers: dict[str, str],
    second_user_headers: dict[str, str],
) -> None:
    """Custom slugs are validated against reserved paths and uniqueness constraints."""
    # 1. Reserved slug rejection
    for reserved in ["admin", "me", "items", "submissions", "projects", "download"]:
        res_resv = client.patch(
            "/api/v1/portfolios/me",
            json={"custom_slug": reserved},
            headers=auth_headers,
        )
        assert res_resv.status_code in (400, 422)

    # 2. Claim valid custom slug
    res_claim = client.patch(
        "/api/v1/portfolios/me",
        json={"custom_slug": "alex-showcase"},
        headers=auth_headers,
    )
    assert res_claim.status_code == 200
    assert res_claim.json()["custom_slug"] == "alex-showcase"

    # 3. Second user attempting to claim the same slug receives 409 Conflict
    res_conflict = client.patch(
        "/api/v1/portfolios/me",
        json={"custom_slug": "alex-showcase"},
        headers=second_user_headers,
    )
    assert res_conflict.status_code == 409


# ── Portfolio Item Curation Tests ───────────────────────────────────────────


def test_add_project_submission_to_portfolio(
    client: TestClient,
    auth_headers: dict[str, str],
    creator_headers: dict[str, str],
    test_setup_project_and_skills: dict[str, str],
) -> None:
    """Learners can feature completed project submissions with demonstrated skills and public deliverables."""
    proj_id = test_setup_project_and_skills["project_id"]

    # 1. Learner creates submission and uploads public & private artifacts
    draft_res = client.post(f"/api/v1/projects/{proj_id}/submissions", headers=auth_headers)
    assert draft_res.status_code == 201
    sub_id = draft_res.json()["id"]

    limiter.reset()
    res_pub_art = client.post(
        f"/api/v1/submissions/{sub_id}/artifacts",
        files={"file": ("project_demo.pdf", io.BytesIO(b"%PDF-1.4 demo"), "application/pdf")},
        data={"is_public": "true"},
        headers=auth_headers,
    )
    assert res_pub_art.status_code == 201

    limiter.reset()
    res_priv_art = client.post(
        f"/api/v1/submissions/{sub_id}/artifacts",
        files={"file": ("internal_notes.txt", io.BytesIO(b"Private notes"), "text/plain")},
        data={"is_public": "false"},
        headers=auth_headers,
    )
    assert res_priv_art.status_code == 201

    # 2. Learner submits
    sub_res = client.post(
        f"/api/v1/submissions/{sub_id}/submit",
        json={"summary": "Production ready fullstack implementation."},
        headers=auth_headers,
    )
    assert sub_res.status_code == 200

    # 3. Evaluator reviews and approves
    eval_res = client.post(
        f"/api/v1/submissions/{sub_id}/evaluation",
        json={
            "criteria_scores": [{"criterion_id": "crit1", "score": 95.0, "feedback": "Superb work"}],
            "feedback": "Outstanding execution.",
            "action": "APPROVE",
        },
        headers=creator_headers,
    )
    assert eval_res.status_code == 200
    assert eval_res.json()["status"] == "COMPLETED"

    # 4. Add submission to portfolio
    item_res = client.post(
        "/api/v1/portfolios/me/items",
        json={
            "item_type": "project_submission",
            "reference_id": sub_id,
            "title": "Fullstack Cloud Showcase",
            "summary": "Demonstrates fullstack systems engineering and cloud storage.",
            "external_url": "https://demo.example.com",
            "visibility": "PUBLIC",
        },
        headers=auth_headers,
    )
    assert item_res.status_code == 201
    item_data = item_res.json()

    assert item_data["title"] == "Fullstack Cloud Showcase"
    assert item_data["reference_id"] == sub_id
    assert item_data["item_type"] == "PROJECT_SUBMISSION"
    assert item_data["sort_order"] == 0
    assert "Fullstack Engineering" in item_data["skills_demonstrated"]

    # Verify ONLY public artifacts are attached to the portfolio item
    assert len(item_data["artifacts"]) == 1
    assert item_data["artifacts"][0]["original_filename"] == "project_demo.pdf"


def test_add_item_submission_validation_rules(
    client: TestClient,
    auth_headers: dict[str, str],
    second_user_headers: dict[str, str],
    test_setup_project_and_skills: dict[str, str],
) -> None:
    """Enforce ownership, completed status, and duplicate submission prevention."""
    proj_id = test_setup_project_and_skills["project_id"]

    # 1. Draft submission cannot be featured
    draft_res = client.post(f"/api/v1/projects/{proj_id}/submissions", headers=auth_headers)
    sub_id = draft_res.json()["id"]

    res_draft_rejected = client.post(
        "/api/v1/portfolios/me/items",
        json={"item_type": "project_submission", "reference_id": sub_id},
        headers=auth_headers,
    )
    assert res_draft_rejected.status_code in (400, 422)

    # 2. Non-existent reference rejected
    res_404 = client.post(
        "/api/v1/portfolios/me/items",
        json={"item_type": "project_submission", "reference_id": "00000000-0000-0000-0000-000000000000"},
        headers=auth_headers,
    )
    assert res_404.status_code == 404

    # 3. Another user's submission rejected
    res_forbidden = client.post(
        "/api/v1/portfolios/me/items",
        json={"item_type": "project_submission", "reference_id": sub_id},
        headers=second_user_headers,
    )
    assert res_forbidden.status_code in (400, 403, 422)


def test_portfolio_item_crud_and_non_destructive_deletion(
    client: TestClient,
    auth_headers: dict[str, str],
    second_user_headers: dict[str, str],
    creator_headers: dict[str, str],
    test_setup_project_and_skills: dict[str, str],
    db: Session,
) -> None:
    """Item edits enforce ownership; deletion removes portfolio item without touching submission or artifacts."""
    proj_id = test_setup_project_and_skills["project_id"]

    # Complete a submission
    draft_res = client.post(f"/api/v1/projects/{proj_id}/submissions", headers=auth_headers)
    sub_id = draft_res.json()["id"]

    limiter.reset()
    art_res = client.post(
        f"/api/v1/submissions/{sub_id}/artifacts",
        files={"file": ("deliverable.txt", io.BytesIO(b"Artifact content"), "text/plain")},
        data={"is_public": "true"},
        headers=auth_headers,
    )
    assert art_res.status_code == 201
    art_id = art_res.json()["id"]

    client.post(f"/api/v1/submissions/{sub_id}/submit", headers=auth_headers)
    eval_res = client.post(
        f"/api/v1/submissions/{sub_id}/evaluation",
        json={
            "criteria_scores": [{"criterion_id": "crit1", "score": 85.0}],
            "feedback": "Great work on deliverables.",
            "action": "APPROVE",
        },
        headers=creator_headers,
    )
    assert eval_res.status_code == 200

    # Add to portfolio
    item_res = client.post(
        "/api/v1/portfolios/me/items",
        json={"item_type": "project_submission", "reference_id": sub_id, "title": "Initial Title"},
        headers=auth_headers,
    )
    assert item_res.status_code == 201
    item_id = item_res.json()["id"]

    # Prevent duplicate item with same reference
    dup_res = client.post(
        "/api/v1/portfolios/me/items",
        json={"item_type": "project_submission", "reference_id": sub_id},
        headers=auth_headers,
    )
    assert dup_res.status_code == 409

    # Second user cannot edit item
    unauth_edit = client.patch(
        f"/api/v1/portfolios/me/items/{item_id}",
        json={"title": "Hacked Title"},
        headers=second_user_headers,
    )
    assert unauth_edit.status_code in (403, 404)

    # Owner updates item
    edit_res = client.patch(
        f"/api/v1/portfolios/me/items/{item_id}",
        json={"title": "Updated Showcase Title", "visibility": "PRIVATE"},
        headers=auth_headers,
    )
    assert edit_res.status_code == 200
    assert edit_res.json()["title"] == "Updated Showcase Title"
    assert edit_res.json()["visibility"] == "PRIVATE"

    # Non-destructive deletion
    del_res = client.delete(f"/api/v1/portfolios/me/items/{item_id}", headers=auth_headers)
    assert del_res.status_code == 204

    # Confirm item removed from portfolio
    me_res = client.get("/api/v1/portfolios/me", headers=auth_headers)
    assert all(it["id"] != item_id for it in me_res.json()["items"])

    # Confirm source submission and artifact still exist in DB and storage!
    sub_in_db = db.query(ProjectSubmission).filter(ProjectSubmission.id == sub_id).first()
    assert sub_in_db is not None
    assert sub_in_db.status == SubmissionStatus.COMPLETED.value

    art_in_db = db.query(ProjectArtifact).filter(ProjectArtifact.id == art_id).first()
    assert art_in_db is not None
    storage = get_storage_service()
    assert storage.exists(art_in_db.storage_key) is True


def test_reorder_portfolio_items(
    client: TestClient,
    auth_headers: dict[str, str],
    second_user_headers: dict[str, str],
) -> None:
    """Learners can update the sequential ordering of their portfolio items."""
    # Add 3 custom showcase items
    item_ids: list[str] = []
    for i in range(3):
        res = client.post(
            "/api/v1/portfolios/me/items",
            json={
                "item_type": "custom",
                "title": f"Project Showcase {i}",
                "summary": f"Summary for project {i}",
                "visibility": "PUBLIC",
            },
            headers=auth_headers,
        )
        assert res.status_code == 201
        item_ids.append(res.json()["id"])

    # Reorder items: [2, 0, 1]
    new_order = [item_ids[2], item_ids[0], item_ids[1]]
    reorder_res = client.post(
        "/api/v1/portfolios/me/items/reorder",
        json={"item_ids": new_order},
        headers=auth_headers,
    )
    assert reorder_res.status_code == 200
    reordered_data = reorder_res.json()
    assert [it["id"] for it in reordered_data] == new_order
    assert [it["sort_order"] for it in reordered_data] == [0, 1, 2]

    # Reorder with foreign item ID rejected
    foreign_res = client.post(
        "/api/v1/portfolios/me/items/reorder",
        json={"item_ids": [item_ids[0]]},
        headers=second_user_headers,
    )
    assert foreign_res.status_code in (403, 404)


# ── Public Showcase & Privacy Filter Tests ──────────────────────────────────


def test_public_portfolio_privacy_enforcement(
    client: TestClient,
    auth_headers: dict[str, str],
    second_user_headers: dict[str, str],
    admin_headers: dict[str, str],
    db: Session,
) -> None:
    """Public showcase respects portfolio visibility and strictly filters out private items."""
    # 1. Setup portfolio with custom slug
    client.patch(
        "/api/v1/portfolios/me",
        json={"custom_slug": "dev-jordan", "visibility": "PRIVATE"},
        headers=auth_headers,
    )

    # Add item 1 (PUBLIC) and item 2 (PRIVATE)
    res_pub_item = client.post(
        "/api/v1/portfolios/me/items",
        json={"item_type": "custom", "title": "Public Work", "visibility": "PUBLIC"},
        headers=auth_headers,
    )
    pub_item_id = res_pub_item.json()["id"]

    res_priv_item = client.post(
        "/api/v1/portfolios/me/items",
        json={"item_type": "custom", "title": "Private Draft Item", "visibility": "PRIVATE"},
        headers=auth_headers,
    )
    priv_item_id = res_priv_item.json()["id"]

    # When portfolio is PRIVATE:
    # Anonymous visitors and other learners receive 403 Forbidden
    res_anon_blocked = client.get("/api/v1/portfolios/dev-jordan")
    assert res_anon_blocked.status_code == 403

    res_other_blocked = client.get("/api/v1/portfolios/dev-jordan", headers=second_user_headers)
    assert res_other_blocked.status_code == 403

    # Owner and Admin can access private portfolio
    res_owner = client.get("/api/v1/portfolios/dev-jordan", headers=auth_headers)
    assert res_owner.status_code == 200
    assert len(res_owner.json()["items"]) == 2

    res_admin = client.get("/api/v1/portfolios/dev-jordan", headers=admin_headers)
    assert res_admin.status_code == 200

    # 2. Change portfolio visibility to PUBLIC
    client.patch("/api/v1/portfolios/me", json={"visibility": "PUBLIC"}, headers=auth_headers)

    # Anonymous visitor can now view the portfolio
    res_public_view = client.get("/api/v1/portfolios/dev-jordan")
    assert res_public_view.status_code == 200
    public_data = res_public_view.json()

    assert public_data["custom_slug"] == "dev-jordan"
    assert public_data["visibility"] == "PUBLIC"

    # CRITICAL PRIVACY CHECK: Only PUBLIC items are visible to anonymous visitors!
    visible_item_ids = [it["id"] for it in public_data["items"]]
    assert pub_item_id in visible_item_ids
    assert priv_item_id not in visible_item_ids
    assert len(public_data["items"]) == 1

    # Owner viewing public portfolio sees ALL items (including private drafts)
    res_owner_view = client.get("/api/v1/portfolios/dev-jordan", headers=auth_headers)
    assert len(res_owner_view.json()["items"]) == 2
