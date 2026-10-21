"""Tests for course version immutability, draft isolation, and transactional publication."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.courses.models import Course, CourseVersion


def test_publishing_validation_checks(
    client: TestClient, creator_headers: dict[str, str], admin_headers: dict[str, str]
) -> None:
    """Publishing must fail if modules, lessons, or blocks are missing."""
    # Create discipline and blank course
    disc_res = client.post(
        "/api/v1/disciplines",
        json={"slug": "general", "name": "General"},
        headers=admin_headers,
    )
    disc_id = disc_res.json()["id"]

    c_res = client.post(
        "/api/v1/courses",
        json={
            "slug": "empty-course",
            "title": "Empty Course",
            "short_description": "A course with no modules yet.",
            "discipline_id": disc_id,
        },
        headers=creator_headers,
    )
    c_id = c_res.json()["id"]

    # 1. Publish with no modules -> fails with 400
    res = client.post(f"/api/v1/courses/{c_id}/publish", headers=creator_headers)
    assert res.status_code == 400
    assert "without any modules" in res.json()["error"]["message"]

    # 2. Add module with no lessons -> fails with 400
    m_res = client.post(
        f"/api/v1/courses/{c_id}/draft/modules",
        json={"title": "Module 1"},
        headers=creator_headers,
    )
    m_id = m_res.json()["id"]

    res = client.post(f"/api/v1/courses/{c_id}/publish", headers=creator_headers)
    assert res.status_code == 400
    assert "has no lessons" in res.json()["error"]["message"]

    # 3. Add lesson with no blocks -> fails with 400
    l_res = client.post(
        f"/api/v1/courses/{c_id}/draft/modules/{m_id}/lessons",
        json={"slug": "l1", "title": "Lesson 1"},
        headers=creator_headers,
    )
    assert l_res.status_code == 201

    res = client.post(f"/api/v1/courses/{c_id}/publish", headers=creator_headers)
    assert res.status_code == 400
    assert "has no content blocks" in res.json()["error"]["message"]


def test_version_snapshot_and_immutability(
    client: TestClient, creator_headers: dict[str, str], admin_headers: dict[str, str], db: Session
) -> None:
    """Publishing creates an immutable snapshot.

    Subsequent draft edits must NOT mutate earlier published versions.
    """
    disc_res = client.post(
        "/api/v1/disciplines",
        json={"slug": "engineering", "name": "Engineering"},
        headers=admin_headers,
    )
    disc_id = disc_res.json()["id"]

    # 1. Create course
    c_res = client.post(
        "/api/v1/courses",
        json={
            "slug": "immutable-systems",
            "title": "Immutable Systems Architecture",
            "short_description": "Building append-only architectures.",
            "discipline_id": disc_id,
        },
        headers=creator_headers,
    )
    c_id = c_res.json()["id"]

    # Add Module 1 and Lesson 1 with Content V1
    m_res = client.post(
        f"/api/v1/courses/{c_id}/draft/modules",
        json={"title": "Module V1", "sort_order": 1},
        headers=creator_headers,
    )
    m_id = m_res.json()["id"]

    l_res = client.post(
        f"/api/v1/courses/{c_id}/draft/modules/{m_id}/lessons",
        json={"slug": "intro-immutability", "title": "Intro Immutability", "sort_order": 1},
        headers=creator_headers,
    )
    l_id = l_res.json()["id"]

    client.put(
        f"/api/v1/courses/{c_id}/draft/lessons/{l_id}/content",
        json={
            "document": {
                "schema_version": "1.0",
                "learning_objectives": ["Understand Version 1"],
                "blocks": [
                    {
                        "id": "b1",
                        "type": "text",
                        "data": {"format": "plain", "text": "Original text v1"},
                    },
                ],
            }
        },
        headers=creator_headers,
    )

    # 2. Publish Version 1
    pub1 = client.post(
        f"/api/v1/courses/{c_id}/publish",
        json={"changelog": "First official release v1.0"},
        headers=creator_headers,
    )
    assert pub1.status_code == 200
    v1_data = pub1.json()
    assert v1_data["version_number"] == 1
    v1_id = v1_data["version_id"]

    # 3. Create or access working draft for Version 2
    # In our system, get_or_create_draft clones the current published version into draft v0
    draft_res = client.get(f"/api/v1/courses/{c_id}/draft", headers=creator_headers)
    assert draft_res.status_code == 200
    draft_data = draft_res.json()
    assert draft_data["version_id"] != v1_id  # Cloned draft has a distinct version ID!
    draft_l_id = draft_data["modules"][0]["lessons"][0]["id"]

    # 4. Modify draft: update text content in draft lesson to "Modified text v2"
    client.put(
        f"/api/v1/courses/{c_id}/draft/lessons/{draft_l_id}/content",
        json={
            "document": {
                "schema_version": "1.0",
                "learning_objectives": ["Understand Version 2"],
                "blocks": [
                    {
                        "id": "b1",
                        "type": "text",
                        "data": {"format": "plain", "text": "Modified text v2"},
                    },
                ],
            }
        },
        headers=creator_headers,
    )

    # Add a brand new Module 2 to the draft
    client.post(
        f"/api/v1/courses/{c_id}/draft/modules",
        json={"title": "Brand New Module 2", "sort_order": 2},
        headers=creator_headers,
    )

    # 5. VERIFY IMMUTABILITY: The public catalog endpoint (serving v1) remains UNCHANGED!
    pub_view = client.get("/api/v1/courses/immutable-systems")
    assert pub_view.status_code == 200
    assert pub_view.json()["version_number"] == 1
    assert len(pub_view.json()["modules"]) == 1
    assert pub_view.json()["modules"][0]["title"] == "Module V1"
    assert (
        pub_view.json()["modules"][0]["lessons"][0]["blocks"][0]["content"]["text"]
        == "Original text v1"
    )

    # Also directly verify v1 database records
    v1_db = db.get(CourseVersion, v1_id)
    assert v1_db is not None
    assert v1_db.version_number == 1
    assert v1_db.published_at is not None
    assert len(v1_db.modules) == 1
    assert v1_db.modules[0].title == "Module V1"

    # 6. Publish Version 2
    # Before publishing, add a lesson and block to Module 2 so validation passes
    draft_after = client.get(f"/api/v1/courses/{c_id}/draft", headers=creator_headers).json()
    m2_id = draft_after["modules"][1]["id"]
    l2_res = client.post(
        f"/api/v1/courses/{c_id}/draft/modules/{m2_id}/lessons",
        json={"slug": "new-lesson-v2", "title": "New Lesson in V2"},
        headers=creator_headers,
    )
    l2_id = l2_res.json()["id"]
    client.put(
        f"/api/v1/courses/{c_id}/draft/lessons/{l2_id}/content",
        json={
            "document": {
                "schema_version": "1.0",
                "blocks": [
                    {
                        "id": "b1",
                        "type": "text",
                        "data": {"format": "plain", "text": "Module 2 text"},
                    }
                ],
            }
        },
        headers=creator_headers,
    )

    pub2 = client.post(
        f"/api/v1/courses/{c_id}/publish",
        json={"changelog": "Second release v2.0"},
        headers=creator_headers,
    )
    assert pub2.status_code == 200
    v2_data = pub2.json()
    assert v2_data["version_number"] == 2

    # 7. Public view now serves Version 2
    pub_view_v2 = client.get("/api/v1/courses/immutable-systems")
    assert pub_view_v2.status_code == 200
    assert pub_view_v2.json()["version_number"] == 2
    assert len(pub_view_v2.json()["modules"]) == 2

    # 8. Historical Version 1 is still in DB, completely intact!
    v1_db_recheck = db.get(CourseVersion, v1_id)
    assert v1_db_recheck.version_number == 1
    assert len(v1_db_recheck.modules) == 1
    assert v1_db_recheck.modules[0].title == "Module V1"


def test_authorization_for_draft_editing_and_publishing(
    client: TestClient,
    admin_headers: dict[str, str],
    creator_headers: dict[str, str],
    auth_headers: dict[str, str],
) -> None:
    """Only course creators and admins can view/edit drafts and publish."""
    disc_res = client.post(
        "/api/v1/disciplines",
        json={"slug": "auth-test-disc", "name": "Auth Test Discipline"},
        headers=admin_headers,
    )
    disc_id = disc_res.json()["id"]

    # Creator creates course
    c_res = client.post(
        "/api/v1/courses",
        json={
            "slug": "creator-owned-course",
            "title": "Creator Owned Course",
            "short_description": "Owned by creator@example.com.",
            "discipline_id": disc_id,
        },
        headers=creator_headers,
    )
    c_id = c_res.json()["id"]

    # Another learner user (auth_headers) attempts to view draft -> 403 Forbidden
    res = client.get(f"/api/v1/courses/{c_id}/draft", headers=auth_headers)
    assert res.status_code == 403

    # Learner user attempts to publish -> 403 Forbidden
    res = client.post(f"/api/v1/courses/{c_id}/publish", headers=auth_headers)
    assert res.status_code == 403

    # Anonymous user attempts to publish -> 401 Unauthorized
    res = client.post(f"/api/v1/courses/{c_id}/publish")
    assert res.status_code == 401

    # Admin CAN view draft and manage
    res = client.get(f"/api/v1/courses/{c_id}/draft", headers=admin_headers)
    assert res.status_code == 200


def test_server_side_metadata_and_transactional_rollback(
    client: TestClient, creator_headers: dict[str, str], admin_headers: dict[str, str], db: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify that publisher_id and published_at are set server-side and that failed publication rolls back."""
    disc_res = client.post(
        "/api/v1/disciplines",
        json={"slug": "sys-admin", "name": "System Administration"},
        headers=admin_headers,
    )
    disc_id = disc_res.json()["id"]

    c_res = client.post(
        "/api/v1/courses",
        json={
            "slug": "server-hardening",
            "title": "Server Hardening",
            "short_description": "Linux security and host defense.",
            "discipline_id": disc_id,
        },
        headers=creator_headers,
    )
    c_id = c_res.json()["id"]

    # Build valid minimal structure
    m_res = client.post(
        f"/api/v1/courses/{c_id}/draft/modules",
        json={"title": "Module 1"},
        headers=creator_headers,
    )
    l_res = client.post(
        f"/api/v1/courses/{c_id}/draft/modules/{m_res.json()['id']}/lessons",
        json={"slug": "firewalls", "title": "Firewalls"},
        headers=creator_headers,
    )
    client.put(
        f"/api/v1/courses/{c_id}/draft/lessons/{l_res.json()['id']}/content",
        json={
            "document": {
                "schema_version": "1.0",
                "blocks": [{"id": "b1", "type": "text", "data": {"format": "plain", "text": "iptables"}}],
            }
        },
        headers=creator_headers,
    )

    # 1. Successful publication sets server-side metadata (publisher_id and published_at)
    pub_res = client.post(
        f"/api/v1/courses/{c_id}/publish",
        json={
            "changelog": "v1.0",
            # Attempt to forge publisher_id and published_at - the server-side Pydantic schema ignores them
            "publisher_id": "forged-id",
            "published_at": "1999-01-01T00:00:00Z",
        },
        headers=creator_headers,
    )
    assert pub_res.status_code == 200
    v1_id = pub_res.json()["version_id"]

    v1_db = db.get(CourseVersion, v1_id)
    assert v1_db is not None
    assert v1_db.publisher_id != "forged-id"  # Not forged!
    assert v1_db.published_at.year >= 2026

    # 2. Test transactional rollback when commit fails
    # Create draft for v2
    client.get(f"/api/v1/courses/{c_id}/draft", headers=creator_headers)

    # Monkeypatch db.commit in CourseService.publish_course to simulate unexpected DB failure
    from app.modules.courses import service as course_service_module

    def failing_commit():
        raise RuntimeError("Simulated database failure during publication commit")

    monkeypatch.setattr(course_service_module.Session, "commit", lambda self: failing_commit())

    fail_res = client.post(f"/api/v1/courses/{c_id}/publish", headers=creator_headers)
    assert fail_res.status_code == 500
    assert "PUBLISH_TRANSACTION_FAILED" in fail_res.json()["error"]["code"]

    # Revert monkeypatch and verify DB state remains at v1
    monkeypatch.undo()

    # The course current_version_id is still v1, NOT v2!
    db.expire_all()
    course_db = db.get(Course, c_id)
    assert course_db.current_version_id == v1_id
    assert course_db.current_version.version_number == 1


def test_version_number_uniqueness_constraint(db: Session, admin_headers: dict[str, str], client: TestClient, creator_headers: dict[str, str]) -> None:
    """Database constraint uq_course_version_number prevents duplicate version numbers for the same course."""
    disc_res = client.post(
        "/api/v1/disciplines",
        json={"slug": "db-internals", "name": "DB Internals"},
        headers=admin_headers,
    )
    disc_id = disc_res.json()["id"]

    c_res = client.post(
        "/api/v1/courses",
        json={
            "slug": "acid-transactions",
            "title": "ACID Transactions",
            "short_description": "Concurrency control and isolation.",
            "discipline_id": disc_id,
        },
        headers=creator_headers,
    )
    c_id = c_res.json()["id"]

    # Directly insert two versions with version_number=1 for the same course
    v1_a = CourseVersion(
        course_id=c_id,
        version_number=1,
        title="Version 1A",
    )
    db.add(v1_a)
    db.commit()

    v1_b = CourseVersion(
        course_id=c_id,
        version_number=1,
        title="Duplicate Version 1B",
    )
    db.add(v1_b)
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()

