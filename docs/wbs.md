# Work Breakdown Structure

## Fuzzy-LLM Hybrid IoT Management System

**Document Status:** Active\
**Last Updated:** 2026-02-04\
**Source Documents:** [thesis-setup.md](thesis-setup.md),
[project-brief.md](project-brief.md), [srs.md](srs.md), [add.md](add.md)

______________________________________________________________________

## 1. Project Overview

This WBS defines the hierarchical decomposition of work required to implement
the Fuzzy-LLM Hybrid IoT Management System for thesis evaluation. The project
implements fuzzy logic as a **semantic bridge** between raw sensor values and
linguistic concepts for LLM-based natural language rule processing.

### 1.1 Scope Boundaries

| In Scope (Thesis MVP)        | Out of Scope (Future Work)    |
| ---------------------------- | ----------------------------- |
| Fuzzy logic semantic bridge  | Web-based user interface      |
| Ollama LLM integration (≤7B) | REST API interface            |
| MQTT device communication    | Multi-protocol device support |
| CLI interface                | Distributed deployment        |
| JSON configuration system    | Advanced conflict resolution  |
| Smart home demo scenario     |                               |
| Docker containerization      |                               |

### 1.2 Key Performance Targets

- End-to-end response: < 5 seconds
- LLM inference: < 3 seconds
- Fuzzy processing: < 100 ms
- Memory footprint: 8 GB total
- Rule interpretation accuracy: ≥ 85%

______________________________________________________________________

## 2. Work Breakdown Structure

### WBS Hierarchy

```
1.0 PROJECT MANAGEMENT
2.0 RESEARCH & ANALYSIS
3.0 SYSTEM DESIGN
4.0 IMPLEMENTATION
    4.1 Device Interface Layer
    4.2 Data Processing Layer (Semantic Bridge)
    4.3 Control & Reasoning Layer
    4.4 Configuration & Management Layer
    4.5 User Interface Layer
    4.6 Integration & Cross-Cutting
5.0 TESTING & VALIDATION
6.0 DOCUMENTATION
7.0 DEMONSTRATION & EVALUATION
```

______________________________________________________________________

## 3. Detailed Work Packages

### 1.0 PROJECT MANAGEMENT

| WBS ID | Work Package                    | Priority | Effort Est. | Dependencies |
| ------ | ------------------------------- | -------- | ----------- | ------------ |
| 1.1    | Project planning & scheduling   | High     | 8h          | —            |
| 1.2    | Development environment setup   | High     | 4h          | —            |
| 1.3    | Repository structure & CI setup | Medium   | 4h          | 1.2          |
| 1.4    | Progress tracking & reporting   | Medium   | Ongoing     | 1.1          |
| 1.5    | Risk monitoring & mitigation    | Medium   | Ongoing     | 1.1          |

**Deliverables:**

- Project schedule and milestones
- Configured development environment
- Git repository with branch strategy
- CI pipeline for automated testing

______________________________________________________________________

### 2.0 RESEARCH & ANALYSIS

| WBS ID | Work Package                             | Priority | Effort Est. | Dependencies |
| ------ | ---------------------------------------- | -------- | ----------- | ------------ |
| 2.1    | Literature review: fuzzy-LLM integration | High     | 24h         | —            |
| 2.2    | Analysis of existing IoT architectures   | High     | 16h         | —            |
| 2.3    | LLM model evaluation & selection         | High     | 16h         | —            |
| 2.4    | Comparative analysis of approaches       | Medium   | 12h         | 2.1, 2.2     |
| 2.5    | Semantic bridge concept formalization    | High     | 8h          | 2.1          |

**Deliverables:**

- Literature review document
- LLM model comparison matrix (Mistral 7B, LLaMA, Phi)
- Architecture pattern analysis
- Justified approach selection

**Key References:**

- Morales Aguilera, F. (2024) — Fuzzy inference + LLM synergy
- Kalita, A. (2025) — LLM-IoT integration
- Liu, X., et al. (2024) — LLMind orchestration

