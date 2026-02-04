# Engineering Task List

## Fuzzy-LLM Hybrid IoT Management System

**Document Status:** Active\
**Last Updated:** 2026-02-04\
**Source Documents:** [wbs.md](wbs.md), [add.md](add.md), [srs.md](srs.md)

______________________________________________________________________

## Overview

This document provides a **chronologically ordered engineering task list**
optimized for autonomous implementation units. Tasks are organized to ensure:

1. **Incremental delivery** — Each phase produces working, testable code
2. **Dependency satisfaction** — Prerequisites are completed before dependent
   tasks
3. **Bottom-up construction** — Foundation layers built before upper layers
4. **Continuous validation** — Tests accompany each implementation phase

### Implementation Strategy

The architecture follows a strict **5-layer design** (Device Interface → Data
Processing → Control & Reasoning → Configuration & Management → User Interface).
Tasks are ordered bottom-up to ensure each layer can be tested independently
before integration.

**Development Environment:** All services (MQTT broker, Ollama LLM, Python
application) are containerized via Docker Compose for consistent development,
testing, and deployment. A Makefile provides convenient commands for common
development tasks.

**Critical Path:** Foundation & Docker → Device Interface → Data Processing
(Semantic Bridge) → Control & Reasoning → Configuration & Management → User
Interface → Integration → Testing → Demo

______________________________________________________________________

## Phase 0: Foundation & Environment Setup

**Goal:** Establish development environment, Docker containerization, and
project infrastructure.

### 0.1 Project Structure & Python Environment

| Task ID | Task                       | Description                                                                               | Acceptance Criteria                                                        | Est. Hours |
| ------- | -------------------------- | ----------------------------------------------------------------------------------------- | -------------------------------------------------------------------------- | ---------- |
| F-001   | Project structure creation | Create directory structure per ADD Section 6.2                                            | All directories exist: src/, config/, rules/, logs/, tests/, bin/, docker/ | 1h         |
| F-002   | Python environment setup   | Create virtual environment with Python 3.9+, configure pyproject.toml or requirements.txt | `python --version` shows 3.9+, venv activates successfully                 | 1h         |
| F-003   | Install core dependencies  | Install paho-mqtt, requests, numpy, jsonschema, click, pytest, pytest-cov                 | All packages install without errors, `pip list` shows all dependencies     | 1h         |
| F-004   | requirements.txt creation  | Create requirements.txt with pinned versions for reproducibility                          | `pip install -r requirements.txt` succeeds on clean venv                   | 1h         |

### 0.2 Docker Containerization

| Task ID | Task                        | Description                                                         | Acceptance Criteria                                  | Est. Hours |
| ------- | --------------------------- | ------------------------------------------------------------------- | ---------------------------------------------------- | ---------- |
| F-005   | Docker directory structure  | Create docker/ directory with subdirectories for each service       | docker/mosquitto/, docker/ollama/, docker/app/ exist | 0.5h       |
| F-006   | Mosquitto Dockerfile        | Create Dockerfile for Eclipse Mosquitto with custom config          | `docker build` succeeds, image runs                  | 1h         |
| F-007   | Mosquitto configuration     | Create mosquitto.conf with authentication, persistence, and logging | Config enables auth, logs to volume                  | 1h         |
| F-008   | Ollama Dockerfile           | Create Dockerfile for Ollama service with model pre-pull script     | `docker build` succeeds, Ollama service starts       | 1.5h       |
| F-009   | Ollama model initialization | Create entrypoint script to pull Mistral 7B on first run            | Model available after container starts               | 1h         |
| F-010   | Application Dockerfile      | Create multi-stage Dockerfile for Python application                | `docker build` succeeds, app runs in container       | 2h         |
| F-011   | Application entrypoint      | Create entrypoint.sh with proper signal handling                    | Container responds to SIGTERM gracefully             | 0.5h       |
| F-012   | docker-compose.yml          | Create Docker Compose file orchestrating all services               | `docker-compose up` starts all services              | 2h         |
| F-013   | Docker networking           | Configure Docker network for inter-container communication          | Containers communicate via service names             | 0.5h       |
| F-014   | Docker volumes              | Configure volumes for persistence (logs, config, rules, models)     | Data persists across container restarts              | 1h         |
| F-015   | Docker environment files    | Create .env.example and .env for configuration                      | Environment variables configurable                   | 0.5h       |
| F-016   | Docker health checks        | Add health checks for all services in docker-compose                | `docker-compose ps` shows health status              | 1h         |
| F-017   | GPU support for Ollama      | Configure optional NVIDIA GPU passthrough for Ollama container      | GPU available in container when present              | 1h         |
| F-018   | Docker documentation        | Document Docker setup in docker/README.md                           | README covers build, run, and troubleshooting        | 1h         |

**Docker Compose Services:**

```yaml
services:
  mosquitto:    # MQTT broker on port 1883
  ollama:       # LLM service on port 11434
  app:          # Python application (depends on mosquitto, ollama)
```

**Volume Mounts:**

| Volume         | Container Path  | Purpose             |
| -------------- | --------------- | ------------------- |
| ./config       | /app/config     | Configuration files |
| ./rules        | /app/rules      | Rule persistence    |
| ./logs         | /app/logs       | Application logs    |
| mosquitto-data | /mosquitto/data | MQTT persistence    |
| mosquitto-logs | /mosquitto/log  | MQTT logs           |
| ollama-models  | /root/.ollama   | LLM models          |

### 0.3 Makefile for Development

| Task ID | Task                     | Description                                           | Acceptance Criteria                                 | Est. Hours |
| ------- | ------------------------ | ----------------------------------------------------- | --------------------------------------------------- | ---------- |
| F-019   | Makefile creation        | Create Makefile with development convenience commands | `make help` shows all available commands            | 1h         |
| F-020   | Docker commands          | Add make targets for Docker operations                | `make up`, `make down`, `make build` work           | 0.5h       |
| F-021   | Development commands     | Add make targets for local development                | `make dev`, `make install` work                     | 0.5h       |
| F-022   | Test commands            | Add make targets for testing                          | `make test`, `make coverage`, `make test-unit` work | 0.5h       |
| F-023   | Lint and format commands | Add make targets for code quality                     | `make lint`, `make format` work                     | 0.5h       |
| F-024   | Utility commands         | Add make targets for common utilities                 | `make clean`, `make logs`, `make shell` work        | 0.5h       |

