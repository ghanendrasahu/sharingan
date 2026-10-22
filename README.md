# LegalLens India

Production-grade AI Legal Document Analyzer for Indian Startups.

## Overview

LegalLens India helps startups, freelancers, employees, landlords/tenants, and small businesses understand contracts by identifying risks, missing clauses, obligations, and providing plain-English explanations with relevant Indian legal sources.

**Important:** This tool provides AI-assisted document analysis and general information. It does not constitute legal advice or create a lawyer-client relationship.

## Features

- PDF and DOCX document upload and processing
- AI-powered contract risk analysis with LangGraph
- Document classification (NDA, employment, lease, vendor, etc.)
- Missing clause detection
- Evidence-based risk analysis with legal citations
- Deterministic risk scoring (explainable, not LLM-based)
- Hybrid retrieval (BM25 + vector search)
- Indian legal corpus (Contract Act, Companies Act, IT Act)
- Contract Q&A with document-grounded answers
- Contract version comparison
- Professional PDF report generation
- Multi-tenant organization support
- Usage tracking and billing with Razorpay

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
       │                Celery Workers          │
       │                   │                    │
       └───────────────────┼────────────────────┘
                           ▼
                    Document Processing
                           │
                    Clause Segmentation
                           │
                    LangGraph Analysis Engine
                    ├── Document Classifier
                    ├── Risk Analyzer
                    ├── Missing Clause Detector
                    ├── Legal Retriever
                    ├── Evidence Verifier
                    ├── Risk Scorer
                    ├── Recommendations
                    └── Quality Checker
                           │
                    Hybrid Retrieval (BM25 + Vector)
                           │
                    Indian Legal Corpus
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React, TypeScript, Vite, Tailwind CSS, shadcn/ui |
| Backend | Python 3.11, FastAPI, Pydantic, SQLAlchemy, Alembic |
| Database | PostgreSQL 16 + asyncpg |
| Cache/Queue | Redis 7, Celery |
| Storage | MinIO (S3-compatible) |
| AI | LangGraph, OpenAI/Groq |
| Payments | Razorpay |
| Infrastructure | Docker, Docker Compose |

## Packages

| Package | Description |
|---------|-------------|
| `packages/ai` | LangGraph analysis engine with 8 nodes |
| `packages/legal` | Indian legal corpus (Contract Act, Companies Act, IT Act) |
| `packages/retrieval` | Hybrid BM25 + vector search with reranking |
| `packages/document_processing` | PDF/DOCX extraction and clause segmentation |

## Local Development

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (the repository is a uv workspace - `uv.lock` pins the full dependency graph)
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

# Install Python dependencies (resolved from the workspace lockfile)
uv sync --all-extras --all-packages

# Install Node dependencies
cd apps/web
npm install
cd ../..

# Run database migrations
cd apps/api
uv run alembic upgrade head
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

## Environment Variables

See `apps/api/.env.example` for all required environment variables.

Key variables:
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `OPENAI_API_KEY` or `GROQ_API_KEY` - LLM provider
- `RAZORPAY_KEY_ID` / `RAZORPAY_KEY_SECRET` - Payment processing
- `MINIO_ACCESS_KEY` / `MINIO_SECRET_KEY` - Object storage

## Testing

```bash
# Run all tests (340+ tests)
make test

# Run specific test suites
uv run pytest apps/api/tests/ -q                 # 224 API tests
uv run pytest packages/ai/tests/ -q              # 19 AI tests
uv run pytest packages/legal/tests/ -q           # 10 legal tests
uv run pytest packages/retrieval/tests/ -q       # 9 retrieval tests
uv run pytest packages/document_processing/tests/ -q  # 78 document processing tests
uv run pytest tests/evaluation/ -q               # 6 evaluation tests
```

## CI/CD

GitHub Actions workflow runs:
- Lint (Ruff)
- Unit tests (pytest, installed from `uv.lock`)
- Web lint & build (ESLint + TypeScript + Vite)
- Security scan (Bandit)
- AI evaluation tests
- Docker build (API, worker and web images)

## Security

- Documents are treated as untrusted input
- Tenant isolation is enforced at the API layer
- File uploads are validated by MIME type, extension, and file signature
- Secrets are never committed to the repository

## License

MIT License - see [LICENSE](LICENSE) for details.
