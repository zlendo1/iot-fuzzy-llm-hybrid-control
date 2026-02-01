# Architecture Design Document

## Fuzzy-LLM Hybrid IoT Management System

______________________________________________________________________

## 1. Introduction

### 1.1 Purpose

This document defines the software architecture for the Fuzzy-LLM Hybrid IoT
Management System. It establishes the system's structural organization,
component responsibilities, communication patterns, and deployment model. This
document serves as the primary reference for all implementation and integration
activities.

### 1.2 Scope

The architecture covers all software components required for offline IoT device
management through natural language rules. Core responsibilities include fuzzy
logic processing of sensor data, LLM-based rule reasoning via Ollama, MQTT-based
device communication, and JSON-driven configuration management. Physical IoT
hardware and device-level firmware fall outside this scope.

### 1.3 Intended Audience

Software developers implementing the system, architects reviewing design
decisions, and technical reviewers validating architectural soundness. Readers
are expected to have familiarity with software architecture patterns, Python,
fuzzy logic fundamentals, and basic knowledge of language models.

### 1.4 Definitions

| Term                | Definition                                                                                                                                   |
| ------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| Membership Function | A mathematical function defining the degree to which a numerical value belongs to a fuzzy linguistic set, returning a value between 0 and 1. |
| Linguistic Variable | A variable whose values are expressed as words or phrases in natural language (e.g., "temperature is hot").                                  |
| Ollama              | An open-source platform for running large language models locally on-device without cloud dependencies.                                      |
| MQTT                | Message Queuing Telemetry Transport — a lightweight publish-subscribe protocol widely adopted for IoT communication.                         |
| Edge Device         | A computing device deployed at the network periphery, close to IoT data sources, with limited computational resources.                       |
| Actuator            | A physical device that performs a control action (e.g., turning on an HVAC unit) in response to a command.                                   |

______________________________________________________________________

## 2. Architectural Overview

### 2.1 Architectural Style

The system adopts a strict layered architecture. Each layer owns a clearly
defined set of responsibilities, and communication flows exclusively between
adjacent layers through well-defined interfaces. No layer may bypass an adjacent
layer to communicate with a non-neighboring layer. Within each layer, internal
components communicate only through a layer coordinator — never directly with
components in other layers.

### 2.2 Design Principles

| Principle           | Description                                                                                                                     |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| Privacy by Design   | All sensor data, rules, and processing remain on-device. No data is transmitted to external services.                           |
| Fail-Safe Operation | The system defaults to safe device states upon component failure. All commands are validated before execution.                  |
| Transparency        | Fuzzy logic mappings are explicit and inspectable. All processing steps are logged for traceability.                            |
| Resource Efficiency | The system is optimized for edge constraints via caching, lazy loading, and efficient data structures.                          |
| Configurability     | System behavior is driven by JSON configuration. Membership functions and device definitions require no code changes to modify. |

### 2.3 Architectural Constraints

| Constraint           | Detail                                                         |
| -------------------- | -------------------------------------------------------------- |
| Language             | Python 3.9 or later                                            |
| LLM Runtime          | Ollama (local service, max 7B parameter models)                |
| Device Protocol      | MQTT via Eclipse Mosquitto broker                              |
| Configuration Format | JSON for all configuration and membership function definitions |
| Network              | No internet connectivity required for core operation           |
| Target Platform      | Linux on x86-64 or ARM64 hardware                              |
| Memory               | 8 GB maximum total footprint including Ollama                  |

______________________________________________________________________

## 3. System Architecture

### 3.1 Layer Overview

The system is organized into five layers. Each layer contains a coordinator
component (shown in bold in the diagram) that serves as the single point of
contact for adjacent layers, and one or more internal components that perform
specialized work within the layer.

