.PHONY: help lint format test security evaluate build deploy

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

lint: ## Run linting
	ruff check apps/api/ packages/document_processing/ --config pyproject.toml
	ruff format --check apps/api/ packages/document_processing/ --config pyproject.toml

format: ## Format code
	ruff check apps/api/ packages/document_processing/ --config pyproject.toml --fix
	ruff format apps/api/ packages/document_processing/ --config pyproject.toml

test: ## Run tests
	python -m pytest apps/api/tests/unit/ packages/document_processing/tests/ -v

test-cov: ## Run tests with coverage
	python -m pytest apps/api/tests/unit/ packages/document_processing/tests/ \
		--cov=apps/api --cov=packages/document_processing \
		--cov-report=html --cov-report=term-missing -v

security: ## Run security scan
	bandit -r apps/api/ -f json -o bandit-report.json || true
	safety check --output json > safety-report.json || true

evaluate: ## Run AI evaluation
	python -m pytest apps/api/tests/unit/test_evaluation.py -v

build: ## Build Docker images
	docker compose build

up: ## Start services
	docker compose up -d

down: ## Stop services
	docker compose down

logs: ## View logs
	docker compose logs -f

migrate: ## Run database migrations
	docker compose exec api python -m alembic upgrade head

seed: ## Seed database
	docker compose exec api python -m app.db.seed
