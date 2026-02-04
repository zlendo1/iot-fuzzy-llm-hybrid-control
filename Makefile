.PHONY: help build up down restart logs logs-app ps shell shell-mqtt \
        install dev dev-deps \
        test test-unit test-int coverage coverage-html \
        lint format check typecheck \
        clean clean-docker clean-all reset \
        pull-model list-models

.DEFAULT_GOAL := help

DOCKER_COMPOSE := docker compose
PYTHON := python
PIP := pip
PYTEST := pytest
VENV := .venv
VENV_BIN := $(VENV)/bin
VENV_PYTHON := $(VENV_BIN)/python
VENV_PIP := $(VENV_BIN)/pip

help:
	@echo "IoT Fuzzy-LLM Hybrid Control System"
	@echo "===================================="
	@echo ""
	@echo "Docker Commands:"
	@echo "  make build          Build all Docker images"
	@echo "  make up             Start all services"
	@echo "  make down           Stop all services"
	@echo "  make restart        Restart all services"
	@echo "  make logs           Tail logs from all services"
	@echo "  make logs-app       Tail logs from app service only"
	@echo "  make ps             Show running containers"
	@echo "  make shell          Open shell in app container"
	@echo "  make shell-mqtt     Open shell in mosquitto container"
	@echo ""
	@echo "Development Commands:"
	@echo "  make install        Install Python dependencies locally"
	@echo "  make dev            Run app locally (outside Docker)"
	@echo "  make dev-deps       Start only mosquitto and ollama in Docker"
	@echo ""
	@echo "Testing Commands:"
	@echo "  make test           Run all tests"
	@echo "  make test-unit      Run unit tests only"
	@echo "  make test-int       Run integration tests only"
	@echo "  make coverage       Run tests with coverage report"
	@echo "  make coverage-html  Generate HTML coverage report"
	@echo ""
	@echo "Code Quality Commands:"
	@echo "  make lint           Run linters (ruff, mypy)"
	@echo "  make format         Format code (ruff format)"
	@echo "  make check          Run all checks (lint + test)"
	@echo "  make typecheck      Run type checking only"
	@echo ""
	@echo "Utility Commands:"
	@echo "  make clean          Remove build artifacts, __pycache__, etc."
	@echo "  make clean-docker   Remove Docker volumes and images"
	@echo "  make clean-all      Full cleanup (clean + clean-docker)"
	@echo "  make reset          Stop services and full cleanup"
	@echo ""
	@echo "Model Management:"
	@echo "  make pull-model     Pull LLM model into Ollama container"
	@echo "  make list-models    List available models in Ollama"


build:
	$(DOCKER_COMPOSE) build

up:
	$(DOCKER_COMPOSE) up -d

down:
	$(DOCKER_COMPOSE) down

restart: down up

logs:
	$(DOCKER_COMPOSE) logs -f

logs-app:
	$(DOCKER_COMPOSE) logs -f app

ps:
	$(DOCKER_COMPOSE) ps

shell:
	$(DOCKER_COMPOSE) exec app bash

shell-mqtt:
	$(DOCKER_COMPOSE) exec mosquitto sh


$(VENV):
	$(PYTHON) -m venv $(VENV)

install: $(VENV)
	$(VENV_PIP) install --upgrade pip
	$(VENV_PIP) install -r requirements.txt
	$(VENV_PIP) install -r requirements-dev.txt
	@echo ""
	@echo "Virtual environment ready. Activate with:"
	@echo "  source $(VENV)/bin/activate"

dev: $(VENV)
	$(VENV_PYTHON) -m src.main

dev-deps:
	$(DOCKER_COMPOSE) up -d mosquitto ollama


test: $(VENV)
	$(VENV_BIN)/pytest tests/ -v

test-unit: $(VENV)
	$(VENV_BIN)/pytest tests/ -v -m "unit"

test-int: $(VENV)
	$(VENV_BIN)/pytest tests/ -v -m "integration"

coverage: $(VENV)
	$(VENV_BIN)/pytest tests/ --cov=src --cov-report=term-missing

coverage-html: $(VENV)
	$(VENV_BIN)/pytest tests/ --cov=src --cov-report=html
	@echo "Coverage report generated in htmlcov/index.html"


lint: $(VENV)
	$(VENV_BIN)/ruff check src/ tests/
	$(VENV_BIN)/mypy src/

format: $(VENV)
	$(VENV_BIN)/ruff format src/ tests/
	$(VENV_BIN)/ruff check --fix src/ tests/

typecheck: $(VENV)
	$(VENV_BIN)/mypy src/

check: lint test


clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type f -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	find . -type f -name "coverage.xml" -delete 2>/dev/null || true
	rm -rf build/ dist/ 2>/dev/null || true
	@echo "Cleaned build artifacts"

clean-docker:
	$(DOCKER_COMPOSE) down -v --rmi local 2>/dev/null || true
	docker volume rm iot-mosquitto-data iot-mosquitto-logs iot-ollama-models 2>/dev/null || true
	@echo "Cleaned Docker resources"

clean-all: clean clean-docker

reset: down clean-all


pull-model:
	$(DOCKER_COMPOSE) exec ollama ollama pull $${OLLAMA_MODEL:-qwen3:0.6b}

list-models:
	$(DOCKER_COMPOSE) exec ollama ollama list