| Layer                      | Coordinator                | Responsibility                                                                                     |
| -------------------------- | -------------------------- | -------------------------------------------------------------------------------------------------- |
| User Interface             | —                          | Exposes CLI, optional Web UI, and optional REST API for user interaction.                          |
| Configuration & Management | System Orchestrator        | Manages system lifecycle, configuration loading, rule persistence, and centralized logging.        |
| Control & Reasoning        | Rule Processing Pipeline   | Evaluates natural language rules against sensor state using the LLM and generates device commands. |
| Data Processing            | Fuzzy Processing Pipeline  | Transforms raw numerical sensor data into linguistic descriptions via fuzzy logic.                 |
| Device Interface           | MQTT Communication Manager | Manages all device communication through the MQTT broker.                                          |

### 3.2 Component Diagram

The following diagram illustrates the layered structure. Bold-bordered boxes
represent layer coordinators. Standard boxes represent internal components.
Arrows between layers indicate the direction of the primary data flow. The MQTT
Broker and Ollama Service are external processes managed independently of the
main application.

```
┌─────────────────────────────────────────────────────────────────────┐
│                      USER INTERFACE LAYER                           │
│                                                                     │
│   CLI Interface  |  Web UI (Optional)  |  REST API (Optional)       │
└───────────────────────────────┬─────────────────────────────────────┘
                                │ User commands and queries
┌───────────────────────────────┼─────────────────────────────────────┐
│          CONFIGURATION & MANAGEMENT LAYER                           │
│                               │                                     │
│              ┌────────────────▼────────────────┐                    │
│              │   SYSTEM ORCHESTRATOR           │  ← Coordinator     │
│              └────────────────┬────────────────┘                    │
│                               │                                     │
│   Configuration Manager  |  Rule Manager  |  Logging Manager        │
└───────────────────────────────┼─────────────────────────────────────┘
                                │ System state, configurations
┌───────────────────────────────┼─────────────────────────────────────┐
│              CONTROL & REASONING LAYER                              │
│                               │                                     │
│              ┌────────────────▼────────────────┐                    │
│              │   RULE PROCESSING PIPELINE      │  ← Coordinator     │
│              └────────────────┬────────────────┘                    │
│                               │                          ┌────────────────┐
│   Rule Interpreter  |  Ollama Client  |  Command Gen.    │ Ollama Service │
│                                                          │ (External)     │
└───────────────────────────────┼──────────────────────────└────────────────┘
                                │ Linguistic descriptions, commands
┌───────────────────────────────┼─────────────────────────────────────┐
│              DATA PROCESSING LAYER                                  │
│                               │                                     │
│              ┌────────────────▼────────────────┐                    │
│              │   FUZZY PROCESSING PIPELINE     │  ← Coordinator     │
│              └────────────────┬────────────────┘                    │
│                               │                                     │
│  Fuzzy Engine  |  Membership Function Library  |  Descriptor Builder│
└───────────────────────────────┼─────────────────────────────────────┘
                                │ Sensor readings, device commands
┌───────────────────────────────┼─────────────────────────────────────┐
│              DEVICE INTERFACE LAYER                                 │
│                               │                                     │
│              ┌────────────────▼────────────────┐                    │
│              │   MQTT COMMUNICATION MANAGER    │  ← Coordinator     │
│              └────────────────┬────────────────┘                    │
│                               │                                     │
│   Device Registry  |  MQTT Client  |  Device Monitor                │
└───────────────────────────────┼─────────────────────────────────────┘
                                │ MQTT messages
                    ┌───────────▼───────────┐
                    │   MQTT Broker         │
                    │   (Eclipse Mosquitto) │  ← External
                    └───────────┬───────────┘
                                │ Device communication
                    ┌───────────▼───────────┐
                    │   Sensors | Actuators │  ← Physical Devices
                    └───────────────────────┘
```

### 3.3 Component Descriptions

#### 3.3.1 Device Interface Layer

MQTT Communication Manager coordinates all device I/O and is the sole interface
between the Device Interface Layer and the Data Processing Layer above it.

- **Device Registry** — Maintains the inventory of all configured sensors and
  actuators, including their MQTT topics, capabilities, and metadata.
- **MQTT Client** — Manages the connection to the Mosquitto broker, handles
  topic subscriptions for sensor data, publishes commands to actuator topics,
  and implements reconnection logic.