**Makefile Targets:**

```makefile
# Docker Commands
make build          # Build all Docker images
make up             # Start all services (docker-compose up -d)
make down           # Stop all services (docker-compose down)
make restart        # Restart all services
make logs           # Tail logs from all services
make logs-app       # Tail logs from app service only
make ps             # Show running containers
make shell          # Open shell in app container
make shell-mqtt     # Open shell in mosquitto container

# Development Commands
make install        # Install Python dependencies locally
make dev            # Run app locally (outside Docker)
make dev-deps       # Start only mosquitto and ollama in Docker

# Testing Commands
make test           # Run all tests
make test-unit      # Run unit tests only
make test-int       # Run integration tests only
make coverage       # Run tests with coverage report
make coverage-html  # Generate HTML coverage report

# Code Quality Commands
make lint           # Run linters (ruff, mypy)
make format         # Format code (black, isort)
make check          # Run all checks (lint + test)

# Utility Commands
make clean          # Remove build artifacts, __pycache__, etc.
make clean-docker   # Remove Docker volumes and images
make reset          # Full reset (clean + clean-docker)
make help           # Show all available commands

# Model Management
make pull-model     # Pull LLM model into Ollama container
make list-models    # List available models in Ollama
```

### 0.4 Common Infrastructure

| Task ID | Task                      | Description                                                           | Acceptance Criteria                            | Est. Hours |
| ------- | ------------------------- | --------------------------------------------------------------------- | ---------------------------------------------- | ---------- |
| F-025   | Logging infrastructure    | Create base logging configuration with structured JSON output         | Logger writes to logs/ directory with rotation | 2h         |
| F-026   | Common utilities module   | Create shared utilities: file I/O, JSON helpers, timestamp formatting | Utility functions pass unit tests              | 2h         |
| F-027   | Base exception classes    | Define custom exception hierarchy for the system                      | Exceptions importable from common module       | 1h         |
| F-028   | Configuration loader base | Create base configuration loading with environment variable support   | Config loads from files and env vars           | 1.5h       |

### 0.5 Development Environment Validation

| Task ID | Task                     | Description                                           | Acceptance Criteria                             | Est. Hours |
| ------- | ------------------------ | ----------------------------------------------------- | ----------------------------------------------- | ---------- |
| F-029   | Docker smoke test        | Verify all containers start and communicate           | `make up && make ps` shows all healthy          | 0.5h       |
| F-030   | MQTT connectivity test   | Verify MQTT broker accessible from app container      | App container publishes/subscribes successfully | 0.5h       |
| F-031   | Ollama connectivity test | Verify Ollama accessible from app container           | App container sends prompt, receives response   | 0.5h       |
| F-032   | Volume persistence test  | Verify data persists across container restarts        | Data survives `make down && make up`            | 0.5h       |
| F-033   | Local development test   | Verify local dev workflow with containerized services | `make dev-deps && make dev` works               | 0.5h       |

**Phase Deliverable:** Fully containerized development environment with all
services orchestrated via Docker Compose and convenient Makefile commands.

**Validation:**

- [ ] `make build` — All Docker images build successfully
- [ ] `make up` — All containers start and show healthy status
- [ ] `make test` — Foundation tests pass
- [ ] `make shell` — Can access app container shell
- [ ] Local development with `make dev-deps && make dev` works

______________________________________________________________________

## Phase 1: Device Interface Layer

**Goal:** Implement MQTT-based device communication (Layer 5 — Bottom).

**SRS References:** FR-DC-001 to FR-DC-007

### 1.1 Device Registry

| Task ID | Task                        | Description                                                            | Acceptance Criteria                                   | Est. Hours |
| ------- | --------------------------- | ---------------------------------------------------------------------- | ----------------------------------------------------- | ---------- |
| DI-001  | Device configuration schema | Define JSON schema for devices.json (sensors, actuators, MQTT topics)  | Schema validates example device configurations        | 2h         |
| DI-002  | Device data models          | Create dataclasses/models for Device, Sensor, Actuator with type hints | Models instantiate correctly from dict/JSON           | 3h         |
| DI-003  | Device Registry class       | Implement DeviceRegistry: load devices, lookup by ID, filter by type   | Registry loads devices.json, returns devices by query | 4h         |
| DI-004  | Device Registry tests       | Unit tests for DeviceRegistry with mock data                           | 95% coverage for device_registry.py                   | 2h         |

### 1.2 MQTT Client

| Task ID | Task                      | Description                                                                             | Acceptance Criteria                                | Est. Hours |
| ------- | ------------------------- | --------------------------------------------------------------------------------------- | -------------------------------------------------- | ---------- |
| DI-005  | MQTT configuration schema | Define JSON schema for mqtt_config.json (broker, auth, client settings)                 | Schema validates example MQTT configurations       | 1h         |
| DI-006  | MQTT Client wrapper       | Implement MQTTClient class wrapping paho-mqtt with connect/disconnect/publish/subscribe | Client connects to Mosquitto broker                | 4h         |
| DI-007  | Connection lifecycle      | Implement connect, disconnect, and reconnection logic with exponential backoff          | Client reconnects automatically on connection loss | 3h         |
| DI-008  | Message callback system   | Implement topic subscription with callback registration                                 | Callbacks fire on message receipt                  | 2h         |
| DI-009  | MQTT Client tests         | Unit tests with mocked broker, integration test with real Mosquitto                     | 90% coverage, integration test passes              | 3h         |

### 1.3 MQTT Communication Manager (Layer Coordinator)

