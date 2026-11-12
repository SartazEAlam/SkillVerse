"""Comprehensive tests for Phase 10 Stage 2:
- Security headers (SEC-10-02)
- Content Security Policy (CSP) rollout mode and directives
- CORS origin, method, header, and credentials hardening
- Cache-Control policies across public, private, portfolio, and artifact endpoints
- Middleware ordering and unhandled 500 response handling
"""

from __future__ import annotations

import shutil
import tempfile

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.config import Settings, settings
from app.infrastructure.security_headers import (
    SecurityHeadersMiddleware,
    build_csp_policy,
    is_verified_https,
)
from app.infrastructure.storage.factory import reset_storage_service
from app.modules.skills.models import Discipline, Skill, SkillDifficulty

# ══════════════════════════════════════════════════════════════════════════════
# 1. Base Security Headers Tests
# ══════════════════════════════════════════════════════════════════════════════


class TestSecurityHeaders:
    """Verify standard defensive response headers across all HTTP status codes."""

    def test_security_headers_on_successful_response(self, client: TestClient):
        """Successful 200 response contains all standard baseline defensive headers."""
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        assert resp.headers.get("x-content-type-options") == "nosniff"
        assert resp.headers.get("x-frame-options") == "DENY"
        assert resp.headers.get("referrer-policy") == "strict-origin-when-cross-origin"
        assert "camera=()" in resp.headers.get("permissions-policy", "")
        assert "microphone=()" in resp.headers.get("permissions-policy", "")
        assert "geolocation=()" in resp.headers.get("permissions-policy", "")
        assert resp.headers.get("x-xss-protection") == "0"

    def test_security_headers_on_401_unauthorized(self, client: TestClient):
        """Authentication failure (401) contains full security headers."""
        resp = client.get("/api/v1/users/me")
        assert resp.status_code == 401
        assert resp.headers.get("x-content-type-options") == "nosniff"
        assert resp.headers.get("x-frame-options") == "DENY"
        assert resp.headers.get("referrer-policy") == "strict-origin-when-cross-origin"
        assert "camera=()" in resp.headers.get("permissions-policy", "")
        assert resp.headers.get("x-xss-protection") == "0"

    def test_security_headers_on_404_not_found(self, client: TestClient):
        """Not found (404) response contains full security headers."""
        resp = client.get("/api/v1/nonexistent-route-endpoint")
        assert resp.status_code == 404
        assert resp.headers.get("x-content-type-options") == "nosniff"
        assert resp.headers.get("x-frame-options") == "DENY"
        assert resp.headers.get("referrer-policy") == "strict-origin-when-cross-origin"

    def test_security_headers_on_422_validation_error(self, client: TestClient):
        """Validation error (422) contains full security headers."""
        resp = client.post("/api/v1/auth/login", json={})
        assert resp.status_code == 422
        assert resp.headers.get("x-content-type-options") == "nosniff"
        assert resp.headers.get("x-frame-options") == "DENY"
        assert resp.headers.get("referrer-policy") == "strict-origin-when-cross-origin"

    def test_security_headers_on_cors_preflight(self, client: TestClient):
        """OPTIONS preflight response contains security headers alongside CORS headers."""
        resp = client.options(
            "/api/v1/auth/login",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )
        assert resp.status_code == 200
        assert resp.headers.get("x-content-type-options") == "nosniff"
        assert resp.headers.get("x-frame-options") == "DENY"
        assert resp.headers.get("referrer-policy") == "strict-origin-when-cross-origin"

    def test_security_headers_on_unhandled_500_response(self):
        """Unhandled 500 error caught by SecurityHeadersMiddleware retains all security headers.

        Guarantees that Starlette's ServerErrorMiddleware does not return an unprotected,
        untyped text error response or leak exception tracebacks.
        """
        app = FastAPI()

        @app.get("/test-crash")
        def crash_endpoint():
            raise RuntimeError("Database connection suddenly dropped")

        app.add_middleware(SecurityHeadersMiddleware, settings=settings)

        test_client = TestClient(app, raise_server_exceptions=False)
        resp = test_client.get("/test-crash")

        assert resp.status_code == 500
        assert resp.headers.get("content-type") == "application/json"
        assert resp.headers.get("x-content-type-options") == "nosniff"
        assert resp.headers.get("x-frame-options") == "DENY"
        assert resp.headers.get("referrer-policy") == "strict-origin-when-cross-origin"
        assert "camera=()" in resp.headers.get("permissions-policy", "")
        assert resp.headers.get("x-xss-protection") == "0"
        assert resp.headers.get("cache-control") == "private, no-store"

        # Ensure no internal traceback is leaked
        data = resp.json()
        assert data["error"]["code"] == "INTERNAL_ERROR"
        assert "Database connection suddenly dropped" not in str(data)

    def test_exception_after_headers_sent_does_not_generate_duplicate_response(self):
        """When an exception occurs after response headers have started streaming,

        the middleware raises the exception without attempting to send a duplicate 500 response.
        """
        app = FastAPI()

        @app.get("/stream-crash")
        def stream_crash():
            from fastapi.responses import StreamingResponse

            def failing_generator():
                yield b"initial chunk"
                raise RuntimeError("Mid-stream failure after headers sent")

            return StreamingResponse(failing_generator(), media_type="text/plain")

        app.add_middleware(SecurityHeadersMiddleware, settings=settings)

        test_client = TestClient(app, raise_server_exceptions=True)
        with pytest.raises(RuntimeError, match="Mid-stream failure"):
            test_client.get("/stream-crash")

    def test_hsts_absent_in_development(self, client: TestClient):
        """HSTS header must NEVER be emitted in development environment."""
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        assert "strict-transport-security" not in resp.headers

    def test_hsts_absent_on_plain_http_even_in_production(self):
        """HSTS must NOT be emitted over plain HTTP, even when production environment is set."""
        prod_settings = Settings(
            environment="production",
            database_url="postgresql://user:pass@localhost:5432/db",
            jwt_secret_key="a" * 64,
            cors_origins=["https://app.skillverse.com"],
            hsts_enabled=True,
        )
        app = FastAPI()

        @app.get("/health")
        def health():
            return {"status": "ok"}

        app.add_middleware(SecurityHeadersMiddleware, settings=prod_settings)

        # Standard HTTP client scheme
        test_client = TestClient(app, base_url="http://testserver")
        resp = test_client.get("/health")
        assert resp.status_code == 200
        assert "strict-transport-security" not in resp.headers

    def test_hsts_present_on_verified_https_in_production(self):
        """HSTS must be emitted over genuine HTTPS in production when enabled."""
        prod_settings = Settings(
            environment="production",
            database_url="postgresql://user:pass@localhost:5432/db",
            jwt_secret_key="a" * 64,
            cors_origins=["https://app.skillverse.com"],
            hsts_enabled=True,
            hsts_max_age=31536000,
        )
        app = FastAPI()

        @app.get("/health")
        def health():
            return {"status": "ok"}

        app.add_middleware(SecurityHeadersMiddleware, settings=prod_settings)

        # HTTPS client scheme
        test_client = TestClient(app, base_url="https://testserver")
        resp = test_client.get("/health")
        assert resp.status_code == 200
        assert resp.headers.get("strict-transport-security") == "max-age=31536000"
        # Preload and includeSubDomains must not be present by default
        assert "preload" not in resp.headers.get("strict-transport-security", "")
        assert "includeSubDomains" not in resp.headers.get("strict-transport-security", "")

    def test_hsts_reverse_proxy_tls_termination_trust_verification(self):
        """X-Forwarded-Proto is only trusted when the client peer IP is in trusted_proxies."""
        prod_settings = Settings(
            environment="production",
            database_url="postgresql://user:pass@localhost:5432/db",
            jwt_secret_key="a" * 64,
            cors_origins=["https://app.skillverse.com"],
            hsts_enabled=True,
            trusted_proxies=["10.0.0.1"],
        )

        # 1. Untrusted peer claiming https -> Rejected
        scope_untrusted = {
            "type": "http",
            "scheme": "http",
            "client": ("192.168.1.50", 12345),
            "headers": [(b"x-forwarded-proto", b"https")],
        }
        assert is_verified_https(scope_untrusted, prod_settings) is False

        # 2. Trusted peer claiming https -> Accepted
        scope_trusted = {
            "type": "http",
            "scheme": "http",
            "client": ("10.0.0.1", 12345),
            "headers": [(b"x-forwarded-proto", b"https")],
        }
        assert is_verified_https(scope_trusted, prod_settings) is True


