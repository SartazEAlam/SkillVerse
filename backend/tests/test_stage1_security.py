"""Comprehensive regression tests for Phase 10 Stage 1 security remediations:
- SEC-10-01: Bounded artifact upload memory usage & 413 Payload Too Large
- SEC-10-04: Trusted proxy IP validation in rate limiter
- SEC-10-05: Gemini API key header transmission & secret sanitization
- SEC-10-07: Submission evaluation and review claim authorization
"""

from __future__ import annotations

import io
import shutil
import tempfile
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException, Request, status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.config import Settings, settings
from app.infrastructure.ai.base import AIProviderError
from app.infrastructure.ai.gemini_provider import GeminiAIProvider
from app.infrastructure.rate_limiter import get_client_ip, is_trusted_proxy, limiter, rate_limit
from app.infrastructure.storage.factory import reset_storage_service
from app.modules.auth.models import User, UserRole
from app.modules.projects.models import (
    ProjectSubmission,
    SubmissionStatus,
)
from app.modules.skills.models import Discipline, Skill, SkillDifficulty

# ══════════════════════════════════════════════════════════════════════════════
# SEC-10-01: Bounded Artifact Upload Memory & Payload Size Limits
# ══════════════════════════════════════════════════════════════════════════════


class TestSec1001BoundedUploadMemory:
    """Tests verifying bounded chunked reading, memory caps, and reliable file closure."""

    @pytest.fixture(autouse=True)
    def isolated_storage(self):
        """Ensure tests run against a clean isolated local storage directory."""
        temp_dir = tempfile.mkdtemp(prefix="test_stage1_storage_")
        old_root = settings.storage_local_root
        old_provider = settings.storage_provider
        settings.storage_local_root = temp_dir
        settings.storage_provider = "local"
        reset_storage_service()

        yield temp_dir

        reset_storage_service()
        settings.storage_local_root = old_root
        settings.storage_provider = old_provider
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def active_submission(
        self,
        client: TestClient,
        creator_headers: dict[str, str],
        auth_headers: dict[str, str],
        db: Session,
    ) -> str:
        """Create a published project and active draft submission for testing uploads."""
        discipline = Discipline(slug="sec01-disc", name="Sec01 Disc", description="Disc")
        db.add(discipline)
        db.commit()

        skill = Skill(
            slug="sec01-skill",
            name="Sec01 Skill",
            discipline_id=discipline.id,
            difficulty_level=SkillDifficulty.INTERMEDIATE,
        )
        db.add(skill)
        db.commit()

        project_res = client.post(
            "/api/v1/projects",
            json={
                "title": "Sec01 Upload Project",
                "short_description": "Testing bounded artifact uploads",
                "full_description": "Full description for testing bounded artifact uploads",
                "discipline_id": discipline.id,
                "difficulty_level": "INTERMEDIATE",
                "requirements": {"deliverables": ["code.zip"]},
                "evaluation_criteria": {
                    "passing_score": 70.0,
                    "rubric": [{"id": "c1", "title": "Crit", "max_score": 100.0, "weight": 1.0}],
                },
                "skills": [{"skill_id": skill.id, "is_primary": True}],
            },
            headers=creator_headers,
        )
        project_id = project_res.json()["id"]
        client.post(f"/api/v1/projects/{project_id}/publish", headers=creator_headers)

        sub_res = client.post(
            f"/api/v1/projects/{project_id}/submissions",
            headers=auth_headers,
        )
        return sub_res.json()["id"]

    def test_upload_within_limit_succeeds(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        active_submission: str,
    ) -> None:
        """Valid file within the size limit uploads successfully with HTTP 201."""
        valid_content = b"SkillVerse Deliverable: Valid bounded memory test content."
        file_obj = io.BytesIO(valid_content)

        res = client.post(
            f"/api/v1/submissions/{active_submission}/artifacts",
            files={"file": ("notes.txt", file_obj, "text/plain")},
            data={"is_public": "true"},
            headers=auth_headers,
        )
        assert res.status_code == 201
        data = res.json()
        assert data["original_filename"] == "notes.txt"
        assert data["file_size_bytes"] == len(valid_content)

    def test_upload_exceeding_size_limit_returns_413(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        active_submission: str,
    ) -> None:
        """Upload exceeding max_file_size_mb returns HTTP 413 Payload Too Large immediately."""
        # Patch limit to 1 MB for fast test execution
        with patch.object(settings, "storage_max_file_size_mb", 1):
            oversized_bytes = b"X" * (1 * 1024 * 1024 + 1024)  # 1MB + 1KB
            file_obj = io.BytesIO(oversized_bytes)

            res = client.post(
                f"/api/v1/submissions/{active_submission}/artifacts",
                files={"file": ("large_file.txt", file_obj, "text/plain")},
                data={"is_public": "false"},
                headers=auth_headers,
            )

            assert res.status_code == 413
            error = res.json()["error"]
            assert error["code"] == "PAYLOAD_TOO_LARGE"
            assert "1MB" in error["message"]
            assert error["details"]["max_size_bytes"] == 1 * 1024 * 1024

    @pytest.mark.asyncio
    async def test_bounded_reading_aborts_early_and_closes_stream(self) -> None:
        """Verify the upload handler reads in 64KB chunks, aborts without consuming all, and closes file."""
        from app.modules.projects.router import upload_artifact

        # Create a mock UploadFile that tracks chunk reads and closure
        mock_file = MagicMock()
        mock_file.read = AsyncMock()
        mock_file.close = AsyncMock()

        # Simulate 3 chunks: first chunk 64KB, second chunk 64KB (total 128KB > limit 100KB)
        chunk_64k = b"A" * (64 * 1024)
        mock_file.read.side_effect = [chunk_64k, chunk_64k, chunk_64k, b""]

        mock_db = MagicMock(spec=Session)
        mock_user = MagicMock(spec=User)

        # Set limit to 0.1 MB (~102KB) so second 64KB chunk exceeds it
        with patch.object(settings, "storage_max_file_size_mb", 0.1):
            with pytest.raises(HTTPException) as exc_info:
                await upload_artifact(
                    submission_id="sub-test",
                    file=mock_file,
                    is_public=False,
                    current_user=mock_user,
                    db=mock_db,
                )

            assert exc_info.value.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
            assert exc_info.value.detail["error"]["code"] == "PAYLOAD_TOO_LARGE"

            # Should have aborted after reading 2 chunks, not reading the 3rd or 4th chunk
            assert mock_file.read.await_count == 2
            # Crucially: file.close() must be called in finally block
            assert mock_file.close.await_count == 1