- **Device Monitor** — Tracks device availability using MQTT Last Will and
  Testament messages and periodic heartbeats. Reports device failures to the
  logging system.

#### 3.3.2 Data Processing Layer

Fuzzy Processing Pipeline transforms raw sensor readings into linguistic
descriptions and is the sole interface between the Device Interface Layer and
the Control & Reasoning Layer.

- **Fuzzy Engine** — Applies membership functions to numerical sensor values and
  computes membership degrees for all configured linguistic terms.
- **Membership Function Library** — Provides implementations of triangular,
  trapezoidal, Gaussian, and sigmoid membership functions. Supports registration
  of custom function types.
- **Linguistic Descriptor Builder** — Formats the output of the Fuzzy Engine
  into structured natural language descriptions suitable for LLM consumption
  (e.g., "temperature is hot (0.85)").

#### 3.3.3 Control & Reasoning Layer

Rule Processing Pipeline orchestrates the full rule evaluation workflow and is
the sole interface between the Data Processing Layer and the Configuration &
Management Layer.

- **Rule Interpreter** — Matches current linguistic sensor states against stored
  rules to identify candidates for evaluation. Implements conflict resolution
  when multiple rules generate commands for the same device.
- **Ollama Client** — Communicates with the Ollama service via its REST API.
  Constructs prompts from sensor states and rule text, submits them for
  inference, and parses the LLM response to extract structured control actions.
- **Command Generator** — Translates abstract actions from the LLM into concrete
  device commands. Validates each command against device capabilities and
  configured safety constraints before passing it for execution.

#### 3.3.4 Configuration & Management Layer

System Orchestrator manages the full system lifecycle and coordinates
initialization, runtime, and shutdown across all layers.

- **Configuration Manager** — Loads and validates all JSON configuration files.
  Provides configuration data to other components. Supports runtime
  configuration updates with automatic backup.
- **Rule Manager** — Provides persistent storage for natural language rules with
  full CRUD support, metadata tracking, and import/export capabilities.
- **Logging Manager** — Centralized structured logging for all system events
  including sensor readings, rule evaluations, device commands, and errors.

#### 3.3.5 User Interface Layer

- **CLI Interface** — Primary interaction tool for system administration, rule
  management, and status monitoring.
- **Web UI (Optional)** — Browser-based interface providing visual rule editing,
  real-time sensor status, and execution history.
- **REST API (Optional)** — HTTP API for programmatic system access and
  third-party integration.

______________________________________________________________________

## 4. Component Interactions

### 4.1 Sensor Data Processing Flow

This flow begins when the MQTT Client receives a sensor reading and ends when a
linguistic description is cached and available for rule evaluation.

| Step | Action                                                                                                          | From → To                                                        |
| ---- | --------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------- |
| 1    | MQTT Client receives sensor value on subscribed topic.                                                          | MQTT Broker → MQTT Client                                        |
| 2    | MQTT Communication Manager routes the reading to the layer above.                                               | MQTT Comm. Manager → Fuzzy Processing Pipeline                   |
| 3    | Fuzzy Processing Pipeline requests membership functions from Configuration Manager via the System Orchestrator. | Fuzzy Processing Pipeline → System Orchestrator → Config Manager |
| 4    | Fuzzy Engine applies membership functions to the numerical value, producing linguistic terms with degrees.      | Fuzzy Engine (internal)                                          |
| 5    | Linguistic Descriptor Builder formats the result into a natural language description.                           | Linguistic Descriptor Builder (internal)                         |
| 6    | Fuzzy Processing Pipeline caches the description and notifies the Rule Processing Pipeline of a state change.   | Fuzzy Processing Pipeline → Rule Processing Pipeline             |

### 4.2 Rule Evaluation Flow

This flow is triggered when the sensor state changes or on a scheduled interval.
It begins with rule matching and ends with command execution.

