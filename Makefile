.PHONY: help build up up-build down restart logs exec shell shell-api shell-worker shell-db shell-redis migrate upgrade downgrade test test-cov generate-docs clean

.DEFAULT_GOAL := help

# ============================================================================
# ProClaim — Convenient Make Commands
# ============================================================================

## Build Docker images without cache
build:
	@echo "Building Docker images without cache..."
	docker compose build --no-cache

## Start all services and rebuild images
up-build:
	@echo "Building and starting all services..."
	docker compose up --build

## Start all services (detached)
up:
	@echo "Starting all services in detached mode..."
	docker compose up -d

## Stop all services
down:
	@echo "Stopping all services..."
	docker compose down

## Restart all services
restart:
	@echo "Restarting all services..."
	docker compose restart

## View logs from a specific service (usage: make logs SERVICE=api)
logs:
	docker compose logs -f $(SERVICE)

## Execute command in api container (usage: make exec CMD="alembic current")
exec:
	docker compose exec api $(CMD)

## Open interactive shell in API container
shell-api:
	docker compose exec api /bin/bash

## Open interactive shell in Worker container
shell-worker:
	docker compose exec worker /bin/bash

## Open PostgreSQL interactive shell
shell-db:
	docker compose exec db psql -U proclaim -d proclaim

## Open Redis CLI
shell-redis:
	docker compose exec redis redis-cli

# ============================================================================
# Database Migrations (Alembic)
# ============================================================================

## Auto-generate new migration (usage: make migrate MSG="add users table")
migrate:
	@echo "Auto-generating Alembic migration..."
	docker compose exec api alembic revision --autogenerate -m "$(MSG)"

## Run all pending migrations (upgrade to head)
upgrade:
	@echo "Running Alembic migrations (upgrade head)..."
	docker compose exec api alembic upgrade head

## Downgrade migrations by 1 revision
downgrade:
	@echo "Downgrading Alembic migrations by 1 revision..."
	docker compose exec api alembic downgrade -1

# ============================================================================
# Testing
# ============================================================================

## Run backend tests

test:
	@echo "Running backend tests..."
	docker compose exec api pytest -q

## Run backend tests with coverage
test-cov:
	@echo "Running backend tests with coverage..."
	docker compose exec api pytest -q --cov=app --cov-report=term-missing

# ============================================================================
# Utilities
# ============================================================================

## Generate mock test documents (PDFs) for extraction testing
generate-docs:
	@echo "Generating mock test documents..."
	cd backend && python scripts/generate_test_docs.py

## Clean up Docker resources (containers, volumes, networks)
clean:
	@echo "Cleaning up Docker resources..."
	docker compose down -v --remove-orphans
	docker system prune -f

## Show available commands
help:
	@echo "ProClaim Makefile Commands"
	@echo "=========================="
	@echo ""
	@echo "Docker Compose:"
	@echo "  make build              Build all images (no cache)"
	@echo "  make up-build           Build and start all services"
	@echo "  make up                 Start all services (detached)"
	@echo "  make down               Stop all services"
	@echo "  make restart            Restart all services"
	@echo "  make logs SERVICE=...   Tail logs for a service (api|worker|db|redis|frontend)"
	@echo ""
	@echo "Shell / Exec:"
	@echo "  make shell-api          Bash into API container"
	@echo "  make shell-worker       Bash into Worker container"
	@echo "  make shell-db           psql into PostgreSQL"
	@echo "  make shell-redis        redis-cli into Redis"
	@echo "  make exec CMD=...       Run a command in API container"
	@echo ""
	@echo "Database Migrations:"
	@echo "  make migrate MSG=...    Auto-generate Alembic migration"
	@echo "  make upgrade            Run migrations (upgrade head)"
	@echo "  make downgrade          Downgrade 1 revision"
	@echo ""
	@echo "Testing:"
	@echo "  make test               Run pytest"
	@echo "  make test-cov           Run pytest with coverage"
	@echo ""
	@echo "Utilities:"
	@echo "  make generate-docs      Create mock PDFs for extraction testing"
	@echo "  make clean              Remove containers, volumes, and prune"
	@echo "  make help               Show this message"
