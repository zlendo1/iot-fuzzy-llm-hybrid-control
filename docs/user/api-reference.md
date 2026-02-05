# API Reference

This document provides comprehensive API documentation for the Fuzzy-LLM Hybrid
IoT Management System. It covers all public interfaces organized by
architectural layer.

______________________________________________________________________

## Table of Contents

- [User Interface Layer](#user-interface-layer)
  - [CLI Commands](#cli-commands)
- [Configuration & Management Layer](#configuration--management-layer)
  - [SystemOrchestrator](#systemorchestrator)
  - [ConfigurationManager](#configurationmanager)
  - [RuleManager](#rulemanager)
- [Control & Reasoning Layer](#control--reasoning-layer)
  - [OllamaClient](#ollamaclient)
  - [RuleInterpreter](#ruleinterpreter)
  - [NaturalLanguageRule](#naturallanguagerule)
- [Data Processing Layer](#data-processing-layer)
  - [FuzzyEngine](#fuzzyengine)
  - [FuzzificationResult](#fuzzificationresult)
- [Device Interface Layer](#device-interface-layer)
  - [DeviceRegistry](#deviceregistry)

______________________________________________________________________

## User Interface Layer

### CLI Commands

The CLI is implemented using Click and provides the primary user interface.

**Entry Point**: `python -m src.interfaces.cli`

#### Global Options

| Option            | Type   | Default  | Description                             |
| ----------------- | ------ | -------- | --------------------------------------- |
| `--config-dir`    | Path   | `config` | Configuration directory path            |
| `--rules-dir`     | Path   | `rules`  | Rules directory path                    |
| `--logs-dir`      | Path   | `logs`   | Logs directory path                     |
| `--format`        | Choice | `table`  | Output format: `table`, `json`, `plain` |
| `--verbose`, `-v` | Flag   | False    | Enable verbose output                   |
| `--version`       | Flag   | -        | Show version and exit                   |

#### System Commands

**`start`** - Start the IoT management system

```bash
iot-fuzzy-llm start [--skip-mqtt] [--skip-ollama]
```

**`stop`** - Stop the running system

```bash
iot-fuzzy-llm stop
```

**`status`** - Display system status

```bash
iot-fuzzy-llm status
```

#### Rule Commands

**`rule add`** - Add a new natural language rule

```bash
iot-fuzzy-llm rule add "If temperature is hot, turn on AC" \
    --id climate_001 --priority 1 -t climate -t cooling
```

| Option        | Type              | Default        | Description                               |
| ------------- | ----------------- | -------------- | ----------------------------------------- |
| `--id`        | String            | Auto-generated | Rule ID                                   |
| `--priority`  | Integer           | 50             | Priority (1-100, higher = more important) |
| `-t`, `--tag` | String (multiple) | -              | Tags for the rule                         |

**`rule list`** - List all rules

```bash
iot-fuzzy-llm rule list [--enabled-only] [-t TAG]
```

**`rule show`** - Show detailed rule information

```bash
iot-fuzzy-llm rule show <rule_id>
```

**`rule enable`** / **`rule disable`** - Toggle rule status

```bash
iot-fuzzy-llm rule enable <rule_id>
iot-fuzzy-llm rule disable <rule_id>
```

**`rule delete`** - Delete a rule

```bash
iot-fuzzy-llm rule delete <rule_id> [--yes]
```

#### Sensor Commands

**`sensor list`** - List all registered sensors

```bash
iot-fuzzy-llm sensor list
```

**`sensor status`** - Show sensor status

```bash
iot-fuzzy-llm sensor status [sensor_id]
```

#### Device Commands

**`device list`** - List all registered devices

```bash
iot-fuzzy-llm device list
```

**`device status`** - Show device status and capabilities

```bash
iot-fuzzy-llm device status [device_id]
```

#### Config Commands

**`config validate`** - Validate all configuration files

```bash
iot-fuzzy-llm config validate
```

**`config reload`** - Reload configuration at runtime

```bash
iot-fuzzy-llm config reload
```

#### Log Commands

**`log tail`** - Show recent log entries

```bash
iot-fuzzy-llm log tail [-n LINES] [--category CATEGORY]
```

| Option          | Type    | Default  | Description                                                      |
| --------------- | ------- | -------- | ---------------------------------------------------------------- |
| `-n`, `--lines` | Integer | 20       | Number of lines to show                                          |
| `--category`    | Choice  | `system` | Log category: `system`, `commands`, `sensors`, `errors`, `rules` |

______________________________________________________________________

## Configuration & Management Layer

### SystemOrchestrator

Central coordinator managing the full system lifecycle.

```python
from src.configuration.system_orchestrator import SystemOrchestrator

orchestrator = SystemOrchestrator(
    config_dir=Path("config"),
    rules_dir=Path("rules"),
    logs_dir=Path("logs")
)
```

#### Constructor Parameters

| Parameter    | Type   | Default          | Description             |
| ------------ | ------ | ---------------- | ----------------------- |
| `config_dir` | `Path` | `Path("config")` | Configuration directory |
| `rules_dir`  | `Path` | `Path("rules")`  | Rules directory         |
| `logs_dir`   | `Path` | `Path("logs")`   | Logs directory          |

#### Properties

| Property               | Type                              | Description                        |
| ---------------------- | --------------------------------- | ---------------------------------- |
| `state`                | `SystemState`                     | Current system state               |
| `is_ready`             | `bool`                            | True if system is READY or RUNNING |
| `initialization_steps` | `list[InitializationStep]`        | List of initialization steps       |
| `config_manager`       | `ConfigurationManager \| None`    | Configuration manager instance     |
| `rule_manager`         | `RuleManager \| None`             | Rule manager instance              |
| `device_registry`      | `DeviceRegistry \| None`          | Device registry instance           |
| `fuzzy_pipeline`       | `FuzzyProcessingPipeline \| None` | Fuzzy processing pipeline          |

#### Methods

**`initialize(skip_mqtt: bool = False, skip_ollama: bool = False) -> bool`**

Initialize the system. Returns True on success.

**`shutdown() -> bool`**

Gracefully shut down the system. Returns True on success.

**`get_system_status() -> dict[str, Any]`**

Get comprehensive system status including component availability.

#### SystemState Enum

```python
class SystemState(Enum):
    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"
```

______________________________________________________________________

### ConfigurationManager

Singleton for global configuration access with schema validation.

```python
from src.configuration.config_manager import ConfigurationManager

manager = ConfigurationManager(
    config_dir=Path("config"),
    schema_dir=Path("config/schemas"),
    cache_ttl=300.0
)
```

#### Constructor Parameters

| Parameter    | Type           | Default              | Description                   |
| ------------ | -------------- | -------------------- | ----------------------------- |
| `config_dir` | `Path`         | `Path("config")`     | Configuration directory       |
| `schema_dir` | `Path \| None` | `config_dir/schemas` | Schema directory              |
| `cache_ttl`  | `float`        | `300.0`              | Cache time-to-live in seconds |

#### Methods

**`load_config(config_name: str, validate: bool = True) -> dict[str, Any]`**

Load a configuration file by name (without `.json` extension).

**`get_config(config_name: str, *keys: str, default: Any = None) -> Any`**

Get a nested configuration value with fallback default.

```python
log_level = manager.get_config("system_config", "logging", "level", default="INFO")
```

**`load_membership_function(sensor_type: str, validate: bool = True) -> dict[str, Any]`**

Load membership function configuration for a sensor type.

**`save_config(config_name: str, config: dict, validate: bool = True, backup: bool = True) -> None`**

Save configuration with optional validation and backup.

**`reload(config_name: str | None = None) -> None`**

Reload configuration (invalidate cache). If no name given, clears all cache.

**`list_configs() -> list[str]`**

List available configuration files.

**`list_membership_functions() -> list[str]`**

List available membership function files.

**`get_all_configs() -> dict[str, dict[str, Any]]`**

Load and return all configuration files.

#### Properties

| Property         | Type             | Description           |
| ---------------- | ---------------- | --------------------- |
| `mqtt_config`    | `dict[str, Any]` | MQTT configuration    |
| `llm_config`     | `dict[str, Any]` | LLM configuration     |
| `devices_config` | `dict[str, Any]` | Devices configuration |

______________________________________________________________________

### RuleManager

Persistent storage and CRUD operations for natural language rules.

```python
from src.configuration.rule_manager import RuleManager

manager = RuleManager(
    rules_file=Path("rules/active_rules.json"),
    auto_save=True
)
```

#### Constructor Parameters

| Parameter    | Type   | Default                           | Description                |
| ------------ | ------ | --------------------------------- | -------------------------- |
| `rules_file` | `Path` | `Path("rules/active_rules.json")` | Rules file path            |
| `auto_save`  | `bool` | `True`                            | Auto-save on modifications |

#### Methods

**`add_rule(rule_id: str, rule_text: str, priority: int = 1, enabled: bool = True, metadata: dict | None = None) -> NaturalLanguageRule`**

Add a new rule.

**`get_rule(rule_id: str) -> NaturalLanguageRule`**

Get a rule by ID. Raises `RuleError` if not found.

**`get_rule_optional(rule_id: str) -> NaturalLanguageRule | None`**

Get a rule by ID or None if not found.

**`update_rule(rule_id: str, rule_text: str | None = None, priority: int | None = None, enabled: bool | None = None, metadata: dict | None = None) -> NaturalLanguageRule`**

Update an existing rule.

**`delete_rule(rule_id: str) -> bool`**

Delete a rule. Returns True if deleted.

**`enable_rule(rule_id: str) -> None`**

Enable a rule.

**`disable_rule(rule_id: str) -> None`**

Disable a rule.

**`get_all_rules() -> list[NaturalLanguageRule]`**

Get all rules.

**`get_enabled_rules() -> list[NaturalLanguageRule]`**

Get only enabled rules.

**`get_rules_by_priority(descending: bool = True) -> list[NaturalLanguageRule]`**

Get rules sorted by priority.

**`export_rules(file_path: Path | str) -> int`**

Export rules to a file. Returns count of exported rules.

**`import_rules(file_path: Path | str, overwrite: bool = False) -> int`**

Import rules from a file. Returns count of imported rules.

**`contains(rule_id: str) -> bool`**

Check if a rule exists.

**`save() -> None`**

Force save rules to disk.

**`reload() -> None`**

Reload rules from disk.

#### Properties

| Property        | Type  | Description             |
| --------------- | ----- | ----------------------- |
| `rule_count`    | `int` | Total number of rules   |
| `enabled_count` | `int` | Number of enabled rules |

______________________________________________________________________

## Control & Reasoning Layer

### OllamaClient

Client for communicating with Ollama REST API.

```python
from src.control_reasoning.ollama_client import OllamaClient, OllamaConfig

config = OllamaConfig.from_json_file(Path("config/llm_config.json"))
client = OllamaClient(config)

if client.is_healthy():
    response = client.generate("What is 2+2?")
    print(response.text)
```

#### Constructor Parameters

| Parameter | Type           | Description                   |
| --------- | -------------- | ----------------------------- |
| `config`  | `OllamaConfig` | Complete Ollama configuration |

#### Methods

**`is_healthy() -> bool`**

Check if Ollama service is running and accessible.

**`get_available_models() -> list[str]`**

Get list of locally available models.

**`verify_model() -> str`**

Verify configured model is available, trying fallbacks if needed. Returns the
verified model name.

**`generate(prompt: str, model: str | None = None, system_prompt: str | None = None) -> OllamaResponse`**

Generate a text completion.

**`close() -> None`**

Close the HTTP session.

#### Properties

| Property       | Type           | Description                |
| -------------- | -------------- | -------------------------- |
| `config`       | `OllamaConfig` | Configuration object       |
| `active_model` | `str \| None`  | Currently active model     |
| `base_url`     | `str`          | Ollama service base URL    |
| `timeout`      | `float`        | Request timeout in seconds |

#### OllamaResponse

| Property                 | Type    | Description             |
| ------------------------ | ------- | ----------------------- |
| `text`                   | `str`   | Generated text          |
| `model`                  | `str`   | Model used              |
| `total_duration_seconds` | `float` | Total duration          |
| `prompt_eval_count`      | `int`   | Prompt tokens evaluated |
| `eval_count`             | `int`   | Tokens generated        |

#### Exceptions

- `OllamaConnectionError` - Cannot connect to service
- `OllamaTimeoutError` - Request timed out
- `OllamaModelNotFoundError` - Configured model not available
- `OllamaGenerationError` - Text generation failed

______________________________________________________________________

### RuleInterpreter

Matches linguistic sensor states to rule conditions.

```python
from src.control_reasoning.rule_interpreter import RuleInterpreter

interpreter = RuleInterpreter(rules=[rule1, rule2])
# or
interpreter = RuleInterpreter.from_json_file(Path("rules/active_rules.json"))
```

#### Methods

**`add_rule(rule: NaturalLanguageRule) -> None`**

Add a rule to the interpreter.

**`remove_rule(rule_id: str) -> bool`**

Remove a rule. Returns True if removed.

**`get_rule(rule_id: str) -> NaturalLanguageRule | None`**

Get a rule by ID.

**`enable_rule(rule_id: str) -> bool`**

Enable a rule. Returns True if found.

**`disable_rule(rule_id: str) -> bool`**

Disable a rule. Returns True if found.

**`find_candidate_rules(sensor_descriptions: Sequence[LinguisticDescription]) -> list[RuleMatch]`**

Find rules matching the current sensor state. Returns matches sorted by
priority.

**`get_rules_by_priority() -> list[NaturalLanguageRule]`**

Get enabled rules sorted by priority.

**`get_rules_by_tag(tag: str) -> list[NaturalLanguageRule]`**

Get rules with a specific tag.

**`record_rule_trigger(rule_id: str) -> bool`**

Record that a rule was triggered.

#### Properties

| Property        | Type                        | Description        |
| --------------- | --------------------------- | ------------------ |
| `rules`         | `list[NaturalLanguageRule]` | All rules          |
| `enabled_rules` | `list[NaturalLanguageRule]` | Only enabled rules |

______________________________________________________________________

### NaturalLanguageRule

Data class representing a natural language rule.

```python
from src.control_reasoning.rule_interpreter import NaturalLanguageRule

rule = NaturalLanguageRule(
    rule_id="climate_001",
    rule_text="If temperature is hot, turn on AC",
    priority=1,
    enabled=True,
    metadata={"tags": ["climate", "cooling"]}
)
```

#### Attributes

| Attribute           | Type             | Default  | Description                        |
| ------------------- | ---------------- | -------- | ---------------------------------- |
| `rule_id`           | `str`            | Required | Unique identifier                  |
| `rule_text`         | `str`            | Required | Natural language rule text         |
| `priority`          | `int`            | `1`      | Priority (higher = more important) |
| `enabled`           | `bool`           | `True`   | Whether rule is active             |
| `created_timestamp` | `str \| None`    | `None`   | ISO 8601 creation timestamp        |
| `last_triggered`    | `str \| None`    | `None`   | ISO 8601 last trigger timestamp    |
| `trigger_count`     | `int`            | `0`      | Number of times triggered          |
| `metadata`          | `dict[str, Any]` | `{}`     | Additional metadata (tags, etc.)   |

#### Methods

**`from_dict(data: dict) -> NaturalLanguageRule`** (classmethod)

Create from dictionary.

**`to_dict() -> dict[str, Any]`**

Convert to dictionary.

**`record_trigger() -> None`**

Record a trigger event (updates timestamp and count).

______________________________________________________________________

## Data Processing Layer

### FuzzyEngine

Applies membership functions to sensor values for fuzzification.

```python
from src.data_processing.fuzzy_engine import FuzzyEngine

engine = FuzzyEngine(
    cache_max_size=1000,
    cache_ttl_seconds=300.0
)
engine.load_configs_from_directory(Path("config/membership_functions"))
```

#### Constructor Parameters

| Parameter           | Type    | Default | Description           |
| ------------------- | ------- | ------- | --------------------- |
| `cache_max_size`    | `int`   | `1000`  | Maximum cache entries |
| `cache_ttl_seconds` | `float` | `300.0` | Cache TTL in seconds  |

#### Methods

**`load_config(config: SensorTypeConfig) -> None`**

Load a sensor type configuration.

**`load_config_from_dict(data: dict[str, Any]) -> None`**

Load configuration from dictionary.

**`load_config_from_file(path: Path) -> None`**

Load configuration from JSON file.

**`load_configs_from_directory(directory: Path) -> int`**

Load all configurations from a directory. Returns count loaded.

**`get_config(sensor_type: str) -> SensorTypeConfig | None`**

Get configuration for a sensor type.

**`get_supported_sensor_types() -> list[str]`**

Get list of configured sensor types.

**`fuzzify(sensor_type: str, value: float, use_cache: bool = True) -> FuzzificationResult`**

Fuzzify a sensor value. Returns membership degrees for all linguistic terms.

**`fuzzify_batch(readings: list[tuple[str, float]], use_cache: bool = True) -> list[FuzzificationResult]`**

Fuzzify multiple sensor readings.

**`clear_cache() -> None`**

Clear the fuzzification cache.

#### Properties

| Property     | Type  | Description        |
| ------------ | ----- | ------------------ |
| `cache_size` | `int` | Current cache size |

______________________________________________________________________

### FuzzificationResult

Result of fuzzifying a sensor value.

```python
result = engine.fuzzify("temperature", 28.5)
print(result.sensor_type)  # "temperature"
print(result.raw_value)    # 28.5
print(result.memberships)  # (("warm", 0.7), ("hot", 0.3))

dominant = result.get_dominant_term()
print(dominant)  # ("warm", 0.7)
```

#### Attributes

| Attribute     | Type                            | Description                   |
| ------------- | ------------------------------- | ----------------------------- |
| `sensor_type` | `str`                           | Type of sensor                |
| `raw_value`   | `float`                         | Original numeric value        |
| `memberships` | `tuple[tuple[str, float], ...]` | Linguistic terms with degrees |
| `timestamp`   | `float`                         | Processing timestamp          |

#### Methods

**`get_dominant_term() -> tuple[str, float] | None`**

Get the term with highest membership degree.

**`to_dict() -> dict[str, Any]`**

Convert to dictionary.

______________________________________________________________________

## Device Interface Layer

### DeviceRegistry

Maintains inventory of all configured sensors and actuators.

```python
from src.device_interface.registry import DeviceRegistry
from src.common.config import ConfigLoader

config_loader = ConfigLoader(config_dir=Path("config"))
registry = DeviceRegistry(config_loader=config_loader)
registry.load("devices.json")
```

#### Constructor Parameters

| Parameter       | Type                   | Default | Description          |
| --------------- | ---------------------- | ------- | -------------------- |
| `config_loader` | `ConfigLoader \| None` | `None`  | Configuration loader |

#### Methods

**`load(config_file: str = "devices.json") -> None`**

Load devices from configuration file.

**`get(device_id: str) -> Device`**

Get device by ID. Raises `DeviceError` if not found.

**`get_optional(device_id: str) -> Device | None`**

Get device by ID or None.

**`exists(device_id: str) -> bool`**

Check if device exists.

**`all_devices() -> list[Device]`**

Get all devices.

**`sensors() -> list[Sensor]`**

Get all sensors.

**`actuators() -> list[Actuator]`**

Get all actuators.

**`by_location(location: str) -> list[Device]`**

Get devices by location.

**`by_device_class(device_class: str) -> list[Device]`**

Get devices by class (e.g., "temperature", "light").

**`by_type(device_type: DeviceType) -> list[Device]`**

Get devices by type (SENSOR or ACTUATOR).

**`get_locations() -> set[str]`**

Get all unique device locations.

**`get_device_classes() -> set[str]`**

Get all unique device classes.

#### Iteration Support

```python
for device in registry:
    print(device.id, device.name)

if "temp_living_room" in registry:
    print("Device exists")

print(len(registry))  # Number of devices
```

______________________________________________________________________

## Exception Hierarchy

```
Exception
├── ConfigurationError    # Configuration loading/validation errors
├── ValidationError       # Schema validation errors
├── RuleError            # Rule management errors
├── DeviceError          # Device registry errors
├── FuzzyEngineError     # Fuzzy processing errors
└── OllamaError          # LLM client errors
    ├── OllamaConnectionError
    ├── OllamaTimeoutError
    ├── OllamaModelNotFoundError
    └── OllamaGenerationError
```

______________________________________________________________________

## See Also

- [User Guide](user-guide.md) - CLI usage and workflows
- [Configuration Guide](configuration-guide.md) - Configuration options
- [Schema Reference](schema-reference.md) - JSON schema documentation
