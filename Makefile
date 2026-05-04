.PHONY: sync
## Install dependencies using uv
sync:
	uv sync

.PHONY: test
## Run pytest tests
test: sync
	uv run pytest tests/ -v

.PHONY: install
## Install dependencies
install: sync

.PHONY: clean
## Clean up cache and build artifacts
clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf build/ dist/ *.egg-info/

.PHONY: nats-up
## Start NATS server
nats-up:
	@$(MAKE) -C infra/nats up

.PHONY: nats-down
## Stop NATS server
nats-down:
	@$(MAKE) -C infra/nats down

.PHONY: nats-status
## Show NATS server status
nats-status:
	@$(MAKE) -C infra/nats status

.PHONY: gen-certs
## Generate TLS certificates for NATS
gen-certs:
	@$(MAKE) -C infra/nats gen-certs

.PHONY: help
## Show this help message
help:
	@awk '/^\.PHONY:/ { target=$$(NF) } /^## / { gsub(/^## /, ""); print "  " target ": " $$0 }' $(MAKEFILE_LIST) | sort

.DEFAULT_GOAL := help