______________________________________________________________________

### 3.0 SYSTEM DESIGN

| WBS ID | Work Package                          | Priority | Effort Est. | Dependencies |
| ------ | ------------------------------------- | -------- | ----------- | ------------ |
| 3.1    | 5-layer architecture design           | High     | 12h         | 2.4, 2.5     |
| 3.2    | Component interface definitions       | High     | 8h          | 3.1          |
| 3.3    | Data flow & interaction diagrams      | High     | 8h          | 3.1          |
| 3.4    | JSON schema design (membership funcs) | High     | 8h          | 3.1          |
| 3.5    | MQTT topic structure design           | High     | 4h          | 3.1          |
| 3.6    | Security architecture (validation)    | Medium   | 6h          | 3.2          |
| 3.7    | Prompt template design                | High     | 8h          | 2.3          |

**Deliverables:**

- Architecture Design Document (add.md) ✓
- Component diagrams and data flow diagrams
- JSON schemas for all configuration types
- MQTT topic conventions
- LLM prompt templates

______________________________________________________________________

### 4.0 IMPLEMENTATION

#### 4.1 Device Interface Layer

| WBS ID | Work Package                   | Priority | Effort Est. | Dependencies | SRS Ref              |
| ------ | ------------------------------ | -------- | ----------- | ------------ | -------------------- |
| 4.1.1  | MQTT Communication Manager     | High     | 16h         | 3.5          | FR-DC-001, FR-DC-002 |
| 4.1.2  | MQTT Client (paho-mqtt)        | High     | 12h         | 4.1.1        | FR-DC-004            |
| 4.1.3  | Device Registry implementation | High     | 12h         | 3.4          | FR-DC-003            |
| 4.1.4  | Device Monitor (heartbeat/LWT) | Medium   | 8h          | 4.1.2        | FR-DC-006            |
| 4.1.5  | Reconnection & error handling  | Medium   | 6h          | 4.1.2        | NFR-REL-002          |

**Components:**

- `src/device_interface/mqtt_manager.py` — Layer coordinator
- `src/device_interface/mqtt_client.py` — Broker connection
- `src/device_interface/device_registry.py` — Device inventory
- `src/device_interface/device_monitor.py` — Availability tracking

**Acceptance Criteria:**

- [ ] Connect to Mosquitto broker with authentication
- [ ] Subscribe to sensor topics and receive readings
- [ ] Publish commands to actuator topics
- [ ] Handle connection loss and automatic reconnection
- [ ] Track device availability via LWT

______________________________________________________________________

#### 4.2 Data Processing Layer (Semantic Bridge)

| WBS ID | Work Package                     | Priority | Effort Est. | Dependencies | SRS Ref              |
| ------ | -------------------------------- | -------- | ----------- | ------------ | -------------------- |
| 4.2.1  | Fuzzy Processing Pipeline        | High     | 12h         | 3.4          | FR-FL-001            |
| 4.2.2  | Membership Function Library      | High     | 16h         | 4.2.1        | FR-FL-004            |
| 4.2.3  | Fuzzy Engine (fuzzification)     | High     | 20h         | 4.2.2        | FR-FL-001, FR-FL-003 |
| 4.2.4  | Linguistic Descriptor Builder    | High     | 12h         | 4.2.3        | FR-FL-005            |
| 4.2.5  | JSON configuration loader        | High     | 8h          | 3.4          | FR-FL-002            |
| 4.2.6  | Configuration validation         | Medium   | 6h          | 4.2.5        | FR-FL-006            |
| 4.2.7  | Fuzzy result caching (LRU + TTL) | Medium   | 6h          | 4.2.3        | NFR-PERF-003         |

**Components:**

- `src/data_processing/fuzzy_pipeline.py` — Layer coordinator
- `src/data_processing/fuzzy_engine.py` — Core fuzzification
- `src/data_processing/membership_functions.py` — Function implementations
- `src/data_processing/descriptor_builder.py` — NL description generation
- `config/membership_functions/*.json` — Per-sensor configurations

