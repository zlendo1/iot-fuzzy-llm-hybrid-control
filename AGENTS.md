# AGENTS.md - Fuzzy-LLM Hybrid IoT Management System

> AI Agent guidance for working with this codebase.

## Project Overview

**Purpose**: Thesis project implementing offline IoT device management through
natural language rules. Uses fuzzy logic as a **semantic bridge** between raw
sensor values and linguistic concepts an LLM can understand.

**Core Flow**:
`Sensor → Fuzzy Logic → Linguistic Description → LLM → Device Commands`

**Example**: Temperature 32°C → "hot (0.85)" → Rule "If hot, turn on AC" →
`turn_on(ac_living_room)`

## Architecture (STRICT - Do Not Violate)

5-layer strict architecture with **layer coordinators**. Communication ONLY
between adjacent layers through coordinators.

```
User Interface          →  src/interfaces/cli.py
         ↓
Configuration & Mgmt    →  src/configuration/system_orchestrator.py (COORDINATOR)
         ↓
Control & Reasoning     →  src/control_reasoning/rule_pipeline.py (COORDINATOR)
         ↓
Data Processing         →  src/data_processing/fuzzy_pipeline.py (COORDINATOR)
         ↓
Device Interface        →  src/device_interface/communication_manager.py (COORDINATOR)
```

**DD-01**: Components within a layer can talk freely. Inter-layer communication
ONLY through the layer coordinator.

## Key Entry Points

| Entry Point                | Purpose                                        |
| -------------------------- | ---------------------------------------------- |
| `src/main.py`              | Application entry point                        |
| `src/application.py`       | Application lifecycle (start/stop/run_forever) |
| `python -m src.interfaces` | CLI interface                                  |
| `docker compose up -d`     | Docker deployment                              |

## Technology Stack

- **Python 3.9+** (strict typing with mypy)
- **Ollama** - Local LLM inference (qwen3:0.6b default)
- **MQTT** - Device communication via Mosquitto
- **JSON** - All configuration (devices, rules, membership functions)
- **pytest** - 826 tests, 83%+ coverage

## Critical Conventions

### Type Safety (MANDATORY)

```python
# REQUIRED: All functions must have type hints
def process_reading(self, reading: SensorReading, sensor_type: str) -> str:

# NEVER use:
# - as any
# - @ts-ignore / type: ignore (unless absolutely necessary with comment)
# - Untyped function definitions
```

### Exception Hierarchy

```python
from src.common.exceptions import (
    IoTFuzzyLLMError,      # Base
    ConfigurationError,    # Config loading/validation
    ValidationError,       # Data validation
    DeviceError,           # Device operations
    MQTTError,             # MQTT specific (extends DeviceError)
    OllamaError,           # LLM client errors
    RuleError,             # Rule processing
)
```

### Logging Pattern

```python
from src.common.logging import get_logger
logger = get_logger(__name__)

# Use structured logging with extra dict
logger.info("Sensor reading processed", extra={
    "sensor_id": reading.sensor_id,
    "value": reading.value,
})
```

### Configuration Loading

```python
from src.common.config import ConfigLoader
config_loader = ConfigLoader(config_dir=Path("config"))
mqtt_config = config_loader.load("mqtt_config.json")
```

## DO NOT (Anti-Patterns)

1. **DO NOT bypass layer coordinators** - Never import from non-adjacent layer
2. **DO NOT suppress type errors** - Fix the actual type issue
3. **DO NOT use `print()`** - Use structured logging via `get_logger()`
4. **DO NOT hardcode paths** - Use `Path` objects and config
5. **DO NOT create circular imports** - Use `TYPE_CHECKING` guards
6. **DO NOT modify config at runtime without atomic write-rename**
7. **DO NOT skip schema validation** for JSON configs
8. **DO NOT add new dependencies** without updating pyproject.toml

## Testing Patterns

```python
# Fixtures in tests/conftest.py
@pytest.fixture
def config_directory(tmp_path: Path) -> Path:
    ...

# Factory functions for test data
from tests.conftest import create_sensor_reading, create_device_command

# Test markers
@pytest.mark.unit
@pytest.mark.integration
@pytest.mark.performance
@pytest.mark.slow
```

**Run tests**: `pytest` or `make test` **Run lint**: `ruff check src tests` or
`make lint`

## Directory Structure Quick Reference

```
iot-master/
├── config/              # JSON configs (devices, MQTT, LLM, membership functions)
├── docker/              # Dockerfiles for app, mosquitto, ollama
├── docs/                # user/ and dev/ documentation
├── rules/               # Natural language rules (active_rules.json)
├── src/                 # Source code (see src/AGENTS.md for details)
│   ├── common/          # Shared utilities, exceptions, logging
│   ├── configuration/   # Orchestrator, ConfigManager, RuleManager, LoggingManager
│   ├── control_reasoning/ # RulePipeline, OllamaClient, CommandGenerator
│   ├── data_processing/ # FuzzyPipeline, FuzzyEngine, MembershipFunctions
│   ├── device_interface/ # MQTTManager, DeviceRegistry, DeviceMonitor
│   └── interfaces/      # CLI
└── tests/               # Mirrors src/ structure
```

## Common Tasks

### Adding a New Sensor Type

1. Create `config/membership_functions/{type}.json` with linguistic variables
2. Add device to `config/devices.json`
3. FuzzyPipeline auto-loads membership functions

### Adding a New Rule

```bash
python -m src.interfaces rule add "If bedroom is cold, turn on heater"
```

### Creating a New Component

1. Determine which layer it belongs to
2. Add to appropriate `src/{layer}/` directory
3. Export through layer's `__init__.py`
4. Only coordinator talks to adjacent layers

## Performance Targets (from ADD Section 8.1)

| Metric               | Target  |
| -------------------- | ------- |
| Fuzzy processing     | < 50ms  |
| Sensor → description | < 100ms |
| LLM inference        | < 3s    |
| Command generation   | < 100ms |
| End-to-end           | < 5s    |
| System startup       | < 30s   |

## Related Documentation

- [docs/dev/add.md](docs/dev/add.md) - Architecture Design Document
- [docs/user/user-guide.md](docs/user/user-guide.md) - CLI usage
- [docs/user/configuration-guide.md](docs/user/configuration-guide.md) - Config
  reference
- [src/AGENTS.md](src/AGENTS.md) - Source code details
