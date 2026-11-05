"""Project discovery, creator authoring, and lifecycle management service."""

from __future__ import annotations

import math
import re
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.modules.auth.models import User, UserRole
from app.modules.projects.exceptions import (
    ProjectConflictError,
    ProjectForbiddenError,
    ProjectNotFoundError,
    ProjectValidationError,
)
from app.modules.projects.models import (
    Project,
    ProjectSkill,
    ProjectStatus,
    ProjectSubmission,
    SubmissionStatus,
)
from app.modules.projects.schemas import (
    ProjectCreateRequest,
    ProjectSkillResponse,
    ProjectUpdateRequest,
    SubmissionSummaryResponse,
)
from app.modules.skills.models import Discipline, Skill


def _slugify(text: str) -> str:
    """Generate a clean URL-safe slug from a human-readable title."""
    s = text.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_-]+", "-", s)
    s = re.sub(r"^-+|-+$", "", s)
    return s or "project"


class ProjectService:
    """Service managing project catalog discovery and creator authoring workflows."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def list_projects(
        self,
        *,
        discipline_id: str | None = None,
        skill_id: str | None = None,
        difficulty_level: str | None = None,
        search: str | None = None,
        status: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        page: int = 1,
        page_size: int = 20,
        current_user: User | None = None,
    ) -> dict[str, Any]:
        """List and filter projects with pagination, sorting, and role-based status exposure."""
        query = select(Project).options(
            selectinload(Project.discipline),
            selectinload(Project.project_skills).selectinload(ProjectSkill.skill),
        )

        # Enforce status exposure: non-creators/non-admins can ONLY see PUBLISHED projects
        is_elevated = current_user is not None and current_user.role in (
            UserRole.CREATOR,
            UserRole.ADMIN,
        )

        if not is_elevated:
            query = query.where(Project.status == ProjectStatus.PUBLISHED.value)
        elif status:
            query = query.where(Project.status == status.upper())

        if discipline_id:
            query = query.where(Project.discipline_id == discipline_id)

        if difficulty_level:
            query = query.where(Project.difficulty_level == difficulty_level.upper())

        if skill_id:
            query = query.where(
                Project.id.in_(
                    select(ProjectSkill.project_id).where(ProjectSkill.skill_id == skill_id)
                )
            )

        if search:
            pattern = f"%{search.strip().lower()}%"
            query = query.where(
                or_(
                    func.lower(Project.title).like(pattern),
                    func.lower(Project.short_description).like(pattern),
                )
            )

        # Count total matching rows
        count_query = select(func.count()).select_from(query.subquery())
        total = self.db.execute(count_query).scalar_one()

        # Sorting
        sort_column_map = {
            "created_at": Project.created_at,
            "title": Project.title,
            "difficulty_level": Project.difficulty_level,
        }
        order_col = sort_column_map.get(sort_by, Project.created_at)
        if sort_order.lower() == "asc":
            query = query.order_by(order_col.asc())
        else:
            query = query.order_by(order_col.desc())

        # Pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        projects = self.db.execute(query).scalars().all()

        # Compute submission counts for each returned project
        project_ids = [p.id for p in projects]
        submission_counts: dict[str, int] = {}
        if project_ids:
            sub_count_stmt = (
                select(ProjectSubmission.project_id, func.count(ProjectSubmission.id))
                .where(
                    ProjectSubmission.project_id.in_(project_ids),
                    ProjectSubmission.status.in_(
                        (
                            SubmissionStatus.SUBMITTED.value,
                            SubmissionStatus.UNDER_REVIEW.value,
                            SubmissionStatus.EVALUATED.value,
                            SubmissionStatus.COMPLETED.value,
                        )
                    ),
                )
                .group_by(ProjectSubmission.project_id)
            )
            for pid, cnt in self.db.execute(sub_count_stmt).all():
                submission_counts[pid] = cnt

        items = []
        for p in projects:
            skills_payload = [
                ProjectSkillResponse(
                    skill_id=ps.skill_id,
                    skill_slug=ps.skill.slug if ps.skill else "",
                    skill_name=ps.skill.name if ps.skill else "",
                    difficulty_level=ps.skill.difficulty_level if ps.skill else "",
                    is_primary=ps.is_primary,
                )
                for ps in p.project_skills
            ]
            items.append(
                {
                    "id": p.id,
                    "slug": p.slug,
                    "title": p.title,
                    "short_description": p.short_description,
                    "discipline_id": p.discipline_id,
                    "discipline_name": p.discipline.name if p.discipline else None,
                    "discipline_slug": p.discipline.slug if p.discipline else None,
                    "difficulty_level": p.difficulty_level,
                    "estimated_duration_hours": p.estimated_duration_hours,
                    "status": p.status,
                    "creator_id": p.creator_id,
                    "created_at": p.created_at,
                    "updated_at": p.updated_at,
                    "skills": skills_payload,
                    "submissions_count": submission_counts.get(p.id, 0),
                }
            )

        pages = math.ceil(total / page_size) if total > 0 else 1
        return {
            "items": items,
            "total": total,
            "page": page,
            "limit": page_size,
            "pages": pages,
        }

    def get_project(
        self,
        project_id_or_slug: str,
        current_user: User | None = None,
    ) -> dict[str, Any]:
        """Fetch project details by UUID or slug with authorization verification."""
        stmt = (
            select(Project)
            .where(or_(Project.id == project_id_or_slug, Project.slug == project_id_or_slug))
            .options(
                selectinload(Project.discipline),
                selectinload(Project.project_skills).selectinload(ProjectSkill.skill),
                selectinload(Project.creator).selectinload(User.profile),
            )
        )
        project = self.db.execute(stmt).scalar_one_or_none()
        if not project:
            raise ProjectNotFoundError(f"Project '{project_id_or_slug}' was not found.")

        # Check visibility
        is_creator = current_user is not None and project.creator_id == current_user.id
        is_admin = current_user is not None and current_user.role == UserRole.ADMIN

        if project.status != ProjectStatus.PUBLISHED.value and not (is_creator or is_admin):
            raise ProjectNotFoundError(f"Project '{project_id_or_slug}' was not found.")

        # If user is authenticated, retrieve their latest submission
        my_submission_payload: SubmissionSummaryResponse | None = None
        if current_user is not None:
            sub_stmt = (
                select(ProjectSubmission)
                .where(
                    ProjectSubmission.project_id == project.id,
                    ProjectSubmission.user_id == current_user.id,
                )
                .order_by(ProjectSubmission.version_number.desc())
                .limit(1)
            )
            latest_sub = self.db.execute(sub_stmt).scalar_one_or_none()
            if latest_sub:
                my_submission_payload = SubmissionSummaryResponse.model_validate(latest_sub)

        # Count submissions
        sub_cnt = self.db.execute(
            select(func.count(ProjectSubmission.id)).where(
                ProjectSubmission.project_id == project.id,
                ProjectSubmission.status.in_(
                    (
                        SubmissionStatus.SUBMITTED.value,
                        SubmissionStatus.UNDER_REVIEW.value,
                        SubmissionStatus.EVALUATED.value,
                        SubmissionStatus.COMPLETED.value,
                    )
                ),
            )
        ).scalar_one()

        creator_name: str | None = None
        if project.creator and project.creator.profile:
            creator_name = project.creator.profile.display_name
        elif project.creator:
            creator_name = project.creator.email.split("@")[0]

        skills_payload = [
            ProjectSkillResponse(
                skill_id=ps.skill_id,
                skill_slug=ps.skill.slug if ps.skill else "",
                skill_name=ps.skill.name if ps.skill else "",
                difficulty_level=ps.skill.difficulty_level if ps.skill else "",
                is_primary=ps.is_primary,
            )
            for ps in project.project_skills
        ]

        return {
            "id": project.id,
            "slug": project.slug,
            "title": project.title,
            "short_description": project.short_description,
            "full_description": project.full_description,
            "discipline_id": project.discipline_id,
            "discipline_name": project.discipline.name if project.discipline else None,
            "discipline_slug": project.discipline.slug if project.discipline else None,
            "difficulty_level": project.difficulty_level,
            "estimated_duration_hours": project.estimated_duration_hours,
            "course_version_id": project.course_version_id,
            "requirements": project.requirements or {},
            "evaluation_criteria": project.evaluation_criteria or {},
            "starter_resources": project.starter_resources or [],
            "status": project.status,
            "creator_id": project.creator_id,
            "creator_name": creator_name,
            "created_at": project.created_at,
            "updated_at": project.updated_at,
            "skills": skills_payload,
            "submissions_count": sub_cnt,
            "my_submission": my_submission_payload,
        }

    def _generate_unique_slug(self, base_title: str, explicit_slug: str | None = None) -> str:
        """Derive a unique project slug, checking against existing records."""
        candidate = explicit_slug or _slugify(base_title)
        existing = self.db.execute(select(Project).where(Project.slug == candidate)).scalar_one_or_none()
        if not existing:
            return candidate

        if explicit_slug:
            raise ProjectConflictError(f"A project with slug '{explicit_slug}' already exists.")

        counter = 2
        while True:
            trial = f"{candidate}-{counter}"
            collision = self.db.execute(select(Project).where(Project.slug == trial)).scalar_one_or_none()
            if not collision:
                return trial
            counter += 1

    def create_project(self, data: ProjectCreateRequest, user: User) -> dict[str, Any]:
        """Author and persist a new practical project in DRAFT status."""
        if user.role not in (UserRole.CREATOR, UserRole.ADMIN):
            raise ProjectForbiddenError("Only creators and administrators can author projects.")

        # Validate discipline
        discipline = self.db.execute(
            select(Discipline).where(Discipline.id == data.discipline_id)
        ).scalar_one_or_none()
        if not discipline:
            raise ProjectValidationError(f"Discipline with ID '{data.discipline_id}' does not exist.")

        # Validate skills
        skill_ids = [s.skill_id for s in data.skills]
        if len(skill_ids) != len(set(skill_ids)):
            raise ProjectValidationError("Duplicate skills specified in project payload.")

        existing_skills = self.db.execute(select(Skill).where(Skill.id.in_(skill_ids))).scalars().all()
        existing_skill_ids = {s.id for s in existing_skills}
        missing_skills = set(skill_ids) - existing_skill_ids
        if missing_skills:
            raise ProjectValidationError(f"Skills do not exist: {sorted(missing_skills)}")

        slug = self._generate_unique_slug(data.title, data.slug)

        # Ensure at least one primary skill
        has_primary = any(s.is_primary for s in data.skills)

        project = Project(
            title=data.title,
            slug=slug,
            short_description=data.short_description,
            full_description=data.full_description,
            discipline_id=data.discipline_id,
            difficulty_level=data.difficulty_level,
            estimated_duration_hours=data.estimated_duration_hours,
            course_version_id=data.course_version_id,
            requirements=data.requirements,
            evaluation_criteria=data.evaluation_criteria,
            starter_resources=data.starter_resources,
            status=ProjectStatus.DRAFT.value,
            creator_id=user.id,
        )
        self.db.add(project)
        self.db.flush()

        for idx, s in enumerate(data.skills):
            is_primary = s.is_primary or (not has_primary and idx == 0)
            ps = ProjectSkill(
                project_id=project.id,
                skill_id=s.skill_id,
                is_primary=is_primary,
            )
            self.db.add(ps)

        self.db.commit()
        return self.get_project(project.id, current_user=user)

    def update_project(
        self,
        project_id: str,
        data: ProjectUpdateRequest,
        user: User,
    ) -> dict[str, Any]:
        """Update draft or published project details with permission checks."""
        project = self.db.execute(select(Project).where(Project.id == project_id)).scalar_one_or_none()
        if not project:
            raise ProjectNotFoundError(f"Project '{project_id}' was not found.")

        is_creator = project.creator_id == user.id
        is_admin = user.role == UserRole.ADMIN
        if not (is_creator or is_admin):
            raise ProjectForbiddenError("You are not authorized to update this project.")

        if data.title is not None:
            project.title = data.title
        if data.slug is not None and data.slug != project.slug:
            project.slug = self._generate_unique_slug(data.title or project.title, data.slug)
        if data.short_description is not None:
            project.short_description = data.short_description
        if data.full_description is not None:
            project.full_description = data.full_description
        if data.difficulty_level is not None:
            project.difficulty_level = data.difficulty_level
        if data.estimated_duration_hours is not None:
            project.estimated_duration_hours = data.estimated_duration_hours
        if data.course_version_id is not None:
            project.course_version_id = data.course_version_id
        if data.requirements is not None:
            project.requirements = data.requirements
        if data.evaluation_criteria is not None:
            project.evaluation_criteria = data.evaluation_criteria
        if data.starter_resources is not None:
            project.starter_resources = data.starter_resources

        if data.discipline_id is not None and data.discipline_id != project.discipline_id:
            disc = self.db.execute(
                select(Discipline).where(Discipline.id == data.discipline_id)
            ).scalar_one_or_none()
            if not disc:
                raise ProjectValidationError(f"Discipline with ID '{data.discipline_id}' does not exist.")
            project.discipline_id = data.discipline_id

        if data.skills is not None:
            skill_ids = [s.skill_id for s in data.skills]
            if len(skill_ids) != len(set(skill_ids)):
                raise ProjectValidationError("Duplicate skills specified in update payload.")
            existing_skills = self.db.execute(select(Skill).where(Skill.id.in_(skill_ids))).scalars().all()
            missing = set(skill_ids) - {s.id for s in existing_skills}
            if missing:
                raise ProjectValidationError(f"Skills do not exist: {sorted(missing)}")

            # Delete current project skills
            for ps in project.project_skills:
                self.db.delete(ps)
            self.db.flush()

            has_primary = any(s.is_primary for s in data.skills)
            for idx, s in enumerate(data.skills):
                is_primary = s.is_primary or (not has_primary and idx == 0)
                new_ps = ProjectSkill(
                    project_id=project.id,
                    skill_id=s.skill_id,
                    is_primary=is_primary,
                )
                self.db.add(new_ps)

        self.db.commit()
        return self.get_project(project.id, current_user=user)

    def publish_project(self, project_id: str, user: User) -> dict[str, Any]:
        """Validate project completeness and transition status to PUBLISHED."""
        project = self.db.execute(
            select(Project)
            .where(Project.id == project_id)
            .options(selectinload(Project.project_skills))
        ).scalar_one_or_none()
        if not project:
            raise ProjectNotFoundError(f"Project '{project_id}' was not found.")

        if not (project.creator_id == user.id or user.role == UserRole.ADMIN):
            raise ProjectForbiddenError("You are not authorized to publish this project.")

        # Completeness validation
        errors: list[str] = []
        if len(project.title.strip()) < 3:
            errors.append("Title must be at least 3 characters.")
        if len(project.short_description.strip()) < 10:
            errors.append("Short description must be at least 10 characters.")
        if len(project.full_description.strip()) < 20:
            errors.append("Full description must be at least 20 characters.")
        if not project.project_skills:
            errors.append("At least one skill must be linked to the project.")

        reqs = project.requirements or {}
        milestones = reqs.get("milestones", [])
        if not milestones and not reqs.get("deliverables"):
            errors.append("Requirements must define at least one milestone or deliverable.")

        eval_criteria = project.evaluation_criteria or {}
        passing_score = eval_criteria.get("passing_score")
        rubric = eval_criteria.get("rubric") or eval_criteria.get("criteria")
        if passing_score is None or not isinstance(passing_score, (int, float)) or passing_score <= 0:
            errors.append("Evaluation criteria must specify a positive numeric passing_score.")
        if not rubric or not isinstance(rubric, list) or len(rubric) == 0:
            errors.append("Evaluation criteria must include at least one rubric criterion.")

        if errors:
            raise ProjectValidationError(
                "Project cannot be published due to missing requirements.",
                details={"errors": errors},
            )

        project.status = ProjectStatus.PUBLISHED.value
        self.db.commit()
        return self.get_project(project.id, current_user=user)

    def archive_project(self, project_id: str, user: User) -> dict[str, Any]:
        """Transition project status to ARCHIVED."""
        project = self.db.execute(select(Project).where(Project.id == project_id)).scalar_one_or_none()
        if not project:
            raise ProjectNotFoundError(f"Project '{project_id}' was not found.")

        if not (project.creator_id == user.id or user.role == UserRole.ADMIN):
            raise ProjectForbiddenError("You are not authorized to archive this project.")

        project.status = ProjectStatus.ARCHIVED.value
        self.db.commit()
        return self.get_project(project.id, current_user=user)
