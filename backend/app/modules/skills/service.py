"""Skills and disciplines service — taxonomy management and prerequisite DAG."""

from __future__ import annotations

import logging
from collections import deque
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload, selectinload

from app.modules.skills.models import Discipline, Skill, SkillDifficulty, SkillPrerequisite

logger = logging.getLogger(__name__)


class SkillServiceError(Exception):
    """Domain exception for taxonomy and prerequisite errors."""

    def __init__(self, message: str, code: str = "SKILL_ERROR", status_code: int = 400) -> None:
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(message)


class SkillService:
    """Service managing disciplines, cross-disciplinary skills, and prerequisite dependencies."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # ── Disciplines ────────────────────────────────────────────────────────

    def list_disciplines(self, only_active: bool = True) -> list[Discipline]:
        """List disciplines ordered by sort_order and name."""
        stmt = (
            select(Discipline)
            .options(selectinload(Discipline.skills))
            .order_by(Discipline.sort_order.asc(), Discipline.name.asc())
        )
        if only_active:
            stmt = stmt.where(Discipline.is_active.is_(True))
        return list(self.db.scalars(stmt).all())

    def get_discipline_by_slug(self, slug: str, only_active: bool = True) -> Discipline | None:
        """Retrieve a discipline by its unique slug."""
        stmt = (
            select(Discipline)
            .options(
                selectinload(Discipline.skills).joinedload(Skill.discipline),
            )
            .where(Discipline.slug == slug)
        )
        if only_active:
            stmt = stmt.where(Discipline.is_active.is_(True))
        return self.db.scalars(stmt).first()

    def get_discipline_by_id(self, discipline_id: str) -> Discipline | None:
        """Retrieve a discipline by UUID."""
        return self.db.get(Discipline, discipline_id)

    def create_discipline(
        self,
        slug: str,
        name: str,
        description: str | None = None,
        icon: str | None = None,
        sort_order: int = 0,
        is_active: bool = True,
    ) -> Discipline:
        """Create a new discipline."""
        existing = self.db.scalars(select(Discipline).where(Discipline.slug == slug)).first()
        if existing:
            raise SkillServiceError(
                f"Discipline with slug '{slug}' already exists.",
                code="DISCIPLINE_ALREADY_EXISTS",
                status_code=409,
            )

        discipline = Discipline(
            slug=slug,
            name=name,
            description=description,
            icon=icon,
            sort_order=sort_order,
            is_active=is_active,
        )
        self.db.add(discipline)
        self.db.commit()
        self.db.refresh(discipline)
        return discipline

    # ── Skills ─────────────────────────────────────────────────────────────

    def list_skills(
        self,
        discipline_slug: str | None = None,
        difficulty: SkillDifficulty | None = None,
        search: str | None = None,
        only_active: bool = True,
    ) -> list[Skill]:
        """List and filter skills with joined discipline information."""
        stmt = (
            select(Skill)
            .join(Skill.discipline)
            .options(joinedload(Skill.discipline))
            .order_by(Skill.sort_order.asc(), Skill.name.asc())
        )

        if only_active:
            stmt = stmt.where(Skill.is_active.is_(True), Discipline.is_active.is_(True))

        if discipline_slug:
            stmt = stmt.where(Discipline.slug == discipline_slug)

        if difficulty:
            stmt = stmt.where(Skill.difficulty_level == difficulty)

        if search and search.strip():
            term = f"%{search.strip().lower()}%"
            stmt = stmt.where(
                or_(
                    func.lower(Skill.name).like(term),
                    func.lower(Skill.slug).like(term),
                    func.lower(Skill.description).like(term),
                )
            )

        return list(self.db.scalars(stmt).all())

    def get_skill_by_slug(self, slug: str, only_active: bool = True) -> Skill | None:
        """Retrieve a skill by slug with full prerequisite and dependent relationships."""
        stmt = (
            select(Skill)
            .options(
                joinedload(Skill.discipline),
                selectinload(Skill.prerequisite_edges).joinedload(
                    SkillPrerequisite.prerequisite_skill
                ),
                selectinload(Skill.dependent_edges).joinedload(SkillPrerequisite.skill),
                selectinload(Skill.course_associations),
            )
            .where(Skill.slug == slug)
        )
        if only_active:
            stmt = stmt.where(Skill.is_active.is_(True))
        return self.db.scalars(stmt).first()

    def get_skill_by_id(self, skill_id: str) -> Skill | None:
        """Retrieve a skill by UUID."""
        stmt = (
            select(Skill)
            .options(
                joinedload(Skill.discipline),
                selectinload(Skill.prerequisite_edges).joinedload(
                    SkillPrerequisite.prerequisite_skill
                ),
                selectinload(Skill.dependent_edges).joinedload(SkillPrerequisite.skill),
                selectinload(Skill.course_associations),
            )
            .where(Skill.id == skill_id)
        )
        return self.db.scalars(stmt).first()

    def create_skill(
        self,
        slug: str,
        name: str,
        discipline_id: str,
        description: str | None = None,
        parent_skill_id: str | None = None,
        difficulty_level: SkillDifficulty = SkillDifficulty.FOUNDATIONAL,
        icon: str | None = None,
        sort_order: int = 0,
        is_active: bool = True,
    ) -> Skill:
        """Create a new skill under an existing discipline."""
        # Validate discipline exists
        discipline = self.get_discipline_by_id(discipline_id)
        if not discipline:
            raise SkillServiceError(
                f"Discipline with id '{discipline_id}' does not exist.",
                code="DISCIPLINE_NOT_FOUND",
                status_code=404,
            )

        # Check unique slug
        existing = self.db.scalars(select(Skill).where(Skill.slug == slug)).first()
        if existing:
            raise SkillServiceError(
                f"Skill with slug '{slug}' already exists.",
                code="SKILL_ALREADY_EXISTS",
                status_code=409,
            )

        # Check parent skill if specified
        if parent_skill_id:
            parent = self.get_skill_by_id(parent_skill_id)
            if not parent:
                raise SkillServiceError(
                    f"Parent skill with id '{parent_skill_id}' does not exist.",
                    code="PARENT_SKILL_NOT_FOUND",
                    status_code=404,
                )

        skill = Skill(
            slug=slug,
            name=name,
            description=description,
            discipline_id=discipline_id,
            parent_skill_id=parent_skill_id,
            difficulty_level=difficulty_level,
            icon=icon,
            sort_order=sort_order,
            is_active=is_active,
        )
        self.db.add(skill)
        self.db.commit()
        self.db.refresh(skill)
        return skill

    def update_skill(
        self,
        skill_id: str,
        name: str | None = None,
        description: str | None = None,
        difficulty_level: SkillDifficulty | None = None,
        icon: str | None = None,
        sort_order: int | None = None,
        is_active: bool | None = None,
    ) -> Skill:
        """Update an existing skill."""
        skill = self.get_skill_by_id(skill_id)
        if not skill:
            raise SkillServiceError(
                f"Skill with id '{skill_id}' not found.",
                code="SKILL_NOT_FOUND",
                status_code=404,
            )

        if name is not None:
            skill.name = name
        if description is not None:
            skill.description = description
        if difficulty_level is not None:
            skill.difficulty_level = difficulty_level
        if icon is not None:
            skill.icon = icon
        if sort_order is not None:
            skill.sort_order = sort_order
        if is_active is not None:
            skill.is_active = is_active

        self.db.commit()
        self.db.refresh(skill)
        return skill

    # ── Prerequisite Relationships & Cycle Detection ───────────────────────

    def add_prerequisite(self, skill_id: str, prerequisite_skill_id: str) -> SkillPrerequisite:
        """Establish a directed dependency: `skill_id` requires `prerequisite_skill_id`.

        Validations performed:
        1. No self-dependency (skill cannot depend on itself).
        2. Both skills must exist and be active.
        3. No duplicate prerequisite relationship.
        4. Cycle detection: adding this dependency must not create a directed cycle in the DAG.
        """
        # 1. Self-dependency check
        if skill_id == prerequisite_skill_id:
            raise SkillServiceError(
                "A skill cannot depend on itself.",
                code="SELF_PREREQUISITE_NOT_ALLOWED",
                status_code=400,
            )

        # 2. Existence check
        skill = self.get_skill_by_id(skill_id)
        if not skill:
            raise SkillServiceError(
                f"Target skill '{skill_id}' not found.",
                code="SKILL_NOT_FOUND",
                status_code=404,
            )

        prereq_skill = self.get_skill_by_id(prereq_id := prerequisite_skill_id)
        if not prereq_skill:
            raise SkillServiceError(
                f"Prerequisite skill '{prereq_id}' not found.",
                code="PREREQUISITE_NOT_FOUND",
                status_code=404,
            )

        # 3. Duplicate check
        existing = self.db.scalars(
            select(SkillPrerequisite).where(
                SkillPrerequisite.skill_id == skill_id,
                SkillPrerequisite.prerequisite_skill_id == prerequisite_skill_id,
            )
        ).first()
        if existing:
            raise SkillServiceError(
                "Prerequisite relationship already exists.",
                code="PREREQUISITE_ALREADY_EXISTS",
                status_code=409,
            )

        # 4. Cycle detection (BFS on the prerequisite graph)
        # If adding (skill_id -> prerequisite_skill_id), we must verify that
        # `prerequisite_skill_id` does NOT already reach `skill_id` via its own prerequisites.
        if self._path_exists(source_id=prerequisite_skill_id, target_id=skill_id):
            raise SkillServiceError(
                "Circular dependency detected: adding this prerequisite would create a dependency cycle.",
                code="CIRCULAR_DEPENDENCY",
                status_code=400,
            )

        prereq = SkillPrerequisite(
            skill_id=skill_id,
            prerequisite_skill_id=prerequisite_skill_id,
        )
        self.db.add(prereq)
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise SkillServiceError(
                "Failed to add prerequisite due to concurrent update or constraint violation.",
                code="PREREQUISITE_CONFLICT",
                status_code=409,
            ) from exc

        return prereq

    def remove_prerequisite(self, skill_id: str, prerequisite_skill_id: str) -> bool:
        """Remove a prerequisite dependency."""
        prereq = self.db.scalars(
            select(SkillPrerequisite).where(
                SkillPrerequisite.skill_id == skill_id,
                SkillPrerequisite.prerequisite_skill_id == prerequisite_skill_id,
            )
        ).first()
        if not prereq:
            raise SkillServiceError(
                "Prerequisite relationship not found.",
                code="PREREQUISITE_NOT_FOUND",
                status_code=404,
            )

        self.db.delete(prereq)
        self.db.commit()
        return True

    def _path_exists(self, source_id: str, target_id: str) -> bool:
        """Check if target_id is reachable from source_id by following prerequisite edges.

        That is, check if source_id requires target_id (directly or transitively).
        """
        visited: set[str] = {source_id}
        queue: deque[str] = deque([source_id])

        while queue:
            curr_id = queue.popleft()
            if curr_id == target_id:
                return True

            # Find all direct prerequisites of curr_id
            prereqs = self.db.scalars(
                select(SkillPrerequisite.prerequisite_skill_id).where(
                    SkillPrerequisite.skill_id == curr_id
                )
            ).all()

            for next_id in prereqs:
                if next_id not in visited:
                    visited.add(next_id)
                    queue.append(next_id)

        return False

    def get_prerequisites(self, skill_id: str) -> list[Skill]:
        """Get all direct prerequisite skills that must be learned before skill_id."""
        stmt = (
            select(Skill)
            .join(SkillPrerequisite, SkillPrerequisite.prerequisite_skill_id == Skill.id)
            .where(SkillPrerequisite.skill_id == skill_id, Skill.is_active.is_(True))
            .order_by(Skill.sort_order.asc(), Skill.name.asc())
        )
        return list(self.db.scalars(stmt).all())

    def get_dependent_skills(self, skill_id: str) -> list[Skill]:
        """Get all direct skills that are unlocked once skill_id is mastered."""
        stmt = (
            select(Skill)
            .join(SkillPrerequisite, SkillPrerequisite.skill_id == Skill.id)
            .where(
                SkillPrerequisite.prerequisite_skill_id == skill_id,
                Skill.is_active.is_(True),
            )
            .order_by(Skill.sort_order.asc(), Skill.name.asc())
        )
        return list(self.db.scalars(stmt).all())

    # ── Taxonomy Map for Skill Map visualization ───────────────────────────

    def get_taxonomy_map(self) -> dict[str, Any]:
        """Return full active taxonomy: disciplines, skills (nodes), and prerequisite links (edges)."""
        disciplines = self.list_disciplines(only_active=True)
        skills = self.list_skills(only_active=True)

        # Query all active edges where both endpoints are active
        edges_stmt = (
            select(SkillPrerequisite)
            .join(Skill, Skill.id == SkillPrerequisite.skill_id)
            .where(Skill.is_active.is_(True))
        )
        all_edges = self.db.scalars(edges_stmt).all()

        active_skill_ids = {s.id for s in skills}
        valid_edges = [
            {"source": e.prerequisite_skill_id, "target": e.skill_id}
            for e in all_edges
            if e.prerequisite_skill_id in active_skill_ids and e.skill_id in active_skill_ids
        ]

        nodes = [
            {
                "id": s.id,
                "slug": s.slug,
                "name": s.name,
                "discipline_slug": s.discipline.slug if s.discipline else "",
                "difficulty_level": s.difficulty_level,
                "description": s.description,
                "icon": s.icon,
            }
            for s in skills
        ]

        disciplines_res = [
            {
                "id": d.id,
                "slug": d.slug,
                "name": d.name,
                "description": d.description,
                "icon": d.icon,
                "sort_order": d.sort_order,
                "is_active": d.is_active,
                "created_at": d.created_at,
                "skills_count": len([s for s in skills if s.discipline_id == d.id]),
            }
            for d in disciplines
        ]

        return {
            "nodes": nodes,
            "edges": valid_edges,
            "disciplines": disciplines_res,
        }
