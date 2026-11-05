"""API endpoints for project catalog discovery, creator authoring, submissions, reviews, and artifacts."""

from __future__ import annotations

from typing import Any

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Response,
    UploadFile,
    status,
)
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.dependencies import (
    get_current_user,
    get_optional_current_user,
    require_creator_or_admin,
)
from app.infrastructure.database import get_db
from app.modules.auth.models import User
from app.modules.projects.artifact_service import ArtifactService
from app.modules.projects.exceptions import ProjectServiceError
from app.modules.projects.portfolio_service import PortfolioService
from app.modules.projects.schemas import (
    ArtifactListResponse,
    ArtifactResponse,
    EvaluationResponse,
    PortfolioDetailResponse,
    PortfolioItemCreateRequest,
    PortfolioItemReorderRequest,
    PortfolioItemResponse,
    PortfolioItemUpdateRequest,
    PortfolioPublicResponse,
    PortfolioUpdateRequest,
    ProjectCreateRequest,
    ProjectDetailResponse,
    ProjectPaginatedResponse,
    ProjectUpdateRequest,
    SubmissionCreateRequest,
    SubmissionDetailResponse,
    SubmissionEvaluationRequest,
    SubmissionHistoryResponse,
    SubmissionReviewClaimResponse,
    SubmissionRevisionRequest,
    SubmissionSummaryResponse,
    SubmissionUpdateRequest,
)
from app.modules.projects.service import ProjectService
from app.modules.projects.submission_service import SubmissionService

router = APIRouter(tags=["Projects & Submissions"])


def _handle_service_error(exc: ProjectServiceError) -> None:
    """Format domain exceptions into standardized SkillVerse API error responses."""
    raise HTTPException(
        status_code=exc.status_code,
        detail={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details if exc.details is not None else {},
            }
        },
    )


# ── Project Catalog Discovery ───────────────────────────────────────────────