| Task ID | Task                           | Description                                                                     | Acceptance Criteria                                          | Est. Hours |
| ------- | ------------------------------ | ------------------------------------------------------------------------------- | ------------------------------------------------------------ | ---------- |
| DI-010  | MQTTCommunicationManager class | Create layer coordinator that orchestrates MQTT Client and Device Registry      | Manager initializes both components                          | 3h         |
| DI-011  | Sensor subscription            | Subscribe to all sensor topics from Device Registry on startup                  | Manager receives sensor readings from all registered sensors | 2h         |
| DI-012  | Actuator command publishing    | Publish commands to actuator topics with proper QoS                             | Commands reach actuator topics, can verify with mqtt-spy     | 2h         |
| DI-013  | Sensor reading data model      | Define SensorReading dataclass (sensor_id, value, unit, timestamp, quality)     | Model serializes to/from JSON                                | 1h         |
| DI-014  | Device command data model      | Define DeviceCommand dataclass (device_id, command_type, parameters, timestamp) | Model serializes to/from JSON                                | 1h         |
| DI-015  | Layer interface definition     | Define abstract interface for upper layer (Data Processing) to interact with    | Interface documented with type hints                         | 1h         |

### 1.4 Device Monitor (Optional — Medium Priority)

| Task ID | Task                 | Description                                           | Acceptance Criteria                          | Est. Hours |
| ------- | -------------------- | ----------------------------------------------------- | -------------------------------------------- | ---------- |
| DI-016  | Device Monitor class | Track device availability via MQTT LWT and heartbeats | Monitor reports device online/offline status | 3h         |
| DI-017  | Device status API    | Expose device availability status through manager     | Upper layers can query device availability   | 2h         |
| DI-018  | Device Monitor tests | Unit tests for availability tracking logic            | 90% coverage for device_monitor.py           | 2h         |

**Phase Deliverable:** Device Interface Layer fully functional — can receive
sensor data and publish actuator commands via MQTT.

**Validation:**

- [ ] Manual test: Publish sensor reading to MQTT topic → Layer receives and
  parses it
- [ ] Manual test: Layer publishes command → Command visible on actuator topic
- [ ] Run `pytest tests/test_device_interface/` — all tests pass

______________________________________________________________________

## Phase 2: Data Processing Layer (Semantic Bridge)

**Goal:** Implement fuzzy logic transformation from numerical values to
linguistic descriptions (Layer 4).

**SRS References:** FR-FL-001 to FR-FL-007

### 2.1 Membership Functions

| Task ID | Task                            | Description                                                  | Acceptance Criteria                                    | Est. Hours |
| ------- | ------------------------------- | ------------------------------------------------------------ | ------------------------------------------------------ | ---------- |
| DP-001  | Membership function schema      | Define JSON schema for membership function configurations    | Schema validates temperature, humidity example configs | 2h         |
| DP-002  | Base MembershipFunction class   | Create abstract base class with compute_degree(value) method | ABC with proper interface                              | 1h         |
| DP-003  | Triangular membership function  | Implement TriangularMF(a, b, c) with compute_degree          | Function returns correct degrees for test values       | 2h         |
| DP-004  | Trapezoidal membership function | Implement TrapezoidalMF(a, b, c, d) with compute_degree      | Function returns correct degrees for test values       | 2h         |
| DP-005  | Gaussian membership function    | Implement GaussianMF(mean, sigma) with compute_degree        | Function returns correct degrees for test values       | 2h         |
| DP-006  | Sigmoid membership function     | Implement SigmoidMF(a, c) with compute_degree                | Function returns correct degrees for test values       | 2h         |
| DP-007  | Membership function factory     | Create factory to instantiate MF from JSON config            | Factory creates correct MF type from config dict       | 2h         |
| DP-008  | Membership function tests       | Comprehensive unit tests for all MF types                    | 100% coverage for membership_functions.py              | 3h         |

### 2.2 Fuzzy Engine

| Task ID | Task                            | Description                                                      | Acceptance Criteria                               | Est. Hours |
| ------- | ------------------------------- | ---------------------------------------------------------------- | ------------------------------------------------- | ---------- |
| DP-009  | Linguistic variable model       | Define LinguisticVariable dataclass (term, membership_function)  | Model loads from JSON config                      | 2h         |
| DP-010  | Sensor type configuration model | Define SensorTypeConfig (sensor_type, unit, universe, variables) | Model loads complete sensor config                | 2h         |
| DP-011  | Fuzzy Engine class              | Implement FuzzyEngine: load configs, fuzzify single value        | Engine computes membership degrees for all terms  | 4h         |
| DP-012  | Multi-sensor support            | Extend FuzzyEngine to handle multiple sensor types               | Engine processes different sensor types correctly | 2h         |
| DP-013  | Confidence threshold filtering  | Filter terms below configurable confidence threshold             | Low-confidence terms excluded from output         | 1h         |
| DP-014  | Fuzzy result caching            | Implement LRU cache with TTL for fuzzification results           | Cache hits on repeated values, expires after TTL  | 3h         |
| DP-015  | Fuzzy Engine tests              | Unit tests for engine with various sensor types                  | 95% coverage for fuzzy_engine.py                  | 3h         |

### 2.3 Linguistic Descriptor Builder

| Task ID | Task                            | Description                                                      | Acceptance Criteria                                 | Est. Hours |
| ------- | ------------------------------- | ---------------------------------------------------------------- | --------------------------------------------------- | ---------- |
| DP-016  | LinguisticDescription model     | Define dataclass (sensor_id, terms[], timestamp, raw_value)      | Model serializes to JSON                            | 1h         |
| DP-017  | Descriptor Builder class        | Convert fuzzy engine output to natural language descriptions     | Builder produces "temperature is hot (0.85)" format | 3h         |
| DP-018  | Multi-term description handling | Handle multiple applicable terms (e.g., "warm (0.6), hot (0.4)") | Builder outputs multiple terms when applicable      | 2h         |
| DP-019  | Descriptor Builder tests        | Unit tests for various description scenarios                     | 95% coverage for descriptor_builder.py              | 2h         |