# ══════════════════════════════════════════════════════════════════════════════
# SEC-10-04: Trusted Proxy IP Validation in Rate Limiter
# ══════════════════════════════════════════════════════════════════════════════


class TestSec1004TrustedProxyIPValidation:
    """Tests verifying trusted proxy validation, secure defaults, and right-to-left traversal."""

    def _make_request(
        self,
        peer_ip: str | None = None,
        forwarded_for: str | None = None,
        path: str = "/api/v1/auth/login",
    ) -> Request:
        """Helper to construct dummy Request with specified peer IP and headers."""
        headers_list: list[tuple[bytes, bytes]] = []
        if forwarded_for is not None:
            headers_list.append((b"x-forwarded-for", forwarded_for.encode("utf-8")))

        scope: dict[str, Any] = {
            "type": "http",
            "method": "POST",
            "path": path,
            "headers": headers_list,
            "client": (peer_ip, 54321) if peer_ip else None,
        }
        return Request(scope)

    def test_default_trusted_proxies_is_empty(self) -> None:
        """Default configuration must have no trusted proxies (trusted_proxies = [])."""
        new_settings = Settings()
        assert new_settings.trusted_proxies == []
        assert settings.trusted_proxies == []

    def test_loopback_peer_not_trusted_by_default(self) -> None:
        """Loopback addresses (127.0.0.1, ::1) must NOT be trusted by default."""
        req_v4 = self._make_request(peer_ip="127.0.0.1", forwarded_for="203.0.113.195")
        assert is_trusted_proxy("127.0.0.1", settings.trusted_proxies) is False
        # With default settings, X-Forwarded-For is completely ignored
        assert get_client_ip(req_v4) == "127.0.0.1"

        req_v6 = self._make_request(peer_ip="::1", forwarded_for="2001:db8::1")
        assert is_trusted_proxy("::1", settings.trusted_proxies) is False
        assert get_client_ip(req_v6) == "::1"

    def test_direct_peer_without_forwarded_for_returns_peer_ip(self) -> None:
        """Direct connection without headers uses the direct peer IP."""
        req = self._make_request(peer_ip="203.0.113.50")
        assert get_client_ip(req) == "203.0.113.50"

    def test_untrusted_peer_forged_forwarded_for_is_ignored(self) -> None:
        """Untrusted client providing X-Forwarded-For is ignored, returning direct peer IP."""
        req = self._make_request(
            peer_ip="198.51.100.22",
            forwarded_for="1.1.1.1, 8.8.8.8",
        )
        assert get_client_ip(req, trusted_proxies=["10.0.0.1"]) == "198.51.100.22"

    def test_single_trusted_proxy_and_one_client(self) -> None:
        """Trusted proxy peer successfully extracts client IP from X-Forwarded-For."""
        req = self._make_request(
            peer_ip="10.0.0.1",
            forwarded_for="203.0.113.99",
        )
        assert get_client_ip(req, trusted_proxies=["10.0.0.1"]) == "203.0.113.99"

    def test_multiple_trusted_proxy_hops(self) -> None:
        """Right-to-left traversal skips intermediate trusted proxies to find the client."""
        trusted = ["10.0.0.1", "10.0.0.2", "10.0.0.3"]
        req = self._make_request(
            peer_ip="10.0.0.3",
            forwarded_for="203.0.113.195, 10.0.0.1, 10.0.0.2",
        )
        # 10.0.0.2 (trusted) -> 10.0.0.1 (trusted) -> 203.0.113.195 (first untrusted)
        assert get_client_ip(req, trusted_proxies=trusted) == "203.0.113.195"

    def test_forged_leftmost_forwarded_address_is_ignored(self) -> None:
        """Leftmost forged addresses are never trusted; rightmost untrusted address is returned."""
        trusted = ["10.0.0.1", "10.0.0.2"]
        req = self._make_request(
            peer_ip="10.0.0.2",
            # Attacker at 203.0.113.50 forged "1.1.1.1, 2.2.2.2"; proxy 10.0.0.1 appended 203.0.113.50
            forwarded_for="1.1.1.1, 2.2.2.2, 203.0.113.50, 10.0.0.1",
        )
        # Walking right-to-left: 10.0.0.1 (trusted) -> 203.0.113.50 (first untrusted, returned)
        assert get_client_ip(req, trusted_proxies=trusted) == "203.0.113.50"

    def test_untrusted_intermediary_in_forwarded_chain(self) -> None:
        """Chain traversal halts at the first untrusted intermediary without inspecting further left."""
        trusted = ["10.0.0.1", "10.0.0.2"]
        req = self._make_request(
            peer_ip="10.0.0.2",
            forwarded_for="198.51.100.1, 203.0.113.5, 10.0.0.1",
        )
        # Walking right-to-left: 10.0.0.1 (trusted) -> 203.0.113.5 (untrusted, returned)
        # 198.51.100.1 is NOT trusted because 203.0.113.5 is an untrusted intermediary
        assert get_client_ip(req, trusted_proxies=trusted) == "203.0.113.5"

    def test_ipv6_chains_and_trusted_proxies(self) -> None:
        """Correctly validates IPv6 trusted proxies and extracts IPv6 client IP."""
        trusted = ["::1", "fd00::/8"]
        req = self._make_request(
            peer_ip="::1",
            forwarded_for="2001:db8::1234, fd00::1",
        )
        assert get_client_ip(req, trusted_proxies=trusted) == "2001:db8::1234"

    def test_cidr_network_in_trusted_proxies(self) -> None:
        """Trusted proxies configured with CIDR subnets correctly identify proxy peers."""
        custom_trusted = ["10.0.0.0/24", "172.16.0.0/16"]
        assert is_trusted_proxy("10.0.0.42", custom_trusted) is True
        assert is_trusted_proxy("172.16.1.100", custom_trusted) is True
        assert is_trusted_proxy("192.168.1.1", custom_trusted) is False

        req = self._make_request(peer_ip="10.0.0.5", forwarded_for="198.51.100.7")
        assert get_client_ip(req, trusted_proxies=custom_trusted) == "198.51.100.7"

    def test_malformed_and_empty_forwarded_values(self) -> None:
        """Malformed or empty forwarded chains safely fall back to the immediate peer IP."""
        trusted = ["10.0.0.1"]

        # Missing header
        req_none = self._make_request(peer_ip="10.0.0.1", forwarded_for=None)
        assert get_client_ip(req_none, trusted_proxies=trusted) == "10.0.0.1"

        # Empty string header
        req_empty = self._make_request(peer_ip="10.0.0.1", forwarded_for="   ")
        assert get_client_ip(req_empty, trusted_proxies=trusted) == "10.0.0.1"

        # Malformed candidate IP in chain
        req_bad = self._make_request(
            peer_ip="10.0.0.1",
            forwarded_for="203.0.113.1, bad-ip-token",
        )
        assert get_client_ip(req_bad, trusted_proxies=trusted) == "10.0.0.1"

        # Empty token in comma-separated list
        req_empty_token = self._make_request(
            peer_ip="10.0.0.1",
            forwarded_for="203.0.113.1, , 10.0.0.1",
        )
        assert get_client_ip(req_empty_token, trusted_proxies=trusted) == "10.0.0.1"

    def test_all_trusted_proxies_in_chain_falls_back_to_peer(self) -> None:
        """If every address in the chain is a trusted proxy, safely falls back to the immediate peer."""
        trusted = ["10.0.0.1", "10.0.0.2"]
        req = self._make_request(
            peer_ip="10.0.0.2",
            forwarded_for="10.0.0.1",
        )
        # All hops are trusted proxies; no external client identified -> return peer
        assert get_client_ip(req, trusted_proxies=trusted) == "10.0.0.2"

    def test_untrusted_client_cannot_rotate_header_to_bypass_rate_limiter(self) -> None:
        """Verify sliding-window limiter blocks untrusted client regardless of forged X-Forwarded-For."""
        limiter.reset()
        dep = rate_limit(max_requests=2, window_seconds=60)

        # Untrusted client sends 2 requests with different spoofed headers
        req1 = self._make_request(peer_ip="192.0.2.1", forwarded_for="1.1.1.1")
        req2 = self._make_request(peer_ip="192.0.2.1", forwarded_for="2.2.2.2")
        req3 = self._make_request(peer_ip="192.0.2.1", forwarded_for="3.3.3.3")

        dep(req1)
        dep(req2)

        # 3rd request from same untrusted peer must be rejected even with a new forged header
        with pytest.raises(HTTPException) as exc_info:
            dep(req3)
        assert exc_info.value.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert exc_info.value.detail["error"]["code"] == "RATE_LIMITED"

    def test_trusted_proxies_config_parsing_and_error_handling(self) -> None:
        """Verify parsing of list, JSON string, comma-separated string, and malformed inputs."""
        # JSON list string
        s1 = Settings(trusted_proxies='["10.0.0.1", "192.168.1.0/24"]')
        assert s1.trusted_proxies == ["10.0.0.1", "192.168.1.0/24"]

        # Comma-separated string
        s2 = Settings(trusted_proxies="10.0.0.1, 10.0.0.2, 172.16.0.0/16")
        assert s2.trusted_proxies == ["10.0.0.1", "10.0.0.2", "172.16.0.0/16"]

        # Empty string
        s3 = Settings(trusted_proxies="")
        assert s3.trusted_proxies == []

        # Malformed entries in trusted_proxies fail closed without raising
        assert is_trusted_proxy("10.0.0.1", ["invalid-cidr/999", "not_an_ip"]) is False