# ══════════════════════════════════════════════════════════════════════════════
# 2. Content Security Policy (CSP) Tests
# ══════════════════════════════════════════════════════════════════════════════


class TestContentSecurityPolicy:
    """Verify CSP directives, rollout mode, and resource restrictions."""

    def test_csp_report_only_mode_active_by_default(self, client: TestClient):
        """During Stage 2 rollout, Content-Security-Policy-Report-Only is emitted, not enforced CSP."""
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        assert "content-security-policy-report-only" in resp.headers
        assert "content-security-policy" not in resp.headers

    def test_csp_enforced_mode_configurable(self):
        """When csp_report_only=False, Content-Security-Policy is enforced."""
        custom_settings = Settings(
            csp_enabled=True,
            csp_report_only=False,
        )
        app = FastAPI()

        @app.get("/test")
        def test_endpoint():
            return {"ok": True}

        app.add_middleware(SecurityHeadersMiddleware, settings=custom_settings)

        test_client = TestClient(app)
        resp = test_client.get("/test")
        assert resp.status_code == 200
        assert "content-security-policy" in resp.headers
        assert "content-security-policy-report-only" not in resp.headers

    def test_csp_required_directives_present(self, client: TestClient):
        """Verify presence of essential defensive CSP directives."""
        resp = client.get("/api/v1/health")
        csp = resp.headers.get("content-security-policy-report-only", "")

        assert "default-src 'self'" in csp
        assert "script-src 'self'" in csp
        assert "font-src 'self' https://fonts.gstatic.com data:" in csp
        assert "img-src 'self' data: blob: https://images.unsplash.com https://lh3.googleusercontent.com" in csp
        assert "frame-src https://www.youtube.com https://www.youtube-nocookie.com https://player.vimeo.com" in csp
        assert "object-src 'none'" in csp
        assert "base-uri 'self'" in csp
        assert "form-action 'self'" in csp
        assert "frame-ancestors 'none'" in csp

    def test_csp_style_src_attr_for_react_dynamic_styles(self, client: TestClient):
        """style-src-attr 'unsafe-inline' safely permits React dynamic style attributes."""
        resp = client.get("/api/v1/health")
        csp = resp.headers.get("content-security-policy-report-only", "")
        assert "style-src-attr 'unsafe-inline'" in csp

    def test_csp_no_unsafe_eval(self, client: TestClient):
        """Neither 'unsafe-eval' nor 'wasm-unsafe-eval' may appear in application CSP."""
        resp = client.get("/api/v1/health")
        csp = resp.headers.get("content-security-policy-report-only", "")
        assert "'unsafe-eval'" not in csp
        assert "wasm-unsafe-eval" not in csp

    def test_csp_no_script_unsafe_inline(self, client: TestClient):
        """'unsafe-inline' must NOT appear in script-src."""
        resp = client.get("/api/v1/health")
        csp = resp.headers.get("content-security-policy-report-only", "")

        directives = dict(d.strip().split(" ", 1) for d in csp.split(";") if d.strip())
        script_src = directives.get("script-src", "")
        assert "'unsafe-inline'" not in script_src

    def test_csp_dev_websocket_absent_in_production(self):
        """Vite HMR ws:// origins and localhost backend origins are absent in production CSP."""
        prod_settings = Settings(
            environment="production",
            database_url="postgresql://user:pass@localhost:5432/db",
            jwt_secret_key="a" * 64,
            cors_origins=["https://app.skillverse.com"],
        )
        csp = build_csp_policy(prod_settings, is_docs=False)
        assert "ws://localhost:5173" not in csp
        assert "ws://127.0.0.1:5173" not in csp
        assert "http://localhost:8000" not in csp
        assert "http://127.0.0.1:8000" not in csp

    def test_csp_dev_connect_src_includes_backend_origins(self):
        """Development CSP includes localhost backend API origins and Vite HMR WebSockets."""
        dev_settings = Settings(
            environment="development",
            api_port=8000,
            cors_origins=["http://localhost:5173"],
        )
        csp = build_csp_policy(dev_settings, is_docs=False)
        assert "http://localhost:8000" in csp
        assert "http://127.0.0.1:8000" in csp
        assert "ws://localhost:5173" in csp

    def test_csp_reporting_behavior(self):
        """Verify report-uri is appended only when configured, and absent by default."""
        # 1. Default (empty) -> No report-uri directive
        default_csp = build_csp_policy(settings, is_docs=False)
        assert "report-uri" not in default_csp

        # 2. Configured -> report-uri appended
        configured_settings = Settings(
            csp_report_uri="https://reports.skillverse.dev/csp",
        )
        custom_csp = build_csp_policy(configured_settings, is_docs=False)
        assert "report-uri https://reports.skillverse.dev/csp" in custom_csp

    def test_csp_docs_scoped_policy(self, client: TestClient):
        """FastAPI /api/docs receives dedicated documentation CSP allowing CDN Swagger assets."""
        resp = client.get("/api/docs")
        if resp.status_code == 200:
            csp = resp.headers.get("content-security-policy-report-only", "")
            assert "https://cdn.jsdelivr.net" in csp
            assert "frame-ancestors 'none'" in csp

    def test_openapi_json_retains_security_headers_without_relaxation(self, client: TestClient):
        """The /openapi.json specification returns JSON with standard security headers."""
        resp = client.get("/openapi.json")
        assert resp.status_code == 200
        assert resp.headers.get("x-content-type-options") == "nosniff"
        assert resp.headers.get("cache-control") == "no-cache"


