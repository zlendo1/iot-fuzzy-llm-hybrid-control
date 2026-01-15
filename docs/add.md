# Architecture Design Document

______________________________________________________________________

## 1. Introduction

### 1.1 Purpose

This document describes the software architecture for the Fuzzy-LLM Hybrid IoT
Management System. The architecture supports natural language rule processing
for IoT device control through integration of fuzzy logic and large language
models. This document serves as the authoritative reference for system design
decisions, component interactions, and implementation guidance.

### 1.2 Scope

The architecture covers all software components required for offline IoT device
management through natural language rules. The system operates on edge devices
and includes fuzzy logic processing, LLM inference, rule interpretation, device
communication, and configuration management. Hardware-specific device drivers
and physical IoT devices fall outside this architecture scope.

### 1.3 Intended Audience

This document addresses software developers implementing the system, system
architects reviewing design decisions, and technical reviewers validating
architectural soundness. Readers should possess knowledge of software
architecture patterns, Python programming, and basic understanding of fuzzy
logic and language models.

### 1.4 Document Organization

Section 2 presents the architectural overview and design principles. Section 3
details the system architecture with component descriptions. Section 4 specifies
component interfaces and interactions. Section 5 describes data architecture and
persistence. Section 6 addresses deployment considerations. Section 7 covers
security architecture. Section 8 discusses performance and scalability. Section
9 documents design decisions and rationale.

______________________________________________________________________

## 2. Architectural Overview

### 2.1 Architectural Style

The system employs a layered architecture with clear separation between data
acquisition, processing, reasoning, and control execution. The architecture
follows these principles:

1. **Separation of Concerns:** Each layer addresses distinct functional
   responsibilities without overlap
2. **Modularity:** Components interact through well-defined interfaces enabling
   independent development and testing
3. **Offline Operation:** No external network dependencies for core
   functionality
4. **Configurability:** JSON-based configuration enables customization without
   code modification
5. **Extensibility:** Plugin architecture supports additional membership
   functions, device protocols, and LLM backends

### 2.2 High-Level Architecture

The system consists of five primary layers:

**Layer 1 - Device Interface Layer:** Handles communication with physical
sensors and actuators through protocol adapters.

**Layer 2 - Data Processing Layer:** Transforms raw sensor data into linguistic
descriptions using fuzzy logic.

**Layer 3 - Reasoning Layer:** Processes linguistic descriptions and natural
language rules using an offline LLM to generate control decisions.

**Layer 4 - Control Layer:** Translates LLM decisions into device-specific
commands and manages execution.

**Layer 5 - Configuration and Management Layer:** Provides configuration
loading, validation, rule storage, and system monitoring.

### 2.3 Architectural Constraints

The architecture operates under these constraints:

1. Python 3.9 or later as implementation language
2. Maximum 8GB RAM footprint including loaded models
3. No internet connectivity for core operations
4. JSON format for all persistent configuration
5. Support for x86-64 and ARM64 processor architectures
6. Linux operating system as deployment target

### 2.4 Design Principles

**Principle 1 - Privacy by Design:** No sensor data, rules, or commands
transmitted to external services.

**Principle 2 - Fail-Safe Operation:** System defaults to safe states on
component failures.

**Principle 3 - Transparency:** All processing steps logged for debugging and
user understanding.

**Principle 4 - Resource Efficiency:** Optimized for edge device constraints
through lazy loading and caching.

**Principle 5 - User-Centric Design:** Natural language interfaces prioritized
over technical configuration.

______________________________________________________________________

## 3. System Architecture

### 3.1 Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER INTERFACE LAYER                         │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │     CLI      │  │   Web UI     │  │  REST API    │           │
│  │  Interface   │  │  (Optional)  │  │  (Optional)  │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
│                                                                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ User commands, queries
                             │
┌────────────────────────────┼────────────────────────────────────┐
│   CONFIGURATION AND MANAGEMENT LAYER                            │
│                            │                                    │
│                            ▼                                    │
│    ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓     │
│    ┃          SYSTEM ORCHESTRATOR / CONTROLLER            ┃     │
│    ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛     │
│                            │                                    │
│         ┌──────────────────┼─────────────────┐                  │
│         │                  │                 │                  │
│  ┌──────▼───────┐  ┌───────▼──────┐  ┌───────▼──────┐           │
│  │Configuration │  │     Rule     │  │   Logging    │           │
│  │   Manager    │  │   Manager    │  │   Manager    │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
│                                                                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ System state, configurations
                             │
┌────────────────────────────┼────────────────────────────────────┐
│       CONTROL AND REASONING LAYER                               │
│                            │                                    │
│                            ▼                                    │
│         ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓       │
│         ┃           RULE PROCESSING PIPELINE            ┃       │
│         ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛       │
│                            │                                    │
│         ┌──────────────────┼─────────────────┐                  │
│         │                  │                 │                  │
│  ┌──────▼───────┐  ┌───────▼──────┐  ┌───────▼──────┐           │
│  │     Rule     │  │     LLM      │  │   Command    │           │
│  │ Interpreter  │  │   Engine     │  │  Generator   │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
│                                                                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ Linguistic descriptions, commands
                             │
