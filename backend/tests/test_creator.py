"""Comprehensive test suite for Phase 7: Creator Studio and Course Authoring."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.modules.activities.models import Activity, GradingConfig
from app.modules.auth.models import User, UserRole
from app.modules.courses.models import Course, CourseVersion, Lesson, Module
from app.modules.skills.models import Discipline, Skill


@pytest.fixture
def test_discipline(db: Session) -> Discipline:
    disc = Discipline(name="Software Engineering", slug="software-engineering", is_active=True)
    db.add(disc)
    db.commit()
    db.refresh(disc)
    return disc


@pytest.fixture
def test_skill(db: Session, test_discipline: Discipline) -> Skill:
    skill = Skill(
        discipline_id=test_discipline.id,
        name="Python Programming",
        slug="python-programming",
        description="Core Python concepts and syntax",
        is_active=True,
    )
    db.add(skill)
    db.commit()
    db.refresh(skill)
    return skill


@pytest.fixture
def second_creator_headers(client: TestClient, db: Session) -> dict[str, str]:
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "creator2@example.com",
            "password": "SecureP@ss2",
            "display_name": "Creator Two",
        },
    )
    user = db.query(User).filter(User.email == "creator2@example.com").first()
    user.role = UserRole.CREATOR
    db.commit()
    res = client.post(
        "/api/v1/auth/login",
        json={"email": "creator2@example.com", "password": "SecureP@ss2"},
    )
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


# ── Creator Authorization & Managed Courses List ───────────────────────────


def test_managed_courses_creator_authorization(
    client: TestClient, creator_headers: dict[str, str], auth_headers: dict[str, str]
):
    """Learners cannot access /courses/managed, but creators can."""
    # Learner access -> 403 Forbidden
    res = client.get("/api/v1/courses/managed", headers=auth_headers)
    assert res.status_code == 403

    # Creator access -> 200 OK
    res = client.get("/api/v1/courses/managed", headers=creator_headers)
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert "total" in data


def test_creator_course_creation_and_listing(
    client: TestClient,
    creator_headers: dict[str, str],
    test_discipline: Discipline,
    test_skill: Skill,
):
    """Creator creates a draft course and sees it in their managed courses."""
    create_payload = {
        "title": "Intro to Advanced Python",
        "slug": "intro-advanced-python",
        "short_description": "Learn modern Python constructs and best practices.",
        "full_description": "Comprehensive course covering typing, concurrency, and architecture.",
        "discipline_id": test_discipline.id,
        "difficulty_level": "INTERMEDIATE",
        "estimated_duration_minutes": 180,
        "learning_objectives": ["Understand typing", "Master async"],
        "skill_ids": [test_skill.id],
    }
    create_res = client.post("/api/v1/courses", json=create_payload, headers=creator_headers)
    assert create_res.status_code == 201
    course_data = create_res.json()
    course_id = course_data["id"]
    assert course_data["title"] == "Intro to Advanced Python"
    assert course_data["status"] == "DRAFT"

    # Listed in managed courses
    managed_res = client.get("/api/v1/courses/managed", headers=creator_headers)
    assert managed_res.status_code == 200
    items = managed_res.json()["items"]
    assert any(c["id"] == course_id for c in items)


def test_cross_creator_isolation(
    client: TestClient,
    creator_headers: dict[str, str],
    second_creator_headers: dict[str, str],
    test_discipline: Discipline,
):
    """Creator 2 cannot edit or delete Creator 1's course draft."""
    create_res = client.post(
        "/api/v1/courses",
        json={
            "title": "Creator 1 Exclusive Course",
            "slug": "creator-1-course",
            "short_description": "Exclusive course.",
            "discipline_id": test_discipline.id,
            "difficulty_level": "BEGINNER",
        },
        headers=creator_headers,
    )
    assert create_res.status_code == 201
    course_id = create_res.json()["id"]

    # Creator 2 attempts to get draft -> 403 Forbidden
    res = client.get(f"/api/v1/courses/{course_id}/draft", headers=second_creator_headers)
    assert res.status_code == 403

    # Creator 2 attempts to update course -> 403 Forbidden
    res = client.patch(
        f"/api/v1/courses/{course_id}",
        json={"title": "Hacked Title"},
        headers=second_creator_headers,
    )
    assert res.status_code == 403

    # Creator 2 attempts to delete course -> 403 Forbidden
    res = client.delete(f"/api/v1/courses/{course_id}", headers=second_creator_headers)
    assert res.status_code == 403


# ── Curriculum Organization: Modules, Lessons, Reordering ─────────────────


