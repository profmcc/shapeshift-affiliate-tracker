.PHONY: help install install-dev test lint format type-check clean run clean-all

help: ## Show this help message
	@echo "ShapeShift Affiliate Listener - Development Commands"
	@echo "=================================================="
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install production dependencies
	pip install -r requirements.txt

install-dev: ## Install development dependencies
	pip install -r requirements.txt[dev]
	pre-commit install

test: ## Run tests with pytest
	pytest -v --cov=src --cov-report=term-missing

test-watch: ## Run tests in watch mode
	pytest -v --cov=src --cov-report=term-missing -f

lint: ## Run linting with ruff
	ruff check .
	ruff format --check .

format: ## Format code with black and ruff
	black .
	ruff format .

type-check: ## Run type checking with mypy
	mypy src/

check: ## Run all quality checks (lint, format, type-check)
	@echo "Running all quality checks..."
	@make lint
	@make type-check
	@echo "All checks passed! ✅"

clean: ## Clean Python cache files
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +

clean-all: clean ## Clean all generated files including build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf .eggs/
	rm -rf .tox/
	rm -rf htmlcov/
	rm -f .coverage
	rm -f coverage.xml

run: ## Run the main listener (example)
	python -m shapeshift_listener.affiliate_fee --chain arbitrum --from-block 22222222 --sink stdout

run-debug: ## Run with debug logging
	LOG_LEVEL=DEBUG python -m shapeshift_listener.affiliate_fee --chain arbitrum --from-block 22222222 --sink stdout

setup: install-dev ## Complete development setup
	@echo "Setting up development environment..."
	@echo "✅ Dependencies installed"
	@echo "✅ Pre-commit hooks installed"
	@echo "✅ Development environment ready!"

ci: ## Run CI checks locally
	@echo "Running CI checks locally..."
	@make check
	@make test
	@echo "All CI checks passed! 🚀"

docker-build: ## Build Docker image
	docker build -t shapeshift-listener .

docker-run: ## Run Docker container
	docker run -it --rm -v $(PWD)/data:/app/data shapeshift-listener

release: ## Prepare a new release
	@echo "Preparing release..."
	@echo "1. Update version in pyproject.toml"
	@echo "2. Update CHANGELOG.md"
	@echo "3. Run: make ci"
	@echo "4. Create git tag"
	@echo "5. Push to GitHub"
	@echo "6. Create GitHub release"

.PHONY: help install install-dev test lint format type-check clean run clean-all setup ci docker-build docker-run release

