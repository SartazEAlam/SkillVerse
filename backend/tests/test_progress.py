"""Comprehensive integration tests for Phase 6 — Enrollments, Progression, Mastery, and Dashboard."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.activities.models import Activity, GradingConfig
from app.modules.auth.models import User
from app.modules.courses.models import (
    Course,
    CourseSkill,
    CourseStatus,
    CourseVersion,
    Lesson,
    Module,
)
from app.modules.progress.models import (
    Achievement,
    SkillMastery,
    SkillMasteryStatus,
)
from app.modules.progress.service import ProgressionService
from app.modules.skills.models import Discipline, Skill, SkillDifficulty, SkillPrerequisite


@pytest.fixture
def test_user(db: Session, registered_user: dict) -> User:
    """Return the user instance created by registered_user fixture."""
    user_data = registered_user.get("user", registered_user)
    email = user_data.get("email", "test@example.com")
    return db.query(User).filter(User.email == email).first()


@pytest.fixture
def test_creator_user(db: Session) -> User:
    """Return a dedicated creator user instance for courses."""
    from app.modules.auth.models import UserRole
    from app.modules.auth.security import hash_password

    creator = db.query(User).filter(User.email == "course_creator@example.com").first()
    if not creator:
        creator = User(
            email="course_creator@example.com",
            password_hash=hash_password("SecureP@ss1"),
            role=UserRole.CREATOR,
        )
        db.add(creator)
        db.commit()
        db.refresh(creator)
    return creator


@pytest.fixture
def test_course_bundle(db: Session, test_creator_user: User) -> dict[str, str]:
    """Create a published course with modules, lessons, skills, and activities."""
    # 1. Create Discipline
    disc = Discipline(slug="tech-prog", name="Technology", sort_order=1)
    db.add(disc)
    db.flush()

    # 2. Create Skill and Prerequisite
    prereq_skill = Skill(
        slug="foundational-logic",
        name="Foundational Logic",
        discipline_id=disc.id,
        difficulty_level=SkillDifficulty.FOUNDATIONAL,
    )
    db.add(prereq_skill)
    db.flush()

    main_skill = Skill(
        slug="advanced-algorithms",
        name="Advanced Algorithms",
        discipline_id=disc.id,
        difficulty_level=SkillDifficulty.ADVANCED,
    )
    db.add(main_skill)
    db.flush()

    link = SkillPrerequisite(skill_id=main_skill.id, prerequisite_skill_id=prereq_skill.id)
    db.add(link)
    db.flush()

    # 3. Create Course
    course = Course(
        slug="algorithms-masterclass",
        title="Algorithms Masterclass",
        short_description="Deep dive into algorithmic complexity.",
        discipline_id=disc.id,
        status=CourseStatus.PUBLISHED,
        creator_id=test_creator_user.id,
    )
    db.add(course)
    db.flush()

    # Link skill to course
    cs = CourseSkill(course_id=course.id, skill_id=main_skill.id, is_primary=True)
    db.add(cs)

    # 4. Create CourseVersion v1
    ver = CourseVersion(
        course_id=course.id,
        version_number=1,
        title="Algorithms Masterclass v1",
        is_active=True,
    )
    db.add(ver)
    db.flush()

    course.current_version_id = ver.id

    # 5. Create Modules & Lessons
    mod1 = Module(course_version_id=ver.id, title="Module 1: Foundations", sort_order=1)
    db.add(mod1)
    db.flush()

    les1 = Lesson(module_id=mod1.id, slug="big-o-notation", title="Big O Notation", sort_order=1)
    les2 = Lesson(module_id=mod1.id, slug="binary-search", title="Binary Search", sort_order=2)
    db.add_all([les1, les2])
    db.flush()

    # 6. Create Activities for les1 and les2
    act1 = Activity(
        lesson_id=les1.id,
        activity_type="single_choice",
        title="Big O Quiz",
        instructions="Select the complexity.",
        configuration={"options": [{"id": "a", "text": "O(1)"}, {"id": "b", "text": "O(n)"}]},
    )
    db.add(act1)
    db.flush()
    db.add(GradingConfig(activity_id=act1.id, grading_type="automated", answer_key={"correct_option_id": "a"}))

    act2 = Activity(
        lesson_id=les2.id,
        activity_type="true_false",
        title="Search Invariant",
        instructions="True or False.",
        configuration={"statement": "Binary search requires sorted array."},
    )
    db.add(act2)
    db.flush()
    db.add(GradingConfig(activity_id=act2.id, grading_type="automated", answer_key={"correct_boolean": True}))

    # 7. Seed Achievements
    ach1 = Achievement(slug="first_lesson", name="First Step", description="First lesson complete.", icon="award")
    ach2 = Achievement(slug="fast_learner", name="Active Learner", description="3 lessons complete.", icon="zap")
    ach3 = Achievement(slug="first_course", name="Course Finisher", description="Course complete.", icon="trophy")
    ach4 = Achievement(slug="perfect_score", name="Sharpshooter", description="100% on test.", icon="target")
    ach5 = Achievement(slug="skill_master", name="Mastery Unlocked", description="Mastered skill.", icon="shield-check")
    ach6 = Achievement(slug="polymath", name="Cross-Disciplinary Thinker", description="2 disciplines.", icon="sparkles")
    db.add_all([ach1, ach2, ach3, ach4, ach5, ach6])

    db.commit()

    return {
        "course_id": course.id,
        "course_slug": course.slug,
        "course_version_id": ver.id,
        "prereq_skill_id": prereq_skill.id,
        "main_skill_id": main_skill.id,
        "module1_id": mod1.id,
        "lesson1_id": les1.id,
        "lesson2_id": les2.id,
        "activity1_id": act1.id,
        "activity2_id": act2.id,
    }


class TestEnrollmentLifecycle:
    """1-4: Course enrollments, idempotency, availability, and authorization."""

    def test_enroll_in_course_success(
        self, client: TestClient, auth_headers: dict[str, str], test_course_bundle: dict[str, str], db: Session, test_user: User
    ) -> None:
        """Learner can enroll in a published course with satisfied prerequisites."""
        # Grant user prerequisite skill mastery so course eligibility passes
        db.add(
            SkillMastery(
                user_id=test_user.id,
                skill_id=test_course_bundle["prereq_skill_id"],
                mastery_level=80.0,
                status=SkillMasteryStatus.PROVISIONAL.value,
            )
        )
        db.commit()

        res = client.post(
            f"/api/v1/courses/{test_course_bundle['course_slug']}/enroll",
            headers=auth_headers,
        )
        assert res.status_code == 201
        data = res.json()
        assert data["course_slug"] == test_course_bundle["course_slug"]
        assert data["status"] == "ENROLLED"
        assert data["lessons_total"] == 2
        assert data["lessons_completed"] == 0
        assert data["progress_percentage"] == 0.0

    def test_duplicate_enrollment_prevention_is_idempotent(
        self, client: TestClient, auth_headers: dict[str, str], test_course_bundle: dict[str, str], db: Session, test_user: User
    ) -> None:
        """Duplicate enrollment requests return existing enrollment cleanly without errors."""
        db.add(
            SkillMastery(
                user_id=test_user.id,
                skill_id=test_course_bundle["prereq_skill_id"],
                mastery_level=80.0,
                status=SkillMasteryStatus.PROVISIONAL.value,
            )
        )
        db.commit()

        res1 = client.post(f"/api/v1/courses/{test_course_bundle['course_slug']}/enroll", headers=auth_headers)
        assert res1.status_code == 201
        enr_id = res1.json()["id"]

        # Second enrollment attempt
        res2 = client.post(f"/api/v1/courses/{test_course_bundle['course_slug']}/enroll", headers=auth_headers)
        assert res2.status_code == 201
        assert res2.json()["id"] == enr_id

    def test_enrollment_rejection_for_unavailable_course(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Enrolling in a nonexistent or draft course returns 404."""
        res = client.post("/api/v1/courses/nonexistent-course-slug/enroll", headers=auth_headers)
        assert res.status_code == 404
        assert res.json()["error"]["code"] == "COURSE_NOT_AVAILABLE"

    def test_cross_user_enrollment_authorization(
        self, client: TestClient, auth_headers: dict[str, str], test_course_bundle: dict[str, str], db: Session, test_user: User
    ) -> None:
        """Learners cannot access another user's private enrollment records."""
        db.add(
            SkillMastery(
                user_id=test_user.id,
                skill_id=test_course_bundle["prereq_skill_id"],
                mastery_level=80.0,
                status=SkillMasteryStatus.PROVISIONAL.value,
            )
        )
        db.commit()

        res1 = client.post(f"/api/v1/courses/{test_course_bundle['course_slug']}/enroll", headers=auth_headers)
        enrollment_id = res1.json()["id"]

        # Register User B
        client.post("/api/v1/auth/register", json={"email": "b_learner@test.com", "password": "SecurePassword1!", "display_name": "Learner B"})
        login_b = client.post("/api/v1/auth/login", json={"email": "b_learner@test.com", "password": "SecurePassword1!"})
        b_token = login_b.json()["access_token"]
        b_headers = {"Authorization": f"Bearer {b_token}"}

        # User B attempts to access User A's enrollment
        res_forbidden = client.get(f"/api/v1/enrollments/{enrollment_id}", headers=b_headers)
        assert res_forbidden.status_code == 403
        assert res_forbidden.json()["error"]["code"] == "FORBIDDEN"


