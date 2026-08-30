# Production Dockerfile for API
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies from pyproject.toml
FROM base AS deps

COPY apps/api/pyproject.toml .
COPY packages/document_processing/pyproject.toml /app/packages/document_processing/pyproject.toml
COPY packages/document_processing/legallens_docproc/__init__.py /app/packages/document_processing/legallens_docproc/__init__.py
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e ".[dev]" 2>/dev/null || \
    pip install --no-cache-dir fastapi uvicorn[standard] pydantic pydantic-settings \
        sqlalchemy alembic asyncpg psycopg2-binary redis celery[redis] \
        python-jose[cryptography] passlib[bcrypt] python-multipart \
        httpx structlog prometheus-client boto3 mangum openai \
        pytest pytest-asyncio pytest-cov ruff mypy pre-commit email-validator

# Production image
FROM base AS production

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home --shell /bin/bash appuser

WORKDIR /app

# Copy installed packages from deps
COPY --from=deps /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin

# Copy application code
COPY apps/api/app ./app
COPY packages/document_processing/legallens_docproc ./packages/document_processing/legallens_docproc

# Set ownership
RUN chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
