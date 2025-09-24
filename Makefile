.PHONY: help setup build start stop restart logs test clean deploy

# Variables
DOCKER_COMPOSE = docker-compose
PYTHON = python3
PROJECT_NAME = face-quality-assessment

# Colors
COLOR_RESET = \033[0m
COLOR_INFO = \033[36m
COLOR_SUCCESS = \033[32m

help: ## Show this help message
	@echo "$(COLOR_INFO)Face Quality Assessment Service - Makefile Commands$(COLOR_RESET)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(COLOR_SUCCESS)%-15s$(COLOR_RESET) %s\n", $$1, $$2}'
	@echo ""

setup: ## Run initial setup
	@echo "$(COLOR_INFO)Running setup...$(COLOR_RESET)"
	@bash scripts/setup.sh

build: ## Build Docker images
	@echo "$(COLOR_INFO)Building Docker images...$(COLOR_RESET)"
	$(DOCKER_COMPOSE) build

build-no-cache: ## Build Docker images without cache
	@echo "$(COLOR_INFO)Building Docker images (no cache)...$(COLOR_RESET)"
	$(DOCKER_COMPOSE) build --no-cache

start: ## Start all services
	@echo "$(COLOR_INFO)Starting services...$(COLOR_RESET)"
	$(DOCKER_COMPOSE) up -d
	@echo "$(COLOR_SUCCESS)Services started successfully!$(COLOR_RESET)"

stop: ## Stop all services
	@echo "$(COLOR_INFO)Stopping services...$(COLOR_RESET)"
	$(DOCKER_COMPOSE) down
	@echo "$(COLOR_SUCCESS)Services stopped successfully!$(COLOR_RESET)"

restart: ## Restart all services
	@echo "$(COLOR_INFO)Restarting services...$(COLOR_RESET)"
	$(DOCKER_COMPOSE) restart

logs: ## View logs
	$(DOCKER_COMPOSE) logs -f

logs-api: ## View API logs
	$(DOCKER_COMPOSE) logs -f face-quality-api

logs-nginx: ## View NGINX logs
	$(DOCKER_COMPOSE) logs -f nginx

status: ## Show service status
	$(DOCKER_COMPOSE) ps

health: ## Check service health
	@curl -s http://localhost/health | python3 -m json.tool

test: ## Run API tests
	@echo "$(COLOR_INFO)Running tests...$(COLOR_RESET)"
	$(PYTHON) scripts/test_api.py

test-unit: ## Run unit tests
	pytest tests/ -v

test-coverage: ## Run tests with coverage
	pytest tests/ -v --cov=app --cov-report=html

shell: ## Open shell in API container
	$(DOCKER_COMPOSE) exec face-quality-api /bin/bash

shell-db: ## Open MongoDB shell
	$(DOCKER_COMPOSE) exec mongodb mongosh

shell-redis: ## Open Redis shell
	$(DOCKER_COMPOSE) exec redis redis-cli

scale: ## Scale worker services (usage: make scale workers=5)
	$(DOCKER_COMPOSE) up -d --scale face-quality-worker-1=$(workers) --scale face-quality-worker-2=$(workers)

clean: ## Clean up containers and volumes
	@echo "$(COLOR_INFO)Cleaning up...$(COLOR_RESET)"
	$(DOCKER_COMPOSE) down -v
	rm -rf logs/* cache/* uploads/* results/*
	@echo "$(COLOR_SUCCESS)Cleanup completed!$(COLOR_RESET)"

clean-all: ## Clean everything including models
	@echo "$(COLOR_INFO)Cleaning everything...$(COLOR_RESET)"
	$(DOCKER_COMPOSE) down -v --rmi all
	rm -rf logs/* cache/* uploads/* results/* models/*
	@echo "$(COLOR_SUCCESS)Full cleanup completed!$(COLOR_RESET)"

backup: ## Backup database and models
	@echo "$(COLOR_INFO)Creating backup...$(COLOR_RESET)"
	mkdir -p backups
	$(DOCKER_COMPOSE) exec -T mongodb mongodump --out /backup
	docker cp $(shell docker-compose ps -q mongodb):/backup ./backups/mongodb-$(shell date +%Y%m%d)
	tar -czf backups/models-$(shell date +%Y%m%d).tar.gz models/
	@echo "$(COLOR_SUCCESS)Backup completed!$(COLOR_RESET)"

restore: ## Restore from backup (usage: make restore date=20240101)
	@echo "$(COLOR_INFO)Restoring backup from $(date)...$(COLOR_RESET)"
	docker cp ./backups/mongodb-$(date) $(shell docker-compose ps -q mongodb):/backup
	$(DOCKER_COMPOSE) exec mongodb mongorestore /backup
	tar -xzf backups/models-$(date).tar.gz
	@echo "$(COLOR_SUCCESS)Restore completed!$(COLOR_RESET)"

lint: ## Run code linting
	flake8 app/ --max-line-length=100
	black app/ --check
	mypy app/

format: ## Format code
	black app/
	isort app/

security-scan: ## Run security scan
	docker scan face-quality-assessment:latest
	pip-audit

deploy-prod: ## Deploy to production
	@echo "$(COLOR_INFO)Deploying to production...$(COLOR_RESET)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		$(DOCKER_COMPOSE) -f docker-compose.yml -f docker-compose.prod.yml up -d; \
		echo "$(COLOR_SUCCESS)Production deployment completed!$(COLOR_RESET)"; \
	fi

update: ## Update services
	git pull
	$(DOCKER_COMPOSE) pull
	$(DOCKER_COMPOSE) up -d
	@echo "$(COLOR_SUCCESS)Services updated!$(COLOR_RESET)"

monitoring: ## Open monitoring dashboards
	@echo "Opening monitoring dashboards..."
	@echo "Prometheus: http://localhost:9090"
	@echo "Grafana: http://localhost:3000"

docs: ## Open API documentation
	@echo "Opening API documentation..."
	@echo "Swagger UI: http://localhost/docs"
	@echo "ReDoc: http://localhost/redoc"

install-dev: ## Install development dependencies
	pip install -r requirements.txt
	pip install pytest pytest-cov black flake8 mypy isort pip-audit

dev: ## Run in development mode
	$(DOCKER_COMPOSE) -f docker-compose.yml -f docker-compose.dev.yml up

gpu-test: ## Test GPU availability
	docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi

init-env: ## Initialize environment file
	@if [ ! -f .env ]; then \
		cp .env.template .env; \
		echo "$(COLOR_SUCCESS).env file created from template$(COLOR_RESET)"; \
		echo "$(COLOR_INFO)Please update the configuration in .env$(COLOR_RESET)"; \
	else \
		echo "$(COLOR_INFO).env file already exists$(COLOR_RESET)"; \
	fi

download-models: ## Download required models
	@echo "$(COLOR_INFO)Downloading models...$(COLOR_RESET)"
	mkdir -p models
	@if [ ! -f models/shape_predictor_68_face_landmarks.dat ]; then \
		wget http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2 -P models/; \
		bunzip2 models/shape_predictor_68_face_landmarks.dat.bz2; \
		echo "$(COLOR_SUCCESS)Models downloaded!$(COLOR_RESET)"; \
	else \
		echo "$(COLOR_INFO)Models already exist$(COLOR_RESET)"; \
	fi

benchmark: ## Run performance benchmark
	@echo "$(COLOR_INFO)Running benchmark...$(COLOR_RESET)"
	@for i in {1..10}; do \
		curl -s -w "Time: %{time_total}s\n" -o /dev/null -X POST http://localhost/api/v1/assess \
			-H "X-API-Key: $$(grep API_KEY .env | cut -d= -f2)" \
			-H "Content-Type: application/json" \
			-d '{"image_base64":"test"}' || true; \
	done