class TestLessonProgressionAndCompletion:
    """5-8: Lesson start, completion requirements, course cascade, and activity triggers."""

    def test_lesson_start_persistence(
        self, client: TestClient, auth_headers: dict[str, str], test_course_bundle: dict[str, str], db: Session, test_user: User
    ) -> None:
        """Starting a lesson updates enrollment status to IN_PROGRESS and initializes LessonProgress."""
        db.add(
            SkillMastery(
                user_id=test_user.id,
                skill_id=test_course_bundle["prereq_skill_id"],
                mastery_level=80.0,
                status=SkillMasteryStatus.PROVISIONAL.value,
            )
        )
        db.commit()

        enr_res = client.post(f"/api/v1/courses/{test_course_bundle['course_slug']}/enroll", headers=auth_headers)
        enr_id = enr_res.json()["id"]

        start_res = client.post(
            f"/api/v1/enrollments/{enr_id}/lessons/{test_course_bundle['lesson1_id']}/start",
            headers=auth_headers,
        )
        assert start_res.status_code == 200
        data = start_res.json()
        assert data["status"] == "IN_PROGRESS"
        assert data["lesson_slug"] == "big-o-notation"
        assert data["started_at"] is not None

        # Check enrollment transitioned to IN_PROGRESS
        enr_check = client.get(f"/api/v1/enrollments/{enr_id}", headers=auth_headers).json()
        assert enr_check["status"] == "IN_PROGRESS"

    def test_lesson_completion_blocked_when_activities_unpassed(
        self, client: TestClient, auth_headers: dict[str, str], test_course_bundle: dict[str, str], db: Session, test_user: User
    ) -> None:
        """A lesson containing required activities cannot be marked complete without passing attempts."""
        db.add(
            SkillMastery(
                user_id=test_user.id,
                skill_id=test_course_bundle["prereq_skill_id"],
                mastery_level=80.0,
                status=SkillMasteryStatus.PROVISIONAL.value,
            )
        )
        db.commit()

        enr_id = client.post(f"/api/v1/courses/{test_course_bundle['course_slug']}/enroll", headers=auth_headers).json()["id"]

        res = client.post(
            f"/api/v1/enrollments/{enr_id}/lessons/{test_course_bundle['lesson1_id']}/complete",
            headers=auth_headers,
        )
        assert res.status_code == 400
        assert res.json()["error"]["code"] == "REQUIRED_ACTIVITIES_INCOMPLETE"

    def test_assessment_passed_triggers_progression_cascade(
        self, client: TestClient, auth_headers: dict[str, str], test_course_bundle: dict[str, str], db: Session, test_user: User
    ) -> None:
        """Passing all required activities automatically cascades to lesson completion and course completion."""
        db.add(
            SkillMastery(
                user_id=test_user.id,
                skill_id=test_course_bundle["prereq_skill_id"],
                mastery_level=80.0,
                status=SkillMasteryStatus.PROVISIONAL.value,
            )
        )
        db.commit()

        enr_id = client.post(f"/api/v1/courses/{test_course_bundle['course_slug']}/enroll", headers=auth_headers).json()["id"]

        # Submit passed attempt for lesson 1 activity
        att1_res = client.post(
            f"/api/v1/activities/{test_course_bundle['activity1_id']}/attempts",
            json={"submission": {"selected_option_id": "a"}},
            headers=auth_headers,
        )
        assert att1_res.status_code == 201
        assert att1_res.json()["passed"] is True

        # Check that Lesson 1 is now automatically completed
        enr_status1 = client.get(f"/api/v1/enrollments/{enr_id}", headers=auth_headers).json()
        assert enr_status1["lessons_completed"] == 1
        assert enr_status1["progress_percentage"] == 50.0
        assert enr_status1["status"] == "IN_PROGRESS"

        # Submit passed attempt for lesson 2 activity
        att2_res = client.post(
            f"/api/v1/activities/{test_course_bundle['activity2_id']}/attempts",
            json={"submission": {"selected_boolean": True}},
            headers=auth_headers,
        )
        assert att2_res.status_code == 201
        assert att2_res.json()["passed"] is True

        # Check that Course is now automatically COMPLETED (100%)
        enr_status2 = client.get(f"/api/v1/enrollments/{enr_id}", headers=auth_headers).json()
        assert enr_status2["lessons_completed"] == 2
        assert enr_status2["progress_percentage"] == 100.0
        assert enr_status2["status"] == "COMPLETED"
        assert enr_status2["completed_at"] is not None