**Membership Function Types:**

1. Triangular: `f(x; a, b, c)`
2. Trapezoidal: `f(x; a, b, c, d)`
3. Gaussian: `f(x; μ, σ)`
4. Sigmoid: `f(x; a, c)`

**Acceptance Criteria:**

- [ ] Load membership functions from JSON at startup
- [ ] Compute membership degrees for all configured terms
- [ ] Generate linguistic descriptions (e.g., "temperature is hot (0.85)")
- [ ] Process 20 sensors within 100ms (NFR-PERF-003)
- [ ] Validate JSON configurations against schema
- [ ] Cache fuzzification results with 300s TTL

______________________________________________________________________

#### 4.3 Control & Reasoning Layer

| WBS ID | Work Package                 | Priority | Effort Est. | Dependencies | SRS Ref                |
| ------ | ---------------------------- | -------- | ----------- | ------------ | ---------------------- |
| 4.3.1  | Rule Processing Pipeline     | High     | 12h         | 4.2.4        | —                      |
| 4.3.2  | Ollama Client implementation | High     | 16h         | 3.7          | FR-LLM-001, FR-LLM-004 |
| 4.3.3  | Prompt construction engine   | High     | 12h         | 4.3.2        | FR-LLM-003             |
| 4.3.4  | LLM response parser          | High     | 12h         | 4.3.2        | FR-LLM-005             |
| 4.3.5  | Rule Interpreter             | High     | 16h         | 4.3.4        | FR-RI-003              |
| 4.3.6  | Command Generator            | High     | 12h         | 4.3.5        | FR-RI-004              |
| 4.3.7  | Command validation pipeline  | Medium   | 10h         | 4.3.6, 4.1.3 | NFR-SEC-003            |
| 4.3.8  | Conflict resolution          | Medium   | 8h          | 4.3.5        | FR-RI-006              |
| 4.3.9  | Inference timeout handling   | Medium   | 4h          | 4.3.2        | FR-LLM-007             |

**Components:**

- `src/control_reasoning/rule_pipeline.py` — Layer coordinator
- `src/control_reasoning/ollama_client.py` — LLM communication
- `src/control_reasoning/prompt_builder.py` — Prompt construction
- `src/control_reasoning/response_parser.py` — Output parsing
- `src/control_reasoning/rule_interpreter.py` — Rule matching
- `src/control_reasoning/command_generator.py` — Action translation
- `src/control_reasoning/command_validator.py` — Safety checks
- `config/prompt_template.txt` — LLM prompt template

**Command Validation Pipeline (7 steps):**

1. Response parsing verification
2. Device existence check
3. Capability match validation
4. Parameter constraint validation
5. Safety whitelist check
6. Rate limit enforcement
7. Critical command flagging

**Acceptance Criteria:**

- [ ] Connect to Ollama service and verify model availability
- [ ] Construct prompts from sensor states + rule text
- [ ] Parse LLM responses into structured actions
- [ ] Complete inference within 3 seconds (NFR-PERF-002)
- [ ] Validate commands before execution
- [ ] Handle inference timeouts gracefully

______________________________________________________________________

#### 4.4 Configuration & Management Layer

| WBS ID | Work Package                      | Priority | Effort Est. | Dependencies | SRS Ref              |
| ------ | --------------------------------- | -------- | ----------- | ------------ | -------------------- |
| 4.4.1  | System Orchestrator               | High     | 16h         | 4.1-4.3      | —                    |
| 4.4.2  | Configuration Manager             | High     | 12h         | 3.4          | FR-CM-001, FR-CM-002 |
| 4.4.3  | Rule Manager (CRUD + persistence) | High     | 12h         | —            | FR-RI-001, FR-RI-002 |
| 4.4.4  | Logging Manager                   | Medium   | 8h          | —            | NFR-MAIN-002         |
| 4.4.5  | Startup/shutdown orchestration    | High     | 8h          | 4.4.1        | —                    |
| 4.4.6  | Configuration backup mechanism    | Low      | 4h          | 4.4.2        | NFR-REL-003          |
| 4.4.7  | Runtime reconfiguration           | Low      | 6h          | 4.4.2        | FR-FL-007            |

