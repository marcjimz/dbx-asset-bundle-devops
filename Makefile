.PHONY: help install test lint format clean validate deploy-dev deploy-stg deploy-prod

# Default target
help:
	@echo "MLOps Pipeline - Available Commands"
	@echo "===================================="
	@echo "make install      - Install dependencies"
	@echo "make test         - Run all tests with coverage"
	@echo "make test-unit    - Run unit tests only"
	@echo "make lint         - Run linting checks"
	@echo "make format       - Format code with Black"
	@echo "make security     - Run security scans"
	@echo "make clean        - Clean temporary files"
	@echo "make validate-dev - Validate DEV bundle"
	@echo "make deploy-dev   - Deploy to DEV environment"
	@echo "make deploy-stg   - Deploy to STG environment"
	@echo "make deploy-prod  - Deploy to PROD environment"
	@echo "make run-training - Run training job in DEV"

# Installation
install:
	pip install -r requirements.txt

# Testing
test:
	pytest tests/ -v --cov=src --cov-report=term --cov-report=html

test-unit:
	pytest tests/unit/ -v

test-integration:
	pytest tests/ -v -m integration

test-smoke:
	pytest tests/ -v -m smoke

# Code Quality
lint:
	flake8 src/ tests/ --max-line-length=100 --exclude=__pycache__
	pylint src/ --disable=C0114,C0115,C0116 || true

format:
	black src/ tests/
	isort src/ tests/

format-check:
	black --check src/ tests/
	isort --check-only src/ tests/

# Security
security:
	bandit -r src/ -f json -o bandit-report.json || true
	bandit -r src/ -f txt
	safety check --json || true
	safety check

secret-scan:
	detect-secrets scan --all-files --force-use-all-plugins \
		--exclude-files '\.git/.*' \
		--exclude-files '\.pytest_cache/.*' \
		--exclude-files '__pycache__/.*' > .secrets.baseline || true

# Cleanup
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete
	find . -type f -name '*.pyo' -delete
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf *.egg-info
	rm -rf dist
	rm -rf build
	rm -rf .tox

# Databricks Bundle Operations
validate-dev:
	databricks bundle validate --target dev

validate-stg:
	databricks bundle validate --target stg

validate-prod:
	databricks bundle validate --target prod

validate-all: validate-dev validate-stg validate-prod

deploy-dev:
	databricks bundle deploy --target dev

deploy-stg:
	databricks bundle deploy --target stg

deploy-prod:
	databricks bundle deploy --target prod

# Run Jobs
run-training:
	databricks bundle run training_job --target dev

run-evaluation:
	databricks bundle run evaluation_job --target dev

run-deployment:
	databricks bundle run deployment_job --target dev

run-pipeline:
	databricks bundle run full_pipeline_job --target dev

# Development Workflow
dev-setup: install validate-dev
	@echo "Development environment ready!"

ci-checks: format-check lint test security
	@echo "All CI checks passed!"

# Release
release:
	@echo "Creating release tag..."
	@read -p "Enter version (e.g., 1.0.0): " version; \
	git tag -a v$$version -m "Release v$$version"; \
	git push origin v$$version
	@echo "Release tag created and pushed!"