┌────────────────────────────┼────────────────────────────────────┐
│          DATA PROCESSING LAYER                                  │
│                            │                                    │
│                            ▼                                    │
│         ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓       │
│         ┃         FUZZY PROCESSING PIPELINE             ┃       │
│         ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛       │
│                            │                                    │
│         ┌──────────────────┼─────────────────┐                  │
│         │                  │                 │                  │
│  ┌──────▼───────┐  ┌───────▼──────┐  ┌───────▼──────┐           │
│  │    Fuzzy     │  │  Membership  │  │  Linguistic  │           │
│  │    Engine    │  │   Function   │  │  Descriptor  │           │
│  │              │  │   Library    │  │   Builder    │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
│                                                                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ Sensor readings, device commands
                             │
┌────────────────────────────┼────────────────────────────────────┐
│          DEVICE INTERFACE LAYER                                 │
│                            │                                    │
│                            ▼                                    │
│         ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓       │
│         ┃       DEVICE COMMUNICATION MANAGER            ┃       │
│         ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛       │
│                            │                                    │
│         ┌──────────────────┼──────────────────┐                 │
│         │                  │                  │                 │
│  ┌──────▼───────┐  ┌───────▼──────┐   ┌───────▼──────┐          │
│  │   Device     │  │   Protocol   │   │   Device     │          │
│  │   Registry   │  │   Adapters   │   │   Monitor    │          │
│  └──────────────┘  └──────────────┘   └──────────────┘          │
│                                                                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ Hardware communication
                             │
                    ┌────────┴────────┐
                    │                 │    
              ┌─────▼─────┐     ┌─────▼─────┐
              │  Sensors  │     │ Actuators │
              │           │     │           │
              └───────────┘     └───────────┘
