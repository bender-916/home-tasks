.PHONY: help install run test build docker-build docker-run helm-install clean

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install Python dependencies
	cd backend && pip install -r requirements.txt

run: ## Run the development server
	cd backend && FLASK_ENV=development python wsgi.py

test: ## Run tests
	cd backend && pytest tests/ -v

test-cov: ## Run tests with coverage
	cd backend && pytest tests/ -v --cov=app --cov-report=html

docker-build: ## Build Docker image
	docker build -f docker/Dockerfile -t home-tasks:latest .

docker-run: ## Run Docker container
	docker run -p 5000:5000 -v home-tasks-data:/data home-tasks:latest

docker-compose-up: ## Start with docker-compose
	docker-compose up --build

docker-compose-down: ## Stop docker-compose
	docker-compose down

helm-install: ## Install Helm chart
	helm install home-tasks ./k8s/helm/home-tasks --namespace home-tasks --create-namespace

helm-uninstall: ## Uninstall Helm chart
	helm uninstall home-tasks --namespace home-tasks

helm-upgrade: ## Upgrade Helm chart
	helm upgrade home-tasks ./k8s/helm/home-tasks --namespace home-tasks

clean: ## Clean up generated files
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/ .coverage

seed: ## Seed database with sample data
	cd backend && python ../scripts/seed-data.py