**Components:**

- `src/configuration/orchestrator.py` — System lifecycle
- `src/configuration/config_manager.py` — Configuration loading
- `src/configuration/rule_manager.py` — Rule persistence
- `src/configuration/logging_manager.py` — Structured logging
- `config/system_config.json` — System parameters
- `config/llm_config.json` — Ollama settings
- `config/mqtt_config.json` — Broker settings
- `config/devices.json` — Device definitions
- `rules/active_rules.json` — Persisted rules

**Acceptance Criteria:**

- [ ] Load and validate all configuration files at startup
- [ ] Persist rules with full CRUD operations
- [ ] Implement atomic write-rename for file safety
- [ ] Log all significant events in structured format
- [ ] Coordinate startup sequence across all layers
- [ ] Create configuration backups before modifications

______________________________________________________________________

#### 4.5 User Interface Layer

| WBS ID | Work Package                         | Priority | Effort Est. | Dependencies | SRS Ref     |
| ------ | ------------------------------------ | -------- | ----------- | ------------ | ----------- |
| 4.5.1  | CLI framework setup (argparse/click) | High     | 4h          | —            | UI-MODE-001 |
| 4.5.2  | Rule management commands             | High     | 8h          | 4.4.3        | FR-UI-001   |
| 4.5.3  | Status display commands              | Medium   | 6h          | 4.2.4        | FR-UI-002   |
| 4.5.4  | Rule execution feedback              | Medium   | 4h          | 4.3.5        | FR-UI-003   |
| 4.5.5  | Configuration commands               | Low      | 6h          | 4.4.2        | FR-UI-004   |
| 4.5.6  | Log viewing commands                 | Low      | 4h          | 4.4.4        | —           |

**CLI Commands:**

```
iot-fuzzy-llm
├── start                    # Start system
├── stop                     # Stop system
├── status                   # Show system status
├── rule
│   ├── add <text>          # Add new rule
│   ├── list                # List all rules
│   ├── show <id>           # Show rule details
│   ├── enable <id>         # Enable rule
│   ├── disable <id>        # Disable rule
│   └── delete <id>         # Delete rule
├── sensor
│   ├── list                # List sensors
│   └── status [id]         # Show sensor values
├── device
│   ├── list                # List all devices
│   └── status [id]         # Show device status
├── config
│   ├── validate            # Validate configs
│   └── reload              # Reload configs
└── log
    └── tail [-n NUM]       # View recent logs
```

**Acceptance Criteria:**

- [ ] Add, list, show, enable, disable, and delete rules via CLI
- [ ] Display sensor status in numerical and linguistic formats
- [ ] Show rule execution feedback
- [ ] Validate configurations from CLI
- [ ] View system logs

______________________________________________________________________

#### 4.6 Integration & Cross-Cutting

| WBS ID | Work Package                 | Priority | Effort Est. | Dependencies | SRS Ref      |
| ------ | ---------------------------- | -------- | ----------- | ------------ | ------------ |
| 4.6.1  | Layer coordinator interfaces | High     | 8h          | 4.1-4.5      | NFR-MAIN-001 |
| 4.6.2  | Event bus implementation     | Medium   | 8h          | 4.6.1        | —            |
| 4.6.3  | Error handling framework     | High     | 6h          | —            | NFR-USE-003  |
| 4.6.4  | Rate limiting implementation | Medium   | 4h          | 4.3.7        | —            |
| 4.6.5  | Caching infrastructure       | Medium   | 6h          | 4.2.7        | —            |
| 4.6.6  | Main application entry point | High     | 4h          | 4.4.5        | —            |

**Acceptance Criteria:**

- [ ] All layers communicate only through coordinators
- [ ] Event bus enables loose coupling for state changes
- [ ] Clear, actionable error messages
- [ ] Rate limiting prevents command flooding
- [ ] Unified caching with LRU + TTL