| Step | Action                                                                                                                  | From → To                                            |
| ---- | ----------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------- |
| 1    | Rule Processing Pipeline requests the current system state (linguistic descriptions) from Fuzzy Processing Pipeline.    | Rule Processing Pipeline → Fuzzy Processing Pipeline |
| 2    | Rule Interpreter identifies candidate rules whose conditions may match the current state.                               | Rule Interpreter (internal)                          |
| 3    | Ollama Client constructs a prompt containing the sensor state and the rule text, then submits it to Ollama.             | Ollama Client → Ollama Service                       |
| 4    | Ollama returns a text response indicating whether the rule applies and what action to take.                             | Ollama Service → Ollama Client                       |
| 5    | Ollama Client parses the response to extract a structured action specification.                                         | Ollama Client (internal)                             |
| 6    | Command Generator validates the action against device capabilities and safety constraints.                              | Command Generator (internal)                         |
| 7    | If conflict resolution is needed (multiple commands targeting the same device), Rule Interpreter resolves the conflict. | Rule Interpreter (internal)                          |
| 8    | Validated commands are passed to MQTT Communication Manager for publication.                                            | Rule Processing Pipeline → MQTT Comm. Manager        |
| 9    | MQTT Client publishes the command to the appropriate actuator topic.                                                    | MQTT Client → MQTT Broker → Actuator                 |

### 4.3 System Startup Flow

| Step | Action                                                                                                |
| ---- | ----------------------------------------------------------------------------------------------------- |
| 1    | System Orchestrator loads and validates all configuration files via Configuration Manager.            |
| 2    | Logging Manager is initialized.                                                                       |
| 3    | Device Registry is populated from device configuration.                                               |
| 4    | MQTT Client connects to Mosquitto broker and subscribes to all configured sensor topics.              |
| 5    | Ollama Client verifies connectivity to Ollama service and confirms the configured model is available. |
| 6    | Membership functions are loaded and validated.                                                        |
| 7    | Rule Manager loads all persisted rules. Rule Interpreter indexes them.                                |
| 8    | Device Monitor begins tracking device availability.                                                   |
| 9    | User interfaces are initialized. System enters the ready state.                                       |

______________________________________________________________________

## 5. Data Architecture

### 5.1 Persistence Model

All persistent data is stored as local JSON files. No database is required.
Atomic write-rename operations prevent file corruption. The Configuration
Manager creates timestamped backups before each modification.

### 5.2 Configuration Schemas

#### 5.2.1 Membership Function Configuration

One file per sensor type, located in `config/membership_functions/`.

```json
{
  "sensor_type": "temperature",
  "unit": "celsius",
  "universe_of_discourse": { "min": -10.0, "max": 50.0 },
  "confidence_threshold": 0.1,
  "linguistic_variables": [
    {
      "term": "cold",
      "function_type": "trapezoidal",
      "parameters": { "a": -10.0, "b": 0.0, "c": 10.0, "d": 15.0 }
    },
    {
      "term": "comfortable",
      "function_type": "triangular",
      "parameters": { "a": 10.0, "b": 20.0, "c": 25.0 }
    },
    {
      "term": "hot",
      "function_type": "trapezoidal",
      "parameters": { "a": 22.0, "b": 27.0, "c": 40.0, "d": 50.0 }
    }
  ]
}
```

#### 5.2.2 Device Configuration

```json
{
  "devices": [
    {
      "device_id": "temp_sensor_living_room",
      "device_type": "sensor",
      "sensor_type": "temperature",
      "location": "Living Room",
      "mqtt": {
        "topic": "home/living_room/temperature",
        "qos": 1,
        "retain": false
      },
      "polling_interval_seconds": 60
    },
    {
      "device_id": "hvac_living_room",
      "device_type": "actuator",
      "location": "Living Room",
      "mqtt": {
        "topic": "home/living_room/hvac/command",
        "status_topic": "home/living_room/hvac/status",
        "qos": 1,
        "retain": true
      },
      "capabilities": ["set_temperature", "set_mode", "power_on", "power_off"],
      "constraints": {
        "temperature_min": 16,
        "temperature_max": 30,
        "modes": ["heating", "cooling", "auto", "off"]
      }
    }
  ]
}
```

