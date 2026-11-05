"""Database model and relational integrity tests for Phase 9 projects and portfolio."""

from __future__ import annotations

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.auth.models import User, UserRole
from app.modules.projects.models import (
    Portfolio,
    PortfolioItem,
    PortfolioItemType,
    PortfolioItemVisibility,
    Project,
    ProjectArtifact,
    ProjectSkill,
    ProjectStatus,
    ProjectSubmission,
    SubmissionStatus,
)
from app.modules.skills.models import Discipline, Skill, SkillDifficulty


@pytest.fixture
def project_test_setup(db: Session) -> dict:
    """Fixture creating prerequisite user, discipline, and skill records."""
    creator = User(
        email="creator_proj@skillverse.dev",
        role=UserRole.CREATOR,
        email_verified=True,
    )
    learner = User(
        email="learner_proj@skillverse.dev",
        role=UserRole.LEARNER,
        email_verified=True,
    )
    evaluator = User(
        email="evaluator_proj@skillverse.dev",
        role=UserRole.CREATOR,
        email_verified=True,
    )
    discipline = Discipline(
        slug="web-dev-proj",
        name="Web Development",
        description="Full stack web programming",
    )
    db.add_all([creator, learner, evaluator, discipline])
    db.commit()

    skill = Skill(
        slug="react-architecture",
        name="React Component Architecture",
        discipline_id=discipline.id,
        difficulty_level=SkillDifficulty.INTERMEDIATE,
    )
    db.add(skill)
    db.commit()

    return {
        "creator": creator,
        "learner": learner,
        "evaluator": evaluator,
        "discipline": discipline,
        "skill": skill,
    }


class TestProjectModels:
    """Tests for Project and ProjectSkill entities."""

    def test_create_project_with_skills(self, db: Session, project_test_setup: dict) -> None:
        creator = project_test_setup["creator"]
        discipline = project_test_setup["discipline"]
        skill = project_test_setup["skill"]

        project = Project(
            slug="responsive-portfolio-project",
            title="Build a Responsive Personal Portfolio",
            short_description="Create a personal showcase website with semantic HTML and modern CSS.",
            full_description="Detailed instructions on building, styling, and deploying a portfolio.",
            discipline_id=discipline.id,
            difficulty_level="BEGINNER",
            estimated_duration_hours=10,
            requirements={
                "milestones": [
                    {"id": "m1", "title": "Design Mockup", "deliverable": "Wireframe image"},
                    {"id": "m2", "title": "Semantic Layout", "deliverable": "HTML markup"},
                ]
            },
            evaluation_criteria={
                "rubric": [
                    {"dimension": "Responsiveness", "weight": 40},
                    {"dimension": "Semantic Structure", "weight": 30},
                    {"dimension": "Visual Appeal", "weight": 30},
                ],
                "passing_score": 75.0,
            },
            starter_resources=[
                {"title": "Starter Template", "url": "https://github.com/skillverse/starter-portfolio"}
            ],
            status=ProjectStatus.PUBLISHED.value,
            creator_id=creator.id,
        )
        db.add(project)
        db.commit()

        # Link project to skill
        project_skill = ProjectSkill(
            project_id=project.id,
            skill_id=skill.id,
            is_primary=True,
        )
        db.add(project_skill)
        db.commit()

        fetched = db.get(Project, project.id)
        assert fetched is not None
        assert fetched.title == "Build a Responsive Personal Portfolio"
        assert len(fetched.project_skills) == 1
        assert fetched.project_skills[0].skill.slug == "react-architecture"
        assert fetched.discipline.slug == "web-dev-proj"
        assert fetched.creator.email == "creator_proj@skillverse.dev"

    def test_project_slug_uniqueness(self, db: Session, project_test_setup: dict) -> None:
        creator = project_test_setup["creator"]
        discipline = project_test_setup["discipline"]

        p1 = Project(
            slug="duplicate-slug-proj",
            title="First Project",
            short_description="Short",
            full_description="Full",
            discipline_id=discipline.id,
            creator_id=creator.id,
        )
        p2 = Project(
            slug="duplicate-slug-proj",
            title="Second Project",
            short_description="Short",
            full_description="Full",
            discipline_id=discipline.id,
            creator_id=creator.id,
        )
        db.add(p1)
        db.commit()

        db.add(p2)
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()