### 2.4 Fuzzy Processing Pipeline (Layer Coordinator)

| Task ID | Task                              | Description                                                          | Acceptance Criteria                                      | Est. Hours |
| ------- | --------------------------------- | -------------------------------------------------------------------- | -------------------------------------------------------- | ---------- |
| DP-020  | FuzzyProcessingPipeline class     | Create layer coordinator orchestrating engine and builder            | Pipeline initializes subcomponents                       | 2h         |
| DP-021  | Configuration loading             | Load all membership function JSONs from config/membership_functions/ | Pipeline loads configs at startup                        | 2h         |
| DP-022  | Configuration validation          | Validate loaded configs against JSON schema                          | Invalid configs rejected with clear errors               | 2h         |
| DP-023  | Process sensor reading            | Full pipeline: SensorReading → LinguisticDescription                 | Pipeline produces linguistic output from numerical input | 2h         |
| DP-024  | State cache                       | Maintain current linguistic state for all sensors                    | State queryable by upper layers                          | 2h         |
| DP-025  | Layer interface definition        | Define interface for Control & Reasoning layer interaction           | Interface documented with type hints                     | 1h         |
| DP-026  | Integration with Device Interface | Wire up to receive SensorReading from Device Interface layer         | Pipeline processes readings from MQTT                    | 3h         |

**Phase Deliverable:** Semantic Bridge operational — numerical sensor values
transformed to linguistic descriptions.

**Validation:**

- [ ] Manual test: Send temperature=28°C → Get "temperature is hot (0.85)"
- [ ] Performance test: Process 20 sensors in < 100ms
- [ ] Run `pytest tests/test_data_processing/` — all tests pass

______________________________________________________________________

## Phase 3: Control & Reasoning Layer

**Goal:** Implement LLM-based rule evaluation and command generation (Layer 3).

**SRS References:** FR-LLM-001 to FR-LLM-008, FR-RI-001 to FR-RI-008

### 3.1 Ollama Client

| Task ID | Task                     | Description                                                                | Acceptance Criteria                           | Est. Hours |
| ------- | ------------------------ | -------------------------------------------------------------------------- | --------------------------------------------- | ---------- |
| CR-001  | LLM configuration schema | Define JSON schema for llm_config.json (provider, model, inference params) | Schema validates example LLM configs          | 1h         |
| CR-002  | Ollama Client class      | Implement client wrapping Ollama REST API (/api/generate)                  | Client sends prompt, receives response        | 4h         |
| CR-003  | Health check             | Implement service availability check via GET /                             | Client reports Ollama online/offline          | 1h         |
| CR-004  | Model verification       | Verify configured model is available via /api/tags                         | Client confirms model exists or reports error | 1h         |
| CR-005  | Inference method         | Implement generate(prompt, params) with streaming disabled                 | Client returns complete response text         | 3h         |
| CR-006  | Timeout handling         | Implement configurable timeout with proper exception                       | Timeout triggers OllamaTimeoutError           | 2h         |
| CR-007  | Fallback model support   | Try fallback models if primary unavailable                                 | Client uses fallback model when primary fails | 2h         |
| CR-008  | Ollama Client tests      | Unit tests with mocked responses, integration with real Ollama             | 90% coverage, integration test passes         | 3h         |

### 3.2 Prompt Construction

| Task ID | Task                      | Description                                                            | Acceptance Criteria                                                | Est. Hours |
| ------- | ------------------------- | ---------------------------------------------------------------------- | ------------------------------------------------------------------ | ---------- |
| CR-009  | Prompt template file      | Create config/prompt_template.txt with placeholders                    | Template file exists with {sensor_state}, {rule_text} placeholders | 2h         |
| CR-010  | PromptBuilder class       | Construct prompts from template, sensor state, and rule                | Builder produces well-formed prompts                               | 3h         |
| CR-011  | Sensor state formatting   | Format multiple sensor descriptions for prompt inclusion               | Formatted state is clear, structured                               | 2h         |
| CR-012  | Action output format spec | Define expected LLM output format (ACTION: device_id, command, params) | Format documented in prompt template                               | 2h         |
| CR-013  | PromptBuilder tests       | Unit tests for prompt construction                                     | 95% coverage for prompt_builder.py                                 | 2h         |

### 3.3 Response Parsing

| Task ID | Task                        | Description                                                              | Acceptance Criteria                              | Est. Hours |
| ------- | --------------------------- | ------------------------------------------------------------------------ | ------------------------------------------------ | ---------- |
| CR-014  | ActionSpec model            | Define dataclass for parsed action (device_id, command_type, parameters) | Model captures all action fields                 | 1h         |
| CR-015  | ResponseParser class        | Parse LLM text response to extract ActionSpec                            | Parser extracts action from well-formed response | 4h         |
| CR-016  | Malformed response handling | Handle responses that don't match expected format                        | Parser returns None or raises clear exception    | 2h         |
| CR-017  | No-action response handling | Detect when LLM determines no action needed                              | Parser returns special "no action" indicator     | 1h         |
| CR-018  | ResponseParser tests        | Unit tests with various response formats                                 | 95% coverage for response_parser.py              | 3h         |

### 3.4 Rule Interpreter

| Task ID | Task                      | Description                                                               | Acceptance Criteria                      | Est. Hours |
| ------- | ------------------------- | ------------------------------------------------------------------------- | ---------------------------------------- | ---------- |
| CR-019  | NaturalLanguageRule model | Define rule dataclass (id, text, priority, enabled, timestamps, metadata) | Model serializes to/from JSON            | 2h         |
| CR-020  | RuleInterpreter class     | Manage rule collection, identify candidates for evaluation                | Interpreter stores and retrieves rules   | 3h         |
| CR-021  | Rule candidate selection  | Select enabled rules for evaluation against current state                 | Only enabled rules considered            | 1h         |
| CR-022  | Single rule evaluation    | Evaluate one rule: build prompt → LLM → parse response                    | Single rule produces action or no-action | 4h         |
| CR-023  | Batch rule evaluation     | Evaluate multiple rules against current state                             | All candidate rules processed            | 2h         |
| CR-024  | RuleInterpreter tests     | Unit tests for rule management and evaluation                             | 90% coverage for rule_interpreter.py     | 3h         |