#### 5.2.3 MQTT Configuration

```json
{
  "mqtt": {
    "broker": {
      "host": "localhost",
      "port": 1883,
      "keepalive": 60
    },
    "authentication": {
      "username": "iot_system",
      "password": "secure_password",
      "use_tls": false
    },
    "client": {
      "client_id": "fuzzy_llm_iot_system",
      "clean_session": true
    },
    "reconnection": {
      "enabled": true,
      "delay_min_seconds": 1,
      "delay_max_seconds": 60
    },
    "last_will": {
      "topic": "system/fuzzy_llm_iot/status",
      "payload": "offline",
      "qos": 1,
      "retain": true
    }
  }
}
```

#### 5.2.4 Ollama / LLM Configuration

```json
{
  "llm": {
    "provider": "ollama",
    "connection": {
      "host": "localhost",
      "port": 11434,
      "timeout_seconds": 30
    },
    "model": {
      "name": "mistral:7b-instruct",
      "fallback_models": ["llama3.2:7b-instruct", "phi3:3.8b"]
    },
    "inference": {
      "temperature": 0.3,
      "max_tokens": 512,
      "top_p": 0.9,
      "top_k": 40,
      "repeat_penalty": 1.1
    },
    "context": {
      "enabled": false,
      "max_history": 5
    }
  }
}
```

#### 5.2.5 System Configuration

```json
{
  "system": { "name": "Fuzzy-LLM IoT System", "version": "1.0.0" },
  "processing": {
    "fuzzy": { "confidence_threshold": 0.1, "cache_ttl_seconds": 300 },
    "rules": { "evaluation_interval_seconds": 5, "conflict_resolution": "priority" }
  },
  "logging": {
    "level": "INFO",
    "format": "json",
    "rotation": { "max_bytes": 104857600, "retention_days": 30 }
  },
  "safety": {
    "command_whitelist_enabled": true,
    "rate_limit": { "enabled": true, "max_commands_per_minute": 60 }
  }
}
```

#### 5.2.6 Rule Storage

```json
{
  "rules": [
    {
      "rule_id": "rule_001",
      "rule_text": "If the temperature is hot and humidity is high, turn on the air conditioner",
      "priority": 1,
      "enabled": true,
      "created_timestamp": "2026-01-15T10:00:00Z",
      "last_triggered": "2026-01-15T14:30:00Z",
      "trigger_count": 12,
      "metadata": { "tags": ["climate", "cooling"] }
    }
  ]
}
```

### 5.3 Caching Strategy

| Cache         | Scope                               | Eviction Policy                                     | Rationale                                                                    |
| ------------- | ----------------------------------- | --------------------------------------------------- | ---------------------------------------------------------------------------- |
| Fuzzy Results | Per sensor type, up to 1000 entries | LRU with 300 s TTL                                  | Avoids redundant membership function computation for repeated sensor values. |
| Device Status | Per device                          | TTL 60 s, updated on MQTT status message            | Reduces repeated broker queries for device availability checks.              |
| Configuration | Entire configuration tree           | Invalidated on file modification or explicit reload | Avoids repeated file I/O for frequently accessed parameters.                 |

______________________________________________________________________

## 6. Deployment Architecture

### 6.1 Deployment Model

The primary deployment target is a single edge device running all system
components locally. The following services must be available on the host:

| Service     | Technology         | Port  | Role                                                                             |
| ----------- | ------------------ | ----- | -------------------------------------------------------------------------------- |
| MQTT Broker | Eclipse Mosquitto  | 1883  | Message routing between IoT devices and the system.                              |
| LLM Runtime | Ollama             | 11434 | Offline LLM inference for rule evaluation.                                       |
| IoT System  | Python Application | —     | Core application orchestrating fuzzy logic, rule evaluation, and device control. |
| Web UI      | Flask (Optional)   | 5000  | Browser-based rule management and monitoring interface.                          |

### 6.2 Directory Structure

