# OpsPilot Makefile
# ==========================================
# Development and deployment automation

.PHONY: help up down dev logs build test clean ps shell migrate seed lint format

# Default target
.DEFAULT_GOAL := help

# Colors for output
CYAN := \033[36m
GREEN := \033[32m
YELLOW := \033[33m
RED := \033[31m
RESET := \033[0m

# Docker compose files
COMPOSE_DEV := docker/docker-compose.yml
COMPOSE_PROD := docker/docker-compose.prod.yml

# ==========================================
# Help
# ==========================================

help: ## Show this help message
	@echo "$(CYAN)OpsPilot - Development Commands$(RESET)"
	@echo "=================================="
	@awk 'BEGIN {FS = ":.*##"; printf ""} /^[a-zA-Z_-]+:.*?##/ { printf "  $(GREEN)%-15s$(RESET) %s\n", $$1, $$2 }' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(YELLOW)Examples:$(RESET)"
	@echo "  make up          # Start all services"
	@echo "  make dev         # Start in development mode with logs"
	@echo "  make logs        # Follow all logs"
	@echo "  make shell s=backend  # Open shell in backend container"

# ==========================================
# Docker Operations
# ==========================================

up: ## Start all services in background
	@echo "$(CYAN)Starting OpsPilot services...$(RESET)"
	docker-compose -f $(COMPOSE_DEV) up -d
	@echo "$(GREEN)Services started!$(RESET)"
	@echo "  Frontend: http://localhost:5173"
	@echo "  Backend:  http://localhost:8000"
	@echo "  Milvus:   http://localhost:19530"

down: ## Stop all services
	@echo "$(CYAN)Stopping OpsPilot services...$(RESET)"
	docker-compose -f $(COMPOSE_DEV) down
	@echo "$(GREEN)Services stopped$(RESET)"

dev: ## Start development mode with logs
	@echo "$(CYAN)Starting OpsPilot in development mode...$(RESET)"
	docker-compose -f $(COMPOSE_DEV) up --build

dev-detach: ## Start development mode in background
	@echo "$(CYAN)Starting OpsPilot in development mode (detached)...$(RESET)"
	docker-compose -f $(COMPOSE_DEV) up -d --build
	@make logs

logs: ## Follow all service logs
	docker-compose -f $(COMPOSE_DEV) logs -f

logs-backend: ## Follow backend logs only
	docker-compose -f $(COMPOSE_DEV) logs -f backend

logs-frontend: ## Follow frontend logs only
	docker-compose -f $(COMPOSE_DEV) logs -f frontend

ps: ## Show running containers
	docker-compose -f $(COMPOSE_DEV) ps

restart: ## Restart all services
	@echo "$(CYAN)Restarting OpsPilot services...$(RESET)"
	docker-compose -f $(COMPOSE_DEV) restart

restart-backend: ## Restart backend service only
	docker-compose -f $(COMPOSE_DEV) restart backend

restart-frontend: ## Restart frontend service only
	docker-compose -f $(COMPOSE_DEV) restart frontend

# ==========================================
# Build Operations
# ==========================================

build: ## Build all Docker images
	@echo "$(CYAN)Building Docker images...$(RESET)"
	docker-compose -f $(COMPOSE_DEV) build
	@echo "$(GREEN)Build completed$(RESET)"

build-backend: ## Build backend image only
	docker-compose -f $(COMPOSE_DEV) build backend

build-frontend: ## Build frontend image only
	docker-compose -f $(COMPOSE_DEV) build frontend

build-sandbox: ## Build sandbox image only
	docker-compose -f $(COMPOSE_DEV) build sandbox

build-prod: ## Build production images
	@echo "$(CYAN)Building production images...$(RESET)"
	docker-compose -f $(COMPOSE_PROD) build
	@echo "$(GREEN)Production build completed$(RESET)"

build-no-cache: ## Build all images without cache
	docker-compose -f $(COMPOSE_DEV) build --no-cache

# ==========================================
# Production Operations
# ==========================================

prod-up: ## Start production environment
	@echo "$(CYAN)Starting production environment...$(RESET)"
	docker-compose -f $(COMPOSE_PROD) up -d
	@echo "$(GREEN)Production environment started$(RESET)"

prod-down: ## Stop production environment
	docker-compose -f $(COMPOSE_PROD) down

prod-logs: ## Follow production logs
	docker-compose -f $(COMPOSE_PROD) logs -f

# ==========================================
# Database Operations
# ==========================================

migrate: ## Run database migrations
	@echo "$(CYAN)Running database migrations...$(RESET)"
	docker-compose -f $(COMPOSE_DEV) exec backend alembic upgrade head

migrate-create: ## Create new migration (usage: make migrate-create m="migration message")
	docker-compose -f $(COMPOSE_DEV) exec backend alembic revision --autogenerate -m "$(m)"

migrate-down: ## Rollback last migration
	docker-compose -f $(COMPOSE_DEV) exec backend alembic downgrade -1

seed: ## Seed database with initial data
	@echo "$(CYAN)Seeding database...$(RESET)"
	docker-compose -f $(COMPOSE_DEV) exec backend python -m app.db.seed

db-shell: ## Open PostgreSQL shell
	docker-compose -f $(COMPOSE_DEV) exec postgres psql -U opspilot -d opspilot

db-backup: ## Backup database
	@echo "$(CYAN)Backing up database...$(RESET)"
	@mkdir -p backups
	docker-compose -f $(COMPOSE_DEV) exec postgres pg_dump -U opspilot opspilot > backups/backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "$(GREEN)Backup created$(RESET)"

# ==========================================
# Testing
# ==========================================

test: ## Run all tests
	@echo "$(CYAN)Running tests...$(RESET)"
	docker-compose -f $(COMPOSE_DEV) exec backend pytest -v

test-cov: ## Run tests with coverage
	docker-compose -f $(COMPOSE_DEV) exec backend pytest --cov=app --cov-report=html

test-watch: ## Run tests in watch mode
	docker-compose -f $(COMPOSE_DEV) exec backend pytest-watch

test-frontend: ## Run frontend tests
	docker-compose -f $(COMPOSE_DEV) exec frontend npm test

# ==========================================
# Code Quality
# ==========================================

lint: ## Run linters
	@echo "$(CYAN)Running linters...$(RESET)"
	docker-compose -f $(COMPOSE_DEV) exec backend flake8 app/
	docker-compose -f $(COMPOSE_DEV) exec backend mypy app/
	docker-compose -f $(COMPOSE_DEV) exec frontend npm run lint

format: ## Format code
	@echo "$(CYAN)Formatting code...$(RESET)"
	docker-compose -f $(COMPOSE_DEV) exec backend black app/
	docker-compose -f $(COMPOSE_DEV) exec backend isort app/
	docker-compose -f $(COMPOSE_DEV) exec frontend npm run format

security: ## Run security checks
	@echo "$(CYAN)Running security checks...$(RESET)"
	docker-compose -f $(COMPOSE_DEV) exec backend bandit -r app/
	docker-compose -f $(COMPOSE_DEV) exec backend safety check

# ==========================================
# Shell Access
# ==========================================

shell: ## Open shell in container (usage: make shell s=backend)
	docker-compose -f $(COMPOSE_DEV) exec $(s) /bin/sh

shell-backend: ## Open shell in backend container
	docker-compose -f $(COMPOSE_DEV) exec backend /bin/bash

shell-frontend: ## Open shell in frontend container
	docker-compose -f $(COMPOSE_DEV) exec frontend /bin/sh

shell-sandbox: ## Open shell in sandbox container
	docker-compose -f $(COMPOSE_DEV) exec sandbox /bin/bash

redis-cli: ## Open Redis CLI
	docker-compose -f $(COMPOSE_DEV) exec redis redis-cli

# ==========================================
# Cleanup
# ==========================================

clean: ## Remove all containers and volumes
	@echo "$(RED)Warning: This will remove all data!$(RESET)"
	@read -p "Are you sure? [y/N] " confirm && [ "$$confirm" = "y" ] || exit 1
	docker-compose -f $(COMPOSE_DEV) down -v --remove-orphans
	@echo "$(GREEN)Cleanup completed$(RESET)"

clean-images: ## Remove all project images
	docker-compose -f $(COMPOSE_DEV) down --rmi all

prune: ## Remove unused Docker resources
	docker system prune -f
	docker volume prune -f

# ==========================================
# Setup
# ==========================================

init: ## Initialize project (first time setup)
	@echo "$(CYAN)Initializing OpsPilot...$(RESET)"
	@if [ ! -f .env ]; then cp .env.example .env; echo "$(GREEN)Created .env from template$(RESET)"; fi
	@mkdir -p src/backend src/frontend
	@make build
	@make up
	@echo "$(GREEN)OpsPilot initialized!$(RESET)"

setup-dirs: ## Create required directories
	@mkdir -p src/backend/app
	@mkdir -p src/frontend/src
	@mkdir -p docker/init-scripts
	@mkdir -p docker/nginx
	@mkdir -p backups
	@echo "$(GREEN)Directories created$(RESET)"

# ==========================================
# Utility
# ==========================================

version: ## Show version info
	@echo "$(CYAN)OpsPilot Version Info$(RESET)"
	@docker --version
	@docker-compose --version

health: ## Check service health
	@echo "$(CYAN)Checking service health...$(RESET)"
	@curl -s http://localhost:8000/health || echo "$(RED)Backend: DOWN$(RESET)"
	@curl -s http://localhost:5173 > /dev/null && echo "$(GREEN)Frontend: UP$(RESET)" || echo "$(RED)Frontend: DOWN$(RESET)"
	@docker-compose -f $(COMPOSE_DEV) exec -T redis redis-cli ping > /dev/null && echo "$(GREEN)Redis: UP$(RESET)" || echo "$(RED)Redis: DOWN$(RESET)"
	@docker-compose -f $(COMPOSE_DEV) exec -T postgres pg_isready -U opspilot > /dev/null && echo "$(GREEN)Postgres: UP$(RESET)" || echo "$(RED)Postgres: DOWN$(RESET)"
