"""Portfolio domain service governing learner showcase configuration, items, reordering, and privacy-aware public views."""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.modules.auth.models import User, UserRole
from app.modules.projects.exceptions import (
    PortfolioItemNotFoundError,
    PortfolioNotFoundError,
    ProjectConflictError,
    ProjectForbiddenError,
    ProjectValidationError,
    SubmissionNotFoundError,
)
from app.modules.projects.models import (
    Portfolio,
    PortfolioItem,
    PortfolioItemType,
    PortfolioItemVisibility,
    Project,
    ProjectSkill,
    ProjectSubmission,
    SubmissionStatus,
)
from app.modules.projects.schemas import (
    PortfolioDetailResponse,
    PortfolioItemCreateRequest,
    PortfolioItemReorderRequest,
    PortfolioItemResponse,
    PortfolioItemUpdateRequest,
    PortfolioPublicResponse,
    PortfolioUpdateRequest,
)

logger = logging.getLogger("skillverse.projects.portfolio")

RESERVED_SLUGS = {
    "me",
    "mine",
    "items",
    "reorder",
    "admin",
    "api",
    "download",
    "artifacts",
    "submissions",
    "projects",
    "public",
    "new",
    "edit",
}


class PortfolioService:
    """Service governing learner portfolio lifecycle, item curation, and public access."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def _format_item(self, item: PortfolioItem) -> PortfolioItemResponse:
        return PortfolioItemResponse(
            id=item.id,
            portfolio_user_id=item.portfolio_user_id,
            item_type=item.item_type,
            reference_id=item.reference_id,
            title=item.title,
            summary=item.summary,
            skills_demonstrated=list(item.skills_demonstrated or []),
            artifacts=list(item.artifacts or []),
            external_url=item.external_url,
            sort_order=item.sort_order,
            visibility=item.visibility,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )

    def _get_or_create_portfolio_entity(self, user: User) -> Portfolio:
        portfolio = self.db.execute(
            select(Portfolio)
            .where(Portfolio.user_id == user.id)
            .options(selectinload(Portfolio.items))
        ).scalar_one_or_none()

        if not portfolio:
            name = (
                user.profile.display_name
                if (user.profile and user.profile.display_name)
                else user.email.split("@")[0]
            )
            portfolio = Portfolio(
                user_id=user.id,
                title=f"{name}'s Portfolio",
                headline="Learner Showcase",
                bio_override=user.profile.bio if (user.profile and user.profile.bio) else None,
                is_public=False,
                settings={"visibility": PortfolioItemVisibility.PRIVATE.value},
                contact_links={},
            )
            self.db.add(portfolio)
            self.db.commit()
            self.db.refresh(portfolio)

        return portfolio

    def get_my_portfolio(self, user: User) -> PortfolioDetailResponse:
        """Retrieve the authenticated learner's complete portfolio profile and items."""
        portfolio = self._get_or_create_portfolio_entity(user)
        items = sorted(portfolio.items or [], key=lambda i: i.sort_order)

        return PortfolioDetailResponse(
            user_id=portfolio.user_id,
            title=portfolio.title,
            headline=portfolio.headline,
            bio_override=portfolio.bio_override,
            custom_slug=portfolio.custom_slug,
            visibility=portfolio.visibility,
            is_public=portfolio.is_public,
            contact_links=portfolio.contact_links or {},
            settings=portfolio.settings or {},
            items=[self._format_item(it) for it in items],
            created_at=portfolio.created_at,
            updated_at=portfolio.updated_at,
        )

    def update_my_portfolio(
        self,
        user: User,
        data: PortfolioUpdateRequest,
    ) -> PortfolioDetailResponse:
        """Update portfolio title, bio, slug, visibility, and display settings."""
        portfolio = self._get_or_create_portfolio_entity(user)

        if data.title is not None:
            portfolio.title = data.title.strip() if data.title else None
        if data.headline is not None:
            portfolio.headline = data.headline.strip() if data.headline else None

        # Accept either bio_override or description alias
        bio = data.bio_override if data.bio_override is not None else data.description
        if bio is not None:
            portfolio.bio_override = bio.strip() if bio else None

        if data.custom_slug is not None:
            slug = data.custom_slug.strip().lower()
            if not slug:
                portfolio.custom_slug = None
            else:
                if slug in RESERVED_SLUGS:
                    raise ProjectValidationError(
                        f"Custom slug '{slug}' is reserved and cannot be used."
                    )
                # Check uniqueness across users
                existing_slug = self.db.execute(
                    select(Portfolio).where(
                        Portfolio.custom_slug == slug,
                        Portfolio.user_id != user.id,
                    )
                ).scalar_one_or_none()
                if existing_slug:
                    raise ProjectConflictError(f"Custom slug '{slug}' is already taken.")
                portfolio.custom_slug = slug

        # Handle visibility
        settings_dict = dict(portfolio.settings or {})
        if data.visibility is not None:
            vis_val = (
                data.visibility.value
                if hasattr(data.visibility, "value")
                else str(data.visibility)
            )
            settings_dict["visibility"] = vis_val
            portfolio.is_public = vis_val in (
                PortfolioItemVisibility.PUBLIC.value,
                PortfolioItemVisibility.UNLISTED.value,
            )
        elif data.is_public is not None:
            portfolio.is_public = data.is_public
            settings_dict["visibility"] = (
                PortfolioItemVisibility.PUBLIC.value
                if data.is_public
                else PortfolioItemVisibility.PRIVATE.value
            )

        if data.settings is not None:
            settings_dict.update(data.settings)
        portfolio.settings = settings_dict

        if data.contact_links is not None:
            portfolio.contact_links = data.contact_links

        self.db.commit()
        self.db.refresh(portfolio)
        return self.get_my_portfolio(user)

    def add_item(
        self,
        user: User,
        data: PortfolioItemCreateRequest,
    ) -> PortfolioItemResponse:
        """Feature an eligible completed project submission or showcase item in the portfolio."""
        portfolio = self._get_or_create_portfolio_entity(user)

        item_type_str = (
            data.item_type.value
            if hasattr(data.item_type, "value")
            else str(data.item_type)
        )
        vis_str = (
            data.visibility.value
            if hasattr(data.visibility, "value")
            else str(data.visibility)
        )

        title = data.title.strip() if data.title else None
        summary = data.summary.strip() if data.summary else (data.description.strip() if data.description else None)
        skills_demonstrated: list[str] = list(data.skills_demonstrated or [])
        artifacts_payload: list[dict[str, Any]] = []

        if item_type_str == PortfolioItemType.PROJECT_SUBMISSION.value:
            if not data.reference_id:
                raise ProjectValidationError(
                    "reference_id is required when adding a project submission to the portfolio."
                )

            submission = self.db.execute(
                select(ProjectSubmission)
                .where(ProjectSubmission.id == data.reference_id)
                .options(
                    selectinload(ProjectSubmission.project).selectinload(Project.project_skills).selectinload(ProjectSkill.skill),
                    selectinload(ProjectSubmission.artifacts),
                )
            ).scalar_one_or_none()

            if not submission:
                raise SubmissionNotFoundError(f"Project submission '{data.reference_id}' was not found.")

            # Rule 1: Learner must own the submission
            if submission.user_id != user.id:
                raise ProjectForbiddenError("You can only add your own project submissions to your portfolio.")

            # Rule 2: Submission status must be COMPLETED
            if submission.status != SubmissionStatus.COMPLETED.value:
                raise ProjectValidationError(
                    f"Only completed project submissions can be added to your portfolio. Current status is '{submission.status}'."
                )

            # Rule 3: Prevent duplicate item references to the same submission
            existing = self.db.execute(
                select(PortfolioItem).where(
                    PortfolioItem.portfolio_user_id == user.id,
                    PortfolioItem.reference_id == submission.id,
                )
            ).scalar_one_or_none()
            if existing:
                raise ProjectConflictError("This project submission is already featured in your portfolio.")

            # Derive title and summary if not customized
            if not title:
                title = submission.title or (submission.project.title if submission.project else "Project Deliverables")
            if not summary:
                summary = submission.summary

            # Auto-populate demonstrated skills from project_skills if not supplied
            if not skills_demonstrated and submission.project and submission.project.project_skills:
                for ps in submission.project.project_skills:
                    if ps.skill and ps.skill.name not in skills_demonstrated:
                        skills_demonstrated.append(ps.skill.name)

            # Auto-populate ONLY public artifacts belonging to this submission
            for a in (submission.artifacts or []):
                if a.is_public:
                    artifacts_payload.append(
                        {
                            "id": a.id,
                            "original_filename": a.original_filename,
                            "mime_type": a.mime_type,
                            "file_size_bytes": a.file_size_bytes,
                            "download_url": f"/api/v1/artifacts/{a.id}/download",
                        }
                    )
        else:
            if not title:
                raise ProjectValidationError("Title is required for portfolio items.")
            if data.artifacts:
                # Custom artifacts must only include safe entries
                artifacts_payload = [
                    a for a in data.artifacts if isinstance(a, dict) and a.get("is_public", True)
                ]

        # Determine next sort_order
        max_order = self.db.execute(
            select(func.max(PortfolioItem.sort_order)).where(
                PortfolioItem.portfolio_user_id == user.id
            )
        ).scalar_one()
        next_order = (max_order if max_order is not None else -1) + 1

        item = PortfolioItem(
            portfolio_user_id=portfolio.user_id,
            item_type=item_type_str,
            reference_id=data.reference_id,
            title=title,
            summary=summary,
            skills_demonstrated=skills_demonstrated,
            artifacts=artifacts_payload,
            external_url=data.external_url.strip() if data.external_url else None,
            sort_order=next_order,
            visibility=vis_str,
        )
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)

        return self._format_item(item)

    def update_item(
        self,
        user: User,
        item_id: str,
        data: PortfolioItemUpdateRequest,
    ) -> PortfolioItemResponse:
        """Update portfolio item title, summary, visibility, or sort order."""
        item = self.db.execute(
            select(PortfolioItem).where(PortfolioItem.id == item_id)
        ).scalar_one_or_none()

        if not item:
            raise PortfolioItemNotFoundError(f"Portfolio item '{item_id}' was not found.")

        # Learners may only manage their own items
        if item.portfolio_user_id != user.id:
            raise ProjectForbiddenError("You can only modify your own portfolio items.")

        if data.title is not None:
            if not data.title.strip():
                raise ProjectValidationError("Title cannot be empty.")
            item.title = data.title.strip()

        summary = data.summary if data.summary is not None else data.description
        if summary is not None:
            item.summary = summary.strip() if summary else None

        if data.visibility is not None:
            item.visibility = (
                data.visibility.value
                if hasattr(data.visibility, "value")
                else str(data.visibility)
            )

        if data.external_url is not None:
            item.external_url = data.external_url.strip() if data.external_url else None

        if data.sort_order is not None:
            item.sort_order = data.sort_order

        self.db.commit()
        self.db.refresh(item)
        return self._format_item(item)

    def delete_item(self, user: User, item_id: str) -> None:
        """Remove a portfolio item without deleting the source submission or artifacts."""
        item = self.db.execute(
            select(PortfolioItem).where(PortfolioItem.id == item_id)
        ).scalar_one_or_none()

        if not item:
            raise PortfolioItemNotFoundError(f"Portfolio item '{item_id}' was not found.")

        if item.portfolio_user_id != user.id:
            raise ProjectForbiddenError("You can only delete your own portfolio items.")

        self.db.delete(item)
        self.db.commit()

    def reorder_items(
        self,
        user: User,
        data: PortfolioItemReorderRequest,
    ) -> list[PortfolioItemResponse]:
        """Update display ordering of portfolio items."""
        items = self.db.execute(
            select(PortfolioItem).where(PortfolioItem.portfolio_user_id == user.id)
        ).scalars().all()

        item_map = {it.id: it for it in items}
        for i_id in data.item_ids:
            if i_id not in item_map:
                raise ProjectForbiddenError(
                    f"Item '{i_id}' does not belong to your portfolio and cannot be reordered."
                )

        for new_order, i_id in enumerate(data.item_ids):
            item_map[i_id].sort_order = new_order

        self.db.commit()

        updated_items = self.db.execute(
            select(PortfolioItem)
            .where(PortfolioItem.portfolio_user_id == user.id)
            .order_by(PortfolioItem.sort_order.asc())
        ).scalars().all()

        return [self._format_item(it) for it in updated_items]

    def get_public_portfolio(
        self,
        slug_or_id: str,
        viewer: User | None = None,
    ) -> PortfolioPublicResponse:
        """Retrieve public or unlisted portfolio profile with strict privacy filtering."""
        portfolio = self.db.execute(
            select(Portfolio)
            .where(
                or_(
                    Portfolio.custom_slug == slug_or_id,
                    Portfolio.user_id == slug_or_id,
                )
            )
            .options(
                selectinload(Portfolio.items),
                selectinload(Portfolio.user).selectinload(User.profile),
            )
        ).scalar_one_or_none()

        if not portfolio:
            raise PortfolioNotFoundError(f"Portfolio '{slug_or_id}' was not found.")

        is_owner = viewer is not None and viewer.id == portfolio.user_id
        is_admin = viewer is not None and viewer.role == UserRole.ADMIN

        vis = portfolio.visibility

        # Private portfolios are completely inaccessible to unprivileged viewers
        if vis == PortfolioItemVisibility.PRIVATE.value and not (is_owner or is_admin):
            raise ProjectForbiddenError("This portfolio is private.")

        # Filter items: only explicitly public items are visible to third-party or anonymous visitors
        if is_owner or is_admin:
            visible_items = sorted(portfolio.items or [], key=lambda i: i.sort_order)
        else:
            visible_items = [
                it
                for it in sorted(portfolio.items or [], key=lambda i: i.sort_order)
                if it.visibility == PortfolioItemVisibility.PUBLIC.value
            ]

        owner_profile = portfolio.user.profile if portfolio.user else None
        display_name = (
            owner_profile.display_name
            if (owner_profile and owner_profile.display_name)
            else (portfolio.user.email.split("@")[0] if portfolio.user else "Anonymous Learner")
        )
        avatar_url = owner_profile.avatar_url if owner_profile else None

        return PortfolioPublicResponse(
            user_id=portfolio.user_id,
            display_name=display_name,
            avatar_url=avatar_url,
            title=portfolio.title,
            headline=portfolio.headline,
            bio_override=portfolio.bio_override,
            custom_slug=portfolio.custom_slug,
            visibility=vis,
            contact_links=portfolio.contact_links or {},
            settings=portfolio.settings or {},
            items=[self._format_item(it) for it in visible_items],
            created_at=portfolio.created_at,
        )