```
/opt/fuzzy-llm-iot/
├── bin/                          # Startup and setup scripts
├── config/
│   ├── membership_functions/     # One JSON file per sensor type
│   ├── devices.json
│   ├── mqtt_config.json
│   ├── llm_config.json
│   ├── system_config.json
│   └── prompt_template.txt
├── rules/
│   └── active_rules.json
├── logs/                         # System, command, sensor, and error logs
├── src/
│   ├── main.py
│   ├── device_interface/         # MQTT client, registry, monitor
│   ├── data_processing/          # Fuzzy engine, membership functions, descriptor
│   ├── control_reasoning/        # Rule interpreter, Ollama client, command generator
│   ├── configuration/            # Config manager, rule manager, logging manager
│   └── interfaces/               # CLI and optional web UI
├── tests/
├── requirements.txt
└── README.md
```

### 6.3 Resource Budget

| Resource                       | Budget  | Allocation                                         |
| ------------------------------ | ------- | -------------------------------------------------- |
| RAM — Ollama (7B model, 4-bit) | 4.0 GB  | LLM model weights and inference buffers.           |
| RAM — OS and base services     | 1.5 GB  | Operating system, Mosquitto, background processes. |
| RAM — Python application       | 1.0 GB  | Runtime, fuzzy engine, caches, rule data.          |
| RAM — Headroom                 | 1.5 GB  | Buffer for peak usage and garbage collection.      |
| Disk — LLM model               | 4–8 GB  | Depends on quantization level selected.            |
| Disk — Logs (30-day retention) | ~3 GB   | Rotated daily, compressed after 24 hours.          |
| Disk — Code and configuration  | ~200 MB | Application files and JSON configs.                |

### 6.4 Containerized Deployment (Optional)

The system can be deployed using Docker Compose with three containers: one for
the Mosquitto MQTT broker, one for the Ollama service, and one for the Python
application. Configuration files, rule data, and logs are mounted as volumes to
allow persistence and easy modification without rebuilding images. GPU access
for the Ollama container is optional and managed via the NVIDIA container
runtime.

______________________________________________________________________

## 7. Security Architecture

### 7.1 Threat Boundaries

| Threat Surface                         | Mitigation                                                                                                                                                    |
| -------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| External network access to sensor data | All processing is local. No data is transmitted externally. Firewall rules restrict MQTT and Ollama to localhost.                                             |
| Unauthorized MQTT access               | Mosquitto supports username/password and TLS client certificate authentication. ACLs restrict per-device topic access.                                        |
| Malicious or erroneous LLM output      | All LLM-generated commands are parsed, validated against a device capability whitelist, and checked against configured safety constraints before execution.   |
| Configuration tampering                | Configuration files use restrictive filesystem permissions. Backups are created before every modification. Schema validation rejects malformed files on load. |
| Excessive command rate                 | A configurable rate limiter prevents more than a set number of commands per device per minute.                                                                |

### 7.2 Command Validation Pipeline

Every command generated by the LLM passes through the following checks before
execution. A command that fails any check is rejected and logged.

| Step | Check                                                                                                      | Failure Action                                      |
| ---- | ---------------------------------------------------------------------------------------------------------- | --------------------------------------------------- |
| 1    | Response Parsing — Verify the LLM output matches the expected ACTION format.                               | Reject; log malformed response.                     |
| 2    | Device Existence — Confirm the target device ID exists in the Device Registry.                             | Reject; log unknown device reference.               |
| 3    | Capability Match — Confirm the command type is in the device's capability list.                            | Reject; log unsupported command.                    |
| 4    | Parameter Constraints — Validate all parameters against device-specific min/max bounds and allowed values. | Reject; log constraint violation.                   |
| 5    | Safety Whitelist — Confirm the command type is in the global safety whitelist.                             | Reject; log whitelist violation.                    |
| 6    | Rate Limit — Check that the device has not exceeded its per-minute command limit.                          | Reject; log rate limit breach.                      |
| 7    | Critical Command Flag — If the command targets a critical device, flag for user confirmation.              | Queue for confirmation; do not execute immediately. |

______________________________________________________________________

## 8. Performance and Scalability