def test_draft_curriculum_crud_and_reorder(
    client: TestClient, creator_headers: dict[str, str], test_discipline: Discipline
):
    """Creator can manage modules, lessons, and batch reorder the curriculum."""
    # 1. Create course
    course_res = client.post(
        "/api/v1/courses",
        json={
            "title": "Curriculum Test Course",
            "slug": "curriculum-test-course",
            "short_description": "Testing curriculum hierarchy.",
            "discipline_id": test_discipline.id,
            "difficulty_level": "BEGINNER",
        },
        headers=creator_headers,
    )
    course_id = course_res.json()["id"]

    # 2. Add two modules
    m1_res = client.post(
        f"/api/v1/courses/{course_id}/draft/modules",
        json={"title": "Module 1", "description": "First module", "sort_order": 0},
        headers=creator_headers,
    )
    assert m1_res.status_code == 201
    m1_id = m1_res.json()["id"]

    m2_res = client.post(
        f"/api/v1/courses/{course_id}/draft/modules",
        json={"title": "Module 2", "description": "Second module", "sort_order": 1},
        headers=creator_headers,
    )
    assert m2_res.status_code == 201
    m2_id = m2_res.json()["id"]

    # 3. Add lessons to module 1
    l1_res = client.post(
        f"/api/v1/courses/{course_id}/draft/modules/{m1_id}/lessons",
        json={
            "title": "Lesson 1A",
            "slug": "lesson-1a",
            "description": "First lesson",
            "sort_order": 0,
            "estimated_minutes": 15,
        },
        headers=creator_headers,
    )
    assert l1_res.status_code == 201
    l1_id = l1_res.json()["id"]

    l2_res = client.post(
        f"/api/v1/courses/{course_id}/draft/modules/{m1_id}/lessons",
        json={
            "title": "Lesson 1B",
            "slug": "lesson-1b",
            "description": "Second lesson",
            "sort_order": 1,
            "estimated_minutes": 20,
        },
        headers=creator_headers,
    )
    assert l2_res.status_code == 201
    l2_id = l2_res.json()["id"]

    # 4. Batch Reorder: swap module order, move lesson 1A to module 2
    reorder_payload = {
        "modules": [
            {"id": m1_id, "sort_order": 1},
            {"id": m2_id, "sort_order": 0},
        ],
        "lessons": [
            {"id": l1_id, "module_id": m2_id, "sort_order": 0},
            {"id": l2_id, "module_id": m1_id, "sort_order": 0},
        ],
    }
    reorder_res = client.post(
        f"/api/v1/courses/{course_id}/draft/reorder",
        json=reorder_payload,
        headers=creator_headers,
    )
    assert reorder_res.status_code == 200

    # 5. Verify updated draft structure
    draft_res = client.get(f"/api/v1/courses/{course_id}/draft", headers=creator_headers)
    assert draft_res.status_code == 200
    modules = draft_res.json()["modules"]
    assert modules[0]["id"] == m2_id
    assert modules[0]["lessons"][0]["id"] == l1_id
    assert modules[1]["id"] == m1_id
    assert modules[1]["lessons"][0]["id"] == l2_id

    # 6. Delete lesson 1B
    del_l2_res = client.delete(
        f"/api/v1/courses/{course_id}/draft/lessons/{l2_id}",
        headers=creator_headers,
    )
    assert del_l2_res.status_code == 204

    # Verify lesson is removed
    draft_after_del = client.get(
        f"/api/v1/courses/{course_id}/draft", headers=creator_headers
    ).json()
    assert len(draft_after_del["modules"][1]["lessons"]) == 0


# ── Activity Authoring & Grading Secrets Protection ────────────────────────