```

### 3.2 Component Descriptions

#### 3.2.1 Device Interface Layer Components

**Device Registry**

Maintains inventory of all connected sensors and actuators with their
capabilities and communication parameters.

**Responsibilities:**

- Register and deregister devices dynamically
- Store device metadata including type, capabilities, and protocol
- Provide device lookup by identifier
- Validate device availability

**Key Interfaces:**

- register_device(device_config) → device_id
- get_device(device_id) → device_info
- list_devices(filter_criteria) → device_list
- remove_device(device_id) → success

**Protocol Adapters**

Implement communication protocols for sensor data acquisition and actuator
control.

**Responsibilities:**

- Abstract protocol-specific communication details
- Handle connection management and error recovery
- Translate between internal data formats and protocol messages
- Support MQTT, HTTP REST, and serial communication

**Key Interfaces:**

- read_sensor(device_id) → sensor_reading
- write_actuator(device_id, command) → execution_result
- subscribe_events(device_id, callback) → subscription_handle
- unsubscribe_events(subscription_handle) → success

**Device Monitor**

Tracks device health and communication status.

**Responsibilities:**

- Monitor device connectivity
- Detect communication failures
- Trigger reconnection attempts
- Report device status to logging system

**Key Interfaces:**

- get_device_status(device_id) → status_info
- check_all_devices() → status_summary
- set_monitoring_interval(interval) → success

#### 3.2.2 Data Processing Layer Components

**Fuzzy Engine**

Core fuzzy logic processing component that fuzzifies numerical sensor values.

**Responsibilities:**

- Apply membership functions to sensor values
- Compute membership degrees for all linguistic terms
- Cache computation results for repeated queries
- Support multiple concurrent fuzzification requests

**Key Interfaces:**

- fuzzify(sensor_value, sensor_type) → linguistic_terms
- batch_fuzzify(sensor_readings) → linguistic_descriptions
- clear_cache() → success

**Membership Function Library**

Provides implementations of standard membership function types.

**Responsibilities:**

- Implement triangular membership functions
- Implement trapezoidal membership functions
- Implement Gaussian membership functions
- Implement sigmoid membership functions
- Support custom membership function plugins

**Key Interfaces:**

- triangular(x, a, b, c) → membership_degree
- trapezoidal(x, a, b, c, d) → membership_degree
- gaussian(x, mean, sigma) → membership_degree
- sigmoid(x, a, c) → membership_degree
- register_custom_function(name, function) → success

**Linguistic Descriptor Builder**

Formats fuzzy logic outputs into structured linguistic descriptions.

**Responsibilities:**

- Combine sensor type, linguistic terms, and membership degrees
- Generate natural language phrases for LLM consumption
- Apply linguistic templates for consistent formatting
- Filter low-confidence terms based on threshold

**Key Interfaces:**

- build_description(sensor_id, linguistic_terms) → description_text
- build_system_state(all_sensor_states) → state_description
- set_confidence_threshold(threshold) → success

#### 3.2.3 Control and Reasoning Layer Components

**Rule Interpreter**

Manages natural language rules and determines which rules apply to current
system state.

**Responsibilities:**

- Store and retrieve natural language rules
- Match current sensor states against rule conditions
- Resolve conflicts between multiple applicable rules
- Track rule execution history

**Key Interfaces:**

- add_rule(rule_text, priority) → rule_id
- remove_rule(rule_id) → success
- get_applicable_rules(current_state) → rule_list
- get_rule_history(rule_id) → execution_history

**LLM Engine**

Executes large language model inference for natural language processing and
decision generation.

**Responsibilities:**

- Load and initialize offline LLM models
- Generate prompts from linguistic descriptions and rules
- Execute model inference with timeout protection
- Parse LLM outputs to extract structured decisions
- Manage model context across interactions

**Key Interfaces:**

- load_model(model_path, config) → success
- generate_decision(prompt_text, timeout) → llm_response
- parse_response(llm_response) → structured_actions
- reset_context() → success

**Command Generator**

Translates LLM decisions into device-specific control commands.

**Responsibilities:**

- Map abstract actions to concrete device commands
- Validate commands against device capabilities
- Handle multi-device coordination
- Apply safety constraints to command parameters

**Key Interfaces:**

- generate_command(action, device_id) → device_command
- validate_command(device_command) → validation_result
- generate_batch_commands(action_list) → command_list

#### 3.2.4 Configuration and Management Layer Components

**Configuration Manager**

Handles loading, validation, and management of JSON configuration files.

**Responsibilities:**

- Load membership function definitions from JSON
- Validate configuration file syntax and semantics
- Provide configuration access to other components
- Support runtime configuration updates
- Export current configuration for backup

**Key Interfaces:**

- load_config(config_path) → config_data
- validate_config(config_data) → validation_result
- get_config(config_key) → config_value
- update_config(config_key, config_value) → success
- export_config(output_path) → success

**Rule Manager**

Persists and manages natural language rules with metadata.

**Responsibilities:**

- Store rules in persistent storage
- Support CRUD operations on rules
- Maintain rule metadata including priority and timestamps
- Enable bulk rule import and export

**Key Interfaces:**

- save_rule(rule) → success
- load_rules() → rule_list
- update_rule(rule_id, rule_data) → success
- delete_rule(rule_id) → success
- export_rules(output_path) → success

**Logging Manager**

Centralized logging infrastructure for system events and debugging.

**Responsibilities:**

- Log sensor readings and device commands
- Record rule evaluations and LLM decisions
- Track system errors and warnings
- Support configurable log levels
- Implement log rotation and archival

**Key Interfaces:**

- log_event(level, message, context) → success
- log_sensor_reading(reading) → success
- log_command_execution(command, result) → success
- set_log_level(level) → success
- rotate_logs() → success

#### 3.2.5 User Interface Layer Components

**CLI Interface**

Command-line interface for system administration and rule management.

**Responsibilities:**

- Accept user commands for system control
- Display system status and sensor readings
- Support interactive rule definition
- Provide configuration management interface

**Key Interfaces:**

- start_cli() → interactive_session
- execute_command(command_string) → command_output

**Web UI (Optional)**

Browser-based interface for visual rule management.

**Responsibilities:**

- Render visual rule editor
- Display real-time sensor status
- Show rule execution history
- Provide configuration forms

**REST API (Optional)**

HTTP API for programmatic system access.

**Responsibilities:**

- Expose rule management endpoints
- Provide sensor and device status queries
- Accept control commands
- Support authentication and authorization

______________________________________________________________________

## 4. Component Interactions

### 4.1 Primary Interaction Flows

#### 4.1.1 Sensor Data Processing Flow

```
Sequence: Sensor Reading → Linguistic Description

1. Device Monitor triggers periodic sensor poll
2. Protocol Adapter reads sensor value
3. Protocol Adapter returns numerical reading to Fuzzy Engine
4. Fuzzy Engine retrieves membership functions from Configuration Manager
5. Membership Function Library computes membership degrees
6. Fuzzy Engine returns linguistic terms with degrees
7. Linguistic Descriptor Builder formats description text
8. Description logged by Logging Manager
9. Description stored in system state cache
```

**Data Flow:**

```
Sensor → Protocol Adapter → Fuzzy Engine → Membership Functions
  ↓                                              ↓
Logging Manager ← Descriptor Builder ← Linguistic Terms
```

#### 4.1.2 Rule Evaluation Flow

```
Sequence: State Change → Rule Evaluation → Action Execution

1. System state updated with new linguistic descriptions
2. Rule Interpreter retrieves applicable rules from Rule Manager
3. For each applicable rule:
   a. Rule Interpreter formats prompt with state and rule
   b. LLM Engine generates decision based on prompt
   c. LLM Engine parses response for actions
   d. Command Generator translates actions to device commands
   e. Command Generator validates commands
4. Conflict resolution applied if multiple commands target same device
5. Valid commands sent to Protocol Adapters
6. Protocol Adapters execute commands on devices
7. Execution results logged by Logging Manager
8. Rule execution history updated in Rule Manager
```

**Data Flow:**

```
System State → Rule Interpreter → LLM Engine → Command Generator
                      ↓                              ↓
                 Rule Manager                Protocol Adapters
                                                     ↓
                                              Physical Devices
```

#### 4.1.3 Configuration Loading Flow

```
Sequence: System Startup → Configuration Loading

