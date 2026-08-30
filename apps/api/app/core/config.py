"""Application settings loaded from environment variables."""

from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings

_INSECURE_DEFAULTS = frozenset({"change-me-in-production", "minioadmin", ""})


class Settings(BaseSettings):
    """Application settings."""

    # Application
    APP_NAME: str = "LegalLens India"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # Security
    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://legallens:legallens@localhost:5432/legallens"
    DATABASE_ECHO: bool = False

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Object Storage (S3-compatible)
    OBJECT_STORAGE_ENDPOINT: str = "http://localhost:9000"
    OBJECT_STORAGE_ACCESS_KEY: str = "minioadmin"
    OBJECT_STORAGE_SECRET_KEY: str = "minioadmin"
    OBJECT_STORAGE_BUCKET: str = "legallens-documents"
    OBJECT_STORAGE_REGION: str = "us-east-1"

    # LLM
    LLM_PROVIDER: str = "openai"
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "gpt-4o"

    # Groq
    GROQ_API_KEY: str = ""
    # Free tier models (no credit card required)
    GROQ_MODEL: str = "llama-3.1-8b-instant"  # Best free: 30 RPM, 500K TPD, 30K TPM
    # Alternative free models:
    # GROQ_MODEL: str = "llama-3.3-70b-versatile"  # Higher quality, 1K RPD
    # GROQ_MODEL: str = "llama-4-scout-instruct"  # Long context, 30K TPM

    # Embeddings
    EMBEDDING_PROVIDER: str = "openai"
    EMBEDDING_API_KEY: str = ""
    EMBEDDING_MODEL: str = "text-embedding-3-small"

    # Razorpay
    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""
    RAZORPAY_WEBHOOK_SECRET: str = ""

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Upload limits
    MAX_UPLOAD_SIZE_MB: int = 50
    ALLOWED_EXTENSIONS: set[str] = {"pdf", "docx"}

    @model_validator(mode="after")
    def _reject_insecure_defaults(self) -> "Settings":
        """Reject insecure default secrets in production."""
        if self.DEBUG:
            return self

        failures: list[str] = []
        if self.SECRET_KEY in _INSECURE_DEFAULTS:
            failures.append("SECRET_KEY")
        if self.OBJECT_STORAGE_ACCESS_KEY in _INSECURE_DEFAULTS:
            failures.append("OBJECT_STORAGE_ACCESS_KEY")
        if self.OBJECT_STORAGE_SECRET_KEY in _INSECURE_DEFAULTS:
            failures.append("OBJECT_STORAGE_SECRET_KEY")

        if failures:
            joined = ", ".join(failures)
            msg = (
                f"Insecure default values detected for {joined}. "
                "Set proper values via environment variables or .env file. "
                "Set DEBUG=true to bypass this check in development."
            )
            raise ValueError(msg)

        return self

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()