@router.get(
    "/projects",
    response_model=ProjectPaginatedResponse,
    summary="List and filter projects in catalog",
)
def list_projects(
    discipline_id: str | None = Query(None, description="Filter by discipline UUID"),
    skill_id: str | None = Query(None, description="Filter by demonstrated skill UUID"),
    difficulty_level: str | None = Query(None, description="BEGINNER, INTERMEDIATE, ADVANCED, EXPERT"),
    search: str | None = Query(None, description="Text search on title and description"),
    status: str | None = Query(None, description="Filter status (Creators and Admins only)"),
    sort_by: str = Query("created_at", pattern="^(created_at|title|difficulty_level)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User | None = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Browse catalog projects with pagination, sorting, and discipline/skill filters."""
    service = ProjectService(db)
    try:
        return service.list_projects(
            discipline_id=discipline_id,
            skill_id=skill_id,
            difficulty_level=difficulty_level,
            search=search,
            status=status,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            page_size=page_size,
            current_user=current_user,
        )
    except ProjectServiceError as exc:
        _handle_service_error(exc)


@router.get(
    "/projects/{project_id_or_slug}",
    response_model=ProjectDetailResponse,
    summary="Retrieve full project details and rubric",
)
def get_project(
    project_id_or_slug: str,
    current_user: User | None = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Retrieve full project specification, rubric, starter resources, and learner's latest submission."""
    service = ProjectService(db)
    try:
        return service.get_project(project_id_or_slug, current_user=current_user)
    except ProjectServiceError as exc:
        _handle_service_error(exc)


# ── Creator Project Authoring ───────────────────────────────────────────────


@router.post(
    "/projects",
    response_model=ProjectDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new project draft",
)
def create_project(
    data: ProjectCreateRequest,
    current_user: User = Depends(require_creator_or_admin),
    db: Session = Depends(get_db),
) -> Any:
    """Author and store a new project specification in draft status."""
    service = ProjectService(db)
    try:
        return service.create_project(data, current_user)
    except ProjectServiceError as exc:
        _handle_service_error(exc)


@router.patch(
    "/projects/{project_id}",
    response_model=ProjectDetailResponse,
    summary="Update project draft or metadata",
)
def update_project(
    project_id: str,
    data: ProjectUpdateRequest,
    current_user: User = Depends(require_creator_or_admin),
    db: Session = Depends(get_db),
) -> Any:
    """Update project details, requirements, rubric, or associated skills."""
    service = ProjectService(db)
    try:
        return service.update_project(project_id, data, current_user)
    except ProjectServiceError as exc:
        _handle_service_error(exc)


@router.post(
    "/projects/{project_id}/publish",
    response_model=ProjectDetailResponse,
    summary="Publish a project to the public catalog",
)
def publish_project(
    project_id: str,
    current_user: User = Depends(require_creator_or_admin),
    db: Session = Depends(get_db),
) -> Any:
    """Validate project completeness (rubric, milestones, skills) and publish."""
    service = ProjectService(db)
    try:
        return service.publish_project(project_id, current_user)
    except ProjectServiceError as exc:
        _handle_service_error(exc)


@router.post(
    "/projects/{project_id}/archive",
    response_model=ProjectDetailResponse,
    summary="Archive a project",
)
def archive_project(
    project_id: str,
    current_user: User = Depends(require_creator_or_admin),
    db: Session = Depends(get_db),
) -> Any:
    """Decommission and archive an existing project."""
    service = ProjectService(db)
    try:
        return service.archive_project(project_id, current_user)
    except ProjectServiceError as exc:
        _handle_service_error(exc)


# ── Learner Submissions Lifecycle ───────────────────────────────────────────


@router.post(
    "/projects/{project_id}/submissions",
    response_model=SubmissionDetailResponse,
    summary="Start project draft or return existing active draft",
)
def start_or_get_submission_draft(
    project_id: str,
    data: SubmissionCreateRequest | None = None,
    response: Response = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Begin working on a project or resume an existing active draft without duplication."""
    service = SubmissionService(db)
    try:
        result, created = service.start_or_get_draft(project_id, current_user, data)
        if response is not None and created:
            response.status_code = status.HTTP_201_CREATED
        return result
    except ProjectServiceError as exc:
        _handle_service_error(exc)


@router.get(
    "/submissions/mine",
    response_model=list[SubmissionSummaryResponse],
    summary="List all submissions by the authenticated learner",
)
def list_my_submissions(
    project_id: str | None = Query(None, description="Optional filter by project UUID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Retrieve all submissions authored by the current learner."""
    service = SubmissionService(db)
    try:
        return service.list_user_submissions(current_user, project_id=project_id)
    except ProjectServiceError as exc:
        _handle_service_error(exc)


@router.get(
    "/submissions/{submission_id}",
    response_model=SubmissionDetailResponse,
    summary="Get submission details by ID",
)
def get_submission(
    submission_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Fetch complete submission record, deliverables, evaluation, and artifacts."""
    service = SubmissionService(db)
    try:
        return service.get_submission(submission_id, current_user)
    except ProjectServiceError as exc:
        _handle_service_error(exc)


@router.patch(
    "/submissions/{submission_id}",
    response_model=SubmissionDetailResponse,
    summary="Update draft deliverables and milestones",
)
def update_draft_submission(
    submission_id: str,
    data: SubmissionUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Update title, notes, answers, or milestone progress of an in-progress draft."""
    service = SubmissionService(db)
    try:
        return service.update_draft(submission_id, current_user, data)
    except ProjectServiceError as exc:
        _handle_service_error(exc)


@router.post(
    "/submissions/{submission_id}/submit",
    response_model=SubmissionDetailResponse,
    summary="Submit project deliverables for evaluation",
)
def submit_project(
    submission_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Submit completed project deliverables, transitioning from DRAFT to SUBMITTED."""
    service = SubmissionService(db)
    try:
        return service.submit_project(submission_id, current_user)
    except ProjectServiceError as exc:
        _handle_service_error(exc)


@router.post(
    "/submissions/{submission_id}/revisions",
    response_model=SubmissionDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an immutable revision draft",
)
def create_submission_revision(
    submission_id: str,
    data: SubmissionRevisionRequest | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Initiate a new revision draft from a submission with CHANGES_REQUESTED status."""
    service = SubmissionService(db)
    try:
        return service.create_revision(submission_id, current_user, data)
    except ProjectServiceError as exc:
        _handle_service_error(exc)


@router.get(
    "/submissions/{submission_id}/history",
    response_model=SubmissionHistoryResponse,
    summary="Get revision history for a project submission",
)
def get_submission_history(
    submission_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """List all sequential versions and revision notes for this project submission."""
    service = SubmissionService(db)
    try:
        return service.get_submission_history(submission_id, current_user)
    except ProjectServiceError as exc:
        _handle_service_error(exc)


# ── Evaluator Review and Grading ────────────────────────────────────────────


@router.post(
    "/submissions/{submission_id}/review",
    response_model=SubmissionReviewClaimResponse,
    summary="Claim submission for review",
)
def claim_submission_review(
    submission_id: str,
    current_user: User = Depends(require_creator_or_admin),
    db: Session = Depends(get_db),
) -> Any:
    """Assign submitted deliverables to current creator or admin for review."""
    service = SubmissionService(db)
    try:
        return service.claim_for_review(submission_id, current_user)
    except ProjectServiceError as exc:
        _handle_service_error(exc)


@router.post(
    "/submissions/{submission_id}/evaluation",
    response_model=EvaluationResponse,
    summary="Evaluate submission against project rubric",
)
def evaluate_submission(
    submission_id: str,
    data: SubmissionEvaluationRequest,
    current_user: User = Depends(require_creator_or_admin),
    db: Session = Depends(get_db),
) -> Any:
    """Score submission against rubric criteria and transition to COMPLETED or CHANGES_REQUESTED."""
    service = SubmissionService(db)
    try:
        return service.evaluate_submission(submission_id, current_user, data)
    except ProjectServiceError as exc:
        _handle_service_error(exc)


# ── Artifact Upload and Secure Download ─────────────────────────────────────


@router.post(
    "/submissions/{submission_id}/artifacts",
    response_model=ArtifactResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload deliverable artifact to draft submission",
)
async def upload_artifact(
    submission_id: str,
    file: UploadFile = File(..., description="Deliverable file (ZIP, PDF, image, text)"),
    is_public: bool = Form(default=False, description="Whether artifact may be displayed in public portfolios"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Upload deliverable artifact enforcing per-file (20MB), total (50MB), and rate limits."""
    service = ArtifactService(db)
    try:
        contents = await file.read()
        return service.upload_artifact(
            submission_id=submission_id,
            user=current_user,
            file_data=contents,
            filename=file.filename or "artifact.bin",
            content_type=file.content_type,
            is_public=is_public,
        )
    except ProjectServiceError as exc:
        _handle_service_error(exc)


@router.get(
    "/submissions/{submission_id}/artifacts",
    response_model=ArtifactListResponse,
    summary="List all artifacts for a submission",
)
def list_submission_artifacts(
    submission_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Retrieve deliverable metadata and download links for a submission."""
    service = ArtifactService(db)
    try:
        return service.list_submission_artifacts(submission_id, current_user)
    except ProjectServiceError as exc:
        _handle_service_error(exc)


@router.delete(
    "/artifacts/{artifact_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an artifact from a draft submission",
)
def delete_artifact(
    artifact_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """Delete an artifact from storage and database (only while submission is DRAFT)."""
    service = ArtifactService(db)
    try:
        service.delete_artifact(artifact_id, current_user)
    except ProjectServiceError as exc:
        _handle_service_error(exc)


@router.get(
    "/artifacts/{artifact_id}/download",
    summary="Download deliverable artifact with security verification",
)
def download_artifact(
    artifact_id: str,
    current_user: User | None = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Download an artifact verifying ownership, reviewer role, or 5-gate public portfolio access."""
    service = ArtifactService(db)
    try:
        stream_gen, filename, mime_type, file_size = service.prepare_download(artifact_id, current_user)
        headers = {
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Content-Type-Options": "nosniff",
            "Content-Length": str(file_size),
        }
        return StreamingResponse(
            stream_gen,
            media_type=mime_type,
            headers=headers,
        )
    except ProjectServiceError as exc:
        _handle_service_error(exc)


# ── Portfolio Showcase & Management ─────────────────────────────────────────


@router.get(
    "/portfolios/me",
    response_model=PortfolioDetailResponse,
    summary="Get authenticated learner's portfolio",
    tags=["Portfolios"],
)
def get_my_portfolio(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Retrieve the authenticated learner's complete portfolio profile and items (auto-created if first visit)."""
    service = PortfolioService(db)
    try:
        return service.get_my_portfolio(current_user)
    except ProjectServiceError as exc:
        _handle_service_error(exc)


@router.patch(
    "/portfolios/me",
    response_model=PortfolioDetailResponse,
    summary="Update authenticated learner's portfolio profile",
    tags=["Portfolios"],
)
def update_my_portfolio(
    data: PortfolioUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Update title, headline, bio, custom slug, visibility, and display settings."""
    service = PortfolioService(db)
    try:
        return service.update_my_portfolio(current_user, data)
    except ProjectServiceError as exc:
        _handle_service_error(exc)


@router.post(
    "/portfolios/me/items",
    response_model=PortfolioItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Feature an item in learner's portfolio",
    tags=["Portfolios"],
)
def add_portfolio_item(
    data: PortfolioItemCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Add a completed project submission or showcase item to learner's portfolio."""
    service = PortfolioService(db)
    try:
        return service.add_item(current_user, data)
    except ProjectServiceError as exc:
        _handle_service_error(exc)


@router.patch(
    "/portfolios/me/items/{item_id}",
    response_model=PortfolioItemResponse,
    summary="Update a portfolio item",
    tags=["Portfolios"],
)
def update_portfolio_item(
    item_id: str,
    data: PortfolioItemUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Update title, summary, visibility, external URL, or sort order for a portfolio item."""
    service = PortfolioService(db)
    try:
        return service.update_item(current_user, item_id, data)
    except ProjectServiceError as exc:
        _handle_service_error(exc)


@router.delete(
    "/portfolios/me/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove an item from portfolio",
    tags=["Portfolios"],
)
def delete_portfolio_item(
    item_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """Non-destructively remove an item from portfolio without deleting the source submission or artifacts."""
    service = PortfolioService(db)
    try:
        service.delete_item(current_user, item_id)
    except ProjectServiceError as exc:
        _handle_service_error(exc)


@router.post(
    "/portfolios/me/items/reorder",
    response_model=list[PortfolioItemResponse],
    summary="Reorder portfolio items",
    tags=["Portfolios"],
)
def reorder_portfolio_items(
    data: PortfolioItemReorderRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Update display order for learner's portfolio items."""
    service = PortfolioService(db)
    try:
        return service.reorder_items(current_user, data)
    except ProjectServiceError as exc:
        _handle_service_error(exc)


@router.get(
    "/portfolios/{slug_or_id}",
    response_model=PortfolioPublicResponse,
    summary="Get public or unlisted portfolio profile",
    tags=["Portfolios"],
)
def get_public_portfolio(
    slug_or_id: str,
    current_user: User | None = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Retrieve public showcase by custom slug or user UUID with strict privacy enforcement."""
    service = PortfolioService(db)
    try:
        return service.get_public_portfolio(slug_or_id, current_user)
    except ProjectServiceError as exc:
        _handle_service_error(exc)