______________________________________________________________________

### 5.0 TESTING & VALIDATION

| WBS ID | Work Package                        | Priority | Effort Est. | Dependencies |
| ------ | ----------------------------------- | -------- | ----------- | ------------ |
| 5.1    | Unit test suite (fuzzy engine)      | High     | 16h         | 4.2          |
| 5.2    | Unit test suite (rule processing)   | High     | 16h         | 4.3          |
| 5.3    | Unit test suite (device interface)  | High     | 12h         | 4.1          |
| 5.4    | Integration tests (end-to-end flow) | High     | 20h         | 4.1-4.5      |
| 5.5    | Performance benchmarks              | High     | 12h         | 5.4          |
| 5.6    | LLM response accuracy testing       | High     | 16h         | 4.3          |
| 5.7    | Configuration validation tests      | Medium   | 8h          | 4.4.2        |
| 5.8    | Error handling & edge case tests    | Medium   | 12h         | 5.4          |
| 5.9    | Security validation tests           | Medium   | 8h          | 4.3.7        |

**Test Coverage Targets:**

- Core components: ≥ 95%
- Integration paths: ≥ 90%
- Configuration schemas: 100%

**Performance Benchmarks:**

| Metric             | Target  | Test Method                 |
| ------------------ | ------- | --------------------------- |
| Fuzzy processing   | < 100ms | 20 sensors batch processing |
| LLM inference      | < 3s    | Average over 50 rule evals  |
| End-to-end latency | < 5s    | Sensor → actuator command   |
| Memory footprint   | < 8GB   | Peak usage under load       |
| Concurrent rules   | 50      | Parallel rule evaluation    |

**Acceptance Criteria:**

- [ ] 95% test coverage for core components
- [ ] All performance targets met in 90% of test cases
- [ ] No critical or high-severity defects unresolved
- [ ] Rule interpretation accuracy ≥ 85%

______________________________________________________________________

### 6.0 DOCUMENTATION

| WBS ID | Work Package                          | Priority | Effort Est. | Dependencies |
| ------ | ------------------------------------- | -------- | ----------- | ------------ |
| 6.1    | API documentation (public interfaces) | High     | 12h         | 4.1-4.5      |
| 6.2    | JSON schema documentation             | High     | 8h          | 3.4          |
| 6.3    | User guide (CLI usage)                | High     | 8h          | 4.5          |
| 6.4    | Installation & deployment guide       | High     | 6h          | 4.6.6        |
| 6.5    | Configuration guide                   | Medium   | 6h          | 4.4.2        |
| 6.6    | Example rules & scenarios             | Medium   | 4h          | 7.1          |
| 6.7    | Code documentation (docstrings)       | Medium   | Ongoing     | 4.1-4.5      |
| 6.8    | Thesis document integration           | High     | 16h         | 5.0, 7.0     |

**Deliverables:**

- Complete API documentation with examples
- JSON schema specifications for all config types
- User guide covering common scenarios
- Installation instructions for Mosquitto + Ollama
- Example natural language rules

______________________________________________________________________

### 7.0 DEMONSTRATION & EVALUATION

| WBS ID | Work Package                      | Priority | Effort Est. | Dependencies |
| ------ | --------------------------------- | -------- | ----------- | ------------ |
| 7.1    | Smart home demo scenario design   | High     | 8h          | 3.0          |
| 7.2    | Demo device configuration         | High     | 6h          | 7.1          |
| 7.3    | Demo membership function tuning   | High     | 8h          | 7.2          |
| 7.4    | Demo rules creation               | High     | 6h          | 7.3          |
| 7.5    | Rule interpretation accuracy eval | High     | 12h         | 7.4          |
| 7.6    | Response time measurement         | High     | 8h          | 7.4          |
| 7.7    | Usability assessment              | High     | 12h         | 7.4          |
| 7.8    | Evaluation report & analysis      | High     | 16h         | 7.5-7.7      |

