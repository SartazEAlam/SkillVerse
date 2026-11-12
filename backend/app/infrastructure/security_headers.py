"""Security headers, Content Security Policy, and Cache-Control middleware.

Phase 10 Stage 2 implementation for application hardening.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from starlette.datastructures import MutableHeaders
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

if TYPE_CHECKING:
    from app.config import Settings

logger = logging.getLogger("skillverse.security")

# Verified external origins from frontend inventory
VERIFIED_FONT_STYLES = "https://fonts.googleapis.com"
VERIFIED_FONT_BINARIES = "https://fonts.gstatic.com"
VERIFIED_IMG_ORIGINS = "https://images.unsplash.com https://lh3.googleusercontent.com"
VERIFIED_FRAME_ORIGINS = (
    "https://www.youtube.com https://www.youtube-nocookie.com https://player.vimeo.com"
)
SWAGGER_CDN = "https://cdn.jsdelivr.net"
FASTAPI_IMG = "https://fastapi.tiangolo.com"


def build_csp_policy(settings: Settings, is_docs: bool = False) -> str:
    """Construct Content Security Policy based on verified application resources."""
    if is_docs:
        # Narrowly scoped documentation CSP for Swagger UI / ReDoc assets
        directives = [
            "default-src 'self'",
            f"script-src 'self' {SWAGGER_CDN} 'unsafe-inline'",
            f"style-src 'self' {SWAGGER_CDN} {VERIFIED_FONT_STYLES} 'unsafe-inline'",
            f"font-src 'self' {VERIFIED_FONT_BINARIES} data:",
            f"img-src 'self' data: {FASTAPI_IMG}",
            "connect-src 'self'",
            "worker-src 'self' blob:",
            "frame-ancestors 'none'",
        ]
        return "; ".join(directives)

    # Standard application CSP directives
    # 1. Connect-src: derive from configured cors_origins + dev backend/WebSocket if applicable
    connect_origins = ["'self'"]
    for origin in settings.cors_origins:
        if origin != "*":
            connect_origins.append(origin)

    if settings.is_development:
        # Include verified development backend API origins and Vite dev server HMR WebSockets
        dev_api_origins = [
            "http://localhost:8000",
            "http://127.0.0.1:8000",
            f"http://localhost:{settings.api_port}",
            f"http://127.0.0.1:{settings.api_port}",
        ]
        dev_ws_origins = ["ws://localhost:5173", "ws://127.0.0.1:5173", "ws://localhost:3000"]
        connect_origins.extend(dev_api_origins)
        connect_origins.extend(dev_ws_origins)

    connect_str = " ".join(dict.fromkeys(connect_origins))

    # 2. Style-src & style-src-attr:
    # In development, Vite dynamically injects <style> tags, needing 'unsafe-inline'.
    # In production, styles are extracted to CSS bundles, allowing 'self' + Google Fonts.
    # style-src-attr 'unsafe-inline' safely permits React dynamic style attributes (progress bars, canvas).
    if settings.is_development:
        style_src = f"style-src 'self' 'unsafe-inline' {VERIFIED_FONT_STYLES}"
    else:
        style_src = f"style-src 'self' {VERIFIED_FONT_STYLES}"

    directives = [
        "default-src 'self'",
        "script-src 'self'",
        style_src,
        "style-src-attr 'unsafe-inline'",
        f"font-src 'self' {VERIFIED_FONT_BINARIES} data:",
        f"img-src 'self' data: blob: {VERIFIED_IMG_ORIGINS}",
        f"frame-src {VERIFIED_FRAME_ORIGINS}",
        f"connect-src {connect_str}",
        "object-src 'none'",
        "base-uri 'self'",
        "form-action 'self'",
        "frame-ancestors 'none'",
    ]

    if settings.csp_report_uri:
        directives.append(f"report-uri {settings.csp_report_uri}")

    return "; ".join(directives)


def is_verified_https(scope: Scope, settings: Settings) -> bool:
    """Determine whether the request is genuinely HTTPS.

    Supports direct TLS termination and reverse-proxy TLS termination via
    X-Forwarded-Proto, only trusting the header when the immediate peer is
    a configured trusted proxy.
    """
    # Direct scheme check
    if scope.get("scheme") == "https":
        return True

    # Reverse-proxy TLS termination check
    headers = dict(scope.get("headers", []))
    forwarded_proto = headers.get(b"x-forwarded-proto", b"").decode("latin-1").lower().strip()
    if forwarded_proto != "https":
        return False

    # Verify peer is a trusted proxy before trusting X-Forwarded-Proto
    client = scope.get("client")
    if not client:
        return False
    peer_ip = client[0]

    from app.infrastructure.rate_limiter import is_trusted_proxy

    return is_trusted_proxy(peer_ip, settings.trusted_proxies)


def get_route_cache_control(method: str, path: str, status_code: int) -> str:
    """Determine appropriate Cache-Control header based on endpoint sensitivity."""
    # Only successful GET requests to specific public metadata can be cached briefly
    if method == "GET" and status_code == 200:
        norm_path = path.rstrip("/") or "/"
        if norm_path in ("/api/v1/skills", "/api/v1/courses", "/api/v1/health"):
            return "public, max-age=60, stale-while-revalidate=120"
        if norm_path in ("/api/docs", "/api/redoc", "/openapi.json"):
            return "no-cache"

    # All authenticated, user-specific, mutable, or error responses must not be cached
    return "private, no-store"


class SecurityHeadersMiddleware:
    """Pure ASGI middleware applying defensive security headers and cache policies.

    Ensures headers are present on:
    - Normal responses (200)
    - Authentication (401) and authorization (403) failures
    - Not found (404) and validation errors (422)
    - CORS preflight responses (OPTIONS)
    - Unhandled server exceptions (500), catching them before Starlette's
      ServerErrorMiddleware can return an unprotected response.
    """

    def __init__(self, app: ASGIApp, settings: Settings | None = None) -> None:
        self.app = app
        if settings is None:
            from app.config import settings as default_settings

            self.settings = default_settings
        else:
            self.settings = settings

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        method = scope.get("method", "GET")
        path = scope.get("path", "")
        headers_sent = False

        async def send_wrapper(message: Message) -> None:
            nonlocal headers_sent
            if message["type"] == "http.response.start":
                headers_sent = True
                status_code = message.get("status", 200)
                headers = MutableHeaders(scope=message)

                # 1. Base Security Headers
                headers.setdefault("X-Content-Type-Options", "nosniff")
                headers.setdefault("X-Frame-Options", "DENY")
                headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
                headers.setdefault(
                    "Permissions-Policy",
                    "camera=(), microphone=(), geolocation=(), payment=(), usb=(), screen-wake-lock=()",
                )
                headers.setdefault("X-XSS-Protection", "0")

                # 2. Content Security Policy (configurable rollout mode)
                if self.settings.csp_enabled:
                    is_docs = path in ("/api/docs", "/api/redoc")
                    csp_val = build_csp_policy(self.settings, is_docs=is_docs)
                    csp_header_name = (
                        "Content-Security-Policy-Report-Only"
                        if self.settings.csp_report_only
                        else "Content-Security-Policy"
                    )
                    headers.setdefault(csp_header_name, csp_val)

                # 3. HTTP Strict Transport Security (HSTS)
                # Only enabled in production and only when genuine HTTPS is verified
                if (
                    self.settings.environment == "production"
                    and self.settings.hsts_enabled
                    and is_verified_https(scope, self.settings)
                ):
                    hsts_parts = [f"max-age={self.settings.hsts_max_age}"]
                    if self.settings.hsts_include_subdomains:
                        hsts_parts.append("includeSubDomains")
                    if self.settings.hsts_preload:
                        hsts_parts.append("preload")
                    headers.setdefault("Strict-Transport-Security", "; ".join(hsts_parts))

                # 4. Cache-Control (conservative, route-aware)
                if "cache-control" not in headers:
                    headers["Cache-Control"] = get_route_cache_control(method, path, status_code)

            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as exc:
            logger.exception("Unhandled server exception caught by SecurityHeadersMiddleware: %s", exc)
            if not headers_sent:
                # Construct safe 500 JSON response with full security headers
                err_headers = {
                    "X-Content-Type-Options": "nosniff",
                    "X-Frame-Options": "DENY",
                    "Referrer-Policy": "strict-origin-when-cross-origin",
                    "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=(), usb=(), screen-wake-lock=()",
                    "X-XSS-Protection": "0",
                    "Cache-Control": "private, no-store",
                }
                if self.settings.csp_enabled:
                    csp_header_name = (
                        "Content-Security-Policy-Report-Only"
                        if self.settings.csp_report_only
                        else "Content-Security-Policy"
                    )
                    err_headers[csp_header_name] = build_csp_policy(self.settings, is_docs=False)

                if (
                    self.settings.environment == "production"
                    and self.settings.hsts_enabled
                    and is_verified_https(scope, self.settings)
                ):
                    err_headers["Strict-Transport-Security"] = f"max-age={self.settings.hsts_max_age}"

                response = JSONResponse(
                    status_code=500,
                    content={
                        "error": {
                            "code": "INTERNAL_ERROR",
                            "message": "An unexpected server error occurred.",
                            "details": {},
                        }
                    },
                    headers=err_headers,
                )
                await response(scope, receive, send)
            else:
                raise
