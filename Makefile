.PHONY: help install dev down build test lint format check clean migrate seed

# Default target
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# =============================================================================
# Setup
# =============================================================================

install: ## Install all dependencies
	cd apps/api && pip install -e ".[dev]"
	cd apps/web && npm install

setup: install ## Full setup (install + env + migrate + seed)
	cp -n apps/api/.env.example apps/api/.env 2>/dev/null || true
	$(MAKE) migrate
	$(MAKE) seed

# =============================================================================
# Development
# =============================================================================

dev: ## Start all services in development mode
	docker compose up -d postgres redis minio
	@echo "Waiting for services..."
	@sleep 5
	cd apps/api && uvicorn app.main:app --reload --port 8000 &
	cd apps/web && npm run dev

dev-docker: ## Start everything in Docker
	docker compose up --build

down: ## Stop all services
	docker compose down

down-clean: ## Stop all services and remove volumes
	docker compose down -v

# =============================================================================
# Database
# =============================================================================

migrate: ## Run database migrations
	cd apps/api && alembic upgrade head

migrate-create: ## Create a new migration (usage: make migrate-create MSG="add users table")
	cd apps/api && alembic revision --autogenerate -m "$(MSG)"

migrate-down: ## Rollback last migration
	cd apps/api && alembic downgrade -1

seed: ## Seed development data
	cd apps/api && python -m app.core.seed

# =============================================================================
# Build
# =============================================================================

build: ## Build all services
	docker compose build

build-web: ## Build web frontend
	cd apps/web && npm run build

# =============================================================================
# Testing
# =============================================================================

test: ## Run all tests
	cd apps/api && pytest -v

test-unit: ## Run unit tests
	cd apps/api && pytest tests/unit -v

test-integration: ## Run integration tests
	cd apps/api && pytest tests/integration -v

test-security: ## Run security tests
	cd apps/api && pytest tests/security -v

test-evaluation: ## Run AI evaluation tests
	cd apps/api && pytest tests/evaluation -v

test-web: ## Run web tests
	cd apps/web && npm run test

test-cov: ## Run tests with coverage
	cd apps/api && pytest --cov=app --cov-report=html --cov-report=term

# =============================================================================
# Code Quality
# =============================================================================

lint: ## Run linting
	cd apps/api && ruff check .
	cd apps/api && mypy .
	cd apps/web && npm run lint

format: ## Format code
	cd apps/api && ruff format .
	cd apps/api && ruff check --fix .
	cd apps/web && npm run format 2>/dev/null || true

check: lint test ## Run all checks (lint + test)

# =============================================================================
# Docker
# =============================================================================

docker-up: ## Start Docker services
	docker compose up -d

docker-down: ## Stop Docker services
	docker compose down

docker-logs: ## View Docker logs
	docker compose logs -f

docker-reset: ## Reset Docker environment
	docker compose down -v --remove-orphans
	docker compose up --build -d

# =============================================================================
# Utilities
# =============================================================================

clean: ## Clean build artifacts
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name node_modules -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true

health: ## Check service health
	@echo "API Health:"
	@curl -s http://localhost:8000/health | python -m json.tool 2>/dev/null || echo "API not running"
	@echo "\nPostgreSQL:"
	@docker compose exec postgres pg_isready -U legallens 2>/dev/null || echo "PostgreSQL not running"
	@echo "\nRedis:"
	@docker compose exec redis redis-cli ping 2>/dev/null || echo "Redis not running"
	@echo "\nMinIO:"
	@curl -s http://localhost:9000/minio/health/live 2>/dev/null && echo "MinIO healthy" || echo "MinIO not running"

logs: ## View API logs
	docker compose logs -f api

logs-worker: ## View worker logs
	docker compose logs -f worker

# =============================================================================
# Pre-commit
# =============================================================================

pre-commit: ## Run pre-commit on all files
	pre-commit run --all-files

pre-commit-install: ## Install pre-commit hooks
	pre-commit install
