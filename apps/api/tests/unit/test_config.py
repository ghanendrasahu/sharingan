"""Unit tests for configuration."""

from app.core.config import Settings, get_settings


def test_settings_defaults():
    """Test default settings values."""
    settings = Settings()
    assert settings.APP_NAME == "LegalLens India"
    assert settings.APP_VERSION == "0.1.0"
    assert settings.API_V1_PREFIX == "/api/v1"
    assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 30
    assert settings.REFRESH_TOKEN_EXPIRE_DAYS == 7
    assert settings.ALGORITHM == "HS256"
    assert settings.MAX_UPLOAD_SIZE_MB == 50
    assert {"pdf", "docx"} == settings.ALLOWED_EXTENSIONS


def test_get_settings_returns_singleton():
    """Test that get_settings returns the same instance."""
    settings1 = get_settings()
    settings2 = get_settings()
    assert settings1 is settings2