1. Configuration Manager loads membership function JSON files
2. Configuration Manager validates JSON schema and semantics
3. Configuration Manager loads device configuration
4. Device Registry populates with configured devices
5. Protocol Adapters initialize for configured devices
6. Rule Manager loads persisted rules
7. LLM Engine loads specified model
8. System enters ready state
```

#### 4.1.4 User Rule Addition Flow

```
Sequence: User Input → Rule Storage → Immediate Evaluation

1. User submits natural language rule through interface
2. CLI/Web UI sends rule to Rule Manager
3. Rule Manager validates basic rule structure
4. Rule Manager assigns rule ID and stores rule
5. Rule Manager notifies Rule Interpreter of new rule
6. Rule Interpreter evaluates rule against current state
7. If applicable, triggers rule evaluation flow
8. User receives confirmation with rule ID
```

### 4.2 Interface Specifications

#### 4.2.1 Internal Component Interfaces

All internal component communication uses Python function calls with
strongly-typed parameters and return values. Components communicate through
abstract base classes enabling interface stability and implementation
flexibility.

**Example Interface Contract:**

```python
class IFuzzyEngine(ABC):
    @abstractmethod
    def fuzzify(self, sensor_value: float, sensor_type: str) -> List[LinguisticTerm]:
        """
        Fuzzify a numerical sensor value.
        
        Args:
            sensor_value: Numerical sensor reading
            sensor_type: Identifier for sensor type (determines membership functions)
            
        Returns:
            List of LinguisticTerm objects with term names and membership degrees
            
        Raises:
            ValueError: If sensor_type not configured
            TypeError: If sensor_value not numeric
        """
        pass
```

#### 4.2.2 Data Transfer Objects

Components exchange data using immutable dataclasses for type safety and
clarity.

**Sensor Reading:**

```python
@dataclass(frozen=True)
class SensorReading:
    sensor_id: str
    timestamp: datetime
    value: float
    unit: str
    quality: Optional[float] = None
```

**Linguistic Term:**

```python
@dataclass(frozen=True)
class LinguisticTerm:
    term: str
    membership_degree: float
    sensor_id: str
```

**Device Command:**

```python
@dataclass(frozen=True)
class DeviceCommand:
    device_id: str
    command_type: str
    parameters: Dict[str, Any]
    timestamp: datetime
    source_rule_id: Optional[str] = None