# ══════════════════════════════════════════════════════════════════════════════
# 3. CORS Hardening Tests
# ══════════════════════════════════════════════════════════════════════════════


class TestCorsHardening:
    """Verify origin validation, method restriction, header restriction, and credentials."""

    def test_cors_allowed_origin_success(self, client: TestClient):
        """Request with configured allowed origin returns Access-Control-Allow-Origin."""
        resp = client.get("/api/v1/health", headers={"Origin": "http://localhost:5173"})
        assert resp.status_code == 200
        assert resp.headers.get("access-control-allow-origin") == "http://localhost:5173"

    def test_cors_disallowed_origin_rejected(self, client: TestClient):
        """Request with untrusted origin does NOT receive Access-Control-Allow-Origin."""
        resp = client.get("/api/v1/health", headers={"Origin": "http://evil-attacker.com"})
        assert resp.status_code == 200
        assert "access-control-allow-origin" not in resp.headers

    def test_cors_preflight_restricted_methods(self, client: TestClient):
        """Preflight OPTIONS returns only allowed methods (no wildcard and no OPTIONS in allowed methods)."""
        resp = client.options(
            "/api/v1/health",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "authorization",
            },
        )
        assert resp.status_code == 200
        allowed_methods = resp.headers.get("access-control-allow-methods", "")
        assert "*" not in allowed_methods
        # OPTIONS should not be in the negotiated methods list
        methods_list = [m.strip() for m in allowed_methods.split(",")]
        assert "OPTIONS" not in methods_list
        assert set(methods_list).issubset({"GET", "POST", "PUT", "PATCH", "DELETE"})
        assert resp.headers.get("access-control-max-age") == "600"

    def test_cors_restricted_request_headers(self, client: TestClient):
        """Allowed headers are restricted; x-goog-api-key must NOT be permitted for browsers."""
        resp = client.options(
            "/api/v1/health",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "authorization, content-type, accept",
            },
        )
        assert resp.status_code == 200
        allowed_headers = resp.headers.get("access-control-allow-headers", "").lower()
        assert "authorization" in allowed_headers
        assert "content-type" in allowed_headers
        assert "x-goog-api-key" not in allowed_headers

    def test_cors_credentials_disabled_for_bearer_auth(self, client: TestClient):
        """Access-Control-Allow-Credentials must not be returned when credentials are false."""
        resp = client.get("/api/v1/health", headers={"Origin": "http://localhost:5173"})
        assert resp.status_code == 200
        assert resp.headers.get("access-control-allow-credentials") is None

    def test_cors_bearer_token_works_with_credentials_false(self, client: TestClient):
        """Bearer token authentication works cleanly with allow_credentials=False."""
        # 1. Register user
        reg_resp = client.post(
            "/api/v1/auth/register",
            json={
                "email": "cors_tester@skillverse.dev",
                "password": "Password123!",
                "display_name": "CORS Tester",
            },
            headers={"Origin": "http://localhost:5173"},
        )
        assert reg_resp.status_code == 201

        login_resp = client.post(
            "/api/v1/auth/login",
            json={"email": "cors_tester@skillverse.dev", "password": "Password123!"},
            headers={"Origin": "http://localhost:5173"},
        )
        assert login_resp.status_code == 200
        token = login_resp.json()["access_token"]

        # 2. Access authenticated resource with Bearer token
        me_resp = client.get(
            "/api/v1/users/me",
            headers={
                "Origin": "http://localhost:5173",
                "Authorization": f"Bearer {token}",
            },
        )
        assert me_resp.status_code == 200
        assert me_resp.json()["email"] == "cors_tester@skillverse.dev"
        assert me_resp.headers.get("access-control-allow-origin") == "http://localhost:5173"

    def test_cors_validator_rejects_wildcard_in_production(self):
        """Settings validator strictly rejects wildcard '*' origin in production."""
        with pytest.raises(ValueError, match="Wildcard CORS origin"):
            Settings(
                environment="production",
                database_url="postgresql://user:pass@localhost:5432/db",
                jwt_secret_key="a" * 64,
                cors_origins=["*"],
            )

    def test_cors_validator_rejects_insecure_http_in_production(self):
        """Settings validator rejects insecure http:// origins in production."""
        with pytest.raises(ValueError, match="Insecure HTTP CORS origin"):
            Settings(
                environment="production",
                database_url="postgresql://user:pass@localhost:5432/db",
                jwt_secret_key="a" * 64,
                cors_origins=["http://app.skillverse.com"],
            )

    def test_cors_validator_rejects_localhost_in_production(self):
        """Settings validator rejects localhost origins in production."""
        with pytest.raises(ValueError, match="Localhost CORS origin"):
            Settings(
                environment="production",
                database_url="postgresql://user:pass@localhost:5432/db",
                jwt_secret_key="a" * 64,
                cors_origins=["https://localhost:5173"],
            )

    def test_cors_validator_rejects_wildcard_with_credentials_in_any_environment(self):
        """Settings validator rejects wildcard origin when allow_credentials is True."""
        with pytest.raises(ValueError, match="CORS credentials cannot be enabled with wildcard"):
            Settings(
                environment="development",
                cors_allow_credentials=True,
                cors_origins=["*"],
            )


