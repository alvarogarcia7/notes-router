.PHONY: help install test run clean lint format type-check

help:
	@echo "NATS Subscriber Python - Available targets:"
	@echo "  install       Install dependencies"
	@echo "  test          Run tests"
	@echo "  run           Run subscriber"
	@echo "  lint          Run linting checks"
	@echo "  format        Format code"
	@echo "  type-check    Run type checking"
	@echo "  clean         Clean up temporary files"
	@echo "  help          Show this help message"

install:
	pip install -e ".[dev]"

test:
	pytest

run:
	python -m nats_subscriber.main

lint:
	flake8 src tests --max-line-length=100
	isort --check-only src tests

format:
	black src tests
	isort src tests

type-check:
	mypy src

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .mypy_cache .coverage htmlcov dist build *.egg-info