def test_activity_authoring_lifecycle_and_security(
    client: TestClient,
    creator_headers: dict[str, str],
    auth_headers: dict[str, str],
    test_discipline: Discipline,
    test_skill: Skill,
):
    """Creator configures activities with answer keys. Learners never see answer keys."""
    # Create course with skill
    course_res = client.post(
        "/api/v1/courses",
        json={
            "title": "Activity Authoring Course",
            "slug": "activity-authoring-course",
            "short_description": "Testing activity authoring.",
            "discipline_id": test_discipline.id,
            "difficulty_level": "INTERMEDIATE",
            "skill_ids": [test_skill.id],
        },
        headers=creator_headers,
    )
    course_id = course_res.json()["id"]

    # Add module & lesson
    m_res = client.post(
        f"/api/v1/courses/{course_id}/draft/modules",
        json={"title": "Mod 1", "description": "Mod 1", "sort_order": 0},
        headers=creator_headers,
    )
    m_id = m_res.json()["id"]

    l_res = client.post(
        f"/api/v1/courses/{course_id}/draft/modules/{m_id}/lessons",
        json={"title": "Lesson 1", "slug": "lesson-1", "sort_order": 0},
        headers=creator_headers,
    )
    lesson_id = l_res.json()["id"]

    # 1. Create activity (quiz) with confidential answer key
    act_payload = {
        "lesson_id": lesson_id,
        "activity_type": "single_choice",
        "title": "Python Syntax Quiz",
        "instructions": "Select the correct output.",
        "configuration": {
            "question": "What does print(type([])) output?",
            "options": [
                {"id": "opt-1", "text": "<class 'list'>"},
                {"id": "opt-2", "text": "<class 'dict'>"},
            ],
            "skill_id": test_skill.id,
        },
        "grading_type": "automated",
        "passing_score": 80.0,
        "answer_key": {"selected_option_id": "opt-1"},
    }
    act_res = client.post("/api/v1/activities", json=act_payload, headers=creator_headers)
    assert act_res.status_code == 201
    activity_id = act_res.json()["id"]

    # Public endpoint (/activities/{id}) must NOT expose answer key
    pub_res = client.get(f"/api/v1/activities/{activity_id}")
    assert pub_res.status_code == 200
    assert "answer_key" not in pub_res.json()

    # Learner attempting authoring endpoint -> 403 Forbidden
    learner_authoring_res = client.get(
        f"/api/v1/activities/{activity_id}/authoring", headers=auth_headers
    )
    assert learner_authoring_res.status_code == 403

    # Creator authoring endpoint -> 200 OK with answer_key
    creator_authoring_res = client.get(
        f"/api/v1/activities/{activity_id}/authoring", headers=creator_headers
    )
    assert creator_authoring_res.status_code == 200
    authoring_data = creator_authoring_res.json()
    assert authoring_data["answer_key"] == {"selected_option_id": "opt-1"}
    assert authoring_data["passing_score"] == 80.0

    # 2. Update activity via PATCH /activities/{id}
    update_res = client.patch(
        f"/api/v1/activities/{activity_id}",
        json={
            "title": "Updated Python Syntax Quiz",
            "passing_score": 100.0,
            "answer_key": {"selected_option_id": "opt-2"},
        },
        headers=creator_headers,
    )
    assert update_res.status_code == 200
    assert update_res.json()["title"] == "Updated Python Syntax Quiz"
    assert update_res.json()["passing_score"] == 100.0
    assert update_res.json()["answer_key"] == {"selected_option_id": "opt-2"}

    # 3. Delete activity
    del_res = client.delete(f"/api/v1/activities/{activity_id}", headers=creator_headers)
    assert del_res.status_code == 204

    # Confirm deletion
    get_del = client.get(f"/api/v1/activities/{activity_id}")
    assert get_del.status_code == 404


# ── Draft Preview & Validation ─────────────────────────────────────────────


def test_draft_validation_and_preview(
    client: TestClient,
    creator_headers: dict[str, str],
    auth_headers: dict[str, str],
    test_discipline: Discipline,
    test_skill: Skill,
):
    """Draft validation finds incomplete structure; preview returns draft content safely."""
    # 1. Create empty course
    course_res = client.post(
        "/api/v1/courses",
        json={
            "title": "Validation Demo Course",
            "slug": "validation-demo-course",
            "short_description": "Short description of course",
            "discipline_id": test_discipline.id,
            "difficulty_level": "BEGINNER",
        },
        headers=creator_headers,
    )
    course_id = course_res.json()["id"]

    # Validate empty draft -> should have errors (no modules)
    val_res = client.get(f"/api/v1/courses/{course_id}/draft/validate", headers=creator_headers)
    assert val_res.status_code == 200
    val_data = val_res.json()
    assert val_data["valid"] is False
    assert any(e["scope"] == "course" for e in val_data["errors"])

    # Attempt to publish invalid draft -> 400 Bad Request
    pub_fail = client.post(f"/api/v1/courses/{course_id}/publish", headers=creator_headers)
    assert pub_fail.status_code == 400
    assert pub_fail.json()["error"]["code"] == "PUBLISH_VALIDATION_ERROR"

    # 2. Add module, lesson, content blocks, and activity to make it valid
    m_res = client.post(
        f"/api/v1/courses/{course_id}/draft/modules",
        json={"title": "Core Module", "description": "Foundations", "sort_order": 0},
        headers=creator_headers,
    )
    m_id = m_res.json()["id"]

    l_res = client.post(
        f"/api/v1/courses/{course_id}/draft/modules/{m_id}/lessons",
        json={"title": "Lesson Alpha", "slug": "lesson-alpha", "sort_order": 0},
        headers=creator_headers,
    )
    lesson_id = l_res.json()["id"]

    # Add content block to lesson
    client.put(
        f"/api/v1/courses/{course_id}/draft/lessons/{lesson_id}/content",
        json={
            "document": {
                "schema_version": "1.0",
                "blocks": [
                    {
                        "id": "blk-1",
                        "type": "text",
                        "data": {"text": "Welcome to Lesson Alpha!"},
                    }
                ],
            }
        },
        headers=creator_headers,
    )

    # Add activity
    client.post(
        "/api/v1/activities",
        json={
            "lesson_id": lesson_id,
            "activity_type": "single_choice",
            "title": "Alpha Quiz",
            "instructions": "Choose correctly",
            "configuration": {
                "question": "What is 2 + 2?",
                "options": [{"id": "4", "text": "4"}, {"id": "5", "text": "5"}],
            },
            "grading_type": "automated",
            "answer_key": {"selected_option_id": "4"},
        },
        headers=creator_headers,
    )

    # 3. Validate again -> now valid!
    val_res2 = client.get(f"/api/v1/courses/{course_id}/draft/validate", headers=creator_headers)
    assert val_res2.status_code == 200
    assert val_res2.json()["valid"] is True

    # 4. Preview draft
    # Learner cannot preview unpublished draft -> 403 Forbidden
    preview_learner = client.get(f"/api/v1/courses/{course_id}/draft/preview", headers=auth_headers)
    assert preview_learner.status_code == 403

    # Creator can preview draft -> 200 OK
    preview_res = client.get(f"/api/v1/courses/{course_id}/draft/preview", headers=creator_headers)
    assert preview_res.status_code == 200
    assert preview_res.json()["title"] == "Validation Demo Course"

    # Preview specific lesson
    preview_lesson = client.get(
        f"/api/v1/courses/{course_id}/draft/preview/lessons/lesson-alpha",
        headers=creator_headers,
    )
    assert preview_lesson.status_code == 200
    assert preview_lesson.json()["title"] == "Lesson Alpha"
    assert len(preview_lesson.json()["blocks"]) == 1

    # 5. Public catalog should NOT see this course yet
    pub_catalog = client.get("/api/v1/courses/validation-demo-course")
    assert pub_catalog.status_code == 404