# ══════════════════════════════════════════════════════════════════════════════
# 4. Cache-Control Policies Tests
# ══════════════════════════════════════════════════════════════════════════════


class TestCacheControlPolicies:
    """Verify route-aware caching: private/no-store for sensitive data, controlled cache for public metadata."""

    @pytest.fixture(autouse=True)
    def isolated_storage(self):
        temp_dir = tempfile.mkdtemp(prefix="test_stage2_storage_")
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

    def test_cache_control_public_catalog_and_metadata(self, client: TestClient):
        """Public read-only catalog and health endpoints receive short shared cache."""
        health_resp = client.get("/api/v1/health")
        assert health_resp.status_code == 200
        assert health_resp.headers.get("cache-control") == "public, max-age=60, stale-while-revalidate=120"

        skills_resp = client.get("/api/v1/skills")
        assert skills_resp.status_code == 200
        assert skills_resp.headers.get("cache-control") == "public, max-age=60, stale-while-revalidate=120"

    def test_cache_control_error_on_public_endpoint_is_not_cached(self, client: TestClient):
        """Error status on catalog endpoints (e.g. 405 Method Not Allowed) returns private, no-store."""
        resp = client.post("/api/v1/health")
        assert resp.status_code == 405
        assert resp.headers.get("cache-control") == "private, no-store"

    def test_cache_control_trailing_slash_public_endpoint(self, client: TestClient):
        """Catalog endpoint with trailing slash returns normalized public cache header."""
        resp = client.get("/api/v1/skills/")
        assert resp.status_code == 200
        assert resp.headers.get("cache-control") == "public, max-age=60, stale-while-revalidate=120"

    def test_cache_control_sensitive_authenticated_routes(self, client: TestClient):
        """Sensitive account and learner data return private, no-store."""
        # Unauthenticated attempt -> 401
        me_401 = client.get("/api/v1/users/me")
        assert me_401.headers.get("cache-control") == "private, no-store"

        # Register and login -> 200
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "cache_tester@skillverse.dev",
                "password": "Password123!",
                "display_name": "Cache Tester",
            },
        )
        login_resp = client.post(
            "/api/v1/auth/login",
            json={"email": "cache_tester@skillverse.dev", "password": "Password123!"},
        )
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        me_200 = client.get("/api/v1/users/me", headers=headers)
        assert me_200.status_code == 200
        assert me_200.headers.get("cache-control") == "private, no-store"

    def test_cache_control_private_portfolios(self, client: TestClient):
        """Private portfolio management (/portfolios/me) returns private, no-store."""
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "portfolio_cache@skillverse.dev",
                "password": "Password123!",
                "display_name": "Portfolio Cache",
            },
        )
        login_resp = client.post(
            "/api/v1/auth/login",
            json={"email": "portfolio_cache@skillverse.dev", "password": "Password123!"},
        )
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        port_resp = client.get("/api/v1/portfolios/me", headers=headers)
        assert port_resp.status_code == 200
        assert port_resp.headers.get("cache-control") == "private, no-store"

    def test_cache_control_public_portfolios_conservative(self, client: TestClient):
        """Public portfolio profile returns private, no-store to prevent stale caching upon visibility changes."""
        reg_resp = client.post(
            "/api/v1/auth/register",
            json={
                "email": "public_port@skillverse.dev",
                "password": "Password123!",
                "display_name": "Public Port User",
            },
        )
        user_id = reg_resp.json()["user"]["id"]

        resp = client.get(f"/api/v1/portfolios/{user_id}")
        assert resp.headers.get("cache-control") == "private, no-store"

    def test_cache_control_artifact_downloads_preserves_download_headers(
        self,
        client: TestClient,
        creator_headers: dict[str, str],
        auth_headers: dict[str, str],
        db: Session,
    ):
        """Artifact downloads return private, no-store while preserving Content-Disposition and nosniff."""
        discipline = Discipline(slug="cache-disc", name="Cache Disc", description="Disc")
        db.add(discipline)
        db.commit()

        skill = Skill(
            slug="cache-skill",
            name="Cache Skill",
            discipline_id=discipline.id,
            difficulty_level=SkillDifficulty.INTERMEDIATE,
        )
        db.add(skill)
        db.commit()

        project_res = client.post(
            "/api/v1/projects",
            json={
                "title": "Cache Upload Project",
                "short_description": "Testing cache artifact uploads",
                "full_description": "Full description for testing cache artifact uploads",
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
        sub_id = sub_res.json()["id"]

        valid_content = b"%PDF-1.4 sample content for artifact download"
        upload_resp = client.post(
            f"/api/v1/submissions/{sub_id}/artifacts",
            files={"file": ("project_report.pdf", valid_content, "application/pdf")},
            data={"is_public": "true"},
            headers=auth_headers,
        )
        assert upload_resp.status_code == 201
        artifact_id = upload_resp.json()["id"]

        dl_resp = client.get(
            f"/api/v1/artifacts/{artifact_id}/download",
            headers=auth_headers,
        )
        assert dl_resp.status_code == 200
        assert dl_resp.headers.get("cache-control") == "private, no-store"
        assert dl_resp.headers.get("x-content-type-options") == "nosniff"
        assert 'attachment; filename="project_report.pdf"' in dl_resp.headers.get("content-disposition", "")
        assert dl_resp.headers.get("content-length") == str(len(valid_content))
        assert dl_resp.content == valid_content
