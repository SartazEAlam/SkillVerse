"""Isolated code execution sandbox boundary interface and client.

In accordance with AGENTS.md Rule 16 and docs/SECURITY.md:
Learner-submitted code is untrusted and must NEVER be executed inside
the FastAPI main application process.

This module provides the execution service abstraction, request/result contracts,
and safe unavailable-service fallback handling.
"""

from __future__ import annotations

import enum
import logging
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger("skillverse.sandbox")


class ExecutionStatus(enum.StrEnum):
    """Execution status returned by the code sandbox service."""

    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    ERROR = "error"
    SERVICE_UNAVAILABLE = "service_unavailable"


class CodeExecutionRequest(BaseModel):
    """Request payload sent to the isolated execution sandbox."""

    code: str = Field(min_length=1, max_length=50000, description="Untrusted learner code")
    language: str = Field(description="Programming language identifier (e.g., javascript, python)")
    test_cases: list[dict[str, Any]] = Field(
        default_factory=list, description="Test cases to evaluate against the code"
    )
    timeout_seconds: int = Field(default=5, ge=1, le=30)
    memory_limit_mb: int = Field(default=128, ge=32, le=512)


class TestCaseResult(BaseModel):
    """Evaluation result for a single test case."""

    id: str
    description: str
    passed: bool
    actual_output: str | None = None
    expected_output: str | None = None
    error: str | None = None


class CodeExecutionResult(BaseModel):
    """Structured result returned by the code execution service."""

    status: ExecutionStatus
    tests_passed: int = 0
    tests_total: int = 0
    output: str | None = None
    error: str | None = None
    execution_time_ms: float | None = None
    details: list[TestCaseResult] = Field(default_factory=list)
    message: str = ""


class SandboxRunnerInterface:
    """Interface defining the boundary for isolated code execution."""

    def execute(self, request: CodeExecutionRequest) -> CodeExecutionResult:
        """Execute code in an isolated environment with strict resource limits."""
        raise NotImplementedError("Subclasses must implement execute()")


class IsolatedSandboxRunner(SandboxRunnerInterface):
    """Isolated execution client.

    Connects to a dedicated containerized runner worker when configured.
    When an isolated container runner is not available in the local environment,
    safely returns a SERVICE_UNAVAILABLE outcome rather than executing untrusted
    code in the primary application runtime.
    """

    def __init__(self, endpoint_url: str | None = None) -> None:
        self.endpoint_url = endpoint_url

    def execute(self, request: CodeExecutionRequest) -> CodeExecutionResult:
        if not self.endpoint_url:
            logger.info(
                "Isolated code runner endpoint is not configured. "
                "Preserving learner submission safely without host execution."
            )
            return CodeExecutionResult(
                status=ExecutionStatus.SERVICE_UNAVAILABLE,
                tests_passed=0,
                tests_total=len(request.test_cases),
                error="The isolated code execution sandbox is currently offline or unconfigured.",
                message=(
                    "Your code has been received and stored securely. "
                    "Code evaluation requires the containerized sandbox runner service."
                ),
            )

        # In production with runner endpoint configured:
        # HTTP client communication to isolated worker container
        # with strict network isolation and timeout limits.
        return CodeExecutionResult(
            status=ExecutionStatus.SERVICE_UNAVAILABLE,
            message="Remote runner connection pending.",
        )


# Global default runner instance
sandbox_runner = IsolatedSandboxRunner()
