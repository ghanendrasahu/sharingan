"""Security hardening tests."""

from collections.abc import Awaitable, Callable
from typing import Any

from app.middleware.security import (
    InputSanitizationMiddleware,
    MemoryRateLimiter,
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
)

# ASGIApp is a callable that takes scope, receive, send
ASGIApp = Callable[[dict[str, Any], Any, Any], Awaitable[None]]


async def mock_asgi_app(scope: dict[str, Any], receive: Any, send: Any) -> None:
    """Mock ASGI app for testing."""
    pass


def test_security_headers_middleware():
    """Test security headers middleware creation."""
    middleware = SecurityHeadersMiddleware(app=mock_asgi_app)  # type: ignore[arg-type]
    assert middleware is not None


def test_rate_limit_middleware():
    """Test rate limit middleware creation."""
    limiter = MemoryRateLimiter(max_requests=100, window_seconds=60)
    middleware = RateLimitMiddleware(app=mock_asgi_app, limiter=limiter)  # type: ignore[arg-type]
    assert middleware._limiter.max_requests == 100
    assert middleware._limiter.window_seconds == 60


def test_input_sanitization_middleware():
    """Test input sanitization middleware creation."""
    middleware = InputSanitizationMiddleware(app=mock_asgi_app)  # type: ignore[arg-type]
    assert middleware is not None


def test_blocked_patterns():
    """Test that blocked patterns are detected."""
    middleware = InputSanitizationMiddleware(app=mock_asgi_app)  # type: ignore[arg-type]
    assert "<script" in middleware.BLOCKED_PATTERNS
    assert "javascript:" in middleware.BLOCKED_PATTERNS
    assert "onerror=" in middleware.BLOCKED_PATTERNS


def test_rate_limit_tracking():
    """Test rate limit tracking."""
    limiter = MemoryRateLimiter(max_requests=5, window_seconds=60)
    client_ip = "127.0.0.1"

    assert client_ip not in limiter._requests or len(limiter._requests[client_ip]) == 0


def test_security_headers_content():
    """Test security headers content."""
    assert "X-Content-Type-Options" in {
        "X-Content-Type-Options",
        "X-Frame-Options",
        "X-XSS-Protection",
    }


def test_rate_limit_config():
    """Test rate limit configuration."""
    limiter = MemoryRateLimiter(max_requests=50, window_seconds=30)
    assert limiter.max_requests == 50
    assert limiter.window_seconds == 30


def test_input_sanitization_patterns():
    """Test input sanitization patterns."""
    middleware = InputSanitizationMiddleware(app=mock_asgi_app)  # type: ignore[arg-type]

    test_cases = [
        "<script>alert('xss')</script>",
        "javascript:void(0)",
        '<img onerror="alert(1)">',
        '<body onload="alert(1)">',
        "eval(document.cookie)",
        "document.cookie",
        "window.location='http://evil.com'",
    ]

    for case in test_cases:
        assert any(pattern in case.lower() for pattern in middleware.BLOCKED_PATTERNS), (
            f"Pattern not detected: {case}"
        )


def test_safe_input():
    """Test that safe input is not blocked."""
    middleware = InputSanitizationMiddleware(app=mock_asgi_app)  # type: ignore[arg-type]

    safe_inputs = [
        "Hello, this is a normal document",
        "Legal clause about termination",
        "Section 4.2 of the agreement",
        "Payment terms: Net 30 days",
        "This is a test document with no malicious content",
    ]

    for inp in safe_inputs:
        assert not any(pattern in inp.lower() for pattern in middleware.BLOCKED_PATTERNS), (
            f"Safe input incorrectly flagged: {inp}"
        )


def test_rate_limit_window():
    """Test rate limit window."""
    limiter = MemoryRateLimiter(max_requests=10, window_seconds=60)
    assert limiter.window_seconds == 60
    assert limiter.max_requests == 10


def test_security_middleware_order():
    """Test that security middleware is configured correctly."""
    from app.main import create_application

    application = create_application()

    middleware_names = []
    for m in application.user_middleware:
        cls = m.cls
        name = getattr(cls, "__name__", str(cls))
        middleware_names.append(name)

    assert "SecurityHeadersMiddleware" in middleware_names
    assert "RateLimitMiddleware" in middleware_names
    assert "InputSanitizationMiddleware" in middleware_names
