.PHONY: help up down status nats-up nats-down nats-status gen-certs env-check listener-time listener-training listener-hn listener-next writer-time writer-training writer-hn writer-next publisher notes-exporter-publisher clean logs listeners writers time training hn next install setup update-parsers-check update-parsers-all update-parser-time update-parser-training update-parser-hn update-parser-next update-time update-training update-hn update-next parser-status parser-versions

# Colors for output
GREEN = \033[0;32m
BLUE = \033[0;34m
YELLOW = \033[1;33m
RED = \033[0;31m
NC = \033[0m # No Color

# Configuration
SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c
MAKEFLAGS += --no-builtin-rules

# Load environment from .env if it exists
ifneq (,$(wildcard .env))
	include .env
endif

# Default values (always set and export)
NATS_URL ?= tls://localhost:4222
NATS_PORT ?= 4222
CERTS_DIR ?= $(shell pwd)/certs

# Always export for subprocesses
export NATS_URL
export NATS_PORT
export CERTS_DIR

# Container and process names
NATS_CONTAINER := nats-server
PIDS_FILE := ./.make-pids

# Help target
help:
	@echo "$(BLUE)╔════════════════════════════════════════════════════════════╗$(NC)"
	@echo "$(BLUE)║             NATS Pipeline Control Plane (mTLS Enabled)      ║$(NC)"
	@echo "$(BLUE)╚════════════════════════════════════════════════════════════╝$(NC)"
	@echo ""
	@echo "$(GREEN)Usage:$(NC) make [target]"
	@echo ""
	@echo "$(GREEN)System Control:$(NC)"
	@echo "  $(YELLOW)up$(NC)              Start entire system (certs + NATS + publishers/listeners)"
	@echo "  $(YELLOW)down$(NC)            Stop all running components"
	@echo "  $(YELLOW)status$(NC)          Show status of all components"
	@echo "  $(YELLOW)logs$(NC)            Show logs from all background processes"
	@echo "  $(YELLOW)clean$(NC)           Remove all process files and cleanup"
	@echo ""
	@echo "$(GREEN)TLS/Security:$(NC)"
	@echo "  $(YELLOW)gen-certs$(NC)       Generate TLS certificates (auto-run on make up)"
	@echo "  $(YELLOW)env-check$(NC)       Verify TLS configuration"
	@echo ""
	@echo "$(GREEN)NATS Server:$(NC)"
	@echo "  $(YELLOW)nats-up$(NC)         Start NATS server in Docker"
	@echo "  $(YELLOW)nats-down$(NC)       Stop NATS server"
	@echo "  $(YELLOW)nats-status$(NC)     Show NATS server status"
	@echo ""
	@echo "$(GREEN)Configuration:$(NC)"
	@echo "  NATS_URL: $(NATS_URL) (mTLS enabled)"
	@echo "  NATS_PORT: $(NATS_PORT)"
	@echo "  CERTS_DIR: $(CERTS_DIR)"
	@echo "  TLS: ✓ Mutual TLS (mTLS) enabled"
	@echo ""

# ============================================================================
# Certificate Generation
# ============================================================================

gen-certs:
	@if [ ! -f "$(CERTS_DIR)/rootCA.pem" ]; then \
		echo "$(YELLOW)Generating TLS certificates...$(NC)"; \
		bash $(shell pwd)/gen-certs.sh; \
	else \
		echo "$(GREEN)✓$(NC) Certificates already exist"; \
	fi

# ============================================================================
# NATS Server Targets
# ============================================================================

nats-up: gen-certs
	@echo "$(GREEN)▶$(NC) Starting NATS server..."
	@if docker ps --format "{{.Names}}" | grep -q "^$(NATS_CONTAINER)$$"; then \
		echo "$(YELLOW)⚠$(NC) NATS container already running"; \
	else \
		docker run -d \
			--name $(NATS_CONTAINER) \
			-p $(NATS_PORT):4222 \
			-v $(CERTS_DIR):/certs:ro \
			-v $(shell pwd)/nats-server.conf:/etc/nats/nats-server.conf:ro \
			nats:latest \
			-c /etc/nats/nats-server.conf \
		&& echo "$(GREEN)✓$(NC) NATS server started on port $(NATS_PORT)"; \
	fi
	@sleep 2

nats-down:
	@echo "$(GREEN)▶$(NC) Stopping NATS server..."
	@docker stop $(NATS_CONTAINER) 2>/dev/null || true
	@docker rm $(NATS_CONTAINER) 2>/dev/null || true
	@echo "$(GREEN)✓$(NC) NATS server stopped"

nats-status:
	@if docker ps --format "{{.Names}}" | grep -q "^$(NATS_CONTAINER)$$"; then \
		echo "$(GREEN)✓$(NC) NATS server is running"; \
	else \
		echo "$(RED)✗$(NC) NATS server is not running"; \
	fi

# ============================================================================
# System Control Targets
# ============================================================================

up: nats-up
	@echo ""
	@echo "$(GREEN)╔════════════════════════════════════════════════════════════╗$(NC)"
	@echo "$(GREEN)║                    NATS Started                            ║$(NC)"
	@echo "$(GREEN)╚════════════════════════════════════════════════════════════╝$(NC)"
	@echo ""
	@echo "$(GREEN)Active Components:$(NC)"
	@echo "  $(GREEN)✓$(NC) NATS server (port $(NATS_PORT))"
	@echo ""

down: nats-down
	@echo ""
	@echo "$(GREEN)╔════════════════════════════════════════════════════════════╗$(NC)"
	@echo "$(GREEN)║                    NATS Stopped                            ║$(NC)"
	@echo "$(GREEN)╚════════════════════════════════════════════════════════════╝$(NC)"
	@echo ""

# ============================================================================
# Status and Monitoring
# ============================================================================

status:
	@echo "$(BLUE)════════════════════════════════════════════════════════════$(NC)"
	@echo "$(BLUE)                   NATS Status                             $(NC)"
	@echo "$(BLUE)════════════════════════════════════════════════════════════$(NC)"
	@echo ""
	@echo "$(BLUE)NATS Server:$(NC)"
	@$(MAKE) nats-status
	@echo ""

logs:
	@echo "$(BLUE)════════════════════════════════════════════════════════════$(NC)"
	@echo "$(BLUE)                   NATS Logs                               $(NC)"
	@echo "$(BLUE)════════════════════════════════════════════════════════════$(NC)"
	@echo ""
	@echo "$(YELLOW)NATS Server:$(NC)"
	@echo "  docker logs -f $(NATS_CONTAINER)"
	@echo ""

# ============================================================================
# Cleanup
# ============================================================================

clean: down
	@echo "$(GREEN)▶$(NC) Cleaning up..."
	@rm -rf $(PIDS_FILE)
	@echo "$(GREEN)✓$(NC) Cleanup complete"

# ============================================================================
# Development Targets
# ============================================================================

env-check:
	@echo "$(BLUE)Environment Configuration:$(NC)"
	@echo "  NATS_URL: $(NATS_URL)"
	@echo "  NATS_PORT: $(NATS_PORT)"
	@echo "  CERTS_DIR: $(CERTS_DIR)"
	@if [ -f "$(CERTS_DIR)/rootCA.pem" ]; then \
		echo "  $(GREEN)✓$(NC) Certificates found"; \
	else \
		echo "  $(RED)✗$(NC) Certificates not found"; \
	fi

# Default target
.DEFAULT_GOAL := help