### 3.5 Command Generator

| Task ID | Task                     | Description                                            | Acceptance Criteria                     | Est. Hours |
| ------- | ------------------------ | ------------------------------------------------------ | --------------------------------------- | ---------- |
| CR-025  | CommandGenerator class   | Translate ActionSpec to DeviceCommand                  | Generator produces valid DeviceCommand  | 3h         |
| CR-026  | Device capability lookup | Query Device Registry for device capabilities          | Generator retrieves device capabilities | 1h         |
| CR-027  | Parameter validation     | Validate command parameters against device constraints | Invalid parameters rejected             | 2h         |
| CR-028  | CommandGenerator tests   | Unit tests for command generation                      | 90% coverage for command_generator.py   | 2h         |

### 3.6 Command Validation Pipeline

| Task ID | Task                       | Description                                   | Acceptance Criteria                   | Est. Hours |
| ------- | -------------------------- | --------------------------------------------- | ------------------------------------- | ---------- |
| CR-029  | CommandValidator class     | Implement 7-step validation pipeline          | Validator rejects invalid commands    | 4h         |
| CR-030  | Device existence check     | Verify device_id exists in registry           | Unknown device rejected               | 1h         |
| CR-031  | Capability match check     | Verify command_type in device capabilities    | Unsupported command rejected          | 1h         |
| CR-032  | Parameter constraint check | Verify parameters within device constraints   | Out-of-range parameters rejected      | 2h         |
| CR-033  | Safety whitelist check     | Verify command against configurable whitelist | Non-whitelisted commands rejected     | 1h         |
| CR-034  | Rate limit check           | Implement per-device rate limiting            | Excessive commands rejected           | 2h         |
| CR-035  | CommandValidator tests     | Unit tests for all validation steps           | 95% coverage for command_validator.py | 3h         |

### 3.7 Conflict Resolution

| Task ID | Task                      | Description                                    | Acceptance Criteria             | Est. Hours |
| ------- | ------------------------- | ---------------------------------------------- | ------------------------------- | ---------- |
| CR-036  | Conflict detection        | Detect multiple commands targeting same device | Conflicts identified            | 2h         |
| CR-037  | Priority-based resolution | Resolve conflicts using rule priority          | Higher priority rule wins       | 2h         |
| CR-038  | Conflict Resolution tests | Unit tests for conflict scenarios              | 90% coverage for conflict logic | 2h         |

### 3.8 Rule Processing Pipeline (Layer Coordinator)

| Task ID | Task                         | Description                                                         | Acceptance Criteria                     | Est. Hours |
| ------- | ---------------------------- | ------------------------------------------------------------------- | --------------------------------------- | ---------- |
| CR-039  | RuleProcessingPipeline class | Create layer coordinator orchestrating all components               | Pipeline initializes subcomponents      | 3h         |
| CR-040  | Evaluation trigger           | Trigger rule evaluation on sensor state change or interval          | Pipeline evaluates rules when triggered | 2h         |
| CR-041  | Full evaluation flow         | sensor state → rule matching → LLM → parsing → validation → command | End-to-end flow produces valid commands | 4h         |
| CR-042  | Command dispatch             | Pass validated commands to Device Interface layer                   | Commands published to MQTT              | 2h         |
| CR-043  | Layer interface definition   | Define interface for Configuration layer interaction                | Interface documented                    | 1h         |

**Phase Deliverable:** LLM-based rule processing operational — natural language
rules generate device commands.

**Validation:**

- [ ] Manual test: Add rule "If temperature is hot, turn on AC" → AC command
  generated when temp=30°C
- [ ] Performance test: LLM inference < 3 seconds
- [ ] Run `pytest tests/test_control_reasoning/` — all tests pass

______________________________________________________________________

## Phase 4: Configuration & Management Layer

**Goal:** Implement system orchestration, configuration management, and rule
persistence (Layer 2).

**SRS References:** FR-CM-001 to FR-CM-004, FR-RI-001, FR-RI-002

### 4.1 Configuration Manager

| Task ID | Task                        | Description                                       | Acceptance Criteria                    | Est. Hours |
| ------- | --------------------------- | ------------------------------------------------- | -------------------------------------- | ---------- |
| CM-001  | System configuration schema | Define JSON schema for system_config.json         | Schema validates example system config | 1h         |
| CM-002  | ConfigurationManager class  | Load and validate all configuration files         | Manager loads all configs at startup   | 4h         |
| CM-003  | Configuration access API    | Provide typed access to configuration values      | Components access config via manager   | 2h         |
| CM-004  | Configuration validation    | Validate all configs against JSON schemas         | Invalid configs rejected with errors   | 2h         |
| CM-005  | Configuration caching       | Cache loaded configs, invalidate on file change   | Configs cached, reload on demand       | 2h         |
| CM-006  | Atomic file writes          | Implement write-rename pattern for config updates | File corruption prevented              | 2h         |
| CM-007  | Configuration backup        | Create timestamped backups before modifications   | Backups created in config/backups/     | 2h         |
| CM-008  | ConfigurationManager tests  | Unit tests for all config operations              | 95% coverage for config_manager.py     | 3h         |

### 4.2 Rule Manager

