.PHONY: sync test install clean help nats-up nats-down nats-status gen-certs

sync:
	uv sync

test: sync
	uv run pytest tests/ -v

install: sync

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf build/ dist/ *.egg-info/

# Infrastructure targets (delegate to infra/nats)
nats-up:
	@$(MAKE) -C infra/nats up

nats-down:
	@$(MAKE) -C infra/nats down

nats-status:
	@$(MAKE) -C infra/nats status

gen-certs:
	@$(MAKE) -C infra/nats gen-certs

help:
	@echo "Available targets:"
	@echo ""
	@echo "Development:"
	@echo "  sync    - Install dependencies using uv"
	@echo "  test    - Run pytest tests"
	@echo "  install - Install dependencies"
	@echo "  clean   - Clean up cache and build artifacts"
	@echo ""
	@echo "Infrastructure (NATS):"
	@echo "  nats-up    - Start NATS server"
	@echo "  nats-down  - Stop NATS server"
	@echo "  nats-status - Show NATS server status"
	@echo "  gen-certs  - Generate TLS certificates for NATS"