```

#### 4.2.3 Event-Based Communication

Components use an event bus for asynchronous notifications of state changes and
system events.

**Event Types:**

- SensorReadingEvent: New sensor data available
- RuleTriggeredEvent: Rule evaluation completed
- CommandExecutedEvent: Device command executed
- ConfigurationChangedEvent: Configuration updated
- SystemErrorEvent: Error condition occurred

**Event Subscription Pattern:**

```python
event_bus.subscribe(SensorReadingEvent, handler_function)
```

### 4.3 Error Handling Strategy

Each component implements consistent error handling:

1. **Input Validation:** Validate all inputs at component boundaries
2. **Exception Propagation:** Propagate exceptions with context to calling
   components
3. **Graceful Degradation:** Continue operation with reduced functionality when
   possible
4. **Error Logging:** Log all errors with stack traces and context
5. **User Notification:** Surface critical errors to user interface

**Error Categories:**

**Configuration Errors:** Invalid JSON, missing required fields, semantic
inconsistencies. System refuses to start until resolved.

**Communication Errors:** Device timeouts, connection failures, protocol errors.
System retries with exponential backoff and continues with available devices.

**Processing Errors:** LLM inference failures, invalid rule syntax, fuzzy
computation errors. System logs error and skips affected operation.

**Resource Errors:** Out of memory, disk full, model loading failures. System
attempts cleanup and notifies user.

______________________________________________________________________

## 5. Data Architecture

### 5.1 Data Storage Architecture

The system employs file-based persistence for all data without database
dependencies.

**Storage Categories:**

1. **Configuration Data:** JSON files containing membership functions, device
   configurations, and system settings
2. **Rule Data:** JSON or line-delimited JSON files storing natural language
   rules with metadata
3. **Log Data:** Structured log files with system events, sensor readings, and
   command executions
4. **Cache Data:** In-memory caches with optional disk persistence for
   performance optimization

### 5.2 Configuration Data Schema

**Membership Function Configuration:**

```json
{
  "sensor_types": [
    {
      "sensor_type": "temperature",
      "unit": "celsius",
      "universe_of_discourse": {
        "min": -10.0,
        "max": 50.0
      },
      "linguistic_variables": [
        {
          "term": "cold",
          "function_type": "trapezoidal",
          "parameters": {
            "a": -10.0,
            "b": 0.0,
            "c": 10.0,
            "d": 15.0
          }
        },
        {
          "term": "comfortable",
          "function_type": "triangular",
          "parameters": {
            "a": 10.0,
            "b": 20.0,
            "c": 25.0
          }
        },
        {
          "term": "hot",
          "function_type": "trapezoidal",
          "parameters": {
            "a": 22.0,
            "b": 27.0,
            "c": 40.0,
            "d": 50.0
          }
        }
      ]
    }
  ]
}
```

**Device Configuration:**

```json
{
  "devices": [
    {
      "device_id": "temp_sensor_living_room",
      "device_type": "sensor",
      "sensor_type": "temperature",
      "protocol": "mqtt",
      "connection": {
        "broker": "localhost",
        "port": 1883,
        "topic": "home/living_room/temperature"
      },
      "polling_interval": 60
    },
    {
      "device_id": "hvac_living_room",
      "device_type": "actuator",
      "protocol": "mqtt",
      "connection": {
        "broker": "localhost",
        "port": 1883,
        "topic": "home/living_room/hvac/control"
      },
      "capabilities": ["set_temperature", "set_mode", "power_on", "power_off"]
    }
  ]
}
```

**LLM Configuration:**

```json
{
  "llm_config": {
    "provider": "ollama",
    "ollama_host": "localhost",
    "ollama_port": 11434,
    "model_name": "mistral:7b-instruct",
    "inference_params": {
      "temperature": 0.3,
      "max_tokens": 512,
      "top_p": 0.9,
      "top_k": 40,
      "repeat_penalty": 1.1
    },
    "timeout_seconds": 5,
    "context_length": 4096,
    "streaming": false,
    "fallback_models": [
      "llama3.2:7b-instruct",
      "phi3:3.8b"
    ]
  }
}
```

### 5.3 Rule Data Schema

**Rule Storage Format:**

```json
{
  "rules": [
    {
      "rule_id": "rule_001",
      "rule_text": "If the temperature is hot and humidity is high, turn on the air conditioner",
      "priority": 1,
      "enabled": true,
      "created_timestamp": "2026-01-15T10:30:00Z",
      "last_triggered": "2026-01-15T14:22:00Z",
      "trigger_count": 5,
      "metadata": {
        "author": "user",
        "tags": ["comfort", "climate_control"]
      }
    }
  ]
}
```

### 5.4 Caching Strategy

**Membership Function Results Cache:**

Cache fuzzification results for identical sensor values within configurable time
window. Invalidate cache on configuration changes.

**Implementation:** In-memory LRU cache with 1000 entry limit per sensor type.

**LLM Context Cache:**

Cache recent LLM interactions to maintain context when enabled. Expire entries
after configurable idle period.

**Implementation:** In-memory circular buffer with configurable size limit.

**Device Status Cache:**

Cache device connectivity status to reduce monitoring overhead. Update on
communication events.

**Implementation:** In-memory dictionary with timestamp-based expiration.

### 5.5 Data Persistence Guarantees

**Atomic Writes:** All configuration and rule file updates use atomic
write-rename pattern to prevent corruption.

**Write-Ahead Logging:** Critical state changes logged before execution to
support recovery.

**Backup Strategy:** Configuration Manager creates timestamped backup before
each modification.

**Data Retention:** Logs rotated daily with 30-day retention by default.
Configurable per deployment.

______________________________________________________________________

## 6. Deployment Architecture

### 6.1 Deployment Models

#### 6.1.1 Single Edge Device Deployment

Complete system deployed on single edge device managing local IoT
infrastructure.

**Components:**

- All system layers on single host
- Local file storage for configuration and logs
- Direct connection to sensors and actuators
- Optional web interface on localhost

**Resource Requirements:**

- 8GB RAM minimum
- 20GB disk space for models and logs
- 4 CPU cores recommended for optimal performance

#### 6.1.2 Distributed Deployment

Sensor nodes communicate with central processing node running fuzzy logic and
LLM components.

**Architecture:**

- Lightweight sensor agents on low-power devices
- Central edge server for processing and reasoning
- MQTT broker for device communication
- Shared configuration storage

**Resource Requirements:**

- Sensor nodes: 256MB RAM, minimal CPU
- Central server: 8GB RAM, 4 CPU cores
- Network: Low-latency local network

#### 6.1.3 Containerized Deployment

Docker containers for simplified deployment and isolation.

**Container Structure:**

- Base container with Python runtime and dependencies
- Model container with LLM weights
- Configuration volume mount
- Data volume for logs and rules

### 6.2 Deployment Components

**Python Virtual Environment:**

```
venv/
├── bin/
│   └── python3
├── lib/
│   └── python3.9/site-packages/
│       ├── transformers/
│       ├── torch/
│       ├── paho-mqtt/
│       └── ...
└── requirements.txt
```

**Directory Structure:**

```
/opt/fuzzy-llm-iot/
├── bin/
│   ├── start_system.sh
│   └── stop_system.sh
├── config/
│   ├── membership_functions/
│   │   ├── temperature.json
│   │   ├── humidity.json
│   │   └── ...
│   ├── devices.json
│   └── llm_config.json
├── models/
│   └── mistral-7b-instruct/
├── rules/
│   └── active_rules.json
├── logs/
│   ├── system.log
│   ├── commands.log
│   └── errors.log
├── src/
│   └── [source code]
└── data/
    └── cache/