| Task ID | Task                | Description                                        | Acceptance Criteria                  | Est. Hours |
| ------- | ------------------- | -------------------------------------------------- | ------------------------------------ | ---------- |
| CM-009  | Rule storage schema | Define JSON schema for active_rules.json           | Schema validates rule storage format | 1h         |
| CM-010  | RuleManager class   | Implement CRUD operations for rules                | Rules persist across restarts        | 4h         |
| CM-011  | Add rule            | Add new rule with auto-generated ID and timestamps | Rule added, persisted to file        | 1h         |
| CM-012  | List rules          | List all rules with filtering (enabled, tags)      | Rules listed with metadata           | 1h         |
| CM-013  | Get rule            | Retrieve single rule by ID                         | Rule retrieved or not-found error    | 1h         |
| CM-014  | Update rule         | Update rule text, priority, or metadata            | Rule updated, file persisted         | 1h         |
| CM-015  | Enable/disable rule | Toggle rule enabled status                         | Status changed, persisted            | 1h         |
| CM-016  | Delete rule         | Remove rule by ID                                  | Rule deleted, file persisted         | 1h         |
| CM-017  | Rule import/export  | Import/export rules from/to JSON file              | Rules portable between systems       | 2h         |
| CM-018  | RuleManager tests   | Unit tests for all CRUD operations                 | 95% coverage for rule_manager.py     | 3h         |

### 4.3 Logging Manager

| Task ID | Task                 | Description                                                               | Acceptance Criteria                  | Est. Hours |
| ------- | -------------------- | ------------------------------------------------------------------------- | ------------------------------------ | ---------- |
| CM-019  | LoggingManager class | Configure structured logging with levels                                  | Logger produces JSON-formatted logs  | 2h         |
| CM-020  | Log rotation         | Implement size-based and time-based rotation                              | Old logs rotated, disk space managed | 2h         |
| CM-021  | Event logging API    | Provide semantic logging methods (log_rule_evaluation, log_command, etc.) | Events logged with structured data   | 2h         |
| CM-022  | LoggingManager tests | Unit tests for logging configuration                                      | 90% coverage for logging_manager.py  | 2h         |

### 4.4 System Orchestrator (Layer Coordinator)

| Task ID | Task                       | Description                                                                 | Acceptance Criteria                              | Est. Hours |
| ------- | -------------------------- | --------------------------------------------------------------------------- | ------------------------------------------------ | ---------- |
| CM-023  | SystemOrchestrator class   | Create layer coordinator managing system lifecycle                          | Orchestrator initializes all components          | 4h         |
| CM-024  | Startup sequence           | Implement ordered startup: config → logging → devices → fuzzy → rules → LLM | System starts in correct order                   | 4h         |
| CM-025  | Dependency injection       | Pass configuration to all layers during initialization                      | All layers receive required config               | 2h         |
| CM-026  | Health monitoring          | Monitor health of all components (MQTT, Ollama)                             | Orchestrator reports system health               | 2h         |
| CM-027  | Shutdown sequence          | Implement graceful shutdown with resource cleanup                           | System shuts down cleanly                        | 2h         |
| CM-028  | Error recovery             | Handle component failures gracefully                                        | System continues operating or restarts component | 3h         |
| CM-029  | Layer interface definition | Define interface for User Interface layer interaction                       | Interface documented                             | 1h         |
| CM-030  | Orchestrator tests         | Unit and integration tests for lifecycle                                    | 90% coverage for orchestrator.py                 | 3h         |

**Phase Deliverable:** System orchestration operational — coordinated
startup/shutdown, configuration management, rule persistence.

**Validation:**

- [ ] Manual test: Start system → All layers initialize in order
- [ ] Manual test: Add rule via RuleManager → Rule persists across restart
- [ ] Run `pytest tests/test_configuration/` — all tests pass

______________________________________________________________________

## Phase 5: User Interface Layer

**Goal:** Implement CLI for system interaction (Layer 1 — Top).

**SRS References:** FR-UI-001 to FR-UI-004, UI-MODE-001

### 5.1 CLI Framework

| Task ID | Task                    | Description                                                  | Acceptance Criteria                         | Est. Hours |
| ------- | ----------------------- | ------------------------------------------------------------ | ------------------------------------------- | ---------- |
| UI-001  | CLI entry point         | Create main CLI entry point using Click                      | `iot-fuzzy-llm --help` works                | 2h         |
| UI-002  | Command group structure | Define command groups: rule, sensor, device, config, log     | Command structure matches ADD specification | 2h         |
| UI-003  | Output formatting       | Implement consistent output formatting (tables, JSON, plain) | Output readable and parseable               | 2h         |
| UI-004  | Error handling          | Implement user-friendly error messages                       | Errors displayed clearly, not stack traces  | 2h         |

### 5.2 System Commands

| Task ID | Task             | Description                                     | Acceptance Criteria                   | Est. Hours |
| ------- | ---------------- | ----------------------------------------------- | ------------------------------------- | ---------- |
| UI-005  | `start` command  | Start the system with optional config path      | System starts, status displayed       | 2h         |
| UI-006  | `stop` command   | Gracefully stop the running system              | System stops cleanly                  | 1h         |
| UI-007  | `status` command | Display system status (components, connections) | Status shows health of all components | 2h         |

### 5.3 Rule Commands

| Task ID | Task                           | Description                    | Acceptance Criteria                | Est. Hours |
| ------- | ------------------------------ | ------------------------------ | ---------------------------------- | ---------- |
| UI-008  | `rule add` command             | Add new natural language rule  | Rule added, confirmation shown     | 2h         |
| UI-009  | `rule list` command            | List all rules with status     | Rules displayed in table format    | 1h         |
| UI-010  | `rule show` command            | Show detailed rule information | Rule details displayed             | 1h         |
| UI-011  | `rule enable/disable` commands | Toggle rule status             | Status changed, confirmation shown | 1h         |
| UI-012  | `rule delete` command          | Delete rule with confirmation  | Rule deleted after confirmation    | 1h         |

### 5.4 Sensor & Device Commands

| Task ID | Task                    | Description                                 | Acceptance Criteria                    | Est. Hours |
| ------- | ----------------------- | ------------------------------------------- | -------------------------------------- | ---------- |
| UI-013  | `sensor list` command   | List all registered sensors                 | Sensors displayed with type, location  | 1h         |
| UI-014  | `sensor status` command | Show sensor values (numerical + linguistic) | Status shows both raw and fuzzy values | 2h         |
| UI-015  | `device list` command   | List all registered devices                 | Devices displayed with type, status    | 1h         |
| UI-016  | `device status` command | Show device status and capabilities         | Device details displayed               | 1h         |

