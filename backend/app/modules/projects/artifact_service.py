"""Artifact lifecycle, storage quota enforcement, concurrency protection, and secure download service."""

from __future__ import annotations

import logging
import re
import threading
from collections import defaultdict
from collections.abc import Generator
from typing import BinaryIO

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app.infrastructure.rate_limiter import limiter
from app.infrastructure.storage.base import (
    StorageError,
    StorageFileTooLargeError,
    StorageInvalidTypeError,
    StorageSecurityError,
)
from app.infrastructure.storage.factory import get_storage_service
from app.modules.auth.models import User, UserRole
from app.modules.projects.exceptions import (
    ArtifactNotFoundError,
    ProjectForbiddenError,
    ProjectServiceError,
    ProjectValidationError,
    SubmissionNotFoundError,
)
from app.modules.projects.models import (
    Portfolio,
    PortfolioItem,
    PortfolioItemVisibility,
    ProjectArtifact,
    ProjectSubmission,
    SubmissionStatus,
)
from app.modules.projects.schemas import ArtifactListResponse, ArtifactResponse

logger = logging.getLogger("skillverse.projects.artifacts")

# Submission upload constraints
MAX_ARTIFACTS_PER_SUBMISSION = 10
MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024  # 20 MB
MAX_AGGREGATE_SUBMISSION_BYTES = 50 * 1024 * 1024  # 50 MB
UPLOAD_RATE_LIMIT_HOURLY = 10  # 10 uploads/hr per user

# In-process lock registry to serialize concurrent uploads per submission in SQLite/local runtimes
_submission_locks: dict[str, threading.Lock] = defaultdict(threading.Lock)
_lock_manager_mutex = threading.Lock()


def _get_submission_lock(submission_id: str) -> threading.Lock:
    """Retrieve an in-process lock per submission to serialize concurrency in SQLite/local environments."""
    with _lock_manager_mutex:
        return _submission_locks[submission_id]


def _sanitize_filename_for_header(filename: str) -> str:
    """Strip header-splitting characters, quotes, and control chars from filename."""
    clean = re.sub(r'[\r\n\0"\\;]', "_", filename).strip()
    return clean or "artifact.bin"