# ══════════════════════════════════════════════════════════════════════════════
# SEC-10-05: Gemini API Key Header Transmission & Secret Sanitization
# ══════════════════════════════════════════════════════════════════════════════


class TestSec1005GeminiKeyHeaderTransmission:
    """Tests verifying API key header transmission and absence of keys from URLs/logs."""

    def test_api_key_sent_via_header_not_in_url(self) -> None:
        """Request URL must contain NO key= query parameter; x-goog-api-key header must be set."""
        provider = GeminiAIProvider(api_key="secret-gemini-token-12345", model="gemini-1.5-flash")

        mock_post_response = MagicMock()
        mock_post_response.status_code = 200
        mock_post_response.json.return_value = {
            "candidates": [
                {
                    "content": {
                        "parts": [{"text": "Hello learner, here is your AI tutor feedback."}]
                    }
                }
            ],
            "usageMetadata": {
                "promptTokenCount": 10,
                "candidatesTokenCount": 20,
                "totalTokenCount": 30,
            },
        }

        with patch("httpx.Client.post") as mock_post:
            mock_post.return_value = mock_post_response

            response = provider._call_gemini(
                system_instruction="You are a helpful tutor",
                prompt="Explain recursion",
            )

            assert "candidates" in response
            assert mock_post.called

            call_args, call_kwargs = mock_post.call_args
            called_url = call_args[0]
            called_headers = call_kwargs.get("headers", {})

            # 1. Verify URL has NO key parameter
            assert "key=" not in called_url
            assert "?" not in called_url
            assert called_url == "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

            # 2. Verify x-goog-api-key header is sent with the secret key
            assert called_headers.get("x-goog-api-key") == "secret-gemini-token-12345"
            assert called_headers.get("Content-Type") == "application/json"

    def test_secret_key_sanitized_on_provider_error(self) -> None:
        """Provider errors must not expose the secret API key in exception messages."""
        secret_key = "super-sensitive-secret-key-xyz"
        provider = GeminiAIProvider(api_key=secret_key, model="gemini-1.5-flash")

        mock_error_res = MagicMock()
        mock_error_res.status_code = 500
        mock_error_res.text = "Internal Google API Error"

        with patch("httpx.Client.post") as mock_post:
            mock_post.return_value = mock_error_res

            with pytest.raises(AIProviderError) as exc_info:
                provider._call_gemini(
                    system_instruction="System instruction",
                    prompt="Test prompt",
                )

            # Ensure secret key is NEVER leaked in the exception text
            assert secret_key not in str(exc_info.value)
            assert "500" in str(exc_info.value)


