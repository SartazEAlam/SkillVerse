"""In-memory and Redis-capable sliding-window rate limiter.

Follows SkillVerse specifications:
- Login: 10 attempts per 15 min per IP/email
- Registration: 5 attempts per hour per IP
- Password reset: 3 attempts per hour per email
- OAuth authorization & callback: 10 attempts per 15 min per IP
"""

from __future__ import annotations

import ipaddress
import time
from collections import defaultdict
from collections.abc import Callable

from fastapi import HTTPException, Request, status


def is_trusted_proxy(ip_str: str, trusted_list: list[str]) -> bool:
    """Check if an IP string belongs to a configured trusted proxy IP or CIDR network.

    Fails safely (returns False) for empty inputs, malformed IPs, and invalid
    CIDR entries in trusted_list.
    """
    if not ip_str or not trusted_list:
        return False
    try:
        ip = ipaddress.ip_address(ip_str.strip())
    except ValueError:
        return False

    for entry in trusted_list:
        entry = entry.strip()
        if not entry:
            continue
        try:
            if "/" in entry:
                network = ipaddress.ip_network(entry, strict=False)
                if ip in network:
                    return True
            else:
                trusted_ip = ipaddress.ip_address(entry)
                if ip == trusted_ip:
                    return True
        except ValueError:
            # Malformed trusted proxy entry: fail closed, do not match
            continue
    return False


def get_client_ip(request: Request, trusted_proxies: list[str] | None = None) -> str:
    """Extract client IP securely using right-to-left reverse proxy traversal.

    Security & Architectural Invariants:
    1. Default Secure Stance:
       No proxies are trusted by default (`trusted_proxies = []`). Loopback
       addresses (127.0.0.1, ::1) are NOT trusted unless explicitly configured.
    2. Untrusted Peer Defense:
       If the immediate connection peer (`request.client.host`) is not in
       `trusted_proxies`, `X-Forwarded-For` is completely ignored to prevent
       arbitrary clients from spoofing client IPs or bypassing rate limits.
    3. Right-to-Left Traversal Across Proxy Hops:
       Standard reverse proxies (e.g. Nginx, AWS ALB, Cloudflare, Traefik)
       append the incoming client address to the right end of the
       `X-Forwarded-For` header. An attacker can prepend arbitrary forged
       addresses to the header before sending the request. By walking the chain
       backwards (right to left):
       - Known trusted intermediate proxy hops are skipped.
       - The first UNTRUSTED address reached is the legitimate external client
         connecting to our edge perimeter.
       - Any spoofed addresses to the left are never reached or trusted.
    4. Safe Failure & Malformed Chain Handling:
       If `X-Forwarded-For` is missing, empty, contains malformed candidates,
       or consists entirely of trusted proxies, the function falls back safely
       to the immediate connection peer (`request.client.host`).
    """
    if trusted_proxies is None:
        try:
            from app.config import settings

            trusted_proxies = settings.trusted_proxies
        except Exception:
            trusted_proxies = []

    peer_ip = request.client.host if request.client else "unknown"
    if peer_ip == "unknown":
        return "unknown"

    if not is_trusted_proxy(peer_ip, trusted_proxies):
        # Peer is not an explicitly trusted proxy; ignore any forwarded headers
        return peer_ip

    forwarded_for = request.headers.get("x-forwarded-for")
    if not forwarded_for or not forwarded_for.strip():
        return peer_ip

    raw_parts = [p.strip() for p in forwarded_for.split(",")]
    if not raw_parts:
        return peer_ip

    # Walk the forwarded chain from right to left (closest hop to furthest client)
    for part in reversed(raw_parts):
        if not part:
            # Empty token indicates malformed forwarded chain
            return peer_ip

        try:
            ipaddress.ip_address(part)
        except ValueError:
            # Malformed candidate IP in chain; cannot safely interpret trust boundary
            return peer_ip

        if is_trusted_proxy(part, trusted_proxies):
            # Intermediary trusted proxy; continue walking left towards the external client
            continue

        # First untrusted entity in the chain is the legitimate client
        return part

    # Entire chain consisted of trusted proxies; safe fallback to immediate peer
    return peer_ip


class SlidingWindowRateLimiter:
    """Sliding-window in-memory rate limiter with clean reset and header support."""

    def __init__(self) -> None:
        # key -> list of float timestamps
        self._records: dict[str, list[float]] = defaultdict(list)

    def check(self, key: str, max_requests: int, window_seconds: int) -> tuple[bool, int, int]:
        """Check if request is allowed.

        Returns (allowed, remaining, retry_after).
        """
        now = time.time()
        cutoff = now - window_seconds
        # Clean older requests outside the current window
        valid_requests = [t for t in self._records[key] if t > cutoff]
        self._records[key] = valid_requests

        if len(valid_requests) >= max_requests:
            oldest = valid_requests[0]
            retry_after = max(1, int(oldest + window_seconds - now))
            return False, 0, retry_after

        # Record this request
        valid_requests.append(now)
        self._records[key] = valid_requests
        remaining = max_requests - len(valid_requests)
        return True, remaining, 0

    def reset(self) -> None:
        """Clear all records (used in testing)."""
        self._records.clear()


# Global in-memory rate limiter instance
limiter = SlidingWindowRateLimiter()


def rate_limit(
    max_requests: int,
    window_seconds: int,
    key_func: Callable[[Request], str] | None = None,
) -> Callable[[Request], None]:
    """FastAPI dependency factory to enforce rate limits."""

    def dependency(request: Request) -> None:
        # Client IP extraction with trusted proxy verification
        client_ip = get_client_ip(request)

        if key_func:
            custom_key = key_func(request)
            rate_key = f"{request.url.path}:{custom_key}"
        else:
            rate_key = f"{request.url.path}:{client_ip}"

        allowed, _remaining, retry_after = limiter.check(
            key=rate_key,
            max_requests=max_requests,
            window_seconds=window_seconds,
        )

        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": {
                        "code": "RATE_LIMITED",
                        "message": f"Too many requests. Please try again in {retry_after} seconds.",
                        "details": {"retry_after": retry_after},
                    }
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(max_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time() + retry_after)),
                },
            )

    return dependency
