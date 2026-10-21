"""Tests for course catalog discovery, search, filtering, pagination, and outline retrieval."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def sample_discipline(client: TestClient, admin_headers: dict[str, str]) -> dict:
    """Create a test discipline."""
    res = client.post(
        "/api/v1/disciplines",
        json={"slug": "technology", "name": "Technology"},
        headers=admin_headers,
    )
    assert res.status_code == 201
    return res.json()


@pytest.fixture
def sample_skills(
    client: TestClient, creator_headers: dict[str, str], sample_discipline: dict
) -> list[dict]:
    """Create two test skills."""
    res1 = client.post(
        "/api/v1/skills",
        json={
            "slug": "frontend-dev",
            "name": "Frontend Development",
            "discipline_id": sample_discipline["id"],
            "difficulty_level": "FOUNDATIONAL",
        },
        headers=creator_headers,
    )
    res2 = client.post(
        "/api/v1/skills",
        json={
            "slug": "backend-dev",
            "name": "Backend Development",
            "discipline_id": sample_discipline["id"],
            "difficulty_level": "INTERMEDIATE",
        },
        headers=creator_headers,
    )
    return [res1.json(), res2.json()]


def test_public_catalog_excludes_draft_courses(
    client: TestClient, creator_headers: dict[str, str], sample_discipline: dict
) -> None:
    """Unpublished draft courses must never be returned in public catalog endpoints."""
    # Create draft course
    create_res = client.post(
        "/api/v1/courses",
        json={
            "slug": "unreleased-draft-course",
            "title": "Secret In-Progress Curriculum",
            "short_description": "A draft curriculum that should not be visible publicly.",
            "discipline_id": sample_discipline["id"],
            "difficulty_level": "BEGINNER",
        },
        headers=creator_headers,
    )
    assert create_res.status_code == 201
    course_id = create_res.json()["id"]

    # Public catalog search returns 0 items
    cat_res = client.get("/api/v1/courses")
    assert cat_res.status_code == 200
    assert cat_res.json()["total"] == 0
    assert len(cat_res.json()["items"]) == 0

    # Public direct slug lookup returns 404
    slug_res = client.get("/api/v1/courses/unreleased-draft-course")
    assert slug_res.status_code == 404

    # But creator CAN access draft endpoint
    draft_res = client.get(f"/api/v1/courses/{course_id}/draft", headers=creator_headers)
    assert draft_res.status_code == 200
    assert draft_res.json()["slug"] == "unreleased-draft-course"


def test_catalog_search_filters_and_pagination(
    client: TestClient,
    creator_headers: dict[str, str],
    sample_discipline: dict,
    sample_skills: list[dict],
) -> None:
    """Test catalog filtering by discipline, difficulty, search term, and pagination."""
    # Create and publish Course 1 (Beginner)
    c1_res = client.post(
        "/api/v1/courses",
        json={
            "slug": "intro-web-architecture",
            "title": "Introduction to Web Architecture",
            "short_description": "Explore client-server fundamentals, protocols, and networks.",
            "discipline_id": sample_discipline["id"],
            "difficulty_level": "BEGINNER",
            "estimated_duration_minutes": 180,
            "skill_ids": [sample_skills[0]["id"]],
        },
        headers=creator_headers,
    )
    c1_id = c1_res.json()["id"]

    # Add module, lesson, and content to Course 1
    m1_res = client.post(
        f"/api/v1/courses/{c1_id}/draft/modules",
        json={"title": "Web Basics", "sort_order": 1},
        headers=creator_headers,
    )
    m1_id = m1_res.json()["id"]

    les1_res = client.post(
        f"/api/v1/courses/{c1_id}/draft/modules/{m1_id}/lessons",
        json={"slug": "http-basics", "title": "HTTP Basics", "sort_order": 1},
        headers=creator_headers,
    )
    les1_id = les1_res.json()["id"]

    client.put(
        f"/api/v1/courses/{c1_id}/draft/lessons/{les1_id}/content",
        json={
            "document": {
                "schema_version": "1.0",
                "learning_objectives": ["Understand HTTP"],
                "blocks": [
                    {"id": "b1", "type": "heading", "data": {"level": 2, "text": "HTTP Overview"}},
                    {
                        "id": "b2",
                        "type": "text",
                        "data": {"format": "markdown", "text": "HTTP is stateless."},
                    },
                ],
            }
        },
        headers=creator_headers,
    )

    # Publish Course 1
    pub1 = client.post(f"/api/v1/courses/{c1_id}/publish", headers=creator_headers)
    assert pub1.status_code == 200

    # Create and publish Course 2 (Intermediate)
    c2_res = client.post(
        "/api/v1/courses",
        json={
            "slug": "advanced-backend-systems",
            "title": "Advanced Backend Systems",
            "short_description": "High-throughput database concurrency and message queuing.",
            "discipline_id": sample_discipline["id"],
            "difficulty_level": "INTERMEDIATE",
            "estimated_duration_minutes": 240,
            "skill_ids": [sample_skills[1]["id"]],
        },
        headers=creator_headers,
    )
    c2_id = c2_res.json()["id"]

    m2_res = client.post(
        f"/api/v1/courses/{c2_id}/draft/modules",
        json={"title": "Concurrency", "sort_order": 1},
        headers=creator_headers,
    )
    m2_id = m2_res.json()["id"]

    les2_res = client.post(
        f"/api/v1/courses/{c2_id}/draft/modules/{m2_id}/lessons",
        json={"slug": "locks-and-mvcc", "title": "Locks and MVCC", "sort_order": 1},
        headers=creator_headers,
    )
    les2_id = les2_res.json()["id"]

    client.put(
        f"/api/v1/courses/{c2_id}/draft/lessons/{les2_id}/content",
        json={
            "document": {
                "schema_version": "1.0",
                "learning_objectives": ["Understand locks"],
                "blocks": [
                    {
                        "id": "b1",
                        "type": "heading",
                        "data": {"level": 2, "text": "Database Locking"},
                    },
                    {
                        "id": "b2",
                        "type": "text",
                        "data": {"format": "markdown", "text": "Pessimistic vs optimistic."},
                    },
                ],
            }
        },
        headers=creator_headers,
    )

    pub2 = client.post(f"/api/v1/courses/{c2_id}/publish", headers=creator_headers)
    assert pub2.status_code == 200

    # 1. Total published courses = 2
    res = client.get("/api/v1/courses")
    assert res.status_code == 200
    assert res.json()["total"] == 2
    assert len(res.json()["items"]) == 2

    # 2. Filter by difficulty = BEGINNER -> returns 1
    res = client.get("/api/v1/courses?difficulty=BEGINNER")
    assert res.status_code == 200
    assert res.json()["total"] == 1
    assert res.json()["items"][0]["slug"] == "intro-web-architecture"

    # 3. Filter by difficulty = INTERMEDIATE -> returns 1
    res = client.get("/api/v1/courses?difficulty=INTERMEDIATE")
    assert res.status_code == 200
    assert res.json()["total"] == 1
    assert res.json()["items"][0]["slug"] == "advanced-backend-systems"

    # 4. Search query
    res = client.get("/api/v1/courses?search=concurrency")
    assert res.status_code == 200
    assert res.json()["total"] == 1
    assert res.json()["items"][0]["slug"] == "advanced-backend-systems"

    # 5. Pagination (limit 1)
    res = client.get("/api/v1/courses?page=1&limit=1")
    assert res.status_code == 200
    assert res.json()["total"] == 2
    assert res.json()["pages"] == 2
    assert len(res.json()["items"]) == 1

    # 6. Retrieve published course details by slug
    res = client.get("/api/v1/courses/intro-web-architecture")
    assert res.status_code == 200
    detail = res.json()
    assert detail["title"] == "Introduction to Web Architecture"
    assert len(detail["modules"]) == 1
    assert len(detail["modules"][0]["lessons"]) == 1
    assert detail["modules"][0]["lessons"][0]["slug"] == "http-basics"
    assert len(detail["skills"]) == 1
    assert detail["skills"][0]["slug"] == "frontend-dev"

    # 7. Retrieve individual lesson by slug
    res = client.get("/api/v1/courses/intro-web-architecture/lessons/http-basics")
    assert res.status_code == 200
    les_data = res.json()
    assert les_data["slug"] == "http-basics"
    assert len(les_data["blocks"]) == 2


def test_archiving_and_unpublishing(
    client: TestClient, creator_headers: dict[str, str], sample_discipline: dict
) -> None:
    """Test that unpublishing and archiving exclude courses while preserving data."""
    # Create course with minimal structure and publish
    c_res = client.post(
        "/api/v1/courses",
        json={
            "slug": "lifecycle-course",
            "title": "Lifecycle Testing Course",
            "short_description": "Testing publish, unpublish, and archive transitions.",
            "discipline_id": sample_discipline["id"],
        },
        headers=creator_headers,
    )
    c_id = c_res.json()["id"]

    m_res = client.post(
        f"/api/v1/courses/{c_id}/draft/modules",
        json={"title": "Module 1"},
        headers=creator_headers,
    )
    l_res = client.post(
        f"/api/v1/courses/{c_id}/draft/modules/{m_res.json()['id']}/lessons",
        json={"slug": "l1", "title": "Lesson 1"},
        headers=creator_headers,
    )
    client.put(
        f"/api/v1/courses/{c_id}/draft/lessons/{l_res.json()['id']}/content",
        json={
            "document": {
                "schema_version": "1.0",
                "blocks": [
                    {"id": "b1", "type": "text", "data": {"format": "plain", "text": "Content"}}
                ],
            }
        },
        headers=creator_headers,
    )

    client.post(f"/api/v1/courses/{c_id}/publish", headers=creator_headers)
    assert client.get("/api/v1/courses/lifecycle-course").status_code == 200

    # Unpublish course -> catalog returns 404
    unpub_res = client.post(f"/api/v1/courses/{c_id}/unpublish", headers=creator_headers)
    assert unpub_res.status_code == 200
    assert client.get("/api/v1/courses/lifecycle-course").status_code == 404

    # Archive course -> catalog returns 404
    arch_res = client.post(f"/api/v1/courses/{c_id}/archive", headers=creator_headers)
    assert arch_res.status_code == 200
    assert client.get("/api/v1/courses/lifecycle-course").status_code == 404


def test_deterministic_module_lesson_and_block_ordering(
    client: TestClient, creator_headers: dict[str, str], sample_discipline: dict
) -> None:
    """Modules, lessons, and blocks must always be returned in deterministic sort_order regardless of insertion sequence."""
    c_res = client.post(
        "/api/v1/courses",
        json={
            "slug": "ordering-test-course",
            "title": "Deterministic Ordering Test",
            "short_description": "Testing stable ordering across hierarchy levels.",
            "discipline_id": sample_discipline["id"],
        },
        headers=creator_headers,
    )
    c_id = c_res.json()["id"]

    # Insert Module 2 FIRST, then Module 1
    m2_res = client.post(
        f"/api/v1/courses/{c_id}/draft/modules",
        json={"title": "Second Module", "sort_order": 2},
        headers=creator_headers,
    )
    m2_id = m2_res.json()["id"]

    m1_res = client.post(
        f"/api/v1/courses/{c_id}/draft/modules",
        json={"title": "First Module", "sort_order": 1},
        headers=creator_headers,
    )
    m1_id = m1_res.json()["id"]

    # In Module 1, insert Lesson B (sort_order=2) FIRST, then Lesson A (sort_order=1)
    client.post(
        f"/api/v1/courses/{c_id}/draft/modules/{m1_id}/lessons",
        json={"slug": "lesson-b", "title": "Lesson B", "sort_order": 2},
        headers=creator_headers,
    )
    l1a_res = client.post(
        f"/api/v1/courses/{c_id}/draft/modules/{m1_id}/lessons",
        json={"slug": "lesson-a", "title": "Lesson A", "sort_order": 1},
        headers=creator_headers,
    )
    l1a_id = l1a_res.json()["id"]

    # Provide blocks for both lessons in Module 1 and lesson in Module 2
    client.put(
        f"/api/v1/courses/{c_id}/draft/lessons/{l1a_id}/content",
        json={
            "document": {
                "schema_version": "1.0",
                "blocks": [
                    {"id": "b1", "type": "heading", "data": {"level": 2, "text": "H1"}},
                    {"id": "b2", "type": "text", "data": {"format": "plain", "text": "T1"}},
                ],
            }
        },
        headers=creator_headers,
    )

    # In Module 2, add Lesson C
    l2_res = client.post(
        f"/api/v1/courses/{c_id}/draft/modules/{m2_id}/lessons",
        json={"slug": "lesson-c", "title": "Lesson C", "sort_order": 1},
        headers=creator_headers,
    )
    client.put(
        f"/api/v1/courses/{c_id}/draft/lessons/{l2_res.json()['id']}/content",
        json={
            "document": {
                "schema_version": "1.0",
                "blocks": [{"id": "b1", "type": "text", "data": {"format": "plain", "text": "M2"}}],
            }
        },
        headers=creator_headers,
    )

    # Add content to Lesson B so publication passes
    draft_info = client.get(f"/api/v1/courses/{c_id}/draft", headers=creator_headers).json()
    l1b_id = next(
        les["id"]
        for mod in draft_info["modules"]
        for les in mod["lessons"]
        if les["slug"] == "lesson-b"
    )
    client.put(
        f"/api/v1/courses/{c_id}/draft/lessons/{l1b_id}/content",
        json={
            "document": {
                "schema_version": "1.0",
                "blocks": [{"id": "b1", "type": "text", "data": {"format": "plain", "text": "LB"}}],
            }
        },
        headers=creator_headers,
    )

    # Publish
    pub_res = client.post(f"/api/v1/courses/{c_id}/publish", headers=creator_headers)
    assert pub_res.status_code == 200

    # Retrieve published course outline
    course_detail = client.get("/api/v1/courses/ordering-test-course").json()
    # Modules must be in sort_order order: Module 1 first, Module 2 second
    assert course_detail["modules"][0]["title"] == "First Module"
    assert course_detail["modules"][0]["sort_order"] == 1
    assert course_detail["modules"][1]["title"] == "Second Module"
    assert course_detail["modules"][1]["sort_order"] == 2

    # Lessons within Module 1 must be sorted: Lesson A first, Lesson B second
    mod1_lessons = course_detail["modules"][0]["lessons"]
    assert mod1_lessons[0]["slug"] == "lesson-a"
    assert mod1_lessons[0]["sort_order"] == 1
    assert mod1_lessons[1]["slug"] == "lesson-b"
    assert mod1_lessons[1]["sort_order"] == 2