```

### 6.3 Installation Process

**Step 1:** Install system dependencies

- Python 3.9+
- CUDA toolkit (optional, for GPU acceleration)
- MQTT broker (if using MQTT devices)

**Step 2:** Create virtual environment and install Python packages

- transformers, torch, numpy, paho-mqtt, flask

**Step 3:** Download and configure LLM model

- Download model weights
- Apply quantization if needed
- Validate model loading

**Step 4:** Configure system

- Create membership function definitions
- Configure device connections
- Set LLM parameters

**Step 5:** Initialize system

- Validate configuration files
- Test device connectivity
- Load initial rules

**Step 6:** Start system services

- Launch background daemon
- Enable web interface (if configured)
- Verify operation

### 6.4 System Monitoring

**Health Checks:**

- Device connectivity status
- LLM inference latency
- Memory usage tracking
- Disk space monitoring

**Metrics Collection:**

- Sensor reading frequency
- Rule evaluation count
- Command execution success rate
- Error rate by category

**Alerting:**

- Device offline alerts
- Resource exhaustion warnings
- Critical error notifications

______________________________________________________________________

## 7. Security Architecture

### 7.1 Security Principles

**Principle 1 - Data Locality:** All processing occurs on local device without
external transmission.

**Principle 2 - Minimal Attack Surface:** No unnecessary network services or
open ports.

**Principle 3 - Input Validation:** All external inputs validated before
processing.

**Principle 4 - Least Privilege:** Components operate with minimum required
permissions.

**Principle 5 - Defense in Depth:** Multiple security layers for critical
functions.

### 7.2 Authentication and Authorization

**Local Access Control:**

File system permissions restrict configuration modification to authorized users.
Web interface (if enabled) requires authentication through configurable
mechanism.

**Device Authentication:**

Protocol adapters support device-specific authentication:

- MQTT: Username/password or client certificates
- HTTP: API keys or OAuth tokens
- Serial: Physical connection security

### 7.3 Data Protection

**Configuration Files:**

Sensitive configuration parameters (credentials, API keys) stored in separate
protected files with restricted permissions (0600).

**Command Validation:**

All device commands validated against safety constraints before execution.
Commands affecting critical systems require explicit user authorization in
configuration.

**LLM Output Validation:**

LLM-generated commands parsed and validated against whitelist of permitted
actions. Malformed or suspicious outputs rejected with logging.

### 7.4 Network Security

**Firewall Rules:**

Recommend host firewall configuration restricting inbound connections to
localhost for web interface and API.

**Communication Encryption:**

Support TLS for MQTT and HTTPS for REST communication when devices support
encrypted protocols.

**Network Segmentation:**

Deploy on isolated IoT network segment separated from general network traffic.

### 7.5 Security Logging

**Security Events:**

Log all authentication attempts, configuration changes, and command executions
with timestamp and source identification.

**Audit Trail:**

Maintain immutable audit log for security-relevant events with integrity
verification.

______________________________________________________________________

## 8. Performance and Scalability

### 8.1 Performance Requirements

**Latency Targets:**

- Sensor reading to linguistic description: \<100ms
- LLM inference for typical rule: \<3s
- End-to-end sensor to actuator: \<5s
- Configuration loading: \<2s

**Throughput Targets:**

- Support 100 sensor readings per second
- Process 50 concurrent rules
- Handle 20 device commands per second

### 8.2 Performance Optimization Strategies

#### 8.2.1 Fuzzy Logic Optimization

**Lazy Evaluation:** Compute membership degrees only for sensor types with
active rules.

**Result Caching:** Cache fuzzification results for identical inputs within time
window.

**Vectorization:** Use NumPy for batch membership function computation.

**Precomputation:** Precompute membership function values at initialization for
discrete sensor ranges.

#### 8.2.2 LLM Optimization

**Model Quantization:** Use 4-bit or 8-bit quantized models to reduce memory and
improve inference speed.

**Prompt Optimization:** Minimize prompt length while maintaining clarity to
reduce token processing time.

**Batch Inference:** Group multiple rule evaluations into single LLM call when
applicable.

**KV Cache:** Leverage key-value cache for repeated context to accelerate
inference.

**Hardware Acceleration:** Use GPU or specialized AI accelerators when
available.

#### 8.2.3 System-Level Optimization

**Asynchronous Processing:** Process sensor readings and rule evaluations
asynchronously to prevent blocking.

**Thread Pooling:** Use thread pool for concurrent device communication.

**Memory Management:** Implement memory limits and garbage collection triggers
to prevent unbounded growth.

**I/O Optimization:** Use buffered I/O for log writes and batch configuration
updates.

### 8.3 Scalability Considerations

#### 8.3.1 Vertical Scalability

System scales vertically by utilizing additional CPU cores and memory:

**Multi-threading:** Thread pool for parallel device communication and rule
evaluation.

**Process Isolation:** Optional multi-process architecture for CPU-intensive
components.

**Memory Scaling:** Support for larger models on systems with increased RAM.

#### 8.3.2 Horizontal Scalability Limitations

Current architecture targets single edge device deployment. Horizontal scaling
requires architectural modifications:

**Device Partitioning:** Split device management across multiple system
instances.

**Rule Distribution:** Distribute rule processing based on device groups.

**Shared State:** Implement distributed state management for coordinated
control.

### 8.4 Resource Management

**Memory Budgeting:**

- LLM model: 3-6GB depending on quantization
- Python runtime and libraries: 500MB
- Fuzzy logic and caching: 500MB
- Operating headroom: 1GB

**CPU Allocation:**

- LLM inference: 1-2 cores during active processing
- Device communication: 1 core
- Background tasks: 1 core

**Disk Usage:**

- Model storage: 5-15GB
- Configuration: 10MB
- Logs: 100MB daily (with rotation)
- Cache: 500MB maximum

______________________________________________________________________

## 9. Design Decisions and Rationale

### 9.1 Architectural Decisions

#### Decision 1: Layered Architecture

**Decision:** Employ strict layered architecture with unidirectional
dependencies.

**Rationale:** Clear separation of concerns enables independent testing,
parallel development, and component replacement. Each layer addresses distinct
functional responsibility reducing complexity.

**Alternatives Considered:**

- Microservices architecture: Rejected due to overhead for single-device
  deployment
- Monolithic architecture: Rejected due to tight coupling and testing
  difficulties

**Trade-offs:** Layered architecture adds indirection overhead but provides
superior maintainability and testability.

#### Decision 2: Offline LLM Execution

**Decision:** Require offline-capable LLM without cloud API dependencies.

**Rationale:** Privacy requirements prohibit external data transmission. Edge
deployments may lack reliable internet connectivity. Local execution provides
deterministic latency.

**Alternatives Considered:**

- Cloud-based LLM APIs: Rejected due to privacy and connectivity constraints
- Hybrid cloud-local fallback: Rejected due to complexity and inconsistent
  behavior

**Trade-offs:** Offline execution limits model size and requires local
computational resources but ensures privacy and availability.

#### Decision 3: JSON Configuration Format

**Decision:** Use JSON for all configuration data and membership function
definitions.

**Rationale:** JSON provides human-readable format with widespread tooling
support. Schema validation enables error detection. No additional dependencies
required.

**Alternatives Considered:**

- YAML: Better human readability but requires additional parsing library
- Python configuration files: Maximum flexibility but security risk from code
  execution
- Binary formats: Rejected due to lack of human readability

**Trade-offs:** JSON lacks some expressiveness of YAML but offers better
security and universal support.

#### Decision 4: File-Based Persistence

**Decision:** Store all persistent data in local files without database.

**Rationale:** Minimal dependencies reduce deployment complexity. Sufficient for
expected data volumes. Easy backup and replication through file copies.

**Alternatives Considered:**

- SQLite database: Additional dependency and complexity for limited benefit
- NoSQL database: Overkill for data scale and query complexity

**Trade-offs:** File-based storage limits query capabilities but simplifies
deployment and reduces resource usage.

### 9.2 Component Design Decisions

#### Decision 5: Event Bus for Component Communication

**Decision:** Implement event bus for asynchronous notifications between
components.

**Rationale:** Decouples components reducing direct dependencies. Supports
multiple subscribers for same event type. Simplifies adding new observers
without modifying publishers.

**Alternatives Considered:**

- Direct function calls only: Simpler but creates tight coupling
- Message queue: More robust but excessive for single-process architecture

**Trade-offs:** Event bus adds complexity but improves extensibility and reduces
coupling.

#### Decision 6: Abstract Protocol Adapters

**Decision:** Define abstract interface for device communication with concrete
protocol implementations.

**Rationale:** Isolates protocol-specific code enabling easy addition of new
protocols. Simplifies testing through mock implementations. Reduces coupling
between device layer and upper layers.

**Alternatives Considered:**

- Protocol-specific device handlers: Simpler but duplicates logic across
  protocols
- Universal adapter: Single adapter for all protocols rejected due to complexity

**Trade-offs:** Abstract adapters require additional classes but provide
superior extensibility.

#### Decision 7: Immutable Data Transfer Objects

**Decision:** Use immutable frozen dataclasses for data exchange between
components.

**Rationale:** Prevents accidental modification improving debugging and thread
safety. Clear data ownership semantics. Type checking support.

**Alternatives Considered:**

- Mutable dictionaries: Flexible but error-prone
- Named tuples: Immutable but less expressive than dataclasses

**Trade-offs:** Immutable objects require creating new instances for
modifications but prevent subtle bugs.

### 9.3 Technology Selection Decisions

#### Decision 8: Python Implementation Language

**Decision:** Implement entire system in Python 3.9+.

**Rationale:** Extensive ecosystem for ML and IoT. Transformers library provides
LLM support. Rapid development and prototyping. Cross-platform compatibility.

**Alternatives Considered:**

- C++: Better performance but slower development and limited ML libraries
- Java: Enterprise support but heavier runtime and limited ML ecosystem
- Rust: Memory safety and performance but steeper learning curve

**Trade-offs:** Python's performance limitations acceptable for system
requirements given development velocity benefits.

#### Decision 9: Ollama for LLM Runtime

**Decision:** Use Ollama service for LLM inference instead of direct model
integration.

**Rationale:**

Ollama provides significant advantages for edge LLM deployment:

1. Simplified model management through CLI commands
2. Automatic optimization for target hardware
3. Support for quantized models reducing memory footprint
4. REST API enables language-agnostic integration
5. Model serving separate from application process
6. Efficient memory management with model loading/unloading
7. Easy model switching without code changes
8. Active development and community support

Service architecture isolates model inference from application logic improving
reliability.

**Alternatives Considered:**

- Hugging Face Transformers: Direct Python integration tighter coupling. Manual
  model management. Memory management within Python process. Complex
  optimization configuration. Benefits: More control over inference, no
  additional service.

- llama.cpp with bindings: Better raw performance. More complex setup and
  integration. Limited model support compared to Ollama. Benefits: Lower memory
  usage, faster inference.

- LangChain: Higher-level abstraction unnecessary for this use case. Adds
  dependency overhead. Ollama integration available but adds unnecessary layer.

- Cloud LLM APIs: Violates offline requirement. Privacy concerns. Network
  dependency. Benefits: No local compute, always latest models.

**Trade-offs:**

Ollama adds dependency on external service requiring separate installation and
management. REST API introduces minor network latency but negligible for edge
deployment. Service architecture requires additional monitoring and error
handling. Benefits outweigh overhead through simplified model management and
optimization.

#### Decision 10: MQTT for IoT Communication

**Decision:** Support MQTT as primary IoT communication protocol.

**Rationale:** Lightweight publish-subscribe protocol designed for IoT.
Widespread device support. Efficient for resource-constrained devices. Quality
of service guarantees.

**Alternatives Considered:**

- HTTP REST only: Simpler but less efficient for continuous updates
- CoAP: IoT-optimized but less common device support
- Proprietary protocols: Rejected due to vendor lock-in

**Trade-offs:** MQTT requires broker infrastructure but provides optimal IoT
communication characteristics.

### 9.4 Security Design Decisions

#### Decision 11: No Built-In User Management

**Decision:** Rely on operating system user permissions for access control.

**Rationale:** System runs on trusted edge devices with physical access control.
OS-level permissions sufficient for single-user or small team deployments.
Reduces implementation complexity.

**Alternatives Considered:**

- Built-in user database: Additional complexity for limited benefit
- Integration with external identity provider: Overkill for edge deployment

**Trade-offs:** Limited multi-user support but simplified implementation and
deployment.

#### Decision 12: Command Whitelisting

**Decision:** Validate LLM-generated commands against configured whitelist.

**Rationale:** Prevents malicious or erroneous LLM outputs from executing
dangerous commands. Defense in depth for critical actuators. Explicit user
control over permitted actions.

**Alternatives Considered:**

- Trust LLM output: Unacceptable security risk
- Interactive confirmation: Defeats automation purpose
- Sandboxed execution: Excessive complexity for deterministic commands

**Trade-offs:** Whitelisting requires configuration effort but provides
essential safety guarantees.

______________________________________________________________________

## 10. Appendices

### Appendix A: Technology Stack

**Core Languages and Runtimes:**

- Python 3.9+
- NumPy for numerical computation
- PyTorch for LLM inference

**LLM and ML Libraries:**

- Ollama for LLM runtime
- Accelerate for optimization
- BitsAndBytes for quantization

**IoT Communication:**

- paho-mqtt for MQTT protocol
- requests for HTTP communication
- pyserial for serial communication

**Configuration and Data:**

- json (standard library)
- jsonschema for validation
- dataclasses (standard library)

**Optional Components:**

- Flask for web interface
- Flask-CORS for API access
- sqlite3 for advanced rule storage

**Development and Testing:**

- pytest for unit testing
- pytest-asyncio for async testing
- black for code formatting
- mypy for type checking

### Appendix B: Design Patterns Used

**Adapter Pattern:** Protocol adapters abstract device communication protocols.

**Factory Pattern:** Device registry creates protocol adapter instances based on
configuration.

**Observer Pattern:** Event bus implements observer pattern for component
notifications.

**Strategy Pattern:** Membership function library uses strategy pattern for
different function types.

**Singleton Pattern:** Configuration manager and logging manager implement
singleton pattern.

**Builder Pattern:** Linguistic descriptor builder constructs complex
description strings.

**Template Method:** Base protocol adapter defines communication template with
protocol-specific implementations.

### Appendix C: Future Architecture Enhancements

**Multi-LLM Support:** Architecture supports future enhancement to use
specialized LLMs for different task types (classification, generation,
reasoning).

**Distributed Deployment:** Event bus and abstract interfaces enable future
distributed deployment with message queue backend.

**Advanced Caching:** Current caching strategy extensible to distributed cache
or persistent cache database.

**Plugin Architecture:** Abstract interfaces support future plugin system for
custom membership functions, protocols, and LLM backends.

**Real-Time Constraint Handling:** Architecture accommodates future real-time
scheduling extensions for time-critical control loops.

**Federated Learning:** Offline architecture compatible with future federated
learning for model improvement across deployments without data sharing.