### 5.5 Configuration & Log Commands

| Task ID | Task                      | Description                      | Acceptance Criteria                  | Est. Hours |
| ------- | ------------------------- | -------------------------------- | ------------------------------------ | ---------- |
| UI-017  | `config validate` command | Validate all configuration files | Validation results displayed         | 1h         |
| UI-018  | `config reload` command   | Reload configuration at runtime  | Configs reloaded, confirmation shown | 1h         |
| UI-019  | `log tail` command        | Show recent log entries          | Last N log entries displayed         | 2h         |

### 5.6 CLI Integration

| Task ID | Task                     | Description                                | Acceptance Criteria                   | Est. Hours |
| ------- | ------------------------ | ------------------------------------------ | ------------------------------------- | ---------- |
| UI-020  | Wire CLI to Orchestrator | Connect CLI commands to SystemOrchestrator | Commands trigger orchestrator methods | 3h         |
| UI-021  | CLI tests                | Unit tests for CLI commands                | 90% coverage for CLI module           | 3h         |

**Phase Deliverable:** CLI operational — all rule management and monitoring
commands functional.

**Validation:**

- [ ] Manual test: Full CLI workflow (start → add rule → check status → stop)
- [ ] Run `pytest tests/test_interfaces/` — all tests pass

______________________________________________________________________

## Phase 6: Integration & Main Application

**Goal:** Wire all layers together into a cohesive application.

### 6.1 Main Application

| Task ID | Task                     | Description                                               | Acceptance Criteria                    | Est. Hours |
| ------- | ------------------------ | --------------------------------------------------------- | -------------------------------------- | ---------- |
| INT-001 | Main entry point         | Create src/main.py as application entry                   | `python -m src.main` starts system     | 2h         |
| INT-002 | Layer wiring             | Connect all layers through coordinators                   | Data flows correctly between layers    | 4h         |
| INT-003 | Event bus implementation | Implement observer pattern for state change notifications | Sensor changes trigger rule evaluation | 4h         |
| INT-004 | End-to-end data flow     | Sensor → Fuzzy → Rule → Command → Actuator                | Complete flow works                    | 4h         |
| INT-005 | Startup script           | Create bin/start.sh for system launch                     | Script starts all required services    | 1h         |

### 6.2 Cross-Cutting Concerns

| Task ID | Task                  | Description                                 | Acceptance Criteria                       | Est. Hours |
| ------- | --------------------- | ------------------------------------------- | ----------------------------------------- | ---------- |
| INT-006 | Global error handling | Implement top-level exception handling      | Uncaught exceptions logged, system stable | 2h         |
| INT-007 | Signal handling       | Handle SIGTERM/SIGINT for graceful shutdown | Ctrl+C triggers clean shutdown            | 1h         |
| INT-008 | Health endpoints      | Internal health check for all components    | Health status queryable                   | 2h         |

**Phase Deliverable:** Integrated application — complete end-to-end
functionality.

**Validation:**

- [ ] Manual test: Full scenario (sensor reading → linguistic description → rule
  match → LLM → command)
- [ ] Integration test suite passes

______________________________________________________________________

## Phase 7: Testing & Validation

**Goal:** Comprehensive testing and performance validation.

### 7.1 Unit Test Suites

| Task ID | Task                        | Description                              | Acceptance Criteria              | Est. Hours |
| ------- | --------------------------- | ---------------------------------------- | -------------------------------- | ---------- |
| TST-001 | Complete unit test coverage | Ensure all modules have unit tests       | 95% coverage for core components | 8h         |
| TST-002 | Edge case tests             | Test boundary conditions and error paths | Edge cases covered               | 4h         |
| TST-003 | Mock infrastructure         | Create reusable mocks for MQTT, Ollama   | Mocks available for all tests    | 3h         |

### 7.2 Integration Tests

| Task ID | Task                    | Description                              | Acceptance Criteria                | Est. Hours |
| ------- | ----------------------- | ---------------------------------------- | ---------------------------------- | ---------- |
| TST-004 | Layer integration tests | Test each layer pair integration         | Inter-layer communication verified | 6h         |
| TST-005 | End-to-end tests        | Full system scenarios with real services | E2E scenarios pass                 | 8h         |
| TST-006 | Error scenario tests    | Test failure modes and recovery          | System handles errors gracefully   | 4h         |

### 7.3 Performance Tests

| Task ID | Task                         | Description                       | Acceptance Criteria   | Est. Hours |
| ------- | ---------------------------- | --------------------------------- | --------------------- | ---------- |
| TST-007 | Fuzzy processing benchmark   | Measure 20-sensor processing time | < 100ms achieved      | 2h         |
| TST-008 | LLM inference benchmark      | Measure rule evaluation latency   | < 3 seconds average   | 2h         |
| TST-009 | End-to-end latency benchmark | Measure sensor-to-command time    | < 5 seconds achieved  | 2h         |
| TST-010 | Memory profiling             | Measure peak memory usage         | < 8GB total footprint | 2h         |
| TST-011 | Concurrent rule benchmark    | Test 50 concurrent rules          | System handles load   | 2h         |

### 7.4 Accuracy Tests

| Task ID | Task                         | Description                                  | Acceptance Criteria | Est. Hours |
| ------- | ---------------------------- | -------------------------------------------- | ------------------- | ---------- |
| TST-012 | Rule interpretation accuracy | Test rule interpretation with diverse inputs | >= 85% accuracy     | 8h         |
| TST-013 | Prompt refinement            | Iterate on prompts to improve accuracy       | Accuracy target met | 4h         |

**Phase Deliverable:** Validated system meeting all performance and accuracy
targets.

**Validation:**

