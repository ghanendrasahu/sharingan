# Production Dockerfile for API
FROM python:3.11-slim AS deps

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# The build toolchain stays in this stage; the runtime image never sees it.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Runtime dependencies come straight from pyproject.toml (excluding the local
# path dependency, which is installed from source below). No `|| fallback`
# install: a build failure must fail the build, and no dev tooling is shipped.
COPY apps/api/pyproject.toml ./pyproject.toml
COPY packages/document_processing ./packages/document_processing
RUN python -c "import tomllib; deps = tomllib.load(open('pyproject.toml', 'rb'))['project']['dependencies']; print('\n'.join(d for d in deps if 'file:' not in d))" > requirements.txt \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir "./packages/document_processing[all]"

# Production image
FROM python:3.11-slim AS production

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Only the runtime shared library for psycopg2/asyncpg.
RUN apt-get update && apt-get install -y --no-install-recommends libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home --shell /bin/bash appuser

WORKDIR /app

# Copy installed packages (legallens_docproc included) from deps
COPY --from=deps /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin

# Copy application code
COPY apps/api/app ./app

# Set ownership
RUN chown -R appuser:appuser /app
USER appuser

# Health check: python stdlib instead of shipping curl just for probes
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=5)" || exit 1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