# ══════════════════════════════════════════════════════════════════════════════
# SEC-10-07: Submission Evaluation and Review Claim Authorization
# ══════════════════════════════════════════════════════════════════════════════


class TestSec1007SubmissionEvaluationAuthorization:
    """Tests verifying role, ownership, and evaluator-assignment authorization rules."""

    @pytest.fixture
    def setup_project_and_submission(
        self,
        client: TestClient,
        creator_headers: dict[str, str],
        auth_headers: dict[str, str],
        db: Session,
    ) -> tuple[str, str]:
        """Creates a project owned by creator_headers and a submitted submission by auth_headers."""
        discipline = Discipline(slug="eval-disc", name="Eval Disc", description="Disc")
        db.add(discipline)
        db.commit()

        skill = Skill(
            slug="eval-skill",
            name="Eval Skill",
            discipline_id=discipline.id,
            difficulty_level=SkillDifficulty.INTERMEDIATE,
        )
        db.add(skill)
        db.commit()

        project_res = client.post(
            "/api/v1/projects",
            json={
                "title": "SEC-10-07 Auth Project",
                "short_description": "Project for testing evaluator authorization",
                "full_description": "Full description for testing evaluator authorization",
                "discipline_id": discipline.id,
                "difficulty_level": "INTERMEDIATE",
                "requirements": {"deliverables": ["repo.git"]},
                "evaluation_criteria": {
                    "passing_score": 70.0,
                    "rubric": [{"id": "c1", "title": "Correctness", "max_score": 100.0, "weight": 1.0}],
                },
                "skills": [{"skill_id": skill.id, "is_primary": True}],
            },
            headers=creator_headers,
        )
        project_id = project_res.json()["id"]
        client.post(f"/api/v1/projects/{project_id}/publish", headers=creator_headers)

        sub_res = client.post(
            f"/api/v1/projects/{project_id}/submissions",
            headers=auth_headers,
        )
        sub_id = sub_res.json()["id"]

        client.patch(
            f"/api/v1/submissions/{sub_id}",
            json={"summary": "Ready for review"},
            headers=auth_headers,
        )
        client.post(f"/api/v1/submissions/{sub_id}/submit", headers=auth_headers)

        return project_id, sub_id

    @pytest.fixture
    def second_creator_headers(self, client: TestClient, db: Session) -> dict[str, str]:
        """Provides authentication headers for an unrelated second CREATOR user."""
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "unrelated_creator@example.com",
                "password": "SecureP@ssword1!",
                "display_name": "Unrelated Creator",
            },
        )
        user = db.query(User).filter(User.email == "unrelated_creator@example.com").first()
        user.role = UserRole.CREATOR
        db.commit()

        res = client.post(
            "/api/v1/auth/login",
            json={"email": "unrelated_creator@example.com", "password": "SecureP@ssword1!"},
        )
        return {"Authorization": f"Bearer {res.json()['access_token']}"}

    def test_authorized_project_creator_can_claim_and_evaluate(
        self,
        client: TestClient,
        creator_headers: dict[str, str],
        setup_project_and_submission: tuple[str, str],
    ) -> None:
        """The creator who authored the project can claim and evaluate submissions."""
        _, sub_id = setup_project_and_submission

        # Project creator claims review
        claim_res = client.post(f"/api/v1/submissions/{sub_id}/review", headers=creator_headers)
        assert claim_res.status_code == 200
        assert claim_res.json()["status"] == "UNDER_REVIEW"

        # Project creator evaluates submission
        eval_payload = {
            "criteria_scores": [{"criterion_id": "c1", "score": 85.0, "feedback": "Good job."}],
            "feedback": "Approved by project creator.",
            "action": "APPROVE",
        }
        eval_res = client.post(
            f"/api/v1/submissions/{sub_id}/evaluation",
            json=eval_payload,
            headers=creator_headers,
        )
        assert eval_res.status_code == 200
        assert eval_res.json()["passed"] is True
        assert eval_res.json()["status"] == "COMPLETED"

    def test_unrelated_creator_cannot_evaluate_and_gets_403(
        self,
        client: TestClient,
        second_creator_headers: dict[str, str],
        setup_project_and_submission: tuple[str, str],
    ) -> None:
        """An unrelated creator cannot evaluate another creator's project submission (HTTP 403)."""
        _, sub_id = setup_project_and_submission

        eval_payload = {
            "criteria_scores": [{"criterion_id": "c1", "score": 90.0, "feedback": "Unauthorized."}],
            "feedback": "Attempt by unrelated creator.",
            "action": "APPROVE",
        }
        res = client.post(
            f"/api/v1/submissions/{sub_id}/evaluation",
            json=eval_payload,
            headers=second_creator_headers,
        )
        assert res.status_code == 403
        assert "not authorized" in res.json()["error"]["message"]

    def test_unrelated_creator_cannot_claim_for_review_and_gets_403(
        self,
        client: TestClient,
        second_creator_headers: dict[str, str],
        setup_project_and_submission: tuple[str, str],
    ) -> None:
        """An unrelated creator cannot claim another creator's project submission for review (HTTP 403)."""
        _, sub_id = setup_project_and_submission

        res = client.post(f"/api/v1/submissions/{sub_id}/review", headers=second_creator_headers)
        assert res.status_code == 403
        assert "not authorized" in res.json()["error"]["message"]

    def test_assigned_evaluator_can_evaluate(
        self,
        client: TestClient,
        db: Session,
        second_creator_headers: dict[str, str],
        setup_project_and_submission: tuple[str, str],
    ) -> None:
        """When explicitly assigned in submission.evaluator_id, that evaluator can evaluate."""
        _, sub_id = setup_project_and_submission

        # Explicitly assign reviewer2 as evaluator
        reviewer2 = db.query(User).filter(User.email == "unrelated_creator@example.com").first()
        submission = db.query(ProjectSubmission).filter(ProjectSubmission.id == sub_id).first()
        submission.evaluator_id = reviewer2.id
        submission.status = SubmissionStatus.UNDER_REVIEW.value
        db.commit()

        eval_payload = {
            "criteria_scores": [{"criterion_id": "c1", "score": 95.0, "feedback": "Assigned evaluation."}],
            "feedback": "Approved by assigned evaluator.",
            "action": "APPROVE",
        }
        res = client.post(
            f"/api/v1/submissions/{sub_id}/evaluation",
            json=eval_payload,
            headers=second_creator_headers,
        )
        assert res.status_code == 200
        assert res.json()["passed"] is True

    def test_admin_can_evaluate_any_submission(
        self,
        client: TestClient,
        admin_headers: dict[str, str],
        setup_project_and_submission: tuple[str, str],
    ) -> None:
        """Administrators have global evaluation permissions across all projects."""
        _, sub_id = setup_project_and_submission

        eval_payload = {
            "criteria_scores": [{"criterion_id": "c1", "score": 100.0, "feedback": "Admin override."}],
            "feedback": "Approved by administrator.",
            "action": "APPROVE",
        }
        res = client.post(
            f"/api/v1/submissions/{sub_id}/evaluation",
            json=eval_payload,
            headers=admin_headers,
        )
        assert res.status_code == 200
        assert res.json()["passed"] is True

    def test_learner_cannot_evaluate_and_gets_403(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        setup_project_and_submission: tuple[str, str],
    ) -> None:
        """Learners cannot evaluate submissions (HTTP 403 Forbidden)."""
        _, sub_id = setup_project_and_submission

        eval_payload = {
            "criteria_scores": [{"criterion_id": "c1", "score": 100.0, "feedback": "Learner attempt."}],
            "feedback": "Self-grading.",
            "action": "APPROVE",
        }
        res = client.post(
            f"/api/v1/submissions/{sub_id}/evaluation",
            json=eval_payload,
            headers=auth_headers,
        )
        assert res.status_code == 403

    def test_creator_cannot_evaluate_own_submission(
        self,
        client: TestClient,
        creator_headers: dict[str, str],
        setup_project_and_submission: tuple[str, str],
    ) -> None:
        """A creator submitting to their own project cannot self-evaluate (HTTP 403)."""
        project_id, _ = setup_project_and_submission

        # Creator starts and submits to their own project
        start_res = client.post(f"/api/v1/projects/{project_id}/submissions", headers=creator_headers)
        own_sub_id = start_res.json()["id"]

        client.patch(
            f"/api/v1/submissions/{own_sub_id}",
            json={"summary": "Creator own solution"},
            headers=creator_headers,
        )
        client.post(f"/api/v1/submissions/{own_sub_id}/submit", headers=creator_headers)

        eval_payload = {
            "criteria_scores": [{"criterion_id": "c1", "score": 100.0, "feedback": "Self-approval."}],
            "feedback": "Approving myself.",
            "action": "APPROVE",
        }
        res = client.post(
            f"/api/v1/submissions/{own_sub_id}/evaluation",
            json=eval_payload,
            headers=creator_headers,
        )
        assert res.status_code == 403
        assert "own submission" in res.json()["error"]["message"]
