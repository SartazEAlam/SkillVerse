"""In-memory and Redis-capable sliding-window rate limiter.

Follows SkillVerse specifications:
- Login: 10 attempts per 15 min per IP/email
- Registration: 5 attempts per hour per IP
- Password reset: 3 attempts per hour per email
- OAuth authorization & callback: 10 attempts per 15 min per IP
"""

from __future__ import annotations

import time
from collections import defaultdict
from collections.abc import Callable

from fastapi import HTTPException, Request, status


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
        # Client IP extraction
        client_ip = request.headers.get("x-forwarded-for", "").split(",")[0].strip() or (
            request.client.host if request.client else "unknown"
        )

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
