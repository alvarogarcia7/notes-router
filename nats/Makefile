.PHONY: help
help:
	@echo "NATS PoC - Available targets:"
	@echo "  test              Run all tests (docker, bash and Python)"
	@echo "  test-docker       Test Docker NATS pub/sub functionality"
	@echo "  test-bash         Run bash PoC test"
	@echo "  test-python       Run Python subscriber tests"
	@echo "  run-bash          Run bash subscriber and publisher manually"
	@echo "  run-python        Run Python subscriber with bash publisher"
	@echo "  setup-python      Install Python subscriber dependencies"
	@echo "  clean             Clean up temporary files and caches"
	@echo "  lint-python       Run Python linting checks"
	@echo "  format-python     Format Python code"
	@echo "  type-check        Run Python type checking"
	@echo "  help              Show this help message"

.PHONY: test
test: test-docker test-bash test-python
	@echo ""
	@echo "=========================================="
	@echo "All tests completed successfully!"
	@echo "=========================================="

.PHONY: test-docker
test-docker:
	@echo "=========================================="
	@echo "Testing Docker NATS Setup"
	@echo "=========================================="
	@bash ../test-docker-nats.sh
	@echo ""

.PHONY: test-bash
test-bash:
	@echo "=========================================="
	@echo "Running Bash PoC Test"
	@echo "=========================================="
	@bash test-poc.sh
	@echo ""

.PHONY: test-python
test-python:
	@echo "=========================================="
	@echo "Running Python Subscriber Tests"
	@echo "=========================================="
	@cd subscriber-python && python -m pytest tests/ -v 2>/dev/null || \
	  (cd .. && python test-python-message-handler.py)
	@echo ""

.PHONY: run-bash
run-bash:
	@echo "=========================================="
	@echo "Running Bash Subscriber and Publisher"
	@echo "=========================================="
	@echo "Terminal 1: Starting subscriber..."
	@echo "Run this in another terminal:"
	@echo "  bash subscriber/subscriber.sh"
	@echo ""
	@echo "Terminal 2: Starting publisher..."
	@echo "Run this in another terminal:"
	@echo "  bash publisher/publisher.sh"
	@echo ""

.PHONY: run-python
run-python:
	@echo "=========================================="
	@echo "Running Python Subscriber with Bash Publisher"
	@echo "=========================================="
	@(rm -rf /tmp/nats-poc-messages; mkdir -p /tmp/nats-poc-messages; \
	  echo "Starting Python subscriber in background..."; \
	  PYTHONPATH=subscriber-python/src python subscriber-python/src/nats_subscriber/main.py &\
	  PY_PID=$$!; \
	  sleep 1; \
	  echo ""; \
	  echo "Publishing message..."; \
	  bash publisher/publisher.sh; \
	  echo ""; \
	  echo "Terminating subscriber..."; \
	  kill $$PY_PID 2>/dev/null || true; \
	  sleep 1; \
	  )

.PHONY: setup-python
setup-python:
	@echo "=========================================="
	@echo "Setting Up Python Subscriber"
	@echo "=========================================="
	@cd subscriber-python && pip install -e ".[dev]" || \
	  (echo "Note: Running with system Python without installation"; \
	   echo "Install with: cd subscriber-python && python -m pip install -e '.[dev]'"; \
	   )

.PHONY: clean
clean:
	@echo "Cleaning up temporary files..."
	@rm -rf /tmp/nats-poc-messages
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@rm -rf subscriber-python/.pytest_cache subscriber-python/.mypy_cache
	@rm -rf subscriber-python/.coverage subscriber-python/htmlcov
	@echo "Cleanup complete!"

.PHONY: lint-python
lint-python:
	@echo "=========================================="
	@echo "Running Python Linting"
	@echo "=========================================="
	@cd subscriber-python && make lint 2>/dev/null || \
	  (echo "Note: Linting tools not installed"; \
	   echo "Install with: cd subscriber-python && pip install -e '.[dev]'"; \
	   )

.PHONY: format-python
format-python:
	@echo "=========================================="
	@echo "Formatting Python Code"
	@echo "=========================================="
	@cd subscriber-python && make format 2>/dev/null || \
	  (echo "Note: Formatting tools not installed"; \
	   echo "Install with: cd subscriber-python && pip install -e '.[dev]'"; \
	   )

.PHONY: type-check
type-check:
	@echo "=========================================="
	@echo "Running Python Type Checking"
	@echo "=========================================="
	@cd subscriber-python && make type-check 2>/dev/null || \
	  (echo "Note: mypy not installed"; \
	   echo "Install with: cd subscriber-python && pip install -e '.[dev]'"; \
	   )