class TestSkillMasteryAndEvidence:
    """9-10: Evidence-backed skill mastery and distinct assessment requirements."""

    def test_failed_attempts_do_not_award_mastery(
        self, client: TestClient, auth_headers: dict[str, str], test_course_bundle: dict[str, str], db: Session, test_user: User
    ) -> None:
        """Failed assessment attempts award no provisional or mastered status."""
        db.add(
            SkillMastery(
                user_id=test_user.id,
                skill_id=test_course_bundle["prereq_skill_id"],
                mastery_level=80.0,
                status=SkillMasteryStatus.PROVISIONAL.value,
            )
        )
        db.commit()

        client.post(f"/api/v1/courses/{test_course_bundle['course_slug']}/enroll", headers=auth_headers)

        # Submit wrong answer (score 0.0, passed False)
        client.post(
            f"/api/v1/activities/{test_course_bundle['activity1_id']}/attempts",
            json={"submission": {"selected_option_id": "b"}},
            headers=auth_headers,
        )

        service = ProgressionService(db)
        mastery = service.recalculate_skill_mastery(test_user.id, test_course_bundle["main_skill_id"])
        assert mastery.status == SkillMasteryStatus.PRACTICING.value
        assert len(mastery.evidence) == 0

    def test_distinct_assessment_evidence_required_for_mastered(
        self, client: TestClient, auth_headers: dict[str, str], test_course_bundle: dict[str, str], db: Session, test_user: User
    ) -> None:
        """Mastery requires passing at least two distinct tasks rather than repeating one question."""
        db.add(
            SkillMastery(
                user_id=test_user.id,
                skill_id=test_course_bundle["prereq_skill_id"],
                mastery_level=80.0,
                status=SkillMasteryStatus.PROVISIONAL.value,
            )
        )
        db.commit()

        client.post(f"/api/v1/courses/{test_course_bundle['course_slug']}/enroll", headers=auth_headers)

        # 1. Pass only Activity 1
        client.post(
            f"/api/v1/activities/{test_course_bundle['activity1_id']}/attempts",
            json={"submission": {"selected_option_id": "a"}},
            headers=auth_headers,
        )

        service = ProgressionService(db)
        mastery1 = service.recalculate_skill_mastery(test_user.id, test_course_bundle["main_skill_id"])
        # Only 1 distinct task passed -> PROVISIONAL, not yet MASTERED
        assert mastery1.status == SkillMasteryStatus.PROVISIONAL.value
        assert len(mastery1.evidence) == 1

        # 2. Pass Activity 2 (distinct assessment in course)
        client.post(
            f"/api/v1/activities/{test_course_bundle['activity2_id']}/attempts",
            json={"submission": {"selected_boolean": True}},
            headers=auth_headers,
        )

        mastery2 = service.recalculate_skill_mastery(test_user.id, test_course_bundle["main_skill_id"])
        # Now 2 distinct tasks passed with >= 80% -> MASTERED!
        assert mastery2.status == SkillMasteryStatus.MASTERED.value
        assert len(mastery2.evidence) == 2