# ── Publishing & Immutable Versioning ──────────────────────────────────────


def test_publishing_workflow_and_immutability(
    client: TestClient,
    creator_headers: dict[str, str],
    test_discipline: Discipline,
):
    """Publishing creates immutable version 1 snapshot; subsequent edits clone a new draft v0."""
    # 1. Create course, module, lesson, content
    c_res = client.post(
        "/api/v1/courses",
        json={
            "title": "Version Lifecycle Course",
            "slug": "version-lifecycle-course",
            "short_description": "Lifecycle testing",
            "discipline_id": test_discipline.id,
            "difficulty_level": "BEGINNER",
        },
        headers=creator_headers,
    )
    course_id = c_res.json()["id"]

    m_res = client.post(
        f"/api/v1/courses/{course_id}/draft/modules",
        json={"title": "Module 1", "description": "Mod 1", "sort_order": 0},
        headers=creator_headers,
    )
    m_id = m_res.json()["id"]

    l_res = client.post(
        f"/api/v1/courses/{course_id}/draft/modules/{m_id}/lessons",
        json={"title": "Lesson 1", "slug": "lesson-1", "sort_order": 0},
        headers=creator_headers,
    )
    lesson_id = l_res.json()["id"]

    client.put(
        f"/api/v1/courses/{course_id}/draft/lessons/{lesson_id}/content",
        json={
            "document": {
                "schema_version": "1.0",
                "blocks": [{"id": "b1", "type": "text", "data": {"text": "Version 1 text"}}],
            }
        },
        headers=creator_headers,
    )

    # 2. Publish version 1
    pub_res = client.post(
        f"/api/v1/courses/{course_id}/publish",
        json={"changelog": "Initial v1 release"},
        headers=creator_headers,
    )
    assert pub_res.status_code == 200
    v1_data = pub_res.json()
    assert v1_data["version_number"] == 1
    assert v1_data["published_at"] is not None

    # 3. Public catalog now returns v1
    v1_public = client.get("/api/v1/courses/version-lifecycle-course")
    assert v1_public.status_code == 200
    assert v1_public.json()["status"] == "PUBLISHED"
    assert v1_public.json()["version_number"] == 1

    # 4. Modifying course reopens a draft (cloning v1 to draft v0)
    draft_res = client.get(f"/api/v1/courses/{course_id}/draft", headers=creator_headers)
    assert draft_res.status_code == 200
    draft_data = draft_res.json()
    draft_lesson_id = draft_data["modules"][0]["lessons"][0]["id"]
    # Draft lesson ID is a clone, distinct from published v1 lesson ID
    assert draft_lesson_id != lesson_id

    # Update draft lesson content
    client.put(
        f"/api/v1/courses/{course_id}/draft/lessons/{draft_lesson_id}/content",
        json={
            "document": {
                "schema_version": "1.0",
                "blocks": [{"id": "b2", "type": "text", "data": {"text": "Version 2 draft text"}}],
            }
        },
        headers=creator_headers,
    )

    # 5. Public catalog still serves IMMUTABLE Version 1!
    v1_check = client.get("/api/v1/courses/version-lifecycle-course/lessons/lesson-1")
    assert v1_check.status_code == 200
    assert v1_check.json()["blocks"][0]["content"]["text"] == "Version 1 text"

    # 6. Publish version 2
    pub2_res = client.post(
        f"/api/v1/courses/{course_id}/publish",
        json={"changelog": "Second v2 release"},
        headers=creator_headers,
    )
    assert pub2_res.status_code == 200
    v2_data = pub2_res.json()
    assert v2_data["version_number"] == 2

    # Public catalog now serves Version 2!
    v2_check = client.get("/api/v1/courses/version-lifecycle-course/lessons/lesson-1")
    assert v2_check.status_code == 200
    assert v2_check.json()["blocks"][0]["content"]["text"] == "Version 2 draft text"


