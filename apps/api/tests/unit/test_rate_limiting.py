"""Rate limiter behavior tests (memory, redis, middleware, prod guard)."""

from __future__ import annotations

from typing import Any

import pytest
from starlette.responses import Response as DownstreamResponse

from app.middleware.security import (
    MemoryRateLimiter,
    RateLimitMiddleware,
    RedisRateLimiter,
    build_rate_limiter,
)


class FakePipeline:
    """Record and replay INCR/EXPIRE against a shared counter store."""

    def __init__(self, store: dict[str, int]) -> None:
        self._store = store
        self._ops: list[tuple[str, Any, ...]] = []

    def incr(self, key: str) -> None:
        self._ops.append(("incr", key))

    def expire(self, key: str, ttl: int) -> None:
        self._ops.append(("expire", key, ttl))

    async def execute(self) -> list[Any]:
        results: list[Any] = []
        for op in self._ops:
            if op[0] == "incr":
                self._store[op[1]] = self._store.get(op[1], 0) + 1
                results.append(self._store[op[1]])
            else:
                results.append(True)
        self._ops = []
        return results


class FakeRedisClient:
    """Minimal redis.asyncio client stand-in backed by FakePipeline."""

    def __init__(self, store: dict[str, int]) -> None:
        self.store = store
        self.fail = False

    def pipeline(self, transaction: bool = False) -> FakePipeline:
        if self.fail:
            msg = "connection refused"
            raise ConnectionError(msg)
        return FakePipeline(self.store)


class _FakeRequest:
    """Starlette Request stand-in carrying a client address."""

    def __init__(self, client_host: str | None) -> None:
        self.client = None if client_host is None else type("Client", (), {"host": client_host})()


class _Callee:
    """Downstream ASGI app that records it was reached."""

    reached = False

    async def __call__(self, request: Any) -> DownstreamResponse:
        self.reached = True
        return DownstreamResponse(status_code=200)


def _redis_limiter(store: dict[str, int], max_requests: int = 2) -> RedisRateLimiter:
    """Build a RedisRateLimiter without touching a real Redis connection."""
    limiter = RedisRateLimiter.__new__(RedisRateLimiter)
    limiter._redis = FakeRedisClient(store)  # type: ignore[attr-defined]
    limiter.max_requests = max_requests
    limiter.window_seconds = 60
    return limiter


@pytest.mark.asyncio
async def test_memory_limiter_blocks_after_quota():
    """Allow the first N requests in the window, block the (N+1)-th."""
    limiter = MemoryRateLimiter(max_requests=3, window_seconds=60)
    ip = "10.0.0.1"

    assert [await limiter.hit(ip) for _ in range(3)] == [True, True, True]
    assert await limiter.hit(ip) is False


@pytest.mark.asyncio
async def test_memory_limiter_window_refresh(monkeypatch: Any):
    """Entries older than the window stop counting, freeing the quota."""
    now = 1_000.0
    monkeypatch.setattr("app.middleware.security.time.time", lambda: now)
    limiter = MemoryRateLimiter(max_requests=2, window_seconds=5)
    ip = "10.0.0.7"

    assert await limiter.hit(ip)
    assert await limiter.hit(ip)
    assert not await limiter.hit(ip)

    now += 6  # advance past window_seconds
    assert await limiter.hit(ip)


@pytest.mark.asyncio
async def test_redis_limiter_shared_counting():
    """A bucket reaching max_requests closes for every caller."""
    store: dict[str, int] = {}
    limiter = _redis_limiter(store, max_requests=2)

    assert await limiter.hit("198.51.100.5")
    assert await limiter.hit("198.51.100.5")
    assert not await limiter.hit("198.51.100.5")

    assert store and all("rate-limit:198.51.100.5:" in key for key in store)


@pytest.mark.asyncio
async def test_middleware_returns_429_with_retry_after():
    """Blocked clients get 429 + Retry-After and never reach the app."""
    middleware = RateLimitMiddleware(
        app=None,  # type: ignore[arg-type]
        limiter=MemoryRateLimiter(max_requests=1, window_seconds=60),
    )
    request = _FakeRequest("203.0.113.9")
    callee = _Callee()

    first = await middleware.dispatch(request, callee)  # type: ignore[arg-type]
    assert first.status_code == 200
    assert callee.reached is True

    callee.reached = False
    second = await middleware.dispatch(request, callee)  # type: ignore[arg-type]
    assert second.status_code == 429
    assert second.headers["Retry-After"] == "60"
    assert callee.reached is False


@pytest.mark.asyncio
async def test_middleware_clientless_requests_limited():
    """Requests without a client address share the 'unknown' bucket."""
    middleware = RateLimitMiddleware(
        app=None,  # type: ignore[arg-type]
        limiter=MemoryRateLimiter(max_requests=1, window_seconds=60),
    )
    request = _FakeRequest(None)

    first = await middleware.dispatch(request, _Callee())  # type: ignore[arg-type]
    second = await middleware.dispatch(request, _Callee())  # type: ignore[arg-type]
    assert first.status_code == 200
    assert second.status_code == 429


@pytest.mark.asyncio
async def test_redis_limiter_fails_open_on_connection_error():
    """Redis outage must not take requests down; it fails open with a warning."""
    store: dict[str, int] = {}
    limiter = _redis_limiter(store)
    limiter._redis.fail = True  # type: ignore[attr-defined]

    assert await limiter.hit("192.0.2.1") is True


@pytest.mark.asyncio
async def test_build_rate_limiter_backend_selection():
    """Factory returns the backend configured on settings."""

    class _Settings:
        RATE_LIMIT_BACKEND = "redis"
        RATE_LIMIT_MAX_REQUESTS = 25
        RATE_LIMIT_WINDOW_SECONDS = 30
        REDIS_URL = "redis://localhost:6379/0"

    redis_limiter = build_rate_limiter(_Settings())  # type: ignore[arg-type]
    assert isinstance(redis_limiter, RedisRateLimiter)
    assert redis_limiter.max_requests == 25

    class _MemSettings(_Settings):
        RATE_LIMIT_BACKEND = "memory"

    assert isinstance(
        build_rate_limiter(_MemSettings()),  # type: ignore[arg-type]
        MemoryRateLimiter,
    )


def test_production_requires_redis_backend():
    """DEBUG=False with the per-worker memory backend must fail fast."""
    from app.core.config import Settings

    with pytest.raises(ValueError, match="RATE_LIMIT_BACKEND"):
        Settings(
            DEBUG=False,
            SECRET_KEY="a-really-secure-production-secret",
            OBJECT_STORAGE_ACCESS_KEY="real-access-key",
            OBJECT_STORAGE_SECRET_KEY="real-secret-key",
            RATE_LIMIT_BACKEND="memory",
        )
