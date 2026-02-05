# Installation Guide

## Fuzzy-LLM Hybrid IoT Management System

**Document Status:** Active\
**Last Updated:** 2026-02-05

This guide covers all installation methods for the Fuzzy-LLM Hybrid IoT
Management System.

______________________________________________________________________

## Table of Contents

1. [System Requirements](#1-system-requirements)
2. [Quick Start with Docker](#2-quick-start-with-docker)
3. [Local Development Setup](#3-local-development-setup)
4. [Manual Installation](#4-manual-installation)
5. [Verifying Installation](#5-verifying-installation)
6. [Troubleshooting](#6-troubleshooting)

______________________________________________________________________

## 1. System Requirements

### Hardware Requirements

| Component | Minimum | Recommended |
| --------- | ------- | ----------- |
| CPU       | 2 cores | 4 cores     |
| RAM       | 4 GB    | 8 GB        |
| Storage   | 5 GB    | 10 GB       |

**Note:** LLM inference runs on CPU only. More cores improve inference speed.

### Software Requirements

| Software       | Version | Purpose                          |
| -------------- | ------- | -------------------------------- |
| Python         | 3.9+    | Runtime                          |
| Docker         | 20.10+  | Containerization (optional)      |
| Docker Compose | 2.0+    | Service orchestration (optional) |
| Git            | 2.0+    | Source control                   |

### Operating System

- Linux (Ubuntu 20.04+, Debian 11+, RHEL 8+)
- macOS (11 Big Sur+)
- Windows 10/11 with WSL2

______________________________________________________________________

## 2. Quick Start with Docker

Docker Compose is the recommended installation method. It handles all
dependencies automatically.

### Prerequisites

- Docker and Docker Compose installed
- 4+ GB RAM available for containers

### Installation Steps

```bash
# 1. Clone the repository
git clone https://github.com/your-org/iot-fuzzy-llm.git
cd iot-fuzzy-llm

# 2. Start all services
docker compose up -d

# 3. Wait for services to be healthy (1-2 minutes for model download)
docker compose ps

# 4. View logs
docker compose logs -f
```

### What Gets Started

| Service     | Container     | Port  | Description           |
| ----------- | ------------- | ----- | --------------------- |
| MQTT Broker | iot-mosquitto | 1883  | Mosquitto MQTT broker |
| Ollama      | iot-ollama    | 11434 | LLM inference service |
| App         | iot-app       | -     | Main application      |

### Environment Variables

Create a `.env` file to customize the deployment:

```bash
# MQTT Configuration
MQTT_PORT=1883

# Ollama Configuration
OLLAMA_PORT=11434
OLLAMA_MODEL=qwen3:0.6b
OLLAMA_PULL_ON_START=true

# Application
LOG_LEVEL=INFO
```

### Common Docker Commands

```bash
# Start services
docker compose up -d

# Stop services
docker compose down

# View logs
docker compose logs -f

# View app logs only
docker compose logs -f app

# Restart services
docker compose restart

# Open shell in app container
docker compose exec app bash

# Pull a different model
OLLAMA_MODEL=qwen3:1.7b docker compose exec ollama ollama pull qwen3:1.7b
```

### Using the Makefile

The project includes a Makefile for convenience:

```bash
# Show all available commands
make help

# Build images
make build

# Start services
make up

# Stop services
make down

# View logs
make logs

# Pull LLM model
make pull-model

# List available models
make list-models
```

______________________________________________________________________

## 3. Local Development Setup

For development, run the application locally while using Docker for
dependencies.

### Step 1: Clone and Setup Virtual Environment

```bash
# Clone repository
git clone https://github.com/your-org/iot-fuzzy-llm.git
cd iot-fuzzy-llm

# Create virtual environment
python -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate     # Windows
```

### Step 2: Install Python Dependencies

```bash
# Install runtime dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt
```

**Runtime Dependencies (requirements.txt):**

| Package    | Version | Purpose                  |
| ---------- | ------- | ------------------------ |
| paho-mqtt  | 2.1.0   | MQTT client              |
| requests   | 2.32.5  | HTTP client for Ollama   |
| numpy      | 2.4.2   | Numerical computation    |
| jsonschema | 4.26.0  | Configuration validation |
| click      | 8.3.1   | CLI framework            |

### Step 3: Start Dependencies with Docker

```bash
# Start only MQTT broker and Ollama
docker compose up -d mosquitto ollama

# Or use Makefile
make dev-deps
```

### Step 4: Run the Application

```bash
# Using CLI
python -m src.interfaces.cli start

# Or use the entry point
iot-fuzzy-llm start
```

### Development Workflow

```bash
# Run tests
make test

# Run with coverage
make coverage

# Run linters
make lint

# Format code
make format

# Type checking
make typecheck

# All checks
make check
```

______________________________________________________________________

## 4. Manual Installation

For environments without Docker, install all components manually.

### Step 1: Install Python Dependencies

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Install Mosquitto MQTT Broker

**Ubuntu/Debian:**

```bash
sudo apt update
sudo apt install mosquitto mosquitto-clients

# Start service
sudo systemctl enable mosquitto
sudo systemctl start mosquitto

# Verify
mosquitto_sub -t 'test' -C 1 &
mosquitto_pub -t 'test' -m 'hello'
```

**macOS:**

```bash
brew install mosquitto

# Start service
brew services start mosquitto
```

**RHEL/CentOS:**

```bash
sudo yum install mosquitto
sudo systemctl enable mosquitto
sudo systemctl start mosquitto
```

### Step 3: Install Ollama

**Linux:**

```bash
curl -fsSL https://ollama.ai/install.sh | sh

# Start service
ollama serve &

# Pull model
ollama pull qwen3:0.6b
```

**macOS:**

```bash
# Download from https://ollama.ai/download
# Or use Homebrew
brew install ollama

# Start and pull model
ollama serve &
ollama pull qwen3:0.6b
```

### Step 4: Configure the System

```bash
# Verify configuration files exist
ls config/

# Expected files:
# - devices.json
# - mqtt_config.json
# - llm_config.json
# - membership_functions/

# Validate configuration
python -m src.interfaces.cli config validate
```

### Step 5: Start the System

```bash
# Start with default configuration
python -m src.interfaces.cli start

# Or skip external services for testing
python -m src.interfaces.cli start --skip-mqtt --skip-ollama
```

______________________________________________________________________

## 5. Verifying Installation

### Health Checks

```bash
# Check system status
iot-fuzzy-llm status

# Expected output:
# System State: RUNNING
# Ready: Yes
# Components:
#   ✓ config_manager: available
#   ✓ device_registry: available
#   ✓ fuzzy_engine: available
#   ✓ ollama_client: available
#   ✓ mqtt_client: available
```

### Verify MQTT Broker

```bash
# Test MQTT connectivity
mosquitto_sub -h localhost -t 'test/#' -C 1 &
mosquitto_pub -h localhost -t 'test/hello' -m 'world'
# Should print: world
```

### Verify Ollama

```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Test model
curl http://localhost:11434/api/generate -d '{
  "model": "qwen3:0.6b",
  "prompt": "Say hello",
  "stream": false
}'
```

### Run Tests

```bash
# Run all tests
make test

# Run with verbose output
pytest tests/ -v

# Expected: 806 tests passing
```

### Validate Configuration

```bash
# Validate all configuration files
iot-fuzzy-llm config validate

# List devices
iot-fuzzy-llm device list

# List rules
iot-fuzzy-llm rule list
```

______________________________________________________________________

## 6. Troubleshooting

### Docker Issues

**Containers not starting:**

```bash
# Check container status
docker compose ps

# View container logs
docker compose logs mosquitto
docker compose logs ollama
docker compose logs app

# Restart services
docker compose down
docker compose up -d
```

**Port conflicts:**

```bash
# Check if ports are in use
lsof -i :1883
lsof -i :11434

# Use different ports in .env
echo "MQTT_PORT=1884" >> .env
echo "OLLAMA_PORT=11435" >> .env
```

### MQTT Connection Issues

**Cannot connect to broker:**

```bash
# Check if Mosquitto is running
systemctl status mosquitto  # Linux
brew services list          # macOS

# Check listening port
netstat -tlnp | grep 1883

# Test with mosquitto client
mosquitto_sub -h localhost -t '#' -v
```

### Ollama Issues

**Model not loading:**

```bash
# Check Ollama status
curl http://localhost:11434/api/tags

# Pull model manually
ollama pull qwen3:0.6b

# Check disk space
df -h
```

**Slow inference:**

- Ensure adequate RAM (4GB minimum)
- Use a smaller model for faster inference
- Check CPU utilization during inference

### Python Environment Issues

**Import errors:**

```bash
# Ensure virtual environment is activated
source .venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Verify installation
pip list | grep -E "paho-mqtt|requests|numpy|jsonschema|click"
```

**Version conflicts:**

```bash
# Use exact versions from requirements.txt
pip install -r requirements.txt --no-deps
```

### Configuration Issues

**Validation errors:**

```bash
# Validate configuration
iot-fuzzy-llm config validate

# Check JSON syntax
python -m json.tool config/devices.json

# Compare against schema
cat config/schemas/devices.schema.json
```

### Common Error Messages

| Error                                 | Cause                   | Solution                     |
| ------------------------------------- | ----------------------- | ---------------------------- |
| `Connection refused: localhost:1883`  | MQTT broker not running | Start Mosquitto              |
| `Connection refused: localhost:11434` | Ollama not running      | Start Ollama service         |
| `Model not found`                     | LLM model not pulled    | Run `ollama pull qwen3:0.6b` |
| `ValidationError`                     | Invalid configuration   | Check JSON syntax and schema |
| `FileNotFoundError: devices.json`     | Missing config file     | Copy from examples or create |

______________________________________________________________________

## See Also

- [User Guide](user-guide.md) - CLI usage instructions
- [Configuration Guide](configuration-guide.md) - Configuration options
- [Demo Walkthrough](demo-walkthrough.md) - Step-by-step demo
- [Troubleshooting](demo-troubleshooting.md) - More troubleshooting tips
