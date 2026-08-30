"""Authentication services - password hashing and JWT tokens."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import bcrypt
import redis.asyncio as aioredis
from jose import JWTError, jwt

from app.core.config import get_settings

settings = get_settings()

_token_blacklist: aioredis.Redis | None = None


def _get_blacklist() -> aioredis.Redis:
    """Get or create the Redis connection for token blacklisting."""
    global _token_blacklist
    if _token_blacklist is None:
        _token_blacklist = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    return _token_blacklist


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except Exception:
        return False


def create_access_token(user_id: UUID, expires_delta: timedelta | None = None) -> str:
    """Create an access token with jti and iat claims."""
    expire = datetime.now(UTC) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode: dict[str, str | UUID | datetime | float] = {
        "sub": str(user_id),
        "exp": expire,
        "iat": datetime.now(UTC),
        "jti": str(uuid4()),
        "type": "access",
    }
    return str(jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM))


def create_refresh_token(user_id: UUID, expires_delta: timedelta | None = None) -> str:
    """Create a refresh token with jti and iat claims."""
    expire = datetime.now(UTC) + (
        expires_delta or timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    to_encode: dict[str, str | UUID | datetime | float] = {
        "sub": str(user_id),
        "exp": expire,
        "iat": datetime.now(UTC),
        "jti": str(uuid4()),
        "type": "refresh",
    }
    return str(jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM))


def decode_token(token: str) -> dict[str, Any] | None:
    """Decode and validate a JWT token."""
    try:
        payload: dict[str, Any] = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None


def get_user_id_from_token(token: str) -> UUID | None:
    """Extract user ID from a token."""
    payload = decode_token(token)
    if payload is None:
        return None
    user_id = payload.get("sub")
    if user_id is None:
        return None
    try:
        return UUID(user_id)
    except ValueError:
        return None


def get_token_type(token: str) -> str | None:
    """Extract token type from a token."""
    payload = decode_token(token)
    if payload is None:
        return None
    return payload.get("type")


async def blacklist_token(token: str) -> bool:
    """Add a token's jti to the Redis blacklist until its expiry.

    Returns True if blacklisted, False if token had no jti or blacklist unavailable.
    """
    payload = decode_token(token)
    if payload is None:
        return False

    jti = payload.get("jti")
    if jti is None:
        return False

    exp = payload.get("exp")
    if exp is None:
        return False

    # Calculate TTL: time until token expires
    if isinstance(exp, datetime):
        ttl_seconds = int((exp - datetime.now(UTC)).total_seconds())
    else:
        ttl_seconds = int(exp - datetime.now(UTC).timestamp())

    if ttl_seconds <= 0:
        return False

    try:
        r = _get_blacklist()
        await r.setex(f"token:blacklist:{jti}", ttl_seconds, "1")
        return True
    except Exception:
        return False


async def is_token_blacklisted(token: str) -> bool:
    """Check if a token's jti is in the Redis blacklist."""
    payload = decode_token(token)
    if payload is None:
        return False

    jti = payload.get("jti")
    if jti is None:
        return False

    try:
        r = _get_blacklist()
        return await r.exists(f"token:blacklist:{jti}") > 0
    except Exception:
        # If Redis is down, don't block the request (fail open)
        return False
