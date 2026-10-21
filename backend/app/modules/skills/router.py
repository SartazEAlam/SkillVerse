"""API endpoints for cross-disciplinary skills, disciplines, and prerequisites."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.dependencies import require_admin, require_creator_or_admin
from app.infrastructure.database import get_db
from app.modules.auth.models import User
from app.modules.skills.models import SkillDifficulty
from app.modules.skills.schemas import (
    DisciplineBase,
    DisciplineDetailResponse,
    DisciplineResponse,
    PrerequisiteAddRequest,
    SkillCreateRequest,
    SkillDetailResponse,
    SkillResponse,
    SkillSummary,
    SkillTaxonomyMapResponse,
    SkillUpdateRequest,
)
from app.modules.skills.service import SkillService, SkillServiceError

router = APIRouter(tags=["Skills & Taxonomy"])


def _get_skill_service(db: Session = Depends(get_db)) -> SkillService:
    return SkillService(db)


# ── Disciplines Endpoints ──────────────────────────────────────────────────


@router.get("/disciplines", response_model=list[DisciplineResponse])
def list_disciplines(
    service: SkillService = Depends(_get_skill_service),
) -> list[dict[str, Any]]:
    """List all active disciplines ordered by presentation sort order."""
    disciplines = service.list_disciplines(only_active=True)
    return [
        {
            "id": d.id,
            "slug": d.slug,
            "name": d.name,
            "description": d.description,
            "icon": d.icon,
            "sort_order": d.sort_order,
            "is_active": d.is_active,
            "created_at": d.created_at,
            "skills_count": len([s for s in d.skills if s.is_active]),
        }
        for d in disciplines
    ]


@router.get("/disciplines/{slug}", response_model=DisciplineDetailResponse)
def get_discipline(
    slug: str,
    service: SkillService = Depends(_get_skill_service),
) -> dict[str, Any]:
    """Retrieve discipline details by slug with all contained skills."""
    discipline = service.get_discipline_by_slug(slug, only_active=True)
    if not discipline:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "DISCIPLINE_NOT_FOUND",
                    "message": f"Discipline '{slug}' not found.",
                }
            },
        )

    active_skills = [s for s in discipline.skills if s.is_active]
    return {
        "id": discipline.id,
        "slug": discipline.slug,
        "name": discipline.name,
        "description": discipline.description,
        "icon": discipline.icon,
        "sort_order": discipline.sort_order,
        "is_active": discipline.is_active,
        "created_at": discipline.created_at,
        "skills_count": len(active_skills),
        "skills": [
            {
                "id": s.id,
                "slug": s.slug,
                "name": s.name,
                "difficulty_level": s.difficulty_level,
                "icon": s.icon,
                "sort_order": s.sort_order,
            }
            for s in active_skills
        ],
    }


@router.post("/disciplines", response_model=DisciplineResponse, status_code=status.HTTP_201_CREATED)
def create_discipline(
    body: DisciplineBase,
    _: User = Depends(require_admin),
    service: SkillService = Depends(_get_skill_service),
) -> dict[str, Any]:
    """Create a new discipline (admin privilege required)."""
    try:
        disc = service.create_discipline(
            slug=body.slug,
            name=body.name,
            description=body.description,
            icon=body.icon,
            sort_order=body.sort_order,
            is_active=body.is_active,
        )
    except SkillServiceError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"error": {"code": e.code, "message": e.message}},
        )

    return {
        "id": disc.id,
        "slug": disc.slug,
        "name": disc.name,
        "description": disc.description,
        "icon": disc.icon,
        "sort_order": disc.sort_order,
        "is_active": disc.is_active,
        "created_at": disc.created_at,
        "skills_count": 0,
    }


# ── Skills Endpoints ───────────────────────────────────────────────────────


@router.get("/skills", response_model=list[SkillResponse])
def list_skills(
    discipline: str | None = Query(None, description="Filter by discipline slug"),
    difficulty: SkillDifficulty | None = Query(None, description="Filter by difficulty level"),
    search: str | None = Query(None, description="Search term for name or description"),
    service: SkillService = Depends(_get_skill_service),
) -> list[dict[str, Any]]:
    """List active skills with optional discipline, difficulty, and search filters."""
    skills = service.list_skills(
        discipline_slug=discipline,
        difficulty=difficulty,
        search=search,
        only_active=True,
    )
    return [
        {
            "id": s.id,
            "slug": s.slug,
            "name": s.name,
            "description": s.description,
            "discipline_id": s.discipline_id,
            "discipline_slug": s.discipline.slug if s.discipline else None,
            "discipline_name": s.discipline.name if s.discipline else None,
            "parent_skill_id": s.parent_skill_id,
            "difficulty_level": s.difficulty_level,
            "icon": s.icon,
            "sort_order": s.sort_order,
            "is_active": s.is_active,
            "created_at": s.created_at,
        }
        for s in skills
    ]


@router.get("/skills/taxonomy/map", response_model=SkillTaxonomyMapResponse)
def get_taxonomy_map(
    service: SkillService = Depends(_get_skill_service),
) -> dict[str, Any]:
    """Retrieve full active skill DAG nodes and edges for the Skill Map visualizer."""
    return service.get_taxonomy_map()


@router.get("/skills/{slug}", response_model=SkillDetailResponse)
def get_skill_by_slug(
    slug: str,
    service: SkillService = Depends(_get_skill_service),
) -> dict[str, Any]:
    """Retrieve skill details including prerequisite skills and unlocked skills."""
    skill = service.get_skill_by_slug(slug, only_active=True)
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "SKILL_NOT_FOUND", "message": f"Skill '{slug}' not found."}},
        )

    prereqs = [
        SkillSummary.model_validate(edge.prerequisite_skill)
        for edge in skill.prerequisite_edges
        if edge.prerequisite_skill.is_active
    ]
    unlocked = [
        SkillSummary.model_validate(edge.skill)
        for edge in skill.dependent_edges
        if edge.skill.is_active
    ]

    return {
        "id": skill.id,
        "slug": skill.slug,
        "name": skill.name,
        "description": skill.description,
        "discipline_id": skill.discipline_id,
        "discipline_slug": skill.discipline.slug if skill.discipline else None,
        "discipline_name": skill.discipline.name if skill.discipline else None,
        "parent_skill_id": skill.parent_skill_id,
        "difficulty_level": skill.difficulty_level,
        "icon": skill.icon,
        "sort_order": skill.sort_order,
        "is_active": skill.is_active,
        "created_at": skill.created_at,
        "prerequisites": prereqs,
        "unlocked_skills": unlocked,
        "courses_count": len(skill.course_associations),
    }


@router.post("/skills", response_model=SkillResponse, status_code=status.HTTP_201_CREATED)
def create_skill(
    body: SkillCreateRequest,
    _: User = Depends(require_creator_or_admin),
    service: SkillService = Depends(_get_skill_service),
) -> dict[str, Any]:
    """Create a new skill (creator or admin privilege required)."""
    try:
        skill = service.create_skill(
            slug=body.slug,
            name=body.name,
            discipline_id=body.discipline_id,
            description=body.description,
            parent_skill_id=body.parent_skill_id,
            difficulty_level=body.difficulty_level,
            icon=body.icon,
            sort_order=body.sort_order,
            is_active=body.is_active,
        )
    except SkillServiceError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"error": {"code": e.code, "message": e.message}},
        )

    return {
        "id": skill.id,
        "slug": skill.slug,
        "name": skill.name,
        "description": skill.description,
        "discipline_id": skill.discipline_id,
        "discipline_slug": skill.discipline.slug if skill.discipline else None,
        "discipline_name": skill.discipline.name if skill.discipline else None,
        "parent_skill_id": skill.parent_skill_id,
        "difficulty_level": skill.difficulty_level,
        "icon": skill.icon,
        "sort_order": skill.sort_order,
        "is_active": skill.is_active,
        "created_at": skill.created_at,
    }


@router.patch("/skills/{skill_id}", response_model=SkillResponse)
def update_skill(
    skill_id: str,
    body: SkillUpdateRequest,
    _: User = Depends(require_creator_or_admin),
    service: SkillService = Depends(_get_skill_service),
) -> dict[str, Any]:
    """Update skill properties (creator or admin privilege required)."""
    try:
        skill = service.update_skill(
            skill_id=skill_id,
            name=body.name,
            description=body.description,
            difficulty_level=body.difficulty_level,
            icon=body.icon,
            sort_order=body.sort_order,
            is_active=body.is_active,
        )
    except SkillServiceError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"error": {"code": e.code, "message": e.message}},
        )

    return {
        "id": skill.id,
        "slug": skill.slug,
        "name": skill.name,
        "description": skill.description,
        "discipline_id": skill.discipline_id,
        "discipline_slug": skill.discipline.slug if skill.discipline else None,
        "discipline_name": skill.discipline.name if skill.discipline else None,
        "parent_skill_id": skill.parent_skill_id,
        "difficulty_level": skill.difficulty_level,
        "icon": skill.icon,
        "sort_order": skill.sort_order,
        "is_active": skill.is_active,
        "created_at": skill.created_at,
    }


# ── Prerequisites Management Endpoints ─────────────────────────────────────


@router.post(
    "/skills/{skill_id}/prerequisites",
    status_code=status.HTTP_201_CREATED,
)
def add_prerequisite(
    skill_id: str,
    body: PrerequisiteAddRequest,
    _: User = Depends(require_creator_or_admin),
    service: SkillService = Depends(_get_skill_service),
) -> dict[str, Any]:
    """Add a directed prerequisite dependency to a skill (creator or admin required).

    Validates:
    - Cannot depend on self (400)
    - Prerequisite must exist (404)
    - No duplicate relationship (409)
    - Rejects circular dependency cycles (400)
    """
    try:
        edge = service.add_prerequisite(
            skill_id=skill_id,
            prerequisite_skill_id=body.prerequisite_skill_id,
        )
    except SkillServiceError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"error": {"code": e.code, "message": e.message}},
        )

    return {
        "skill_id": edge.skill_id,
        "prerequisite_skill_id": edge.prerequisite_skill_id,
        "created_at": edge.created_at.isoformat() if edge.created_at else None,
    }


@router.delete(
    "/skills/{skill_id}/prerequisites/{prerequisite_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_prerequisite(
    skill_id: str,
    prerequisite_id: str,
    _: User = Depends(require_creator_or_admin),
    service: SkillService = Depends(_get_skill_service),
) -> None:
    """Remove a directed prerequisite relationship (creator or admin required)."""
    try:
        service.remove_prerequisite(
            skill_id=skill_id,
            prerequisite_skill_id=prerequisite_id,
        )
    except SkillServiceError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"error": {"code": e.code, "message": e.message}},
        )
