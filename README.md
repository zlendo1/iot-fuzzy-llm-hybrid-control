# Fuzzy-LLM Hybrid IoT Management System

A thesis project implementing a novel approach to IoT device management that
combines fuzzy logic with Large Language Models (LLMs) for natural language rule
processing. The system runs on edge devices with CPU-only inference via Ollama.

## Overview

This system uses fuzzy logic as a semantic bridge between raw IoT sensor values
and an LLM. Sensor readings are transformed into linguistic descriptions (e.g.,
"temperature is hot (0.85)") which the LLM can then reason about to evaluate
natural language rules and generate device commands.

## Key Features

- Natural language rules (e.g., "If the living room is hot and humid, turn on
  the AC")
- Fuzzy logic preprocessing for semantic sensor interpretation
- Local LLM inference via Ollama (no cloud dependency)
- Privacy by design - all processing stays on-device
- MQTT-based IoT device communication
- Configurable membership functions for any sensor type

## Architecture

```
User Interface Layer        (CLI)
         |
Configuration & Management  (Orchestrator, Config, Rules, Logging)
         |
Control & Reasoning         (Rule Pipeline, LLM Client, Command Generation)
         |
Data Processing            (Fuzzy Engine, Linguistic Descriptors)
         |
Device Interface           (MQTT Communication, Device Registry)
```

## Quick Start

### Prerequisites

- Python 3.9+
- Docker and Docker Compose (recommended)
- OR: Mosquitto MQTT broker + Ollama installed locally

### Docker (Recommended)

```bash
docker compose up -d
```

### Local Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Start MQTT broker and Ollama separately
# Then run:
python -m src.main
```

## Project Structure

```
iot-master/
├── config/              # JSON configuration files
│   ├── devices.json     # Sensor and actuator definitions
│   ├── llm_config.json  # Ollama LLM configuration
│   ├── mqtt_config.json # MQTT broker settings
│   └── membership_functions/  # Fuzzy membership function definitions
├── docker/              # Docker configurations
├── docs/                # Documentation
│   ├── user/            # User guides and API reference
│   └── dev/             # Design documents and specifications
├── logs/                # System log files (JSON format)
├── rules/               # Natural language rule definitions
│   └── active_rules.json
├── src/                 # Source code (5 layers)
│   ├── configuration/   # System orchestrator, config, rules, logging
│   ├── control_reasoning/ # Rule pipeline, LLM client, command generation
│   ├── data_processing/ # Fuzzy engine, linguistic descriptors
│   ├── device_interface/ # MQTT client, device registry
│   └── interfaces/      # CLI interface
└── tests/               # Test suite (806 tests, 83% coverage)
```

## Documentation

- [Installation Guide](docs/user/installation-guide.md)
- [User Guide](docs/user/user-guide.md)
- [API Reference](docs/user/api-reference.md)
- [Configuration Guide](docs/user/configuration-guide.md)
- [Example Rules](docs/user/example-rules.md)
- [Architecture Design Document](docs/dev/add.md)

## Demo Scenario

The system includes a pre-configured smart home demo with:

- 14 devices (7 sensors, 7 actuators)
- 10 natural language rules
- 4 sensor types with fuzzy membership functions

See [Demo Walkthrough](docs/user/demo-walkthrough.md) for details.

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Quick check
pytest --tb=line -q
```

## License

See [LICENSE](LICENSE) file for details.
