"""Automated tests verifying database seed script idempotency and course outline completeness."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.courses.models import Course, CourseStatus
from app.modules.courses.service import CourseService
from app.modules.skills.models import Discipline, Skill, SkillPrerequisite
from app.seed import run_seed


def test_seed_creates_complete_taxonomy_and_courses(db: Session) -> None:
    """Verify that run_seed creates disciplines, skills, prerequisites, and courses."""
    run_seed()

    # 1. Disciplines check
    disc_count = db.scalar(select(func.count(Discipline.id)))
    assert disc_count == 7

    # 2. Skills check
    skill_count = db.scalar(select(func.count(Skill.id)))
    assert skill_count == 15

    # 3. Prerequisites check
    prereq_count = db.scalar(select(func.count(SkillPrerequisite.skill_id)))
    assert prereq_count == 12

    # 4. Courses check
    courses = list(db.scalars(select(Course).order_by(Course.slug)).all())
    assert len(courses) == 3
    slugs = [c.slug for c in courses]
    assert "web-development-foundations" in slugs
    assert "spoken-english-communication" in slugs
    assert "personal-productivity" in slugs

    # Verify all 3 courses have status PUBLISHED
    for c in courses:
        assert c.status == CourseStatus.PUBLISHED
        assert c.current_version_id is not None
        assert c.current_version.is_active is True
        assert c.current_version.published_at is not None

    # Verify Course A: Web Development Foundations has 6 modules
    web_course = db.scalars(
        select(Course).where(Course.slug == "web-development-foundations")
    ).first()
    assert web_course is not None
    assert len(web_course.current_version.modules) == 6

    # Verify Course B: Spoken English has 6 modules
    speech_course = db.scalars(
        select(Course).where(Course.slug == "spoken-english-communication")
    ).first()
    assert speech_course is not None
    assert len(speech_course.current_version.modules) == 6

    # Verify Course C: Personal Productivity has 6 modules in published v1, plus a draft open
    prod_course = db.scalars(select(Course).where(Course.slug == "personal-productivity")).first()
    assert prod_course is not None
    assert len(prod_course.current_version.modules) == 6
    # Check that draft exists
    cs = CourseService(db)
    draft = cs.get_or_create_draft(prod_course.id)
    assert draft.version_number == 0
    assert draft.published_at is None


def test_seed_idempotency(db: Session) -> None:
    """Running seed multiple times must be strictly idempotent without creating duplicates."""
    run_seed()
    first_disc_count = db.scalar(select(func.count(Discipline.id)))
    first_skill_count = db.scalar(select(func.count(Skill.id)))
    first_course_count = db.scalar(select(func.count(Course.id)))

    # Re-run seed on existing data
    run_seed()
    assert db.scalar(select(func.count(Discipline.id))) == first_disc_count
    assert db.scalar(select(func.count(Skill.id))) == first_skill_count
    assert db.scalar(select(func.count(Course.id))) == first_course_count