class TestSubmissionAndArtifactModels:
    """Tests for ProjectSubmission, revision relationships, and ProjectArtifact."""

    def test_submission_lifecycle_and_revisions(self, db: Session, project_test_setup: dict) -> None:
        creator = project_test_setup["creator"]
        learner = project_test_setup["learner"]
        discipline = project_test_setup["discipline"]

        project = Project(
            slug="task-manager-project",
            title="Build a Task Manager",
            short_description="Full stack task app",
            full_description="Build a CRUD task app",
            discipline_id=discipline.id,
            creator_id=creator.id,
        )
        db.add(project)
        db.commit()

        # Create initial submission (v1)
        sub_v1 = ProjectSubmission(
            project_id=project.id,
            user_id=learner.id,
            version_number=1,
            status=SubmissionStatus.CHANGES_REQUESTED.value,
            title="My Task Manager App v1",
            summary="Initial submission with basic UI",
            content={"repository_url": "https://github.com/learner/task-app"},
            milestones_completed=["m1"],
            evaluation={"feedback": "Good start, please complete responsiveness."},
            score=65.0,
            passed=False,
        )
        db.add(sub_v1)
        db.commit()

        # Create revision submission (v2) referencing v1
        sub_v2 = ProjectSubmission(
            project_id=project.id,
            user_id=learner.id,
            version_number=2,
            revision_of_id=sub_v1.id,
            status=SubmissionStatus.EVALUATED.value,
            title="My Task Manager App v2",
            summary="Updated responsive styles and added local storage",
            content={"repository_url": "https://github.com/learner/task-app", "demo_url": "https://task-app.dev"},
            milestones_completed=["m1", "m2"],
            evaluation={"feedback": "Excellent revisions! All criteria passed."},
            score=92.0,
            passed=True,
            evaluator_id=project_test_setup["evaluator"].id,
        )
        db.add(sub_v2)
        db.commit()

        # Verify revision relationship navigation
        fetched_v1 = db.get(ProjectSubmission, sub_v1.id)
        fetched_v2 = db.get(ProjectSubmission, sub_v2.id)

        assert fetched_v2.revision_of is not None
        assert fetched_v2.revision_of.id == sub_v1.id
        assert len(fetched_v1.revisions) == 1
        assert fetched_v1.revisions[0].id == sub_v2.id

    def test_submission_version_uniqueness_per_learner_and_project(
        self, db: Session, project_test_setup: dict
    ) -> None:
        creator = project_test_setup["creator"]
        learner = project_test_setup["learner"]
        discipline = project_test_setup["discipline"]

        project = Project(
            slug="unique-version-project",
            title="Version Check Project",
            short_description="Short",
            full_description="Full",
            discipline_id=discipline.id,
            creator_id=creator.id,
        )
        db.add(project)
        db.commit()

        sub1 = ProjectSubmission(
            project_id=project.id,
            user_id=learner.id,
            version_number=1,
            status=SubmissionStatus.DRAFT.value,
        )
        sub2 = ProjectSubmission(
            project_id=project.id,
            user_id=learner.id,
            version_number=1,  # Duplicate version number for same learner and project
            status=SubmissionStatus.DRAFT.value,
        )
        db.add(sub1)
        db.commit()

        db.add(sub2)
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()

    def test_project_artifact_attachment_and_cascade_deletion(
        self, db: Session, project_test_setup: dict
    ) -> None:
        creator = project_test_setup["creator"]
        learner = project_test_setup["learner"]
        discipline = project_test_setup["discipline"]

        project = Project(
            slug="artifact-cascade-project",
            title="Artifact Cascade Project",
            short_description="Short",
            full_description="Full",
            discipline_id=discipline.id,
            creator_id=creator.id,
        )
        db.add(project)
        db.commit()

        submission = ProjectSubmission(
            project_id=project.id,
            user_id=learner.id,
            version_number=1,
            status=SubmissionStatus.SUBMITTED.value,
        )
        db.add(submission)
        db.commit()

        artifact = ProjectArtifact(
            submission_id=submission.id,
            user_id=learner.id,
            storage_key="artifacts/2026/10/bundle_abc123.zip",
            original_filename="source_code_bundle.zip",
            mime_type="application/zip",
            file_size_bytes=45200,
            checksum_sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            is_public=False,
        )
        db.add(artifact)
        db.commit()

        # Check artifact relationship navigation
        fetched_sub = db.get(ProjectSubmission, submission.id)
        assert len(fetched_sub.artifacts) == 1
        assert fetched_sub.artifacts[0].original_filename == "source_code_bundle.zip"

        # Verify cascade deletion: deleting submission deletes its child artifacts
        db.delete(fetched_sub)
        db.commit()

        deleted_artifact = db.get(ProjectArtifact, artifact.id)
        assert deleted_artifact is None