# ── Publishing Validation Hardening Regression Tests ────────────────────────


def _setup_valid_draft_curriculum(
    client: TestClient,
    creator_headers: dict[str, str],
    course_id: str,
    slug_prefix: str = "valid",
) -> tuple[str, str, str]:
    """Helper to populate a course draft with a valid module, lesson, block, and activity."""
    m_res = client.post(
        f"/api/v1/courses/{course_id}/draft/modules",
        json={"title": f"Module {slug_prefix}", "sort_order": 0},
        headers=creator_headers,
    )
    m_id = m_res.json()["id"]

    l_res = client.post(
        f"/api/v1/courses/{course_id}/draft/modules/{m_id}/lessons",
        json={"title": f"Lesson {slug_prefix}", "slug": f"lesson-{slug_prefix}", "sort_order": 0},
        headers=creator_headers,
    )
    lesson_id = l_res.json()["id"]

    client.put(
        f"/api/v1/courses/{course_id}/draft/lessons/{lesson_id}/content",
        json={
            "document": {
                "schema_version": "1.0",
                "blocks": [
                    {
                        "id": f"blk-{slug_prefix}",
                        "type": "text",
                        "data": {"text": f"Content block for {slug_prefix}."},
                    }
                ],
            }
        },
        headers=creator_headers,
    )

    act_res = client.post(
        "/api/v1/activities",
        json={
            "lesson_id": lesson_id,
            "activity_type": "single_choice",
            "title": f"Quiz {slug_prefix}",
            "instructions": "Select the correct answer.",
            "configuration": {
                "question": "What is 1 + 1?",
                "options": [{"id": "2", "text": "2"}, {"id": "3", "text": "3"}],
            },
            "grading_type": "automated",
            "answer_key": {"selected_option_id": "2"},
        },
        headers=creator_headers,
    )
    activity_id = act_res.json()["id"]
    return m_id, lesson_id, activity_id


def test_publish_fails_on_invalid_course_metadata(
    client: TestClient,
    creator_headers: dict[str, str],
    test_discipline: Discipline,
    db: Session,
) -> None:
    """A draft cannot be published if course metadata fails mandatory rules."""
    c_res = client.post(
        "/api/v1/courses",
        json={
            "slug": "metadata-hardening-course",
            "title": "Metadata Hardening Course",
            "short_description": "Validating metadata hardening rules.",
            "discipline_id": test_discipline.id,
        },
        headers=creator_headers,
    )
    course_id = c_res.json()["id"]
    _setup_valid_draft_curriculum(client, creator_headers, course_id, "meta")

    course = db.get(Course, course_id)
    assert course is not None

    # 1. Inactive discipline
    test_discipline.is_active = False
    db.commit()
    db.expire_all()

    res_disc = client.post(f"/api/v1/courses/{course_id}/publish", headers=creator_headers)
    assert res_disc.status_code == 400
    assert res_disc.json()["error"]["code"] == "PUBLISH_VALIDATION_ERROR"
    assert "Course must be assigned to an active discipline." in res_disc.json()["error"]["message"]

    # Verify validation endpoint reports same error
    val_disc = client.get(f"/api/v1/courses/{course_id}/draft/validate", headers=creator_headers)
    assert val_disc.status_code == 200
    assert val_disc.json()["valid"] is False
    assert any(
        e["message"] == "Course must be assigned to an active discipline."
        for e in val_disc.json()["errors"]
    )

    # Restore discipline
    test_discipline.is_active = True
    db.commit()
    db.expire_all()

    # 2. Course title < 3 characters
    original_title = course.title
    course.title = "AB"
    db.commit()
    db.expire_all()

    res_title = client.post(f"/api/v1/courses/{course_id}/publish", headers=creator_headers)
    assert res_title.status_code == 400
    assert res_title.json()["error"]["code"] == "PUBLISH_VALIDATION_ERROR"
    assert (
        "Course title must be at least 3 characters long." in res_title.json()["error"]["message"]
    )

    # Restore title
    course.title = original_title
    db.commit()
    db.expire_all()

    # 3. Course short_description < 10 characters
    original_desc = course.short_description
    course.short_description = "Tiny"
    db.commit()
    db.expire_all()

    res_desc = client.post(f"/api/v1/courses/{course_id}/publish", headers=creator_headers)
    assert res_desc.status_code == 400
    assert res_desc.json()["error"]["code"] == "PUBLISH_VALIDATION_ERROR"
    assert (
        "Course short description must be at least 10 characters long."
        in res_desc.json()["error"]["message"]
    )

    # Restore short description -> now publishing succeeds!
    course.short_description = original_desc
    db.commit()
    db.expire_all()

    res_ok = client.post(f"/api/v1/courses/{course_id}/publish", headers=creator_headers)
    assert res_ok.status_code == 200
    assert res_ok.json()["version_number"] == 1


