"""Learner project submission lifecycle, revision tracking, and evaluator review service."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.orm.attributes import flag_modified

from app.modules.auth.models import User, UserRole
from app.modules.projects.exceptions import (
    ProjectConflictError,
    ProjectForbiddenError,
    ProjectNotFoundError,
    ProjectValidationError,
    SubmissionNotFoundError,
)
from app.modules.projects.models import (
    Project,
    ProjectArtifact,
    ProjectStatus,
    ProjectSubmission,
    SubmissionStatus,
)
from app.modules.projects.schemas import (
    ArtifactResponse,
    SubmissionCreateRequest,
    SubmissionEvaluationRequest,
    SubmissionRevisionRequest,
    SubmissionSummaryResponse,
    SubmissionUpdateRequest,
)

logger = logging.getLogger("skillverse.projects.submission")


class SubmissionService:
    """Service managing submissions, revision trees, review assignments, and rubric evaluations."""

    def __init__(self, db: Session) -> None:
        self.db = db

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

    def _format_submission(self, sub: ProjectSubmission, user: User) -> dict[str, Any]:
        evaluator_name: str | None = None
        if sub.evaluator and sub.evaluator.profile:
            evaluator_name = sub.evaluator.profile.display_name
        elif sub.evaluator:
            evaluator_name = sub.evaluator.email.split("@")[0]

        revisions_count = self.db.execute(
            select(func.count(ProjectSubmission.id)).where(
                ProjectSubmission.revision_of_id == sub.id
            )
        ).scalar_one()

        artifacts_payload = [self._format_artifact(a) for a in (sub.artifacts or [])]

        history = list((sub.content or {}).get("transition_history", []))
        if not history and sub.evaluation and "transition_history" in sub.evaluation:
            history = list(sub.evaluation["transition_history"])

        return {
            "id": sub.id,
            "project_id": sub.project_id,
            "user_id": sub.user_id,
            "version_number": sub.version_number,
            "revision_of_id": sub.revision_of_id,
            "status": sub.status,
            "title": sub.title,
            "summary": sub.summary,
            "content": sub.content or {},
            "milestones_completed": sub.milestones_completed or [],
            "evaluation": sub.evaluation,
            "score": sub.score,
            "passed": sub.passed,
            "submitted_at": sub.submitted_at,
            "evaluated_at": sub.evaluated_at,
            "evaluator_id": sub.evaluator_id,
            "evaluator_name": evaluator_name,
            "artifacts": artifacts_payload,
            "revisions_count": revisions_count,
            "transition_history": history,
            "created_at": sub.created_at,
            "updated_at": sub.updated_at,
        }

    def start_or_get_draft(
        self,
        project_id: str,
        user: User,
        data: SubmissionCreateRequest | None = None,
    ) -> tuple[dict[str, Any], bool]:
        """Start working on a project or retrieve an existing active draft.

        Returns (submission_dict, created_flag).
        """
        # Ensure project exists and is published (or testing by creator/admin)
        project = self.db.execute(select(Project).where(Project.id == project_id)).scalar_one_or_none()
        if not project:
            raise ProjectNotFoundError(f"Project '{project_id}' was not found.")

        is_creator = project.creator_id == user.id
        is_admin = user.role == UserRole.ADMIN
        if project.status != ProjectStatus.PUBLISHED.value and not (is_creator or is_admin):
            raise ProjectNotFoundError(f"Project '{project_id}' was not found.")

        # Check 1: Return existing active DRAFT if already present
        existing_draft = self.db.execute(
            select(ProjectSubmission)
            .where(
                ProjectSubmission.project_id == project.id,
                ProjectSubmission.user_id == user.id,
                ProjectSubmission.status == SubmissionStatus.DRAFT.value,
            )
            .options(
                selectinload(ProjectSubmission.artifacts),
                selectinload(ProjectSubmission.evaluator),
            )
        ).scalar_one_or_none()

        if existing_draft:
            return self._format_submission(existing_draft, user), False

        # Check 2: Prevent duplicate submissions while in-flight review is pending
        in_flight = self.db.execute(
            select(ProjectSubmission).where(
                ProjectSubmission.project_id == project.id,
                ProjectSubmission.user_id == user.id,
                ProjectSubmission.status.in_(
                    (
                        SubmissionStatus.SUBMITTED.value,
                        SubmissionStatus.UNDER_REVIEW.value,
                    )
                ),
            )
        ).scalar_one_or_none()

        if in_flight:
            raise ProjectConflictError(
                "You have an active submission currently awaiting evaluation.",
                details={"submission_id": in_flight.id, "status": in_flight.status},
            )

        # Check 3: If changes were requested on latest submission, prompt for revision
        latest_sub = self.db.execute(
            select(ProjectSubmission)
            .where(
                ProjectSubmission.project_id == project.id,
                ProjectSubmission.user_id == user.id,
            )
            .order_by(ProjectSubmission.version_number.desc())
        ).scalars().first()

        if latest_sub and latest_sub.status == SubmissionStatus.CHANGES_REQUESTED.value:
            raise ProjectConflictError(
                "Changes were requested on your previous submission. Please initiate a revision.",
                details={"submission_id": latest_sub.id},
            )

        # Compute version number
        max_v = self.db.execute(
            select(func.max(ProjectSubmission.version_number)).where(
                ProjectSubmission.project_id == project.id,
                ProjectSubmission.user_id == user.id,
            )
        ).scalar_one()
        next_version = (max_v or 0) + 1

        title = data.title if data and data.title else f"Submission v{next_version} for {project.title}"
        summary = data.summary if data else None
        content = dict(data.content) if data and data.content else {}
        content["transition_history"] = [
            {
                "from_status": None,
                "to_status": SubmissionStatus.DRAFT.value,
                "timestamp": datetime.now(UTC).isoformat(),
                "triggered_by": user.id,
                "reason": "Draft started by learner",
            }
        ]

        submission = ProjectSubmission(
            project_id=project.id,
            user_id=user.id,
            version_number=next_version,
            status=SubmissionStatus.DRAFT.value,
            title=title,
            summary=summary,
            content=content,
            milestones_completed=[],
        )
        self.db.add(submission)
        self.db.commit()

        # Reload with relationships
        reloaded = self.db.execute(
            select(ProjectSubmission)
            .where(ProjectSubmission.id == submission.id)
            .options(
                selectinload(ProjectSubmission.artifacts),
                selectinload(ProjectSubmission.evaluator),
            )
        ).scalar_one()

        return self._format_submission(reloaded, user), True

    def get_submission(self, submission_id: str, user: User) -> dict[str, Any]:
        """Fetch a submission with access authorization verification."""
        stmt = (
            select(ProjectSubmission)
            .where(ProjectSubmission.id == submission_id)
            .options(
                selectinload(ProjectSubmission.artifacts),
                selectinload(ProjectSubmission.project),
                selectinload(ProjectSubmission.evaluator),
            )
        )
        submission = self.db.execute(stmt).scalar_one_or_none()
        if not submission:
            raise SubmissionNotFoundError(f"Submission '{submission_id}' was not found.")

        # Authorization: owner, project creator, assigned evaluator, or admin
        is_owner = submission.user_id == user.id
        is_creator = submission.project and submission.project.creator_id == user.id
        is_evaluator = submission.evaluator_id == user.id
        is_admin = user.role == UserRole.ADMIN

        if not (is_owner or is_creator or is_evaluator or is_admin):
            raise ProjectForbiddenError("You are not authorized to view this submission.")

        return self._format_submission(submission, user)

    def list_user_submissions(
        self,
        user: User,
        project_id: str | None = None,
    ) -> list[SubmissionSummaryResponse]:
        """List all submissions by a learner across projects or for a specific project."""
        query = select(ProjectSubmission).where(ProjectSubmission.user_id == user.id)
        if project_id:
            query = query.where(ProjectSubmission.project_id == project_id)

        query = query.order_by(ProjectSubmission.created_at.desc())
        subs = self.db.execute(query).scalars().all()
        return [SubmissionSummaryResponse.model_validate(s) for s in subs]

    def update_draft(
        self,
        submission_id: str,
        user: User,
        data: SubmissionUpdateRequest,
    ) -> dict[str, Any]:
        """Update draft submission deliverables and milestone checklist."""
        submission = self.db.execute(
            select(ProjectSubmission)
            .where(ProjectSubmission.id == submission_id)
            .options(
                selectinload(ProjectSubmission.artifacts),
                selectinload(ProjectSubmission.evaluator),
            )
        ).scalar_one_or_none()
        if not submission:
            raise SubmissionNotFoundError(f"Submission '{submission_id}' was not found.")

        if submission.user_id != user.id:
            raise ProjectForbiddenError("You can only modify your own submissions.")

        if submission.status != SubmissionStatus.DRAFT.value:
            raise ProjectValidationError(
                f"Cannot edit submission in '{submission.status}' status. Only DRAFT submissions can be edited."
            )

        if data.title is not None:
            submission.title = data.title
        if data.summary is not None:
            submission.summary = data.summary
        if data.content is not None:
            submission.content = data.content
        if data.milestones_completed is not None:
            submission.milestones_completed = data.milestones_completed

        self.db.commit()
        return self._format_submission(submission, user)

    def submit_project(self, submission_id: str, user: User) -> dict[str, Any]:
        """Validate submission contents and transition from DRAFT to SUBMITTED."""
        submission = self.db.execute(
            select(ProjectSubmission)
            .where(ProjectSubmission.id == submission_id)
            .options(
                selectinload(ProjectSubmission.artifacts),
                selectinload(ProjectSubmission.evaluator),
            )
        ).scalar_one_or_none()
        if not submission:
            raise SubmissionNotFoundError(f"Submission '{submission_id}' was not found.")

        if submission.user_id != user.id:
            raise ProjectForbiddenError("You can only submit your own work.")

        if submission.status != SubmissionStatus.DRAFT.value:
            raise ProjectValidationError(
                f"Submission is currently in '{submission.status}' status and cannot be submitted."
            )

        has_content = bool(submission.content and any(submission.content.values()))
        has_artifacts = bool(submission.artifacts and len(submission.artifacts) > 0)
        has_summary = bool(submission.summary and len(submission.summary.strip()) > 0)

        if not (has_content or has_artifacts or has_summary):
            raise ProjectValidationError(
                "Cannot submit an empty draft. Please provide deliverables, summary notes, or uploaded artifacts."
            )

        history = list(submission.content.get("transition_history", []))
        history.append({
            "from_status": SubmissionStatus.DRAFT.value,
            "to_status": SubmissionStatus.SUBMITTED.value,
            "timestamp": datetime.now(UTC).isoformat(),
            "triggered_by": user.id,
            "reason": "Deliverables submitted for review",
        })
        submission.content["transition_history"] = history
        flag_modified(submission, "content")

        submission.status = SubmissionStatus.SUBMITTED.value
        submission.submitted_at = datetime.now(UTC)
        self.db.commit()

        # Recalculate skill mastery for all demonstrated skills (transitions to PRACTICING)
        try:
            from app.modules.progress.service import ProgressionService
            from app.modules.projects.models import ProjectSkill

            prog_service = ProgressionService(self.db)
            project_skills = self.db.scalars(
                select(ProjectSkill).where(ProjectSkill.project_id == submission.project_id)
            ).all()
            for ps in project_skills:
                prog_service.recalculate_skill_mastery(submission.user_id, ps.skill_id)
        except Exception as exc:
            logger.warning(
                "Failed to recalculate skill mastery on submission %s: %s",
                submission.id,
                exc,
            )

        return self._format_submission(submission, user)

    def create_revision(
        self,
        submission_id: str,
        user: User,
        data: SubmissionRevisionRequest | None = None,
    ) -> dict[str, Any]:
        """Initiate an immutable revision draft from a submission with CHANGES_REQUESTED status."""
        source = self.db.execute(
            select(ProjectSubmission).where(ProjectSubmission.id == submission_id)
        ).scalar_one_or_none()
        if not source:
            raise SubmissionNotFoundError(f"Submission '{submission_id}' was not found.")

        # Revisions must never cross user boundaries
        if source.user_id != user.id:
            raise ProjectForbiddenError("You cannot create a revision for another learner's submission.")

        # Source must be CHANGES_REQUESTED
        if source.status != SubmissionStatus.CHANGES_REQUESTED.value:
            raise ProjectValidationError(
                f"Revisions can only be created when changes were requested. Current status: '{source.status}'."
            )

        # Check if an active draft revision already exists
        existing_rev_draft = self.db.execute(
            select(ProjectSubmission)
            .where(
                ProjectSubmission.revision_of_id == source.id,
                ProjectSubmission.status == SubmissionStatus.DRAFT.value,
            )
            .options(
                selectinload(ProjectSubmission.artifacts),
                selectinload(ProjectSubmission.evaluator),
            )
        ).scalar_one_or_none()

        if existing_rev_draft:
            return self._format_submission(existing_rev_draft, user)

        # Compute next version number
        max_v = self.db.execute(
            select(func.max(ProjectSubmission.version_number)).where(
                ProjectSubmission.project_id == source.project_id,
                ProjectSubmission.user_id == user.id,
            )
        ).scalar_one()
        next_v = (max_v or source.version_number) + 1

        title = data.title if (data and data.title) else f"{source.title or 'Submission'} (Rev {next_v})"
        summary = data.summary if (data and data.summary) else source.summary
        rev_content = dict(data.content) if (data and data.content) else dict(source.content or {})
        rev_content["transition_history"] = [
            {
                "from_status": None,
                "to_status": SubmissionStatus.DRAFT.value,
                "timestamp": datetime.now(UTC).isoformat(),
                "triggered_by": user.id,
                "reason": f"Revision v{next_v} initiated from submission {source.id}",
            }
        ]

        new_submission = ProjectSubmission(
            project_id=source.project_id,
            user_id=user.id,
            version_number=next_v,
            revision_of_id=source.id,
            status=SubmissionStatus.DRAFT.value,
            title=title,
            summary=summary,
            content=rev_content,
            milestones_completed=list(source.milestones_completed or []),
        )
        self.db.add(new_submission)
        self.db.commit()

        reloaded = self.db.execute(
            select(ProjectSubmission)
            .where(ProjectSubmission.id == new_submission.id)
            .options(
                selectinload(ProjectSubmission.artifacts),
                selectinload(ProjectSubmission.evaluator),
            )
        ).scalar_one()

        return self._format_submission(reloaded, user)

    def get_submission_history(self, submission_id: str, user: User) -> dict[str, Any]:
        """Retrieve all versions in the revision chain for a project submission."""
        target = self.db.execute(
            select(ProjectSubmission)
            .where(ProjectSubmission.id == submission_id)
            .options(selectinload(ProjectSubmission.project))
        ).scalar_one_or_none()
        if not target:
            raise SubmissionNotFoundError(f"Submission '{submission_id}' was not found.")

        # Authorization: owner, project creator, evaluator, or admin
        is_owner = target.user_id == user.id
        is_creator = target.project and target.project.creator_id == user.id
        is_evaluator = target.evaluator_id == user.id
        is_admin = user.role == UserRole.ADMIN

        if not (is_owner or is_creator or is_evaluator or is_admin):
            raise ProjectForbiddenError("You are not authorized to view this submission history.")

        # Query all versions for this learner and project
        stmt = (
            select(ProjectSubmission)
            .where(
                ProjectSubmission.project_id == target.project_id,
                ProjectSubmission.user_id == target.user_id,
            )
            .order_by(ProjectSubmission.version_number.asc())
        )
        all_versions = self.db.execute(stmt).scalars().all()

        return {
            "project_id": target.project_id,
            "user_id": target.user_id,
            "current_version": target.version_number,
            "submissions": [SubmissionSummaryResponse.model_validate(v) for v in all_versions],
        }

    def claim_for_review(self, submission_id: str, evaluator: User) -> dict[str, Any]:
        """Claim a submitted project for evaluation, enforcing role and self-evaluation rules."""
        if evaluator.role not in (UserRole.CREATOR, UserRole.ADMIN):
            raise ProjectForbiddenError("Only creators and administrators can claim submissions for review.")

        submission = self.db.execute(
            select(ProjectSubmission).where(ProjectSubmission.id == submission_id)
        ).scalar_one_or_none()
        if not submission:
            raise SubmissionNotFoundError(f"Submission '{submission_id}' was not found.")

        # Self-evaluation prevention
        if evaluator.id == submission.user_id:
            raise ProjectForbiddenError("You cannot evaluate or claim your own submission.")

        if submission.status not in (SubmissionStatus.SUBMITTED.value, SubmissionStatus.UNDER_REVIEW.value):
            raise ProjectValidationError(
                f"Submission is in '{submission.status}' status and cannot be claimed for review."
            )

        # If already claimed by another evaluator, prevent hijacking unless admin
        if (
            submission.status == SubmissionStatus.UNDER_REVIEW.value
            and submission.evaluator_id
            and submission.evaluator_id != evaluator.id
            and evaluator.role != UserRole.ADMIN
        ):
            raise ProjectConflictError("This submission is already under review by another evaluator.")

        submission.status = SubmissionStatus.UNDER_REVIEW.value
        submission.evaluator_id = evaluator.id

        history = list(submission.content.get("transition_history", []))
        if not any(t.get("to_status") == SubmissionStatus.UNDER_REVIEW.value for t in history):
            history.append({
                "from_status": SubmissionStatus.SUBMITTED.value,
                "to_status": SubmissionStatus.UNDER_REVIEW.value,
                "timestamp": datetime.now(UTC).isoformat(),
                "triggered_by": evaluator.id,
                "reason": "Claimed by evaluator for review",
            })
            submission.content["transition_history"] = history
            flag_modified(submission, "content")

        self.db.commit()

        return {
            "submission_id": submission.id,
            "status": submission.status,
            "evaluator_id": evaluator.id,
            "claimed_at": datetime.now(UTC),
        }

    def evaluate_submission(
        self,
        submission_id: str,
        evaluator: User,
        eval_data: SubmissionEvaluationRequest,
    ) -> dict[str, Any]:
        """Grade a submission against the project rubric and determine pass/revision outcome."""
        if evaluator.role not in (UserRole.CREATOR, UserRole.ADMIN):
            raise ProjectForbiddenError("Only creators and administrators can evaluate submissions.")

        submission = self.db.execute(
            select(ProjectSubmission)
            .where(ProjectSubmission.id == submission_id)
            .options(selectinload(ProjectSubmission.project))
        ).scalar_one_or_none()
        if not submission:
            raise SubmissionNotFoundError(f"Submission '{submission_id}' was not found.")

        # Self-evaluation strictly blocked
        if evaluator.id == submission.user_id:
            raise ProjectForbiddenError("You cannot evaluate your own submission.")

        if submission.status not in (
            SubmissionStatus.SUBMITTED.value,
            SubmissionStatus.UNDER_REVIEW.value,
            SubmissionStatus.EVALUATED.value,
        ):
            raise ProjectValidationError(
                f"Cannot evaluate submission in '{submission.status}' status."
            )

        # Assigned evaluator enforcement
        if (
            submission.evaluator_id
            and submission.evaluator_id != evaluator.id
            and evaluator.role != UserRole.ADMIN
        ):
            raise ProjectForbiddenError("Only the assigned evaluator or an admin may complete this evaluation.")

        # Auto-claim if submitted
        history = list(submission.content.get("transition_history", []))
        if submission.status == SubmissionStatus.SUBMITTED.value:
            history.append({
                "from_status": SubmissionStatus.SUBMITTED.value,
                "to_status": SubmissionStatus.UNDER_REVIEW.value,
                "timestamp": datetime.now(UTC).isoformat(),
                "triggered_by": evaluator.id,
                "reason": "Submission transitioned to review by evaluator",
            })
            submission.status = SubmissionStatus.UNDER_REVIEW.value
            submission.evaluator_id = evaluator.id
            self.db.flush()

        project = submission.project
        criteria_cfg = project.evaluation_criteria if project else {}
        passing_score = float(criteria_cfg.get("passing_score", 70.0))
        rubric_list = criteria_cfg.get("rubric") or criteria_cfg.get("criteria") or []

        # Map rubric criteria by ID
        rubric_by_id = {c.get("id"): c for c in rubric_list if isinstance(c, dict) and "id" in c}

        # Calculate score from criteria
        total_score = 0.0
        scores_breakdown: list[dict[str, Any]] = []

        if eval_data.criteria_scores:
            total_weight = 0.0
            weighted_sum = 0.0
            for cs in eval_data.criteria_scores:
                crit_def = rubric_by_id.get(cs.criterion_id, {})
                max_score = float(crit_def.get("max_score", 100.0))
                weight = float(crit_def.get("weight", 1.0))

                if cs.score < 0:
                    raise ProjectValidationError(f"Score for '{cs.criterion_id}' cannot be negative.")
                if cs.score > max_score:
                    raise ProjectValidationError(
                        f"Score {cs.score} for '{cs.criterion_id}' exceeds maximum allowed ({max_score})."
                    )

                # Normalized percentage (0..100)
                norm_score = (cs.score / max_score) * 100.0 if max_score > 0 else 0.0
                weighted_sum += norm_score * weight
                total_weight += weight

                scores_breakdown.append(
                    {
                        "criterion_id": cs.criterion_id,
                        "title": crit_def.get("title", cs.criterion_id),
                        "score": cs.score,
                        "max_score": max_score,
                        "weight": weight,
                        "feedback": cs.feedback,
                    }
                )

            total_score = round(weighted_sum / total_weight, 2) if total_weight > 0 else 0.0

        # Step 2 & 3: Persist evaluation record and transition submission to EVALUATED
        eval_time = datetime.now(UTC)
        submission.score = total_score
        submission.evaluator_id = evaluator.id
        submission.evaluated_at = eval_time
        submission.status = SubmissionStatus.EVALUATED.value
        self.db.flush()

        evaluated_transition = {
            "from_status": SubmissionStatus.UNDER_REVIEW.value,
            "to_status": SubmissionStatus.EVALUATED.value,
            "timestamp": eval_time.isoformat(),
            "triggered_by": evaluator.id,
            "reason": f"Rubric scored at {total_score}% against passing threshold {passing_score}%",
        }
        history.append(evaluated_transition)

        # Step 4 & 5: Verify passing criteria and transition to COMPLETED (or CHANGES_REQUESTED)
        action = eval_data.action.strip().upper() if eval_data.action else None
        if action == "REQUEST_CHANGES":
            passed = False
            next_status = SubmissionStatus.CHANGES_REQUESTED.value
            trans_reason = "Revisions requested by evaluator"
        elif action == "APPROVE":
            passed = True
            next_status = SubmissionStatus.COMPLETED.value
            trans_reason = "Approved by evaluator"
        else:
            passed = total_score >= passing_score
            if passed:
                next_status = SubmissionStatus.COMPLETED.value
                trans_reason = f"Passing criteria satisfied: score {total_score} >= {passing_score}"
            else:
                next_status = SubmissionStatus.CHANGES_REQUESTED.value
                trans_reason = f"Score {total_score} below passing threshold {passing_score}"

        submission.passed = passed
        submission.status = next_status
        completion_transition = {
            "from_status": SubmissionStatus.EVALUATED.value,
            "to_status": next_status,
            "timestamp": datetime.now(UTC).isoformat(),
            "triggered_by": evaluator.id,
            "reason": trans_reason,
        }
        history.append(completion_transition)
        submission.content["transition_history"] = history
        flag_modified(submission, "content")

        # Step 6: Preserve both lifecycle transitions in reliable audit/history mechanism
        eval_payload = {
            "feedback": eval_data.feedback,
            "score": total_score,
            "passing_score": passing_score,
            "passed": passed,
            "criteria_scores": scores_breakdown,
            "action": action,
            "evaluator_id": evaluator.id,
            "evaluated_at": eval_time.isoformat(),
            "transition_history": history,
            "lifecycle_transitions": [evaluated_transition, completion_transition],
        }
        submission.evaluation = eval_payload
        flag_modified(submission, "evaluation")

        self.db.commit()

        # Trigger skill mastery recalculation for all skills demonstrated by this project
        if submission.status in (SubmissionStatus.COMPLETED.value, SubmissionStatus.CHANGES_REQUESTED.value):
            try:
                from app.modules.progress.service import ProgressionService
                from app.modules.projects.models import ProjectSkill

                prog_service = ProgressionService(self.db)
                project_skills = self.db.scalars(
                    select(ProjectSkill).where(ProjectSkill.project_id == submission.project_id)
                ).all()
                for ps in project_skills:
                    prog_service.recalculate_skill_mastery(submission.user_id, ps.skill_id)
            except Exception as exc:
                logger.warning(
                    "Failed to recalculate skill mastery for project submission %s: %s",
                    submission.id,
                    exc,
                )

        return {
            "submission_id": submission.id,
            "status": submission.status,
            "score": total_score,
            "passed": passed,
            "evaluation": eval_payload,
            "evaluated_at": submission.evaluated_at,
            "evaluator_id": evaluator.id,
            "transition_history": history,
        }
