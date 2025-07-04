.PHONY: help install install-dev test test-unit test-integration test-e2e coverage lint format type-check clean build docs examples

help:  ## Show this help message
	@echo "Lightweight Task Runner with DAG Scheduling - Development Commands"
	@echo "=================================================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install package and dependencies
	pip install -r requirements.txt
	pip install -e .

install-dev:  ## Install package with development dependencies
	pip install -r requirements.txt
	pip install -e .[dev]

test:  ## Run all tests
	python -m pytest

test-unit:  ## Run unit tests only
	python -m pytest tests/unit/ -v

test-integration:  ## Run integration tests only
	python -m pytest tests/integration/ -v

test-e2e:  ## Run end-to-end tests only
	python -m pytest tests/e2e/ -v

coverage:  ## Run tests with coverage report
	python -m pytest --cov=task_runner --cov-report=html --cov-report=term-missing

lint:  ## Run linting checks
	flake8 task_runner/ tests/ examples/

format:  ## Format code with Black
	black task_runner/ tests/ examples/

type-check:  ## Run type checking with mypy
	mypy task_runner/

quality: lint type-check  ## Run all code quality checks

clean:  ## Clean build artifacts and cache
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

build:  ## Build package
	python setup.py sdist bdist_wheel

examples:  ## Run example DAGs
	@echo "Running simple example..."
	python -m task_runner.cli run --config examples/simple_dag.json
	@echo "\nRunning complex example..."
	python -m task_runner.cli run --config examples/complex_dag.json

validate-examples:  ## Validate all example configurations
	@echo "Validating example configurations..."
	python -m task_runner.cli validate --config examples/simple_dag.json
	python -m task_runner.cli validate --config examples/complex_dag.json
	python -m task_runner.cli validate --config examples/retry_dag.json
	python -m task_runner.cli validate --config examples/shell_dag.json

visualize-examples:  ## Visualize all example DAGs
	@echo "Simple DAG visualization:"
	python -m task_runner.cli visualize --config examples/simple_dag.json
	@echo "\nComplex DAG visualization:"
	python -m task_runner.cli visualize --config examples/complex_dag.json

dev-setup:  ## Complete development environment setup
	python -m venv venv
	@echo "Virtual environment created. Activate it and run 'make install-dev'"

check: quality test  ## Run all checks (quality + tests)

release-check: clean quality test build  ## Prepare for release (full check + build)

docker-build:  ## Build Docker image (if Dockerfile exists)
	docker build -t task-runner .

docker-run:  ## Run in Docker container
	docker run -it --rm task-runner

benchmark:  ## Run performance benchmarks
	@echo "Running performance benchmarks..."
	@echo "This would run benchmark scripts if implemented"

docs:  ## Generate documentation
	@echo "Documentation generation not implemented yet"
	@echo "README.md contains current documentation"

install-hooks:  ## Install git pre-commit hooks
	@echo "Installing pre-commit hooks..."
	@echo "#!/bin/sh" > .git/hooks/pre-commit
	@echo "make quality" >> .git/hooks/pre-commit
	@chmod +x .git/hooks/pre-commit
	@echo "Pre-commit hooks installed"

demo:  ## Run interactive demo
	@echo "Running interactive demo..."
	python -m task_runner.cli visualize --config examples/simple_dag.json
	@echo "\nPress Enter to run the DAG..."
	@read
	python -m task_runner.cli run --config examples/simple_dag.json

init-project:  ## Initialize new project structure
	@echo "Project already initialized!"
	@echo "Use 'make install-dev' to set up development environment"
