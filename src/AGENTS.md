# src/AGENTS.md - Source Code Guide

> Layer-by-layer guide for AI agents working with the source code.

## Architecture Summary

Strict 5-layer architecture. **NEVER bypass layers** - use coordinators only.

```
interfaces/         CLI, user commands
     ↓
configuration/      SystemOrchestrator (COORDINATOR)
     ↓
control_reasoning/  RuleProcessingPipeline (COORDINATOR)
     ↓
data_processing/    FuzzyProcessingPipeline (COORDINATOR)
     ↓
device_interface/   MQTTCommunicationManager (COORDINATOR)
```

## Entry Points

| File             | Purpose                                                         |
| ---------------- | --------------------------------------------------------------- |
| `main.py`        | Entry point, calls `Application.run_forever()`                  |
| `application.py` | Full lifecycle: start/stop, HTTP status server, evaluation loop |

## Layer 1: User Interface (`interfaces/`)

**Purpose**: User interaction via CLI

| File          | Responsibility                                          |
| ------------- | ------------------------------------------------------- |
| `cli.py`      | Click-based CLI commands (status, rule, config, sensor) |
| `__main__.py` | Enables `python -m src.interfaces`                      |

**Key Pattern**: CLI queries orchestrator for status, delegates to RuleManager
for rule ops.

## Layer 2: Configuration & Management (`configuration/`)

**Coordinator**: `SystemOrchestrator`

| File                     | Responsibility                                              |
| ------------------------ | ----------------------------------------------------------- |
| `system_orchestrator.py` | 10-step initialization, lifecycle, cross-layer coordination |
| `config_manager.py`      | Load/validate JSON configs, schema validation               |
| `rule_manager.py`        | CRUD for rules, persistence to `rules/active_rules.json`    |
| `logging_manager.py`     | Structured JSON logging, rotation, retention                |

**Initialization Steps** (in order):

1. Load config → 2. Init logging → 3. Populate registry → 4. Connect MQTT →
2. Verify Ollama → 6. Load membership functions → 7. Load rules → 7b. Init rule
   pipeline → 8. Start device monitor → 9. Init interfaces → 10. Ready

## Layer 3: Control & Reasoning (`control_reasoning/`)

**Coordinator**: `RuleProcessingPipeline`

| File                   | Responsibility                                                              |
| ---------------------- | --------------------------------------------------------------------------- |
| `rule_pipeline.py`     | Orchestrates rule evaluation: interpret → LLM → parse → generate → validate |
| `ollama_client.py`     | HTTP client for Ollama API, health checks, model switching                  |
| `rule_interpreter.py`  | `NaturalLanguageRule` dataclass, rule parsing                               |
| `prompt_builder.py`    | Builds LLM prompts from sensor state + rules                                |
| `response_parser.py`   | Extracts actions from LLM output                                            |
| `command_generator.py` | Creates `DeviceCommand` objects from parsed actions                         |
| `command_validator.py` | Validates commands against device capabilities                              |
| `conflict_resolver.py` | Resolves conflicting commands (priority-based)                              |

**Key Data Flow**:

```
LinguisticDescriptions → PromptBuilder → OllamaClient → ResponseParser → CommandGenerator → CommandValidator
```

## Layer 4: Data Processing (`data_processing/`)

**Coordinator**: `FuzzyProcessingPipeline`

| File                       | Responsibility                                                |
| -------------------------- | ------------------------------------------------------------- |
| `fuzzy_pipeline.py`        | Orchestrates: reading → fuzzy engine → linguistic description |
| `fuzzy_engine.py`          | Core fuzzy logic: applies membership functions to values      |
| `membership_functions.py`  | Triangular, trapezoidal, gaussian MF implementations          |
| `linguistic_descriptor.py` | `LinguisticDescription`, `TermMembership` dataclasses         |

**Key Data Types**:

```python
@dataclass
class LinguisticDescription:
    sensor_id: str
    sensor_type: str
    raw_value: float
    terms: tuple[TermMembership, ...]  # e.g., ("hot", 0.85), ("warm", 0.15)
    unit: str | None
```

## Layer 5: Device Interface (`device_interface/`)

**Coordinator**: `MQTTCommunicationManager`

| File                       | Responsibility                                                |
| -------------------------- | ------------------------------------------------------------- |
| `communication_manager.py` | High-level MQTT ops, reading callbacks, command sending       |
| `mqtt_client.py`           | Low-level paho-mqtt wrapper, connection handling              |
| `registry.py`              | `DeviceRegistry` - loads devices from config, provides lookup |
| `device_monitor.py`        | Tracks device availability, timeout detection                 |
| `messages.py`              | `SensorReading`, `DeviceCommand`, `CommandType` dataclasses   |
| `models.py`                | `Device`, `Sensor`, `Actuator` models                         |

## Shared Utilities (`common/`)

| File            | Responsibility                           |
| --------------- | ---------------------------------------- |
| `exceptions.py` | Exception hierarchy (see root AGENTS.md) |
| `logging.py`    | `get_logger()` factory, JSON formatter   |
| `config.py`     | `ConfigLoader` for JSON files            |
| `utils.py`      | Misc utilities                           |

## Code Patterns

### TYPE_CHECKING Guards (avoid circular imports)

```python
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.control_reasoning.rule_pipeline import RuleProcessingPipeline
```

### Dataclass Usage

```python
from dataclasses import dataclass, field

@dataclass
class ApplicationConfig:
    config_dir: Path = field(default_factory=lambda: Path("config"))
```

### Thread-Safe State

```python
self._lock = threading.RLock()

def method(self) -> bool:
    with self._lock:
        # Protected code
```

### Lazy Initialization

```python
_component: Component | None = field(default=None, init=False)

@property
def component(self) -> Component | None:
    return self._component
```

## Adding New Features

### New Sensor Type

1. Create `config/membership_functions/{type}.json`
2. Add devices to `config/devices.json`
3. FuzzyPipeline auto-discovers new membership functions

### New CLI Command

1. Add command in `interfaces/cli.py` using Click decorators
2. Delegate to orchestrator or appropriate manager
3. Keep CLI thin - business logic in layers

### New Device Capability

1. Update `config/devices.json` with new capability
2. Extend `CommandValidator` if needed
3. Update `CommandGenerator` action patterns

## Testing Conventions

- Test files mirror source: `test_configuration/test_system_orchestrator.py`
- Use fixtures from `tests/conftest.py`
- Factory functions: `create_sensor_reading()`, `create_device_command()`
- Mock external services (MQTT, Ollama) in unit tests

## Performance Considerations

- **Caching**: FuzzyEngine caches membership function computations
- **Lazy loading**: Components initialized only when needed
- **Thread pools**: Not used - single evaluation loop with interval
- **Memory**: Target < 8GB total footprint for edge deployment