### 8.1 Latency Targets

| Operation                                      | Target   | Rationale                                                      |
| ---------------------------------------------- | -------- | -------------------------------------------------------------- |
| Fuzzy logic processing (per sensor)            | < 50 ms  | Minimal preprocessing overhead before LLM evaluation.          |
| Sensor reading to linguistic description       | < 100 ms | Ensures prompt data is current when rule evaluation begins.    |
| LLM inference (single rule)                    | < 3 s    | Acceptable delay for non-emergency control decisions.          |
| Command generation and validation              | < 100 ms | Negligible overhead after LLM inference completes.             |
| End-to-end (sensor change to actuator command) | < 5 s    | Maximum acceptable latency for typical IoT scenarios.          |
| System startup                                 | < 30 s   | Includes Ollama model verification and MQTT broker connection. |

### 8.2 Optimization Strategies

| Area          | Strategy                                                                                                                                                                    |
| ------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Fuzzy Logic   | Cache fuzzification results with TTL. Use NumPy vectorization for batch computation. Skip terms below confidence threshold.                                                 |
| LLM Inference | Use quantized models (4-bit preferred) to reduce memory and improve throughput. Minimize prompt length. Consider batch evaluation for multiple related rules.               |
| MQTT          | Use wildcard subscriptions to reduce broker load. Select QoS level per topic based on data criticality. Implement connection pooling.                                       |
| System        | Process sensor readings and rule evaluations asynchronously. Use thread pools for parallel device communication. Implement memory monitoring with automatic cache eviction. |

### 8.3 Scalability Limits

The single-device architecture supports up to approximately 200 connected
devices, 1,000 active rules, and 100 sensor readings per second. Exceeding these
limits requires a distributed deployment model in which multiple edge nodes
share a common MQTT broker and coordinate via a central rule repository.

______________________________________________________________________

## 9. Design Decisions and Rationale

### DD-01: Strict Layered Architecture

- **Decision:** Communication between layers flows exclusively through adjacent
  layers via coordinator components. Internal components do not communicate
  across layer boundaries.
- **Rationale:** Enforces separation of concerns, reduces coupling, and makes
  the system testable at each layer independently.
- **Alternatives considered:** Microservices — rejected due to unnecessary
  network overhead on a single device. Monolithic — rejected due to tight
  coupling.

### DD-02: Ollama for LLM Inference

- **Decision:** LLM inference is handled by the Ollama service, accessed via its
  REST API.
- **Rationale:** Ollama simplifies model management, handles quantization and
  memory optimization automatically, and isolates model loading from the
  application process. It supports easy model switching via configuration.
- **Alternatives considered:** Hugging Face Transformers — more complex setup,
  higher memory overhead, and tighter coupling to Python process. llama.cpp —
  better raw performance but harder integration and narrower model support.

### DD-03: MQTT as Device Protocol

- **Decision:** MQTT is the primary protocol for all sensor and actuator
  communication, brokered by Mosquitto.
- **Rationale:** MQTT is lightweight, natively supports pub-sub for IoT,
  provides QoS guarantees, and enables device monitoring via Last Will and
  Testament messages.
- **Alternatives considered:** HTTP REST — inefficient for continuous sensor
  streams due to polling overhead. CoAP — less broad device support. Proprietary
  — rejected due to vendor lock-in.

### DD-04: JSON for All Configuration

- **Decision:** Membership functions, device definitions, system parameters, and
  rules are all stored as JSON.
- **Rationale:** JSON is human-readable, universally supported,
  schema-validatable, and requires no code execution — unlike Python config
  files.
- **Alternatives considered:** YAML — slightly more readable but requires an
  additional parsing library. XML — verbose and declining in modern use.

### DD-05: File-Based Persistence

- **Decision:** All persistent data is stored as local files. No database is
  used.
- **Rationale:** Eliminates a deployment dependency. File volumes are sufficient
  for the expected data scale. Enables trivial backup via file copy.
- **Alternatives considered:** SQLite — unnecessary complexity for the data
  volume. NoSQL databases — significant overhead for edge deployment.

