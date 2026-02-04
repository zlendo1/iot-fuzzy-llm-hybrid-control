# Docker Setup

This directory contains Docker configurations for the IoT Fuzzy-LLM Hybrid
Control System, optimized for edge and embedded deployment.

## Directory Structure

```
docker/
├── mosquitto/          # MQTT broker configuration
│   ├── Dockerfile
│   ├── mosquitto.conf
│   └── entrypoint.sh
├── ollama/             # LLM service configuration
│   ├── Dockerfile
│   └── entrypoint.sh
└── app/                # Python application configuration
    ├── Dockerfile
    └── entrypoint.sh
```

## Quick Start

```bash
docker compose up -d
```

## Services

| Service   | Port  | Description                    |
| --------- | ----- | ------------------------------ |
| mosquitto | 1883  | Eclipse Mosquitto MQTT broker  |
| ollama    | 11434 | Ollama LLM service (CPU-based) |
| app       | -     | Python application             |

## Edge Deployment

This system is designed for edge devices with limited resources. The default
configuration uses lightweight models optimized for CPU inference:

- **Default model**: `qwen3:0.6b` (~400MB, fast CPU inference)
- **Alternative models** for edge deployment:
  - `qwen3:1.7b` (~1GB)
  - `qwen3:4b` (~2.5GB)
  - `tinyllama` (~600MB)

## Environment Variables

Copy `.env.example` to `.env` and configure:

| Variable             | Default    | Description                           |
| -------------------- | ---------- | ------------------------------------- |
| MQTT_PORT            | 1883       | MQTT broker port                      |
| OLLAMA_PORT          | 11434      | Ollama API port                       |
| OLLAMA_MODEL         | qwen3:0.6b | LLM model (use small models for edge) |
| OLLAMA_PULL_ON_START | true       | Auto-pull model on startup            |
| LOG_LEVEL            | INFO       | Application log level                 |

## Building

```bash
docker compose build
```

## Common Commands

```bash
docker compose up -d              # Start all services
docker compose down               # Stop all services
docker compose logs -f            # Follow logs
docker compose logs -f app        # Follow app logs only
docker compose ps                 # Show running containers
docker compose exec app bash      # Shell into app container
docker compose exec mosquitto sh  # Shell into mosquitto container
```

## Volumes

| Volume             | Purpose                  |
| ------------------ | ------------------------ |
| iot-mosquitto-data | MQTT message persistence |
| iot-mosquitto-logs | MQTT broker logs         |
| iot-ollama-models  | Downloaded LLM models    |

## Health Checks

All services include health checks:

- **mosquitto**: Tests MQTT subscription capability
- **ollama**: Tests API availability at `/api/tags`
- **app**: Verifies Python runtime

Check health status:

```bash
docker compose ps
```

## Resource Requirements

Minimum requirements for edge deployment:

| Resource | Minimum      | Recommended |
| -------- | ------------ | ----------- |
| RAM      | 2GB          | 4GB         |
| Storage  | 2GB          | 5GB         |
| CPU      | ARM64/x86-64 | Multi-core  |

## Troubleshooting

### Ollama fails to start

Check if the model is being pulled:

```bash
docker compose logs -f ollama
```

First startup may take several minutes to download the model.

### MQTT connection refused

Ensure mosquitto is healthy:

```bash
docker compose ps mosquitto
docker compose logs mosquitto
```

### Slow inference on edge device

Try a smaller model:

```bash
OLLAMA_MODEL=qwen3:0.6b docker compose up -d
```

### Reset everything

```bash
docker compose down -v
docker compose build --no-cache
docker compose up -d
```
