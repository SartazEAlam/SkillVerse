"""Unit and integration tests for cross-disciplinary skills, disciplines, and prerequisite DAG."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_discipline_lifecycle_and_authorization(
    client: TestClient, admin_headers: dict[str, str], auth_headers: dict[str, str]
) -> None:
    """Test discipline creation requires admin, and public endpoints list active disciplines."""
    # Anonymous cannot create
    res = client.post("/api/v1/disciplines", json={"slug": "technology", "name": "Technology"})
    assert res.status_code == 401

    # Learner role cannot create (403 Forbidden)
    res = client.post(
        "/api/v1/disciplines",
        json={"slug": "technology", "name": "Technology"},
        headers=auth_headers,
    )
    assert res.status_code == 403

    # Admin creates successfully
    res = client.post(
        "/api/v1/disciplines",
        json={
            "slug": "technology",
            "name": "Technology",
            "description": "Software engineering and computer systems.",
            "icon": "code",
            "sort_order": 1,
            "is_active": True,
        },
        headers=admin_headers,
    )
    assert res.status_code == 201
    disc_data = res.json()
    assert disc_data["slug"] == "technology"
    assert disc_data["name"] == "Technology"

    # Duplicate slug rejected with 409
    res = client.post(
        "/api/v1/disciplines",
        json={"slug": "technology", "name": "Duplicate Tech"},
        headers=admin_headers,
    )
    assert res.status_code == 409

    # Public listing
    res = client.get("/api/v1/disciplines")
    assert res.status_code == 200
    items = res.json()
    assert len(items) == 1
    assert items[0]["slug"] == "technology"

    # Public retrieve by slug
    res = client.get("/api/v1/disciplines/technology")
    assert res.status_code == 200
    assert res.json()["name"] == "Technology"

    # Nonexistent slug
    res = client.get("/api/v1/disciplines/nonexistent")
    assert res.status_code == 404


def test_skill_creation_and_filtering(
    client: TestClient, admin_headers: dict[str, str], creator_headers: dict[str, str]
) -> None:
    """Test skill creation, unique slug, and query filtering."""
    # Create discipline
    disc_res = client.post(
        "/api/v1/disciplines",
        json={"slug": "communication", "name": "Communication"},
        headers=admin_headers,
    )
    disc_id = disc_res.json()["id"]

    # Creator creates foundational skill
    res = client.post(
        "/api/v1/skills",
        json={
            "slug": "speaking-confidence",
            "name": "Speaking Confidence",
            "discipline_id": disc_id,
            "difficulty_level": "FOUNDATIONAL",
            "description": "Vocal pacing and articulation.",
            "sort_order": 1,
        },
        headers=creator_headers,
    )
    assert res.status_code == 201
    skill_a = res.json()
    assert skill_a["slug"] == "speaking-confidence"

    # Creator creates intermediate skill
    res = client.post(
        "/api/v1/skills",
        json={
            "slug": "workplace-dialogue",
            "name": "Workplace Dialogue",
            "discipline_id": disc_id,
            "difficulty_level": "INTERMEDIATE",
            "description": "Cross-functional meetings.",
            "sort_order": 2,
        },
        headers=creator_headers,
    )
    assert res.status_code == 201
    assert res.json()["slug"] == "workplace-dialogue"

    # Filter by discipline
    res = client.get("/api/v1/skills?discipline=communication")
    assert res.status_code == 200
    assert len(res.json()) == 2

    # Filter by difficulty
    res = client.get("/api/v1/skills?difficulty=FOUNDATIONAL")
    assert res.status_code == 200
    items = res.json()
    assert len(items) == 1
    assert items[0]["slug"] == "speaking-confidence"

    # Search filter
    res = client.get("/api/v1/skills?search=workplace")
    assert res.status_code == 200
    items = res.json()
    assert len(items) == 1
    assert items[0]["slug"] == "workplace-dialogue"


def test_prerequisite_validation_and_cycle_detection(
    client: TestClient, admin_headers: dict[str, str], creator_headers: dict[str, str]
) -> None:
    """Test prerequisite links, self-dependency rejection, duplicate rejection, and cycle checks."""
    # Create discipline
    disc_res = client.post(
        "/api/v1/disciplines",
        json={"slug": "tech", "name": "Technology"},
        headers=admin_headers,
    )
    disc_id = disc_res.json()["id"]

    # Create 3 skills: Skill A, Skill B, Skill C
    res_a = client.post(
        "/api/v1/skills",
        json={
            "slug": "skill-a",
            "name": "Skill A",
            "discipline_id": disc_id,
            "difficulty_level": "FOUNDATIONAL",
        },
        headers=creator_headers,
    )
    res_b = client.post(
        "/api/v1/skills",
        json={
            "slug": "skill-b",
            "name": "Skill B",
            "discipline_id": disc_id,
            "difficulty_level": "INTERMEDIATE",
        },
        headers=creator_headers,
    )
    res_c = client.post(
        "/api/v1/skills",
        json={
            "slug": "skill-c",
            "name": "Skill C",
            "discipline_id": disc_id,
            "difficulty_level": "ADVANCED",
        },
        headers=creator_headers,
    )
    id_a = res_a.json()["id"]
    id_b = res_b.json()["id"]
    id_c = res_c.json()["id"]

    # 1. Reject self-dependency (A cannot require A)
    res = client.post(
        f"/api/v1/skills/{id_a}/prerequisites",
        json={"prerequisite_skill_id": id_a},
        headers=creator_headers,
    )
    assert res.status_code == 400
    assert "cannot depend on itself" in res.json()["error"]["message"]

    # 2. Add valid prerequisite: B requires A (A is prerequisite for B)
    res = client.post(
        f"/api/v1/skills/{id_b}/prerequisites",
        json={"prerequisite_skill_id": id_a},
        headers=creator_headers,
    )
    assert res.status_code == 201

    # 3. Reject duplicate prerequisite relationship
    res = client.post(
        f"/api/v1/skills/{id_b}/prerequisites",
        json={"prerequisite_skill_id": id_a},
        headers=creator_headers,
    )
    assert res.status_code == 409

    # 4. Direct 2-node cycle rejection: A cannot require B (since B already requires A)
    res = client.post(
        f"/api/v1/skills/{id_a}/prerequisites",
        json={"prerequisite_skill_id": id_b},
        headers=creator_headers,
    )
    assert res.status_code == 400
    assert "Circular dependency detected" in res.json()["error"]["message"]

    # 5. Link C requires B: path is now A -> B -> C
    res = client.post(
        f"/api/v1/skills/{id_c}/prerequisites",
        json={"prerequisite_skill_id": id_b},
        headers=creator_headers,
    )
    assert res.status_code == 201

    # 6. Transitive cycle rejection: A cannot require C (C transitively requires A via B)
    res = client.post(
        f"/api/v1/skills/{id_a}/prerequisites",
        json={"prerequisite_skill_id": id_c},
        headers=creator_headers,
    )
    assert res.status_code == 400
    assert "Circular dependency detected" in res.json()["error"]["message"]

    # Verify skill details reflect prerequisites and unlocked skills
    res = client.get("/api/v1/skills/skill-b")
    assert res.status_code == 200
    data = res.json()
    assert len(data["prerequisites"]) == 1
    assert data["prerequisites"][0]["id"] == id_a
    assert len(data["unlocked_skills"]) == 1
    assert data["unlocked_skills"][0]["id"] == id_c

    # Verify Skill Map endpoint contains all nodes and edges
    res = client.get("/api/v1/skills/taxonomy/map")
    assert res.status_code == 200
    map_data = res.json()
    assert len(map_data["nodes"]) == 3
    assert len(map_data["edges"]) == 2

    # Remove prerequisite
    del_res = client.delete(
        f"/api/v1/skills/{id_b}/prerequisites/{id_a}",
        headers=creator_headers,
    )
    assert del_res.status_code == 204

    # Verify edge removed
    res = client.get("/api/v1/skills/skill-b")
    assert len(res.json()["prerequisites"]) == 0


def test_long_prerequisite_chain_and_diamond_dag(
    client: TestClient, admin_headers: dict[str, str], creator_headers: dict[str, str]
) -> None:
    """Verify cycle detection on long dependency chains (5+ nodes) and permit valid diamond DAGs."""
    disc_res = client.post(
        "/api/v1/disciplines",
        json={"slug": "math", "name": "Mathematics"},
        headers=admin_headers,
    )
    disc_id = disc_res.json()["id"]

    # Create 5 skills: S1 -> S2 -> S3 -> S4 -> S5
    skill_ids = []
    for i in range(1, 6):
        res = client.post(
            "/api/v1/skills",
            json={
                "slug": f"skill-step-{i}",
                "name": f"Skill Step {i}",
                "discipline_id": disc_id,
                "sort_order": i,
            },
            headers=creator_headers,
        )
        assert res.status_code == 201
        skill_ids.append(res.json()["id"])

    s1, s2, s3, s4, s5 = skill_ids

    # Build linear chain: s2 requires s1; s3 requires s2; s4 requires s3; s5 requires s4
    # Learning order: s1 -> s2 -> s3 -> s4 -> s5
    for src, dst in [(s2, s1), (s3, s2), (s4, s3), (s5, s4)]:
        link_res = client.post(
            f"/api/v1/skills/{src}/prerequisites",
            json={"prerequisite_skill_id": dst},
            headers=creator_headers,
        )
        assert link_res.status_code == 201

    # Attempt to close the loop: s1 requires s5 -> must be rejected as circular dependency
    cycle_res = client.post(
        f"/api/v1/skills/{s1}/prerequisites",
        json={"prerequisite_skill_id": s5},
        headers=creator_headers,
    )
    assert cycle_res.status_code == 400
    assert "Circular dependency detected" in cycle_res.json()["error"]["message"]

    # Also test intermediate cycle: s2 requires s5 -> must be rejected
    mid_cycle = client.post(
        f"/api/v1/skills/{s2}/prerequisites",
        json={"prerequisite_skill_id": s5},
        headers=creator_headers,
    )
    assert mid_cycle.status_code == 400
    assert "Circular dependency detected" in mid_cycle.json()["error"]["message"]

    # Valid Diamond DAG: create an alternative branch s2_alt that requires s1, and s4 requires s2_alt
    alt_res = client.post(
        "/api/v1/skills",
        json={
            "slug": "skill-step-2-alt",
            "name": "Skill Step 2 Alt",
            "discipline_id": disc_id,
        },
        headers=creator_headers,
    )
    s2_alt = alt_res.json()["id"]

    res_d1 = client.post(
        f"/api/v1/skills/{s2_alt}/prerequisites",
        json={"prerequisite_skill_id": s1},
        headers=creator_headers,
    )
    assert res_d1.status_code == 201

    res_d2 = client.post(
        f"/api/v1/skills/{s4}/prerequisites",
        json={"prerequisite_skill_id": s2_alt},
        headers=creator_headers,
    )
    assert res_d2.status_code == 201  # Diamond pattern is non-cyclic and valid!

