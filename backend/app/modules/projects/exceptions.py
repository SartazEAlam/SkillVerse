"""Domain exceptions for the projects, submissions, and artifact modules."""

from __future__ import annotations

from typing import Any


class ProjectServiceError(Exception):
    """Base domain exception for project operations."""

    def __init__(
        self,
        message: str,
        code: str = "PROJECT_ERROR",
        status_code: int = 400,
        details: Any = None,
    ) -> None:
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details
        super().__init__(message)


class ProjectNotFoundError(ProjectServiceError):
    def __init__(self, message: str = "Project not found.", details: Any = None) -> None:
        super().__init__(message, code="NOT_FOUND", status_code=404, details=details)


class ProjectValidationError(ProjectServiceError):
    def __init__(self, message: str, details: Any = None) -> None:
        super().__init__(message, code="VALIDATION_ERROR", status_code=422, details=details)


class ProjectForbiddenError(ProjectServiceError):
    def __init__(self, message: str = "Forbidden.", details: Any = None) -> None:
        super().__init__(message, code="FORBIDDEN", status_code=403, details=details)


class ProjectConflictError(ProjectServiceError):
    def __init__(self, message: str, details: Any = None) -> None:
        super().__init__(message, code="CONFLICT", status_code=409, details=details)


class SubmissionNotFoundError(ProjectServiceError):
    def __init__(self, message: str = "Submission not found.", details: Any = None) -> None:
        super().__init__(message, code="NOT_FOUND", status_code=404, details=details)


class ArtifactNotFoundError(ProjectServiceError):
    def __init__(self, message: str = "Artifact not found.", details: Any = None) -> None:
        super().__init__(message, code="NOT_FOUND", status_code=404, details=details)


class PortfolioNotFoundError(ProjectServiceError):
    def __init__(self, message: str = "Portfolio not found.", details: Any = None) -> None:
        super().__init__(message, code="NOT_FOUND", status_code=404, details=details)


class PortfolioItemNotFoundError(ProjectServiceError):
    def __init__(self, message: str = "Portfolio item not found.", details: Any = None) -> None:
        super().__init__(message, code="NOT_FOUND", status_code=404, details=details)