def test_publish_fails_on_invalid_module_or_lesson_title(
    client: TestClient,
    creator_headers: dict[str, str],
    test_discipline: Discipline,
    db: Session,
) -> None:
    """A draft cannot be published if a module or lesson has an invalid title or missing slug."""
    c_res = client.post(
        "/api/v1/courses",
        json={
            "slug": "module-title-validation-course",
            "title": "Module Title Validation Course",
            "short_description": "Validating module and lesson title requirements.",
            "discipline_id": test_discipline.id,
        },
        headers=creator_headers,
    )
    course_id = c_res.json()["id"]
    m_id, lesson_id, _ = _setup_valid_draft_curriculum(client, creator_headers, course_id, "titles")

    mod = db.get(Module, m_id)
    les = db.get(Lesson, lesson_id)
    assert mod is not None
    assert les is not None

    # 1. Module title < 2 characters
    original_mod_title = mod.title
    mod.title = "M"
    db.commit()
    db.expire_all()

    res_mod = client.post(f"/api/v1/courses/{course_id}/publish", headers=creator_headers)
    assert res_mod.status_code == 400
    assert res_mod.json()["error"]["code"] == "PUBLISH_VALIDATION_ERROR"
    assert (
        "Module 'M' title must be at least 2 characters long." in res_mod.json()["error"]["message"]
    )

    mod.title = original_mod_title
    db.commit()
    db.expire_all()

    # 2. Lesson title < 2 characters
    original_les_title = les.title
    les.title = "L"
    db.commit()
    db.expire_all()

    res_les = client.post(f"/api/v1/courses/{course_id}/publish", headers=creator_headers)
    assert res_les.status_code == 400
    assert res_les.json()["error"]["code"] == "PUBLISH_VALIDATION_ERROR"
    assert (
        "Lesson 'L' title must be at least 2 characters long." in res_les.json()["error"]["message"]
    )

    les.title = original_les_title
    db.commit()
    db.expire_all()

    # 3. Lesson missing slug
    original_slug = les.slug
    les.slug = ""
    db.commit()
    db.expire_all()

    res_slug = client.post(f"/api/v1/courses/{course_id}/publish", headers=creator_headers)
    assert res_slug.status_code == 400
    assert res_slug.json()["error"]["code"] == "PUBLISH_VALIDATION_ERROR"
    assert "is missing a URL slug" in res_slug.json()["error"]["message"]

    les.slug = original_slug
    db.commit()
    db.expire_all()

    # 4. Module has no lessons
    client.post(
        f"/api/v1/courses/{course_id}/draft/modules",
        json={"title": "Empty Module", "sort_order": 1},
        headers=creator_headers,
    )
    res_empty_mod = client.post(f"/api/v1/courses/{course_id}/publish", headers=creator_headers)
    assert res_empty_mod.status_code == 400
    assert res_empty_mod.json()["error"]["code"] == "PUBLISH_VALIDATION_ERROR"
    assert "has no lessons" in res_empty_mod.json()["error"]["message"]