**Smart Home Demo Scenario:**

Devices:

- Temperature sensor (living room, bedroom)
- Humidity sensor (living room)
- Motion sensor (entrance)
- Light sensor (living room)
- HVAC actuator (living room)
- Lighting actuator (living room, entrance)
- Smart blinds actuator (living room)

Example Rules:

1. "If the temperature is hot and humidity is high, turn on the air conditioner"
2. "When motion is detected at night, turn on the entrance lights"
3. "If the room is cold in the morning, increase the heating"
4. "When it's too bright, close the blinds halfway"

**Evaluation Metrics (per thesis assignment):**

| Metric                       | Target   | Measurement Method              |
| ---------------------------- | -------- | ------------------------------- |
| Rule interpretation accuracy | ≥ 85%    | Correct action / total rules    |
| End-to-end response time     | < 5s     | Sensor reading → command issued |
| Usability rating             | ≥ 4/5    | User survey (non-technical)     |
| Setup time (basic scenario)  | < 30 min | Timed user study                |

______________________________________________________________________

## 4. Dependencies & Critical Path

### 4.1 Dependency Graph

```
                    ┌─────────────┐
                    │ 2.0 Research│
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  3.0 Design │
                    └──────┬──────┘
                           │
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
    ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
    │4.1 Device   │ │4.2 Data Proc│ │4.3 Control  │
    │Interface    │ │(Semantic    │ │& Reasoning  │
    └─────┬───────┘ │Bridge)      │ └─────┬───────┘
          │         └──────┬──────┘       │
          │                │              │
          └────────────────┼──────────────┘
                           │
                    ┌──────▼──────┐
                    │4.4 Config & │
                    │Management   │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │4.5 User     │
                    │Interface    │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │4.6 Integr.  │
                    └──────┬──────┘
                           │
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
    ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
    │5.0 Testing  │ │6.0 Docs     │ │7.0 Demo &   │
    │             │ │             │ │Evaluation   │
    └─────────────┘ └─────────────┘ └─────────────┘
```

### 4.2 Critical Path

1. **2.0 Research & Analysis** →
2. **3.0 System Design** →
3. **4.2 Data Processing (Semantic Bridge)** →
4. **4.3 Control & Reasoning** →
5. **4.4 Configuration & Management** →
6. **4.6 Integration** →
7. **5.4 Integration Tests** →
8. **7.0 Demonstration & Evaluation**

**Estimated Critical Path Duration:** ~280 hours

______________________________________________________________________

## 5. Risk Register

| Risk ID | Risk Description                          | Probability | Impact | Mitigation                                      |
| ------- | ----------------------------------------- | ----------- | ------ | ----------------------------------------------- |
| R1      | LLM inference too slow on target hardware | Medium      | High   | Use quantized models (4-bit); implement caching |
| R2      | LLM outputs inconsistent/ambiguous        | Medium      | High   | Robust prompt engineering; validation pipeline  |
| R3      | Memory exceeds 8GB limit                  | Low         | High   | Profile early; use smaller model if needed      |
| R4      | MQTT connectivity issues                  | Low         | Medium | Implement reconnection logic; queue commands    |
| R5      | Fuzzy configuration complexity            | Medium      | Medium | Provide default templates; clear documentation  |
| R6      | Rule interpretation accuracy < 85%        | Medium      | High   | Iterative prompt refinement; fallback rules     |
| R7      | Integration complexity between layers     | Medium      | Medium | Clear interfaces; thorough integration testing  |

______________________________________________________________________

## 6. Resource Requirements

### 6.1 Development Environment

| Component   | Requirement                       |
| ----------- | --------------------------------- |
| Python      | 3.9+                              |
| Ollama      | Latest (with Mistral 7B model)    |
| MQTT Broker | Eclipse Mosquitto 2.0+            |
| RAM         | 16 GB recommended (8 GB minimum)  |
| Disk        | 20 GB (incl. LLM model)           |
| OS          | Linux (Ubuntu 22.04+ recommended) |

