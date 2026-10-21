"""Security middleware for hardening the application."""

from __future__ import annotations

import logging
import time
from collections import defaultdict
from typing import TYPE_CHECKING, Any, ClassVar, Protocol

from fastapi import Request, Response
from redis import asyncio as aioredis
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

if TYPE_CHECKING:
    from app.core.config import Settings

logger = logging.getLogger(__name__)


class RateLimiter(Protocol):
    """Per-client quota keeper. ``hit`` returns True while under quota."""

    window_seconds: int

    async def hit(self, key: str) -> bool: ...


class MemoryRateLimiter:
    """Sliding-window limiter scoped to a single process.

    Counters live in the worker's own memory, so this cannot enforce a
    global quota behind multiple uvicorn workers. Use for development
    and testing only.
    """

    def __init__(self, max_requests: int = 100, window_seconds: int = 60) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)

    async def hit(self, key: str) -> bool:
        now = time.time()
        active = [t for t in self._requests[key] if now - t < self.window_seconds]
        self._requests[key] = active
        if len(active) >= self.max_requests:
            return False
        self._requests[key].append(now)
        return True


class RedisRateLimiter:
    """Fixed-window limiter backed by Redis, shared across all workers.

    Buckets are keyed per client and per window, incremented atomically on
    every request. If Redis is unreachable the limiter fails open (logging
    a warning) so a cache outage never takes the API down.
    """

    def __init__(self, redis_url: str, max_requests: int = 100, window_seconds: int = 60) -> None:
        self._redis = aioredis.from_url(redis_url, decode_responses=True)
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    async def hit(self, key: str) -> bool:
        now = int(time.time())
        bucket = f"rate-limit:{key}:{now // self.window_seconds}"
        ttl = self.window_seconds - (now % self.window_seconds) + 1
        try:
            pipeline = self._redis.pipeline(transaction=False)
            pipeline.incr(bucket)
            pipeline.expire(bucket, ttl)
            counts = await pipeline.execute()
            return int(counts[0]) <= self.max_requests
        except Exception:
            logger.warning("Redis unreachable; rate limiter failing open", exc_info=True)
            return True


def build_rate_limiter(settings: Settings) -> RateLimiter:
    """Create the limiter that matches the configured backend."""
    kwargs = {
        "max_requests": settings.RATE_LIMIT_MAX_REQUESTS,
        "window_seconds": settings.RATE_LIMIT_WINDOW_SECONDS,
    }
    if settings.RATE_LIMIT_BACKEND == "redis":
        return RedisRateLimiter(settings.REDIS_URL, **kwargs)
    return MemoryRateLimiter(**kwargs)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Enforce per-client request quotas via a pluggable limiter."""

    def __init__(self, app: Any, limiter: RateLimiter) -> None:
        super().__init__(app)
        self._limiter = limiter

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        client_ip = request.client.host if request.client else "unknown"

        if not await self._limiter.hit(client_ip):
            return Response(
                content='{"error": "Rate limit exceeded"}',
                status_code=429,
                media_type="application/json",
                headers={"Retry-After": str(self._limiter.window_seconds)},
            )

        return await call_next(request)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to responses."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'"
        )
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"

        return response


class InputSanitizationMiddleware(BaseHTTPMiddleware):
    """Sanitize user input to prevent injection attacks."""

    BLOCKED_PATTERNS: ClassVar[list[str]] = [
        "<script",
        "javascript:",
        "onerror=",
        "onload=",
        "eval(",
        "document.cookie",
        "window.location",
    ]

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method in ("POST", "PUT", "PATCH"):
            body = await request.body()
            body_str = body.decode("utf-8", errors="ignore").lower()

            for pattern in self.BLOCKED_PATTERNS:
                if pattern in body_str:
                    return Response(
                        content='{"error": "Invalid input detected"}',
                        status_code=400,
                        media_type="application/json",
                    )

        return await call_next(request)