class TestPrerequisiteEnforcement:
    """11: Prerequisite validation through direct API calls."""

    def test_enrollment_rejected_when_prerequisite_unmet(
        self, client: TestClient, auth_headers: dict[str, str], test_course_bundle: dict[str, str]
    ) -> None:
        """Enrolling without meeting prerequisite skills returns 400 with PREREQUISITE_NOT_MET."""
        res = client.post(
            f"/api/v1/courses/{test_course_bundle['course_slug']}/enroll",
            headers=auth_headers,
        )
        assert res.status_code == 400
        assert res.json()["error"]["code"] == "PREREQUISITE_NOT_MET"
        assert "Foundational Logic" in res.json()["error"]["details"]["unmet_prerequisites"]

    def test_prerequisite_endpoint_reports_status(
        self, client: TestClient, auth_headers: dict[str, str], test_course_bundle: dict[str, str]
    ) -> None:
        """GET /courses/{slug}/prerequisites accurately reports unmet requirements."""
        res = client.get(
            f"/api/v1/courses/{test_course_bundle['course_slug']}/prerequisites",
            headers=auth_headers,
        )
        assert res.status_code == 200
        data = res.json()
        assert data["eligible"] is False
        assert len(data["prerequisites"]) == 1
        assert data["prerequisites"][0]["skill_name"] == "Foundational Logic"
        assert data["prerequisites"][0]["satisfied"] is False


class TestResumeLearningAndDashboard:
    """12-14: Resume learning, recommendations, dashboard, and achievements."""

    def test_resume_learning_selects_first_incomplete_lesson(
        self, client: TestClient, auth_headers: dict[str, str], test_course_bundle: dict[str, str], db: Session, test_user: User
    ) -> None:
        """Resume learning points to the first uncompleted lesson in the enrolled course version."""
        db.add(
            SkillMastery(
                user_id=test_user.id,
                skill_id=test_course_bundle["prereq_skill_id"],
                mastery_level=80.0,
                status=SkillMasteryStatus.PROVISIONAL.value,
            )
        )
        db.commit()

        client.post(f"/api/v1/courses/{test_course_bundle['course_slug']}/enroll", headers=auth_headers)

        service = ProgressionService(db)
        resume = service.get_resume_learning(test_user.id)
        assert resume is not None
        assert resume.lesson_slug == "big-o-notation"
        assert resume.course_slug == test_course_bundle["course_slug"]

        # Now complete lesson 1
        client.post(
            f"/api/v1/activities/{test_course_bundle['activity1_id']}/attempts",
            json={"submission": {"selected_option_id": "a"}},
            headers=auth_headers,
        )

        # Resume should now advance to lesson 2
        resume2 = service.get_resume_learning(test_user.id)
        assert resume2 is not None
        assert resume2.lesson_slug == "binary-search"

    def test_dashboard_summary_and_achievements(
        self, client: TestClient, auth_headers: dict[str, str], test_course_bundle: dict[str, str], db: Session, test_user: User
    ) -> None:
        """GET /progress/dashboard consolidates active enrollments, resume item, skills, and achievements."""
        db.add(
            SkillMastery(
                user_id=test_user.id,
                skill_id=test_course_bundle["prereq_skill_id"],
                mastery_level=80.0,
                status=SkillMasteryStatus.PROVISIONAL.value,
            )
        )
        db.commit()

        client.post(f"/api/v1/courses/{test_course_bundle['course_slug']}/enroll", headers=auth_headers)

        # Submit perfect score attempt
        client.post(
            f"/api/v1/activities/{test_course_bundle['activity1_id']}/attempts",
            json={"submission": {"selected_option_id": "a"}},
            headers=auth_headers,
        )

        dash_res = client.get("/api/v1/progress/dashboard", headers=auth_headers)
        assert dash_res.status_code == 200
        dash = dash_res.json()

        assert len(dash["enrolled_courses"]) == 1
        assert dash["enrolled_courses"][0]["lessons_completed"] == 1
        assert dash["resume_learning"]["lesson_slug"] == "binary-search"
        assert len(dash["achievements"]) >= 6

        # Check earned achievements
        earned = [a for a in dash["achievements"] if a["earned"]]
        earned_slugs = [a["slug"] for a in earned]
        assert "first_lesson" in earned_slugs
        assert "perfect_score" in earned_slugs