def test_publish_fails_on_invalid_activity_configuration(
    client: TestClient,
    creator_headers: dict[str, str],
    test_discipline: Discipline,
    db: Session,
) -> None:
    """A draft cannot be published if an active activity is incomplete or misconfigured."""
    c_res = client.post(
        "/api/v1/courses",
        json={
            "slug": "activity-hardening-course",
            "title": "Activity Hardening Course",
            "short_description": "Validating activity configuration requirements.",
            "discipline_id": test_discipline.id,
        },
        headers=creator_headers,
    )
    course_id = c_res.json()["id"]
    _, _, act_id = _setup_valid_draft_curriculum(client, creator_headers, course_id, "act")

    act = db.get(Activity, act_id)
    assert act is not None

    # 1. Active activity missing title
    original_title = act.title
    act.title = "   "
    db.commit()
    db.expire_all()

    res_title = client.post(f"/api/v1/courses/{course_id}/publish", headers=creator_headers)
    assert res_title.status_code == 400
    assert res_title.json()["error"]["code"] == "PUBLISH_VALIDATION_ERROR"
    assert "is missing a title" in res_title.json()["error"]["message"]

    act.title = original_title
    db.commit()
    db.expire_all()

    # 2. Active activity missing instructions
    original_instructions = act.instructions
    act.instructions = ""
    db.commit()
    db.expire_all()

    res_inst = client.post(f"/api/v1/courses/{course_id}/publish", headers=creator_headers)
    assert res_inst.status_code == 400
    assert res_inst.json()["error"]["code"] == "PUBLISH_VALIDATION_ERROR"
    assert "is missing instructions" in res_inst.json()["error"]["message"]

    act.instructions = original_instructions
    db.commit()
    db.expire_all()

    # 3. Active activity missing grading configuration
    if act.grading_config:
        db.delete(act.grading_config)
        db.commit()
        db.expire_all()

    res_no_gc = client.post(f"/api/v1/courses/{course_id}/publish", headers=creator_headers)
    assert res_no_gc.status_code == 400
    assert res_no_gc.json()["error"]["code"] == "PUBLISH_VALIDATION_ERROR"
    assert "is missing grading configuration" in res_no_gc.json()["error"]["message"]

    # 4. Activity with invalid passing score (< 0 or > 100)
    gc = GradingConfig(
        activity_id=act.id,
        grading_type="automated",
        passing_score=120.0,
        answer_key={"selected_option_id": "2"},
    )
    db.add(gc)
    db.commit()
    db.expire_all()

    res_score = client.post(f"/api/v1/courses/{course_id}/publish", headers=creator_headers)
    assert res_score.status_code == 400
    assert res_score.json()["error"]["code"] == "PUBLISH_VALIDATION_ERROR"
    assert "invalid passing score" in res_score.json()["error"]["message"]

    gc.passing_score = 75.0
    db.commit()
    db.expire_all()

    # 5. Activity skill tag references a skill not associated with this course
    unassociated_skill = Skill(
        discipline_id=test_discipline.id,
        name="Unassociated Skill",
        slug="unassociated-skill",
        description="Skill not linked to the course",
        is_active=True,
    )
    db.add(unassociated_skill)
    db.commit()
    db.refresh(unassociated_skill)

    act.configuration = {"skill_id": unassociated_skill.id}
    db.commit()
    db.expire_all()

    res_skill = client.post(f"/api/v1/courses/{course_id}/publish", headers=creator_headers)
    assert res_skill.status_code == 400
    assert res_skill.json()["error"]["code"] == "PUBLISH_VALIDATION_ERROR"
    assert "which is not associated with this course" in res_skill.json()["error"]["message"]

    # 6. Inactive activity does NOT block publish even if configuration references unassociated skill
    act.is_active = False
    db.commit()
    db.expire_all()

    res_ok = client.post(f"/api/v1/courses/{course_id}/publish", headers=creator_headers)
    assert res_ok.status_code == 200
    assert res_ok.json()["version_number"] == 1


def test_unauthorized_creator_cannot_publish_course(
    client: TestClient,
    creator_headers: dict[str, str],
    second_creator_headers: dict[str, str],
    admin_headers: dict[str, str],
    test_discipline: Discipline,
) -> None:
    """Non-owner creators cannot publish someone else's course, but admins can."""
    c_res = client.post(
        "/api/v1/courses",
        json={
            "slug": "auth-protected-course",
            "title": "Auth Protected Course",
            "short_description": "Validating authorization on publishing endpoint.",
            "discipline_id": test_discipline.id,
        },
        headers=creator_headers,
    )
    course_id = c_res.json()["id"]
    _setup_valid_draft_curriculum(client, creator_headers, course_id, "auth")

    # Unauthorized creator attempt -> 403 Forbidden
    res_unauth = client.post(f"/api/v1/courses/{course_id}/publish", headers=second_creator_headers)
    assert res_unauth.status_code == 403
    assert res_unauth.json()["error"]["code"] == "FORBIDDEN"

    # Administrator CAN publish
    res_admin = client.post(f"/api/v1/courses/{course_id}/publish", headers=admin_headers)
    assert res_admin.status_code == 200
    assert res_admin.json()["version_number"] == 1


