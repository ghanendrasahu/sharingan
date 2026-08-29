"""Unit tests for authentication services."""

from uuid import uuid4

from app.services.auth import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_token_type,
    get_user_id_from_token,
    hash_password,
    verify_password,
)


def test_hash_password():
    """Test password hashing."""
    password = "test_password_123"
    hashed = hash_password(password)
    assert hashed != password
    assert verify_password(password, hashed)


def test_verify_password():
    """Test password verification."""
    password = "secure_password_456"
    hashed = hash_password(password)
    assert verify_password(password, hashed) is True
    assert verify_password("wrong_password", hashed) is False


def test_create_access_token():
    """Test access token creation."""
    user_id = uuid4()
    token = create_access_token(user_id)
    assert isinstance(token, str)
    assert len(token) > 0


def test_create_refresh_token():
    """Test refresh token creation."""
    user_id = uuid4()
    token = create_refresh_token(user_id)
    assert isinstance(token, str)
    assert len(token) > 0


def test_decode_token():
    """Test token decoding."""
    user_id = uuid4()
    token = create_access_token(user_id)
    payload = decode_token(token)
    assert payload is not None
    assert payload["sub"] == str(user_id)
    assert payload["type"] == "access"


def test_decode_invalid_token():
    """Test decoding invalid token."""
    payload = decode_token("invalid_token")
    assert payload is None


def test_get_user_id_from_token():
    """Test extracting user ID from token."""
    user_id = uuid4()
    token = create_access_token(user_id)
    extracted_id = get_user_id_from_token(token)
    assert extracted_id == user_id


def test_get_user_id_from_invalid_token():
    """Test extracting user ID from invalid token."""
    result = get_user_id_from_token("invalid_token")
    assert result is None


def test_get_token_type():
    """Test extracting token type."""
    user_id = uuid4()
    access_token = create_access_token(user_id)
    refresh_token = create_refresh_token(user_id)
    assert get_token_type(access_token) == "access"
    assert get_token_type(refresh_token) == "refresh"


def test_token_expiry():
    """Test that tokens have expiration."""
    from datetime import timedelta

    from jose import jwt

    from app.core.config import get_settings

    settings = get_settings()
    user_id = uuid4()
    token = create_access_token(user_id, expires_delta=timedelta(seconds=1))
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert "exp" in payload