class TestSkillMasteryAttributionRegression:
    """Focused regression tests demonstrating strict skill mastery attribution."""

    def test_assessment_for_one_skill_cannot_increase_unrelated_skill_mastery(
        self, client: TestClient, auth_headers: dict[str, str], db: Session, test_user: User, test_creator_user: User
    ) -> None:
        """In a multi-skill course, an assessment for Skill A must not increase mastery for Skill B."""
        # 1. Create discipline & 2 distinct skills
        disc = Discipline(slug="multi-disc", name="Multi Discipline", sort_order=10)
        db.add(disc)
        db.flush()

        skill_a = Skill(
            slug="css-flexbox-skill",
            name="CSS Flexbox Mastery",
            discipline_id=disc.id,
            difficulty_level=SkillDifficulty.INTERMEDIATE,
        )
        skill_b = Skill(
            slug="sql-queries-skill",
            name="SQL Query Engineering",
            discipline_id=disc.id,
            difficulty_level=SkillDifficulty.INTERMEDIATE,
        )
        db.add_all([skill_a, skill_b])
        db.flush()

        # 2. Create multi-skill published course
        course = Course(
            slug="fullstack-essentials",
            title="Fullstack Essentials",
            short_description="Covers both CSS layouts and SQL databases.",
            discipline_id=disc.id,
            creator_id=test_creator_user.id,
            status=CourseStatus.PUBLISHED,
        )
        db.add(course)
        db.flush()

        # Associate BOTH skills with this course
        cs_a = CourseSkill(course_id=course.id, skill_id=skill_a.id, is_primary=True)
        cs_b = CourseSkill(course_id=course.id, skill_id=skill_b.id, is_primary=False)
        db.add_all([cs_a, cs_b])

        ver = CourseVersion(
            course_id=course.id,
            version_number=1,
            title="Fullstack Essentials v1",
            is_active=True,
        )
        db.add(ver)
        db.flush()
        course.current_version_id = ver.id

        mod1 = Module(course_version_id=ver.id, title="Frontend Module", sort_order=1)
        mod2 = Module(course_version_id=ver.id, title="Backend Module", sort_order=2)
        db.add_all([mod1, mod2])
        db.flush()

        les_a1 = Lesson(module_id=mod1.id, slug="flex-basics", title="Flex Basics", sort_order=1)
        les_a2 = Lesson(module_id=mod1.id, slug="flex-advanced", title="Flex Advanced", sort_order=2)
        les_b1 = Lesson(module_id=mod2.id, slug="sql-selects", title="SQL Selects", sort_order=1)
        db.add_all([les_a1, les_a2, les_b1])
        db.flush()

        # Activity A1 explicitly assesses skill_a
        act_a1 = Activity(
            lesson_id=les_a1.id,
            activity_type="single_choice",
            title="Flexbox Direction Quiz",
            instructions="Select direction.",
            configuration={"skill_id": skill_a.id, "options": [{"id": "row", "text": "row"}, {"id": "col", "text": "col"}]},
        )
        # Activity A2 explicitly assesses skill_a
        act_a2 = Activity(
            lesson_id=les_a2.id,
            activity_type="single_choice",
            title="Flexbox Align Quiz",
            instructions="Select alignment.",
            configuration={"skill_id": skill_a.id, "options": [{"id": "center", "text": "center"}, {"id": "start", "text": "start"}]},
        )
        # Activity B1 explicitly assesses skill_b
        act_b1 = Activity(
            lesson_id=les_b1.id,
            activity_type="single_choice",
            title="SQL Filtering Quiz",
            instructions="Select keyword.",
            configuration={"skill_id": skill_b.id, "options": [{"id": "where", "text": "WHERE"}, {"id": "group", "text": "GROUP"}]},
        )
        db.add_all([act_a1, act_a2, act_b1])
        db.flush()

        db.add(GradingConfig(activity_id=act_a1.id, grading_type="automated", answer_key={"correct_option_id": "row"}))
        db.add(GradingConfig(activity_id=act_a2.id, grading_type="automated", answer_key={"correct_option_id": "center"}))
        db.add(GradingConfig(activity_id=act_b1.id, grading_type="automated", answer_key={"correct_option_id": "where"}))
        db.commit()

        # 3. Learner enrolls in course
        enroll_res = client.post(f"/api/v1/courses/{course.slug}/enroll", headers=auth_headers)
        assert enroll_res.status_code == 201

        service = ProgressionService(db)

        # Initial check: learner is enrolled, so both skills initialize to LEARNING with 0 evidence
        mastery_a = service.recalculate_skill_mastery(test_user.id, skill_a.id)
        mastery_b = service.recalculate_skill_mastery(test_user.id, skill_b.id)
        assert mastery_a.status == SkillMasteryStatus.LEARNING.value
        assert len(mastery_a.evidence) == 0
        assert mastery_b.status == SkillMasteryStatus.LEARNING.value
        assert len(mastery_b.evidence) == 0

        # 4. Learner completes and passes Activity A1 (Skill A)
        sub1 = client.post(
            f"/api/v1/activities/{act_a1.id}/attempts",
            json={"submission": {"selected_option_id": "row"}},
            headers=auth_headers,
        )
        assert sub1.status_code == 201
        assert sub1.json()["passed"] is True

        mastery_a_after1 = service.recalculate_skill_mastery(test_user.id, skill_a.id)
        mastery_b_after1 = service.recalculate_skill_mastery(test_user.id, skill_b.id)

        # Skill A gained evidence and became PROVISIONAL
        assert mastery_a_after1.status == SkillMasteryStatus.PROVISIONAL.value
        assert len(mastery_a_after1.evidence) == 1
        assert mastery_a_after1.evidence[0]["activity_id"] == act_a1.id

        # CRITICAL INVARIANT: Skill B must NOT have received evidence from Skill A's activity!
        assert mastery_b_after1.status == SkillMasteryStatus.LEARNING.value
        assert len(mastery_b_after1.evidence) == 0
        assert mastery_b_after1.mastery_level == 10.0

        # 5. Learner completes and passes Activity A2 (Second distinct task for Skill A)
        sub2 = client.post(
            f"/api/v1/activities/{act_a2.id}/attempts",
            json={"submission": {"selected_option_id": "center"}},
            headers=auth_headers,
        )
        assert sub2.status_code == 201

        mastery_a_after2 = service.recalculate_skill_mastery(test_user.id, skill_a.id)
        mastery_b_after2 = service.recalculate_skill_mastery(test_user.id, skill_b.id)

        # Skill A now has 2 distinct tasks passed with 100% -> MASTERED
        assert mastery_a_after2.status == SkillMasteryStatus.MASTERED.value
        assert len(mastery_a_after2.evidence) == 2

        # Skill B must REMAIN at LEARNING with zero evidence, completely unaffected!
        assert mastery_b_after2.status == SkillMasteryStatus.LEARNING.value
        assert len(mastery_b_after2.evidence) == 0
        assert mastery_b_after2.mastery_level == 10.0

    def test_unattributed_activity_in_multi_skill_course_handled_safely(
        self, client: TestClient, auth_headers: dict[str, str], db: Session, test_user: User, test_creator_user: User
    ) -> None:
        """An activity in a multi-skill course without explicit tags or contextual match is handled safely."""
        disc = Discipline(slug="disc-safe-handling", name="Safe Handling Discipline", sort_order=20)
        db.add(disc)
        db.flush()

        skill_x = Skill(slug="react-patterns", name="React Component Patterns", discipline_id=disc.id, difficulty_level=SkillDifficulty.INTERMEDIATE)
        skill_y = Skill(slug="docker-devops", name="Docker DevOps Automation", discipline_id=disc.id, difficulty_level=SkillDifficulty.INTERMEDIATE)
        db.add_all([skill_x, skill_y])
        db.flush()

        course = Course(
            slug="hybrid-cloud-course",
            title="Hybrid Cloud Course",
            short_description="Multi-skill course covering React and Docker.",
            discipline_id=disc.id,
            creator_id=test_creator_user.id,
            status=CourseStatus.PUBLISHED,
        )
        db.add(course)
        db.flush()

        db.add_all([
            CourseSkill(course_id=course.id, skill_id=skill_x.id, is_primary=True),
            CourseSkill(course_id=course.id, skill_id=skill_y.id, is_primary=False),
        ])

        ver = CourseVersion(course_id=course.id, version_number=1, title="v1", is_active=True)
        db.add(ver)
        db.flush()
        course.current_version_id = ver.id

        mod = Module(course_version_id=ver.id, title="General Checkpoints", sort_order=1)
        db.add(mod)
        db.flush()

        # Lesson with generic title/slug that does not match either skill
        les = Lesson(module_id=mod.id, slug="weekly-checkpoint-1", title="Weekly Checkpoint 1", sort_order=1)
        db.add(les)
        db.flush()

        # Activity without any skill_id or skill_slug
        act = Activity(
            lesson_id=les.id,
            activity_type="single_choice",
            title="General Checkpoint Quiz",
            instructions="Select an option.",
            configuration={"options": [{"id": "opt1", "text": "Option 1"}, {"id": "opt2", "text": "Option 2"}]},
        )
        db.add(act)
        db.flush()
        db.add(GradingConfig(activity_id=act.id, grading_type="automated", answer_key={"correct_option_id": "opt1"}))
        db.commit()

        # Enroll learner
        enroll_res = client.post(f"/api/v1/courses/{course.slug}/enroll", headers=auth_headers)
        assert enroll_res.status_code == 201

        # Learner passes the generic activity with 100%
        sub_res = client.post(
            f"/api/v1/activities/{act.id}/attempts",
            json={"submission": {"selected_option_id": "opt1"}},
            headers=auth_headers,
        )
        assert sub_res.status_code == 201
        assert sub_res.json()["passed"] is True

        service = ProgressionService(db)
        mastery_x = service.recalculate_skill_mastery(test_user.id, skill_x.id)
        mastery_y = service.recalculate_skill_mastery(test_user.id, skill_y.id)

        # Neither skill gains evidence or false mastery from this un-attributed activity
        assert len(mastery_x.evidence) == 0
        assert mastery_x.status == SkillMasteryStatus.LEARNING.value
        assert mastery_x.mastery_level == 10.0

        assert len(mastery_y.evidence) == 0
        assert mastery_y.status == SkillMasteryStatus.LEARNING.value
        assert mastery_y.mastery_level == 10.0

    def test_single_skill_course_activities_attribute_correctly_without_explicit_tags(
        self, client: TestClient, auth_headers: dict[str, str], db: Session, test_user: User, test_creator_user: User
    ) -> None:
        """In a single-skill course, activities without explicit skill tags correctly attribute to that course's skill."""
        disc = Discipline(slug="disc-single-skill", name="Single Skill Discipline", sort_order=25)
        db.add(disc)
        db.flush()

        skill_sole = Skill(slug="rust-memory-safety", name="Rust Memory Safety", discipline_id=disc.id, difficulty_level=SkillDifficulty.ADVANCED)
        db.add(skill_sole)
        db.flush()

        course = Course(
            slug="rust-borrow-checker-deep-dive",
            title="Rust Borrow Checker Deep Dive",
            short_description="Exclusively focuses on Rust memory safety.",
            discipline_id=disc.id,
            creator_id=test_creator_user.id,
            status=CourseStatus.PUBLISHED,
        )
        db.add(course)
        db.flush()

        db.add(CourseSkill(course_id=course.id, skill_id=skill_sole.id, is_primary=True))

        ver = CourseVersion(course_id=course.id, version_number=1, title="v1", is_active=True)
        db.add(ver)
        db.flush()
        course.current_version_id = ver.id

        mod = Module(course_version_id=ver.id, title="Borrowing Basics", sort_order=1)
        db.add(mod)
        db.flush()

        les = Lesson(module_id=mod.id, slug="lifetimes-intro", title="Lifetimes Introduction", sort_order=1)
        db.add(les)
        db.flush()

        # Activity without explicit skill_id or skill_slug
        act = Activity(
            lesson_id=les.id,
            activity_type="single_choice",
            title="Lifetime Bounds Quiz",
            instructions="Select valid lifetime.",
            configuration={"options": [{"id": "a", "text": "'a"}, {"id": "b", "text": "'static"}]},
        )
        db.add(act)
        db.flush()
        db.add(GradingConfig(activity_id=act.id, grading_type="automated", answer_key={"correct_option_id": "a"}))
        db.commit()

        enroll_res = client.post(f"/api/v1/courses/{course.slug}/enroll", headers=auth_headers)
        assert enroll_res.status_code == 201

        sub_res = client.post(
            f"/api/v1/activities/{act.id}/attempts",
            json={"submission": {"selected_option_id": "a"}},
            headers=auth_headers,
        )
        assert sub_res.status_code == 201

        service = ProgressionService(db)
        mastery = service.recalculate_skill_mastery(test_user.id, skill_sole.id)
        assert len(mastery.evidence) == 1
        assert mastery.evidence[0]["activity_id"] == act.id
        assert mastery.status == SkillMasteryStatus.PROVISIONAL.value
        assert mastery.mastery_level == 100.0

    def test_course_recommendations_respect_unmet_prerequisites(
        self, client: TestClient, auth_headers: dict[str, str], db: Session, test_user: User, test_creator_user: User
    ) -> None:
        """Course recommendations only suggest unenrolled courses whose prerequisites are satisfied."""
        disc = Discipline(slug="disc-recs-test", name="Recommendation Testing Discipline", sort_order=30)
        db.add(disc)
        db.flush()

        prereq_skill = Skill(slug="linear-algebra-prereq", name="Linear Algebra Prerequisite", discipline_id=disc.id, difficulty_level=SkillDifficulty.FOUNDATIONAL)
        adv_skill = Skill(slug="quantum-computing", name="Quantum Computing Fundamentals", discipline_id=disc.id, difficulty_level=SkillDifficulty.ADVANCED)
        intro_skill = Skill(slug="creative-writing", name="Creative Writing Fundamentals", discipline_id=disc.id, difficulty_level=SkillDifficulty.FOUNDATIONAL)
        db.add_all([prereq_skill, adv_skill, intro_skill])
        db.flush()

        # Link prerequisite: adv_skill requires prereq_skill
        db.add(SkillPrerequisite(skill_id=adv_skill.id, prerequisite_skill_id=prereq_skill.id))

        # Course 1: Advanced Quantum Computing (Requires prereq_skill which learner does NOT have)
        course_adv = Course(
            slug="adv-quantum-101",
            title="Advanced Quantum 101",
            short_description="Requires Linear Algebra.",
            discipline_id=disc.id,
            creator_id=test_creator_user.id,
            status=CourseStatus.PUBLISHED,
        )
        # Course 2: Creative Writing (No prerequisites required)
        course_open = Course(
            slug="open-creative-writing",
            title="Creative Writing Intro",
            short_description="Open enrollment, no prerequisites required.",
            discipline_id=disc.id,
            creator_id=test_creator_user.id,
            status=CourseStatus.PUBLISHED,
        )
        db.add_all([course_adv, course_open])
        db.flush()

        db.add(CourseSkill(course_id=course_adv.id, skill_id=adv_skill.id, is_primary=True))
        db.add(CourseSkill(course_id=course_open.id, skill_id=intro_skill.id, is_primary=True))

        ver_adv = CourseVersion(course_id=course_adv.id, version_number=1, title="v1", is_active=True)
        ver_open = CourseVersion(course_id=course_open.id, version_number=1, title="v1", is_active=True)
        db.add_all([ver_adv, ver_open])
        db.flush()
        course_adv.current_version_id = ver_adv.id
        course_open.current_version_id = ver_open.id
        db.commit()

        service = ProgressionService(db)

        # Learner has NOT satisfied prereq_skill
        recs = service.get_recommendations(test_user.id)
        explore_recs = [r for r in recs if r.action_type == "explore_next"]

        # Ineligible course_adv MUST NOT be recommended
        rec_slugs = [r.link.replace("/courses/", "") for r in explore_recs]
        assert "adv-quantum-101" not in rec_slugs

        # Eligible course_open MUST be recommended
        assert "open-creative-writing" in rec_slugs

        # Now satisfy prereq_skill for learner
        db.add(
            SkillMastery(
                user_id=test_user.id,
                skill_id=prereq_skill.id,
                mastery_level=85.0,
                status=SkillMasteryStatus.PROVISIONAL.value,
            )
        )
        db.commit()

        # Also enroll in course_open so course_adv is next in line
        client.post(f"/api/v1/courses/{course_open.slug}/enroll", headers=auth_headers)

        recs_after = service.get_recommendations(test_user.id)
        explore_recs_after = [r for r in recs_after if r.action_type == "explore_next"]
        rec_slugs_after = [r.link.replace("/courses/", "") for r in explore_recs_after]

        # Now that prerequisites are satisfied, course_adv is eligible and recommended!
        assert "adv-quantum-101" in rec_slugs_after