def test_validation_endpoint_and_publishing_endpoint_agreement(
    client: TestClient,
    creator_headers: dict[str, str],
    test_discipline: Discipline,
) -> None:
    """Validation endpoint and publishing endpoint report identical mandatory validation errors."""
    c_res = client.post(
        "/api/v1/courses",
        json={
            "slug": "endpoint-agreement-course",
            "title": "Endpoint Agreement Course",
            "short_description": "Validating agreement between validate and publish.",
            "discipline_id": test_discipline.id,
        },
        headers=creator_headers,
    )
    course_id = c_res.json()["id"]

    # 1. Empty draft: both report "no modules" error
    val_res = client.get(f"/api/v1/courses/{course_id}/draft/validate", headers=creator_headers)
    pub_res = client.post(f"/api/v1/courses/{course_id}/publish", headers=creator_headers)

    assert val_res.status_code == 200
    assert val_res.json()["valid"] is False
    assert pub_res.status_code == 400
    assert pub_res.json()["error"]["code"] == "PUBLISH_VALIDATION_ERROR"
    # Mandatory error agreement
    assert pub_res.json()["error"]["message"] == val_res.json()["errors"][0]["message"]
    assert pub_res.json()["error"]["details"] == val_res.json()["errors"]

    # 2. Add valid curriculum without skill associations
    _setup_valid_draft_curriculum(client, creator_headers, course_id, "agree")

    # Validate draft -> valid: True, but contains warnings
    val_res2 = client.get(f"/api/v1/courses/{course_id}/draft/validate", headers=creator_headers)
    assert val_res2.status_code == 200
    val_data2 = val_res2.json()
    assert val_data2["valid"] is True
    assert len(val_data2["errors"]) == 0
    assert len(val_data2["warnings"]) > 0
    assert any("associated skills" in w["message"] for w in val_data2["warnings"])

    # Publishing succeeds even with skill warning!
    pub_res2 = client.post(f"/api/v1/courses/{course_id}/publish", headers=creator_headers)
    assert pub_res2.status_code == 200
    assert pub_res2.json()["version_number"] == 1


def test_valid_draft_publish_and_immutability_preservation(
    client: TestClient,
    creator_headers: dict[str, str],
    test_discipline: Discipline,
    db: Session,
) -> None:
    """Publication preserves earlier published versions as immutable and tracks historical versions."""
    c_res = client.post(
        "/api/v1/courses",
        json={
            "slug": "immutability-assurance-course",
            "title": "Immutability Assurance Course",
            "short_description": "Assuring published version immutability and history.",
            "discipline_id": test_discipline.id,
        },
        headers=creator_headers,
    )
    course_id = c_res.json()["id"]
    _, lesson_id, _ = _setup_valid_draft_curriculum(client, creator_headers, course_id, "v1")

    # Publish version 1
    pub1 = client.post(
        f"/api/v1/courses/{course_id}/publish",
        json={"changelog": "Release 1.0"},
        headers=creator_headers,
    )
    assert pub1.status_code == 200
    v1_id = pub1.json()["version_id"]
    assert pub1.json()["version_number"] == 1

    # Open fresh draft by updating curriculum
    draft_res = client.get(f"/api/v1/courses/{course_id}/draft", headers=creator_headers)
    assert draft_res.status_code == 200
    draft_lesson_id = draft_res.json()["modules"][0]["lessons"][0]["id"]
    assert draft_lesson_id != lesson_id

    # Update draft lesson block
    client.put(
        f"/api/v1/courses/{course_id}/draft/lessons/{draft_lesson_id}/content",
        json={
            "document": {
                "schema_version": "1.0",
                "blocks": [
                    {
                        "id": "blk-v2",
                        "type": "text",
                        "data": {"text": "Updated content for version 2."},
                    }
                ],
            }
        },
        headers=creator_headers,
    )

    # Verify published v1 lesson is completely unchanged
    v1_check = client.get("/api/v1/courses/immutability-assurance-course/lessons/lesson-v1")
    assert v1_check.status_code == 200
    assert v1_check.json()["blocks"][0]["content"]["text"] == "Content block for v1."

    # Publish version 2
    pub2 = client.post(
        f"/api/v1/courses/{course_id}/publish",
        json={"changelog": "Release 2.0"},
        headers=creator_headers,
    )
    assert pub2.status_code == 200
    v2_id = pub2.json()["version_id"]
    assert pub2.json()["version_number"] == 2
    assert v2_id != v1_id

    # Verify historical records in DB
    db.expire_all()
    v1_record = db.get(CourseVersion, v1_id)
    v2_record = db.get(CourseVersion, v2_id)
    assert v1_record is not None
    assert v2_record is not None
    assert v1_record.version_number == 1
    assert v1_record.is_active is False
    assert v2_record.version_number == 2
    assert v2_record.is_active is True