### 6.2 Python Dependencies

| Package    | Purpose                      |
| ---------- | ---------------------------- |
| paho-mqtt  | MQTT client                  |
| requests   | Ollama REST API              |
| numpy      | Vectorized fuzzy computation |
| jsonschema | Configuration validation     |
| click      | CLI framework                |
| pytest     | Testing framework            |
| pytest-cov | Coverage reporting           |

### 6.3 Effort Estimates Summary

| Phase                          | Estimated Hours |
| ------------------------------ | --------------- |
| 1.0 Project Management         | 16h + ongoing   |
| 2.0 Research & Analysis        | 76h             |
| 3.0 System Design              | 54h             |
| 4.0 Implementation             | 314h            |
| 5.0 Testing & Validation       | 120h            |
| 6.0 Documentation              | 60h             |
| 7.0 Demonstration & Evaluation | 76h             |
| **Total**                      | **~716h**       |

______________________________________________________________________

## 7. Milestones

| Milestone | Description                     | Criteria                                          |
| --------- | ------------------------------- | ------------------------------------------------- |
| M1        | Research & Design Complete      | Literature review, ADD, SRS finalized             |
| M2        | Semantic Bridge Functional      | Fuzzy processing produces linguistic descriptions |
| M3        | LLM Integration Complete        | Ollama client processes rules, generates commands |
| M4        | Device Communication Functional | MQTT send/receive working with test devices       |
| M5        | End-to-End Flow Working         | Sensor → fuzzy → LLM → command → actuator         |
| M6        | CLI Complete                    | All rule management commands operational          |
| M7        | Testing Complete                | 95% coverage, all performance targets met         |
| M8        | Demo Scenario Ready             | Smart home demo fully operational                 |
| M9        | Evaluation Complete             | Accuracy, response time, usability measured       |
| M10       | Thesis Submission Ready         | All documentation complete, code finalized        |

______________________________________________________________________

## 8. Appendices

### Appendix A: Requirements Traceability

| WBS Package | SRS Requirements                                 |
| ----------- | ------------------------------------------------ |
| 4.1         | FR-DC-001 to FR-DC-007                           |
| 4.2         | FR-FL-001 to FR-FL-007                           |
| 4.3         | FR-LLM-001 to FR-LLM-008, FR-RI-001 to FR-RI-008 |
| 4.4         | FR-CM-001 to FR-CM-004                           |
| 4.5         | FR-UI-001 to FR-UI-004, UI-MODE-001              |
| 5.0         | NFR-PERF-001 to NFR-PERF-005, NFR-USE-001        |

### Appendix B: Directory Structure Reference

```
/opt/fuzzy-llm-iot/
├── bin/                          # Startup scripts
├── config/
│   ├── membership_functions/     # Per-sensor JSON configs
│   ├── devices.json
│   ├── mqtt_config.json
│   ├── llm_config.json
│   ├── system_config.json
│   └── prompt_template.txt
├── rules/
│   └── active_rules.json
├── logs/
├── src/
│   ├── main.py
│   ├── device_interface/
│   ├── data_processing/
│   ├── control_reasoning/
│   ├── configuration/
│   └── interfaces/
├── tests/
├── docs/
├── requirements.txt
└── README.md
```

### Appendix C: Glossary

| Term                | Definition                                                             |
| ------------------- | ---------------------------------------------------------------------- |
| Semantic Bridge     | Fuzzy logic layer transforming numerical values to linguistic concepts |
| Membership Function | Mathematical function defining degree of belonging to a fuzzy set      |
| Linguistic Variable | Variable with natural language values (e.g., "hot", "cold")            |
| Fuzzification       | Process of converting crisp values to fuzzy membership degrees         |
| Ollama              | Platform for running LLMs locally without cloud dependencies           |
| LWT                 | Last Will and Testament — MQTT message sent on unexpected disconnect   |

______________________________________________________________________

*This WBS is a living document and should be updated as the project progresses.*