### DD-06: Per-Rule LLM Prompting

- **Decision:** Each rule is evaluated in a separate LLM inference call rather
  than batching all rules into one prompt.
- **Rationale:** Focused prompts improve LLM accuracy and simplify response
  parsing. Independent calls enable parallel evaluation and clear attribution of
  commands to specific rules.
- **Alternatives considered:** Batch prompting — reduces API calls but increases
  prompt complexity and makes output parsing unreliable.

### DD-07: Command Validation Before Execution

- **Decision:** All LLM-generated commands pass through a multi-step validation
  pipeline before being published to MQTT.
- **Rationale:** LLMs can produce hallucinated or invalid outputs. Validation
  against device capabilities, safety whitelists, and rate limits prevents
  erroneous or dangerous commands from reaching physical devices.
- **Alternatives considered:** Trusting LLM output directly — unacceptable risk
  for physical device control.

______________________________________________________________________

## 10. Appendices

### Appendix A: Technology Stack

| Category    | Technology                    | Role                                                      |
| ----------- | ----------------------------- | --------------------------------------------------------- |
| Language    | Python 3.9+                   | Core application implementation.                          |
| LLM Runtime | Ollama                        | Local LLM model serving and inference.                    |
| LLM Model   | Mistral 7B Instruct (default) | Natural language rule processing and decision generation. |
| MQTT Broker | Eclipse Mosquitto 2.0+        | Message routing for IoT device communication.             |
| MQTT Client | paho-mqtt                     | Python MQTT client library.                               |
| HTTP Client | requests                      | REST communication with Ollama API.                       |
| Numerical   | NumPy                         | Vectorized membership function computation.               |
| Validation  | jsonschema                    | JSON configuration schema validation.                     |
| Web UI      | Flask (optional)              | Lightweight HTTP server for web interface.                |
| Testing     | pytest                        | Unit and integration testing framework.                   |

### Appendix B: Ollama API Reference

The Ollama Client interacts with the Ollama service using the following
endpoints.

| Endpoint                            | Method | Purpose                                                      |
| ----------------------------------- | ------ | ------------------------------------------------------------ |
| `http://{host}:{port}/`             | GET    | Health check — confirms Ollama service is running.           |
| `http://{host}:{port}/api/tags`     | GET    | Lists all locally available models.                          |
| `http://{host}:{port}/api/generate` | POST   | Submits a prompt and receives a generated text response.     |
| `http://{host}:{port}/api/pull`     | POST   | Downloads a model to local storage (used during setup only). |

### Appendix C: MQTT Topic Convention

The system uses the following topic hierarchy for device communication.

| Topic Pattern                    | Direction         | Purpose                                        |
| -------------------------------- | ----------------- | ---------------------------------------------- |
| `home/{zone}/{sensor_type}`      | Sensor → System   | Sensor data publications.                      |
| `home/{zone}/{actuator}/command` | System → Actuator | Control commands to actuators.                 |
| `home/{zone}/{actuator}/status`  | Actuator → System | Actuator state confirmations.                  |
| `system/fuzzy_llm_iot/status`    | System → Broker   | System online/offline Last Will and Testament. |
| `{device_id}/heartbeat`          | Device → System   | Periodic device availability heartbeat.        |

### Appendix D: Design Patterns

| Pattern              | Usage                                                                                                                    |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| Layered Architecture | System-wide structural organization with strict adjacent-layer communication.                                            |
| Adapter              | Protocol adapters abstract device-specific communication details behind a unified interface.                             |
| Factory              | Device Registry creates appropriate communication handlers based on device configuration.                                |
| Strategy             | Membership Function Library applies different function types (triangular, trapezoidal, etc.) through a common interface. |
| Observer             | Event bus notifies components of state changes (e.g., sensor updates triggering rule evaluation) without tight coupling. |
| Builder              | Linguistic Descriptor Builder assembles complex description strings from structured fuzzy logic output.                  |
| Singleton            | Configuration Manager and Logging Manager maintain single instances accessible system-wide.                              |