- [ ] 95% test coverage
- [ ] All performance targets met
- [ ] Rule interpretation accuracy >= 85%

______________________________________________________________________

## Phase 8: Smart Home Demo Scenario

**Goal:** Create and validate the demonstration scenario for thesis evaluation.

### 8.1 Demo Configuration

| Task ID  | Task                      | Description                                 | Acceptance Criteria              | Est. Hours |
| -------- | ------------------------- | ------------------------------------------- | -------------------------------- | ---------- |
| DEMO-001 | Demo device configuration | Configure demo devices (sensors, actuators) | devices.json configured for demo | 2h         |
| DEMO-002 | Demo membership functions | Tune membership functions for demo sensors  | Membership functions calibrated  | 3h         |
| DEMO-003 | Demo MQTT topics          | Configure MQTT topics for demo scenario     | Topics documented and functional | 1h         |

### 8.2 Demo Rules

| Task ID  | Task                   | Description                                              | Acceptance Criteria     | Est. Hours |
| -------- | ---------------------- | -------------------------------------------------------- | ----------------------- | ---------- |
| DEMO-004 | Climate control rules  | "If temperature is hot and humidity is high, turn on AC" | Rule triggers correctly | 2h         |
| DEMO-005 | Lighting control rules | "When motion detected at night, turn on lights"          | Rule triggers correctly | 2h         |
| DEMO-006 | Heating control rules  | "If room is cold in morning, increase heating"           | Rule triggers correctly | 2h         |
| DEMO-007 | Blind control rules    | "When too bright, close blinds halfway"                  | Rule triggers correctly | 2h         |

### 8.3 Demo Validation

| Task ID  | Task                       | Description                          | Acceptance Criteria            | Est. Hours |
| -------- | -------------------------- | ------------------------------------ | ------------------------------ | ---------- |
| DEMO-008 | Demo walkthrough           | Document step-by-step demo execution | Demo script documented         | 2h         |
| DEMO-009 | Demo video/screenshots     | Capture demo execution evidence      | Visual evidence captured       | 2h         |
| DEMO-010 | Demo troubleshooting guide | Document common issues and fixes     | Troubleshooting guide complete | 2h         |

**Phase Deliverable:** Working demonstration scenario for thesis evaluation.

______________________________________________________________________

## Phase 9: Documentation & Finalization

**Goal:** Complete all documentation for thesis submission.

| Task ID | Task                        | Description                                 | Acceptance Criteria             | Est. Hours |
| ------- | --------------------------- | ------------------------------------------- | ------------------------------- | ---------- |
| DOC-001 | API documentation           | Document all public interfaces              | All public APIs documented      | 6h         |
| DOC-002 | JSON schema documentation   | Document all configuration schemas          | Schemas fully documented        | 4h         |
| DOC-003 | User guide                  | Document CLI usage and common workflows     | User guide complete             | 4h         |
| DOC-004 | Installation guide          | Document installation on clean system       | Guide verified on fresh install | 3h         |
| DOC-005 | Configuration guide         | Document all configuration options          | Config guide complete           | 3h         |
| DOC-006 | Example rules documentation | Document example rules with explanations    | Examples documented             | 2h         |
| DOC-007 | Evaluation report           | Document evaluation methodology and results | Report complete with data       | 8h         |
| DOC-008 | Code review and cleanup     | Final code review, formatting, docstrings   | Code ready for submission       | 4h         |

**Phase Deliverable:** Complete documentation ready for thesis submission.

______________________________________________________________________

## Summary: Implementation Order

For autonomous implementation units, execute phases in this order:

01. **Phase 0: Foundation** — Docker containerization, Makefile, environment
    setup (required before any development)
02. **Phase 1: Device Interface** — Bottom layer, no dependencies on other
    layers
03. **Phase 2: Data Processing** — Depends on Phase 1 interface
04. **Phase 3: Control & Reasoning** — Depends on Phase 2 interface
05. **Phase 4: Configuration & Management** — Depends on Phases 1-3 interfaces
06. **Phase 5: User Interface** — Depends on Phase 4 interface
07. **Phase 6: Integration** — Wires all phases together
08. **Phase 7: Testing** — Validates all phases
09. **Phase 8: Demo Scenario** — Uses integrated system
10. **Phase 9: Documentation** — Documents completed system

### Quick Start: Docker Development Environment

After Phase 0 is complete, all development follows this workflow:

```bash
# First time setup
make build              # Build all Docker images
make pull-model         # Pull Mistral 7B model (takes time)

# Daily development
make up                 # Start all services
make logs               # Monitor logs in real-time
make test               # Run tests

# Hybrid development (app locally, services in Docker)
make dev-deps           # Start only mosquitto + ollama
make dev                # Run Python app locally

# Cleanup
make down               # Stop all services
make clean              # Remove artifacts
```

### Quick Start for Autonomous Units

Each autonomous unit should:

1. **Verify Docker environment** — Run `make ps` to confirm services are running
2. **Read this document** to understand task context and dependencies
3. **Complete prerequisites** — Verify dependent tasks are complete
4. **Implement task** — Follow acceptance criteria
5. **Write tests** — Ensure coverage targets met
6. **Validate** — Run `make test` and phase validation tests
7. **Document** — Update relevant documentation

### Estimated Total Effort

| Phase                               | Estimated Hours |
| ----------------------------------- | --------------- |
| Phase 0: Foundation & Docker        | 28h             |
| Phase 1: Device Interface           | 45h             |
| Phase 2: Data Processing            | 52h             |
| Phase 3: Control & Reasoning        | 85h             |
| Phase 4: Configuration & Management | 50h             |
| Phase 5: User Interface             | 30h             |
| Phase 6: Integration                | 20h             |
| Phase 7: Testing                    | 55h             |
| Phase 8: Demo Scenario              | 20h             |
| Phase 9: Documentation              | 34h             |
| **Total**                           | **~419h**       |

______________________________________________________________________

*This document is a living reference. Update task statuses as implementation
progresses.*
