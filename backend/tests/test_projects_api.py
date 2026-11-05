"""API tests for project catalog discovery, authoring, publishing, and archiving."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.modules.skills.models import Discipline, Skill, SkillDifficulty


@pytest.fixture
def project_taxonomy(db: Session) -> dict[str, str]:
    """Seed test disciplines and skills for project authoring."""
    discipline = Discipline(
        slug="technology-api",
        name="Technology",
        description="Computer science, engineering, and software development",
    )
    db.add(discipline)
    db.commit()

    skill_fastapi = Skill(
        slug="fastapi-core",
        name="FastAPI Development",
        discipline_id=discipline.id,
        difficulty_level=SkillDifficulty.INTERMEDIATE,
    )
    skill_sql = Skill(
        slug="sql-architecture",
        name="Relational Database Design",
        discipline_id=discipline.id,
        difficulty_level=SkillDifficulty.ADVANCED,
    )
    db.add_all([skill_fastapi, skill_sql])
    db.commit()

    return {
        "discipline_id": discipline.id,
        "skill_fastapi_id": skill_fastapi.id,
        "skill_sql_id": skill_sql.id,
    }


def test_create_project_as_creator(
    client: TestClient,
    creator_headers: dict[str, str],
    project_taxonomy: dict[str, str],
) -> None:
    """Creator can author a new project draft with valid requirements and rubric."""
    payload = {
        "title": "Cloud Inventory Service",
        "slug": "cloud-inventory-service",
        "short_description": "Build a scalable cloud inventory API service using FastAPI.",
        "full_description": "Comprehensive capstone project requiring database migrations, rate limiting, and secure endpoints.",
        "discipline_id": project_taxonomy["discipline_id"],
        "difficulty_level": "INTERMEDIATE",
        "estimated_duration_hours": 15,
        "requirements": {
            "milestones": [
                {"id": "m1", "title": "Schema Design", "description": "Model inventory items"},
                {"id": "m2", "title": "API Routes", "description": "Implement CRUD endpoints"},
            ],
            "deliverables": ["GitHub repository link", "Live documentation URL"],
        },
        "evaluation_criteria": {
            "passing_score": 75.0,
            "rubric": [
                {"id": "c1", "title": "Database Schema", "max_score": 40.0, "weight": 1.0},
                {"id": "c2", "title": "API Correctness", "max_score": 60.0, "weight": 1.0},
            ],
        },
        "starter_resources": [
            {"title": "Starter Repo", "url": "https://github.com/example/inventory-starter"}
        ],
        "skills": [
            {"skill_id": project_taxonomy["skill_fastapi_id"], "is_primary": True},
            {"skill_id": project_taxonomy["skill_sql_id"], "is_primary": False},
        ],
    }

    res = client.post("/api/v1/projects", json=payload, headers=creator_headers)
    assert res.status_code == 201
    data = res.json()
    assert data["title"] == "Cloud Inventory Service"
    assert data["slug"] == "cloud-inventory-service"
    assert data["status"] == "DRAFT"
    assert len(data["skills"]) == 2
    fastapi_skill = next(
        s for s in data["skills"] if s["skill_id"] == project_taxonomy["skill_fastapi_id"]
    )
    assert fastapi_skill["is_primary"] is True
    assert data["requirements"]["milestones"][0]["id"] == "m1"


def test_create_project_forbidden_for_learner(
    client: TestClient,
    auth_headers: dict[str, str],
    project_taxonomy: dict[str, str],
) -> None:
    """Learners cannot author projects."""
    payload = {
        "title": "Unauthorized Project",
        "short_description": "Short description for project",
        "full_description": "Full description for project here with enough words.",
        "discipline_id": project_taxonomy["discipline_id"],
        "skills": [{"skill_id": project_taxonomy["skill_fastapi_id"], "is_primary": True}],
    }
    res = client.post("/api/v1/projects", json=payload, headers=auth_headers)
    assert res.status_code == 403


def test_create_project_validation_errors(
    client: TestClient,
    creator_headers: dict[str, str],
    project_taxonomy: dict[str, str],
) -> None:
    """Invalid discipline or missing skills yield 422 validation errors."""
    bad_payload = {
        "title": "Bad Project",
        "short_description": "Short description for project.",
        "full_description": "Full description with enough length for project.",
        "discipline_id": "non-existent-discipline-id",
        "skills": [{"skill_id": project_taxonomy["skill_fastapi_id"], "is_primary": True}],
    }
    res = client.post("/api/v1/projects", json=bad_payload, headers=creator_headers)
    assert res.status_code == 422


def test_publish_project_completeness_validation(
    client: TestClient,
    creator_headers: dict[str, str],
    project_taxonomy: dict[str, str],
) -> None:
    """Publishing fails if milestones or passing criteria are missing."""
    incomplete_payload = {
        "title": "Incomplete Project Spec",
        "short_description": "Short description for testing completeness.",
        "full_description": "Full description for testing project completeness validations.",
        "discipline_id": project_taxonomy["discipline_id"],
        "skills": [{"skill_id": project_taxonomy["skill_fastapi_id"], "is_primary": True}],
    }
    res = client.post("/api/v1/projects", json=incomplete_payload, headers=creator_headers)
    assert res.status_code == 201
    proj_id = res.json()["id"]

    # Attempt to publish incomplete project
    pub_res = client.post(f"/api/v1/projects/{proj_id}/publish", headers=creator_headers)
    assert pub_res.status_code == 422
    assert "cannot be published" in pub_res.json()["error"]["message"]

    # Update with required milestones and rubric
    update_payload = {
        "requirements": {
            "milestones": [{"id": "m1", "title": "Milestone 1", "description": "Complete setup"}]
        },
        "evaluation_criteria": {
            "passing_score": 70.0,
            "rubric": [{"id": "crit-1", "title": "Architecture", "max_score": 100.0, "weight": 1.0}],
        },
    }
    patch_res = client.patch(f"/api/v1/projects/{proj_id}", json=update_payload, headers=creator_headers)
    assert patch_res.status_code == 200

    # Publish again - should succeed
    pub_res2 = client.post(f"/api/v1/projects/{proj_id}/publish", headers=creator_headers)
    assert pub_res2.status_code == 200
    assert pub_res2.json()["status"] == "PUBLISHED"


def test_project_visibility_and_catalog_discovery(
    client: TestClient,
    creator_headers: dict[str, str],
    auth_headers: dict[str, str],
    project_taxonomy: dict[str, str],
) -> None:
    """Learners see only PUBLISHED projects in discovery list and detail endpoints."""
    # 1. Author draft project
    payload = {
        "title": "Secret Draft Project",
        "short_description": "Internal work in progress project.",
        "full_description": "Comprehensive specification for an internal draft project.",
        "discipline_id": project_taxonomy["discipline_id"],
        "difficulty_level": "ADVANCED",
        "requirements": {"milestones": [{"id": "m1", "title": "M1"}]},
        "evaluation_criteria": {
            "passing_score": 80.0,
            "rubric": [{"id": "c1", "max_score": 100.0}],
        },
        "skills": [{"skill_id": project_taxonomy["skill_fastapi_id"], "is_primary": True}],
    }
    res = client.post("/api/v1/projects", json=payload, headers=creator_headers)
    assert res.status_code == 201
    draft_id = res.json()["id"]

    # 2. Learner queries catalog: draft should NOT appear
    learner_list = client.get("/api/v1/projects", headers=auth_headers)
    assert learner_list.status_code == 200
    ids = [p["id"] for p in learner_list.json()["items"]]
    assert draft_id not in ids

    # 3. Learner tries direct GET on draft: returns 404
    direct_get = client.get(f"/api/v1/projects/{draft_id}", headers=auth_headers)
    assert direct_get.status_code == 404

    # 4. Creator direct GET on draft: succeeds
    creator_get = client.get(f"/api/v1/projects/{draft_id}", headers=creator_headers)
    assert creator_get.status_code == 200
    assert creator_get.json()["id"] == draft_id

    # 5. Creator publishes project
    pub = client.post(f"/api/v1/projects/{draft_id}/publish", headers=creator_headers)
    assert pub.status_code == 200

    # 6. Learner queries catalog: now visible!
    learner_list2 = client.get("/api/v1/projects", headers=auth_headers)
    assert learner_list2.status_code == 200
    ids2 = [p["id"] for p in learner_list2.json()["items"]]
    assert draft_id in ids2

    # 7. Learner direct GET: now succeeds
    direct_get2 = client.get(f"/api/v1/projects/{draft_id}", headers=auth_headers)
    assert direct_get2.status_code == 200
    assert direct_get2.json()["title"] == "Secret Draft Project"


def test_archive_project(
    client: TestClient,
    creator_headers: dict[str, str],
    project_taxonomy: dict[str, str],
) -> None:
    """Creator can archive an existing project."""
    payload = {
        "title": "Project to Archive",
        "short_description": "Short description of project to archive.",
        "full_description": "Full detailed description of project to archive.",
        "discipline_id": project_taxonomy["discipline_id"],
        "skills": [{"skill_id": project_taxonomy["skill_fastapi_id"], "is_primary": True}],
    }
    create_res = client.post("/api/v1/projects", json=payload, headers=creator_headers)
    assert create_res.status_code == 201
    proj_id = create_res.json()["id"]

    arch_res = client.post(f"/api/v1/projects/{proj_id}/archive", headers=creator_headers)
    assert arch_res.status_code == 200
    assert arch_res.json()["status"] == "ARCHIVED"
