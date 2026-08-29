# LegalLens India

Production-grade AI Legal Document Analyzer for Indian Startups.

## Overview

LegalLens India helps startups, freelancers, employees, landlords/tenants, and small businesses understand contracts by identifying risks, missing clauses, obligations, and providing plain-English explanations with relevant Indian legal sources.

**Important:** This tool provides AI-assisted document analysis and general information. It does not constitute legal advice or create a lawyer-client relationship.

## Features

- PDF and DOCX document upload and processing
- AI-powered contract risk analysis
- Missing clause detection
- Key obligation extraction
- Contract Q&A
- Contract version comparison
- Professional PDF report generation
- Multi-tenant organization support
- Usage tracking and billing

## Architecture

```
                    React (Vite + TypeScript)
                           │
                           ▼
                    FastAPI (Python 3.11)
                           │
       ┌───────────────────┼────────────────────┐
       │                   │                    │
       ▼                   ▼                    ▼
 PostgreSQL              Redis              S3/MinIO
 (pgvector)                                    │
       │                   │                    │
       │                   ▼                    │
       │                Workers                 │
       │                   │                    │
       └───────────────────┼────────────────────┘
                           ▼
                    Document Engine
                           │
                    Clause Segmentation
                           │
                    LangGraph Engine
                           │
                    Legal RAG Engine
                           │
                    Indian Legal Corpus
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React, TypeScript, Vite, Tailwind CSS, shadcn/ui |
| Backend | Python 3.11, FastAPI, Pydantic, SQLAlchemy, Alembic |
| Database | PostgreSQL 16 + pgvector |
| Cache/Queue | Redis 7 |
| Storage | MinIO (S3-compatible) |
| AI | LangGraph, OpenAI/Anthropic |
| Workers | Celery |
| Infrastructure | Docker, Docker Compose |

## Local Development

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker & Docker Compose
- Git

### Quick Start

```bash
# Clone the repository
git clone https://github.com/ghanendrasahu/sharingan.git
cd sharingan

# Copy environment file
cp apps/api/.env.example apps/api/.env

# Start infrastructure services
docker compose up -d postgres redis minio

# Install Python dependencies
cd apps/api
pip install -e ".[dev]"
cd ../..

# Install Node dependencies
cd apps/web
npm install
cd ../..

# Run database migrations
cd apps/api
alembic upgrade head
cd ../..

# Start development servers
make dev
```

### Docker Development

```bash
# Start everything in Docker
docker compose up --build

# Or start infrastructure only
docker compose up -d postgres redis minio
```

### Available Commands

```bash
make help           # Show all available commands
make dev            # Start development servers
make test           # Run all tests
make lint           # Run linting
make format         # Format code
make check          # Run lint + tests
make migrate        # Run database migrations
make seed           # Seed development data
make health         # Check service health
make docker-reset   # Reset Docker environment
```

## Environment Variables

See `apps/api/.env.example` for all required environment variables.

Key variables:
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `LLM_API_KEY` - OpenAI/Anthropic API key
- `RAZORPAY_KEY_ID` / `RAZORPAY_KEY_SECRET` - Payment processing

## Project Structure

```
legallens-india/
├── apps/
│   ├── api/           # FastAPI backend
│   └── web/           # React frontend
├── packages/
│   ├── ai/            # LLM abstraction, LangGraph
│   ├── legal/         # Legal knowledge, citations
│   ├── document_processing/  # PDF/DOCX extraction
│   ├── retrieval/     # RAG, vector search
│   └── shared/        # Common utilities
├── workers/
│   ├── document_worker/   # Document processing tasks
│   └── analysis_worker/   # Analysis pipeline tasks
├── infrastructure/
│   ├── docker/        # Dockerfiles
│   ├── nginx/         # Reverse proxy config
│   └── terraform/     # Cloud infrastructure
├── data/
│   ├── raw/           # Raw documents (gitignored)
│   ├── processed/     # Processed data (gitignored)
│   └── evaluation/    # Test datasets
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── security/
│   └── evaluation/
├── docs/              # Documentation
├── scripts/           # Utility scripts
├── docker-compose.yml
├── Makefile
└── pyproject.toml
```

## API Documentation

When running in development mode, API documentation is available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Testing

```bash
# Run all tests
make test

# Run with coverage
make test-cov

# Run specific test categories
make test-unit
make test-integration
make test-security
make test-evaluation
```

## Deployment

See `docs/deployment.md` for production deployment instructions.

## Security

- Documents are treated as untrusted input
- Tenant isolation is enforced at the API layer
- File uploads are validated by MIME type, extension, and file signature
- Secrets are never committed to the repository
- See `docs/security.md` for details

## Limitations

- AI analysis is not a substitute for professional legal advice
- Legal information may not reflect the most recent changes in law
- Jurisdiction-specific nuances may require local legal expertise
- Complex documents may require manual review

## License

MIT License - see [LICENSE](LICENSE) for details.