class TestProgressionFailureRecoveryRegression:
    """Regression tests for transactional recovery when progression cascades are interrupted."""

    def test_graded_attempt_preserved_and_reconciled_after_cascade_interruption(
        self, client: TestClient, auth_headers: dict[str, str], test_course_bundle: dict[str, str], db: Session, test_user: User, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """If progression cascade encounters an unexpected exception, the graded attempt is preserved and healed upon inspection."""
        db.add(
            SkillMastery(
                user_id=test_user.id,
                skill_id=test_course_bundle["prereq_skill_id"],
                mastery_level=80.0,
                status=SkillMasteryStatus.PROVISIONAL.value,
            )
        )
        db.commit()

        enroll_res = client.post(f"/api/v1/courses/{test_course_bundle['course_slug']}/enroll", headers=auth_headers)
        enrollment_id = enroll_res.json()["id"]

        # Mock ProgressionService.handle_activity_completed to simulate a transient database exception
        def _failing_handle(*args: object, **kwargs: object) -> None:
            raise RuntimeError("Simulated transient deadlock during progression cascade")

        monkeypatch.setattr(ProgressionService, "handle_activity_completed", _failing_handle)

        # Learner submits passing attempt while cascade fails
        res = client.post(
            f"/api/v1/activities/{test_course_bundle['activity1_id']}/attempts",
            json={"submission": {"selected_option_id": "a"}},
            headers=auth_headers,
        )
        # Attempt submission succeeds: the attempt was graded and committed
        assert res.status_code == 201
        attempt_data = res.json()
        assert attempt_data["passed"] is True
        assert attempt_data["score"] == 100.0

        # Verify cascade was interrupted: lesson is not completed immediately due to simulated failure
        service = ProgressionService(db)
        from app.modules.progress.models import LessonProgress, LessonProgressStatus
        prog_unhealed = db.scalars(
            select(LessonProgress).where(
                LessonProgress.enrollment_id == enrollment_id,
                LessonProgress.lesson_id == test_course_bundle["lesson1_id"],
            )
        ).first()
        assert prog_unhealed is None or prog_unhealed.status != LessonProgressStatus.COMPLETED.value

        # Restore normal handle_activity_completed
        monkeypatch.undo()

        # Learner now visits the dashboard or opens their enrollment: self-healing reconciliation runs
        reconciled = service.reconcile_enrollment_progress(enrollment_id)
        assert reconciled is True

        prog_healed = db.scalars(
            select(LessonProgress).where(
                LessonProgress.enrollment_id == enrollment_id,
                LessonProgress.lesson_id == test_course_bundle["lesson1_id"],
            )
        ).first()
        assert prog_healed is not None
        assert prog_healed.status == LessonProgressStatus.COMPLETED.value
        assert prog_healed.completed_at is not None

        # Skill mastery was also healed from the saved attempt
        mastery = service.recalculate_skill_mastery(test_user.id, test_course_bundle["main_skill_id"])
        assert len(mastery.evidence) == 1
        assert mastery.evidence[0]["activity_id"] == test_course_bundle["activity1_id"]