class ArtifactService:
    """Service governing artifact ingestion, transactional rollback, limits, and gated downloads."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.storage = get_storage_service()

    def _format_artifact(self, artifact: ProjectArtifact) -> ArtifactResponse:
        return ArtifactResponse(
            id=artifact.id,
            submission_id=artifact.submission_id,
            user_id=artifact.user_id,
            storage_key=artifact.storage_key,
            original_filename=artifact.original_filename,
            mime_type=artifact.mime_type,
            file_size_bytes=artifact.file_size_bytes,
            checksum_sha256=artifact.checksum_sha256,
            is_public=artifact.is_public,
            created_at=artifact.created_at,
            download_url=f"/api/v1/artifacts/{artifact.id}/download",
        )

    def upload_artifact(
        self,
        submission_id: str,
        user: User,
        file_data: bytes | BinaryIO,
        filename: str,
        content_type: str | None = None,
        is_public: bool = False,
    ) -> ArtifactResponse:
        """Upload deliverable artifact with row locking, quotas, rate limiting, and atomic cleanup."""
        with _get_submission_lock(submission_id):
            # 1. User upload rate limit check (max 10 uploads/hour per user)
            rate_key = f"artifact_upload:{user.id}"
            allowed, _remaining, retry_after = limiter.check(
                key=rate_key,
                max_requests=UPLOAD_RATE_LIMIT_HOURLY,
                window_seconds=3600,
            )
            if not allowed:
                raise ProjectServiceError(
                    f"Hourly upload limit exceeded. Try again in {retry_after} seconds.",
                    code="RATE_LIMITED",
                    status_code=429,
                    details={"retry_after": retry_after},
                )

            # 2. Concurrency protection: Lock submission row for updates within the active transaction
            submission = self.db.execute(
                select(ProjectSubmission)
                .where(ProjectSubmission.id == submission_id)
                .with_for_update()
            ).scalar_one_or_none()

            if not submission:
                raise SubmissionNotFoundError(f"Submission '{submission_id}' was not found.")

            # 3. Ownership and status validation
            if submission.user_id != user.id:
                raise ProjectForbiddenError("You can only upload artifacts to your own submission.")

            if submission.status != SubmissionStatus.DRAFT.value:
                raise ProjectValidationError(
                    f"Artifacts can only be attached to draft submissions. Current status: '{submission.status}'."
                )

            # 4. Count and Aggregate Size Limit Verification
            existing_artifacts = self.db.execute(
                select(ProjectArtifact).where(ProjectArtifact.submission_id == submission.id)
            ).scalars().all()

            if len(existing_artifacts) >= MAX_ARTIFACTS_PER_SUBMISSION:
                raise ProjectValidationError(
                    f"Cannot exceed the maximum limit of {MAX_ARTIFACTS_PER_SUBMISSION} artifacts per submission."
                )

            # Check preliminary file size if bytes
            initial_size = len(file_data) if isinstance(file_data, (bytes, bytearray)) else None
            if initial_size is not None and initial_size > MAX_FILE_SIZE_BYTES:
                raise ProjectValidationError(
                    f"File size exceeds individual artifact limit of {MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB."
                )

            current_aggregate = sum(a.file_size_bytes for a in existing_artifacts)
            if initial_size is not None and (current_aggregate + initial_size > MAX_AGGREGATE_SUBMISSION_BYTES):
                raise ProjectValidationError(
                    f"Total submission deliverables would exceed aggregate limit of "
                    f"{MAX_AGGREGATE_SUBMISSION_BYTES // (1024 * 1024)} MB. "
                    f"Current total: {current_aggregate / (1024*1024):.1f} MB."
                )

            # 5. Persist to storage backend with fixed server-controlled prefix
            server_prefix = f"submissions/{submission.id}"
            try:
                stored_meta = self.storage.store(
                    file_data=file_data,
                    filename=filename,
                    content_type=content_type,
                    prefix=server_prefix,
                )
            except StorageInvalidTypeError as exc:
                raise ProjectValidationError(str(exc)) from exc
            except StorageFileTooLargeError as exc:
                raise ProjectValidationError(str(exc)) from exc
            except StorageSecurityError as exc:
                raise ProjectValidationError(f"Security violation: {exc}") from exc
            except StorageError as exc:
                raise ProjectServiceError(f"Storage failed: {exc}", status_code=500) from exc

            # Verify aggregate size post-storage (for streams where initial size was unknown)
            if current_aggregate + stored_meta.file_size_bytes > MAX_AGGREGATE_SUBMISSION_BYTES:
                self.storage.delete(stored_meta.storage_key)
                raise ProjectValidationError(
                    f"Total submission deliverables exceed aggregate limit of "
                    f"{MAX_AGGREGATE_SUBMISSION_BYTES // (1024 * 1024)} MB."
                )

            # 6. Database record persistence with transactional rollback
            artifact = ProjectArtifact(
                submission_id=submission.id,
                user_id=user.id,
                storage_key=stored_meta.storage_key,
                original_filename=stored_meta.original_filename,
                mime_type=stored_meta.mime_type,
                file_size_bytes=stored_meta.file_size_bytes,
                checksum_sha256=stored_meta.checksum_sha256,
                is_public=is_public,
            )

            try:
                self.db.add(artifact)
                self.db.commit()
                self.db.refresh(artifact)
            except Exception as exc:
                self.db.rollback()
                logger.error("Database error saving artifact, rolling back stored file %s: %s", stored_meta.storage_key, exc)
                self.storage.delete(stored_meta.storage_key)
                raise

            return self._format_artifact(artifact)

    def list_submission_artifacts(
        self,
        submission_id: str,
        user: User,
    ) -> ArtifactListResponse:
        """List artifacts attached to a submission if caller has access."""
        submission = self.db.execute(
            select(ProjectSubmission)
            .where(ProjectSubmission.id == submission_id)
            .options(
                selectinload(ProjectSubmission.artifacts),
                selectinload(ProjectSubmission.project),
            )
        ).scalar_one_or_none()
        if not submission:
            raise SubmissionNotFoundError(f"Submission '{submission_id}' was not found.")

        is_owner = submission.user_id == user.id
        is_creator = submission.project and submission.project.creator_id == user.id
        is_evaluator = submission.evaluator_id == user.id
        is_admin = user.role == UserRole.ADMIN

        if not (is_owner or is_creator or is_evaluator or is_admin):
            raise ProjectForbiddenError("You are not authorized to view artifacts for this submission.")

        artifacts_payload = [self._format_artifact(a) for a in submission.artifacts]
        total_size = sum(a.file_size_bytes for a in submission.artifacts)

        return ArtifactListResponse(
            submission_id=submission.id,
            total_count=len(artifacts_payload),
            total_size_bytes=total_size,
            artifacts=artifacts_payload,
        )

    def delete_artifact(self, artifact_id: str, user: User) -> None:
        """Remove an artifact from storage and database (only while submission is DRAFT)."""
        artifact = self.db.execute(
            select(ProjectArtifact)
            .where(ProjectArtifact.id == artifact_id)
            .options(selectinload(ProjectArtifact.submission))
        ).scalar_one_or_none()
        if not artifact:
            raise ArtifactNotFoundError(f"Artifact '{artifact_id}' was not found.")

        if artifact.user_id != user.id:
            raise ProjectForbiddenError("You can only delete your own artifacts.")

        if artifact.submission.status != SubmissionStatus.DRAFT.value:
            raise ProjectValidationError(
                f"Artifacts cannot be deleted once submission is in '{artifact.submission.status}' status."
            )

        storage_key = artifact.storage_key
        self.db.delete(artifact)
        self.db.commit()

        # Delete from disk
        self.storage.delete(storage_key)

    def check_download_authorization(
        self,
        artifact: ProjectArtifact,
        user: User | None,
    ) -> bool:
        """Verify download authorization using ownership, reviewer roles, or 5 public portfolio gates."""
        # 1. Privileged or direct ownership authorization
        if user is not None:
            if artifact.user_id == user.id:
                return True
            if user.role == UserRole.ADMIN:
                return True
            submission = artifact.submission
            if submission.evaluator_id == user.id:
                return True
            if submission.project and submission.project.creator_id == user.id:
                return True

        # 2. Strict 5-Gate Public Portfolio Verification for Anonymous or Third-Party Users
        submission = artifact.submission

        # Gate 1: Submission must be COMPLETED
        if submission.status != SubmissionStatus.COMPLETED.value:
            return False

        # Gate 2: Artifact must be flagged public
        if not artifact.is_public:
            return False

        # Gate 3: Learner's portfolio must exist and be marked public
        portfolio = self.db.execute(
            select(Portfolio).where(Portfolio.user_id == artifact.user_id)
        ).scalar_one_or_none()
        if not portfolio or not portfolio.is_public:
            return False

        # Gate 4 & 5: Public PortfolioItem exists referencing this submission or artifact with PUBLIC visibility
        portfolio_item = self.db.execute(
            select(PortfolioItem).where(
                PortfolioItem.portfolio_user_id == artifact.user_id,
                PortfolioItem.visibility == PortfolioItemVisibility.PUBLIC.value,
                or_(
                    PortfolioItem.reference_id == submission.id,
                    PortfolioItem.reference_id == artifact.id,
                ),
            )
        ).scalars().first()

        return bool(portfolio_item)

    def prepare_download(
        self,
        artifact_id: str,
        user: User | None,
    ) -> tuple[Generator[bytes, None, None], str, str, int]:
        """Verify authorization and return streaming generator, safe filename, content type, and size."""
        artifact = self.db.execute(
            select(ProjectArtifact)
            .where(ProjectArtifact.id == artifact_id)
            .options(
                selectinload(ProjectArtifact.submission).selectinload(ProjectSubmission.project)
            )
        ).scalar_one_or_none()
        if not artifact:
            raise ArtifactNotFoundError(f"Artifact '{artifact_id}' was not found.")

        authorized = self.check_download_authorization(artifact, user)
        if not authorized:
            raise ProjectForbiddenError("You are not authorized to download this artifact.")

        safe_filename = _sanitize_filename_for_header(artifact.original_filename)
        stream_gen = self.storage.retrieve_stream(artifact.storage_key)

        return (
            stream_gen,
            safe_filename,
            artifact.mime_type or "application/octet-stream",
            artifact.file_size_bytes,
        )