class TestPortfolioModels:
    """Tests for Portfolio and PortfolioItem entities."""

    def test_portfolio_one_to_one_with_user_and_items(
        self, db: Session, project_test_setup: dict
    ) -> None:
        learner = project_test_setup["learner"]

        portfolio = Portfolio(
            user_id=learner.id,
            is_public=True,
            custom_slug="priya-developer",
            title="Full-Stack Web Developer",
            headline="Building usable, performant web applications",
            bio_override="Passionate about UI engineering and accessible applications.",
            contact_links={
                "github": "https://github.com/learner",
                "linkedin": "https://linkedin.com/in/learner",
            },
            settings={"show_skills": True, "show_achievements": True},
        )
        db.add(portfolio)
        db.commit()

        # Add portfolio items with sort order
        item1 = PortfolioItem(
            portfolio_user_id=portfolio.user_id,
            item_type=PortfolioItemType.PROJECT_SUBMISSION.value,
            title="Responsive Showcase Website",
            summary="Demonstrating semantic layout and responsive CSS Grid.",
            skills_demonstrated=["react-architecture"],
            external_url="https://learner.github.io/portfolio",
            sort_order=1,
            visibility=PortfolioItemVisibility.PUBLIC.value,
        )
        item2 = PortfolioItem(
            portfolio_user_id=portfolio.user_id,
            item_type=PortfolioItemType.ACHIEVEMENT.value,
            title="Skill Master: React Foundations",
            summary="Verified evidence standard achieved across course activities.",
            sort_order=2,
            visibility=PortfolioItemVisibility.PUBLIC.value,
        )
        db.add_all([item1, item2])
        db.commit()

        fetched_port = db.get(Portfolio, learner.id)
        assert fetched_port is not None
        assert fetched_port.custom_slug == "priya-developer"
        assert len(fetched_port.items) == 2
        assert fetched_port.items[0].title == "Responsive Showcase Website"
        assert fetched_port.items[1].title == "Skill Master: React Foundations"

    def test_portfolio_user_id_primary_key_enforces_single_portfolio(
        self, db: Session, project_test_setup: dict
    ) -> None:
        learner = project_test_setup["learner"]

        p1 = Portfolio(user_id=learner.id, custom_slug="slug-one")
        db.add(p1)
        db.commit()
        db.expunge(p1)

        # Second portfolio for same user should fail primary key constraint
        p2 = Portfolio(user_id=learner.id, custom_slug="slug-two")
        db.add(p2)
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()

    def test_portfolio_custom_slug_uniqueness(
        self, db: Session, project_test_setup: dict
    ) -> None:
        creator = project_test_setup["creator"]
        evaluator = project_test_setup["evaluator"]

        p1 = Portfolio(user_id=creator.id, custom_slug="shared-unique-slug")
        p2 = Portfolio(user_id=evaluator.id, custom_slug="shared-unique-slug")

        db.add(p1)
        db.commit()

        db.add(p2)
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()
