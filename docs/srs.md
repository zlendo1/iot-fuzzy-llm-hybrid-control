# Software Requirements Specification

## Fuzzy-LLM Hybrid IoT Management System

**Document Status:** Active\
**Last Updated:** 2026-02-04\
**Source Documents:** [thesis-setup.md](thesis-setup.md),
[project-brief.md](project-brief.md)

______________________________________________________________________

## 1. Introduction

### 1.1 Purpose

This document specifies the software requirements for a hybrid system that
integrates fuzzy logic and large language models for IoT device management
through natural language rules. Fuzzy logic serves as a **semantic bridge**
between raw numerical sensor values and linguistic concepts that an LLM can
understand and process. This specification serves as the authoritative reference
for system design, implementation, testing, and validation **within the thesis
scope defined in [thesis-setup.md](thesis-setup.md)**.

### 1.2 Scope

The system accepts natural language control rules from users, translates
numerical sensor data into linguistic descriptions using fuzzy logic as a
**semantic bridge**, processes these descriptions with an offline LLM, and
generates control commands for IoT devices. The system operates entirely offline
on edge devices without external network dependencies.

### 1.2.1 Thesis Prototype Scope (MVP)

The thesis prototype implements the following core requirements:

| Category         | MVP Features                                                       |
| ---------------- | ------------------------------------------------------------------ |
| Fuzzy Logic      | JSON-based membership functions, linguistic variables              |
| LLM Integration  | Ollama-based offline inference (lightweight edge models, CPU-only) |
| Rule Processing  | Free-form natural language rules, LLM interpretation               |
| Device Interface | MQTT communication via Mosquitto broker                            |
| User Interface   | Command-line interface for rule management                         |
| Deployment       | Docker Compose containerization for edge devices                   |
| Demonstration    | Smart home automation scenario                                     |

### 1.2.2 Out of Scope (Future Work)

The following features are documented for extensibility but are **not required**
for thesis evaluation:

- Web-based user interface (UI-MODE-002)
- REST API interface (UI-MODE-003)
- HTTP REST and serial device protocols (FR-DC-004 partial)
- Multi-node distributed deployment

### 1.3 Definitions and Acronyms

- **IoT:** Internet of Things
- **LLM:** Large Language Model
- **Fuzzy Logic:** Mathematical framework for reasoning with imprecise or
  qualitative information
- **Semantic Bridge:** The fuzzy logic layer that transforms numerical sensor
  values into linguistic concepts understandable by the LLM
- **Membership Function:** Mathematical function defining the degree to which a
  value belongs to a fuzzy set
- **Linguistic Variable:** Variable whose values are words or sentences in
  natural language
- **Edge Device:** Computing device deployed at the network edge near data
  sources
- **Actuator:** Device that converts control signals into physical actions
- **Ollama:** Open-source platform for running LLMs locally without cloud
  dependencies

### 1.4 References

- **thesis-setup.md:** Authoritative thesis assignment defining research scope
- **project-brief.md:** High-level project overview and objectives
- **add.md:** Architecture Design Document
- IEEE 830-1998: IEEE Recommended Practice for Software Requirements
  Specifications

### 1.5 Overview

This document contains functional requirements, non-functional requirements,
system interfaces, and performance specifications. Requirements are organized by
system component and assigned unique identifiers for traceability.

______________________________________________________________________

## 2. Overall Description

### 2.1 Product Perspective

The system consists of four primary components implementing the **semantic
bridge** architecture:

1. **Fuzzy Logic Module (Semantic Bridge):** Converts numerical sensor data to
   linguistic descriptions that an LLM can understand
2. **LLM Interface:** Processes linguistic data and natural language rules via
   Ollama
3. **Rule Interpretation System:** Maps LLM outputs to device control actions
4. **Device Control Interface:** Communicates with IoT sensors and actuators via
   MQTT

### 2.2 Product Functions

The system performs the following high-level functions:

- Acquire numerical data from IoT sensors
- Apply fuzzy logic transformations to generate linguistic descriptions
- Accept and parse natural language control rules from users
- Process linguistic sensor states and rules using an offline LLM
- Generate device control commands based on LLM reasoning
- Execute control commands on IoT actuators
- Provide configuration interfaces for fuzzy logic parameters

### 2.3 User Characteristics

**Primary Users:** Non-technical individuals managing IoT environments without
programming expertise. Users can express control logic in natural language and
understand qualitative sensor descriptions.

**Secondary Users:** System administrators and technical personnel responsible
for initial configuration, membership function definition, and system
deployment.

### 2.4 Constraints

- Python implementation language
- Offline LLM operation via Ollama without internet connectivity
- LLM model size limited to 7 billion parameters maximum
- JSON format for all configuration data
- MQTT protocol for device communication (thesis prototype)
- Edge device deployment on resource-constrained hardware
- No transmission of data to external services

### 2.5 Assumptions and Dependencies

- Target hardware supports Python runtime environment
- Sufficient computational resources exist for LLM inference
- Sensors and actuators provide standard communication interfaces
- Users can express control logic in coherent natural language
- JSON configuration files are syntactically valid

______________________________________________________________________

## 3. Functional Requirements

### 3.1 Fuzzy Logic Module (Semantic Bridge)

#### FR-FL-001: Numerical Data Processing

The system shall accept numerical sensor values and map them to linguistic
variables using configurable membership functions.

**Priority:** High\
**Input:** Numerical sensor value, sensor type identifier\
**Output:** Set of linguistic terms with membership degrees\
**Rationale:** Core functionality for translating quantitative data to
qualitative descriptions

#### FR-FL-002: JSON Configuration Loading

The system shall load membership function definitions from JSON configuration
files at runtime.

**Priority:** High\
**Input:** JSON file path\
**Output:** Loaded membership function definitions\
**Rationale:** Enables dynamic reconfiguration without code modification

#### FR-FL-003: Multiple Sensor Support

The system shall support simultaneous processing of data from multiple sensor
types with independent linguistic variable definitions.

**Priority:** High\
**Input:** Multiple sensor readings with type identifiers\
**Output:** Linguistic descriptions for each sensor\
**Rationale:** IoT environments contain heterogeneous sensor arrays

#### FR-FL-004: Membership Function Types

The system shall support the following membership function types: triangular,
trapezoidal, Gaussian, and sigmoid.

**Priority:** Medium\
**Input:** Function type specification in JSON\
**Output:** Computed membership degrees\
**Rationale:** Common membership function types cover most IoT use cases

#### FR-FL-005: Linguistic Term Generation

The system shall generate complete linguistic descriptions combining sensor
type, linguistic term, and membership degree.

**Priority:** High\
**Input:** Sensor value, membership function results\
**Output:** Formatted linguistic description\
**Example:** "temperature is high (0.85)"\
**Rationale:** LLM requires structured linguistic input

#### FR-FL-006: Configuration Validation

The system shall validate JSON configuration files for syntactic correctness and
semantic consistency before loading.

**Priority:** Medium\
**Input:** JSON configuration file\
**Output:** Validation report with errors or success confirmation\
**Rationale:** Prevents runtime errors from malformed configurations

#### FR-FL-007: Runtime Reconfiguration

The system shall allow modification of membership functions during runtime
without system restart.

**Priority:** Low\
**Input:** Updated JSON configuration\
**Output:** Confirmation of successful reconfiguration\
**Rationale:** Facilitates iterative tuning and adaptation

### 3.2 LLM Interface

#### FR-LLM-001: Offline Model Loading

The system shall load and initialize a lightweight offline LLM optimized for
edge deployment via Ollama from local storage. CPU-only inference is required.

**Priority:** High\
**Input:** Model name, Ollama configuration parameters\
**Output:** Initialized model instance ready for inference via Ollama REST API\
**Rationale:** Core requirement for offline operation on resource-constrained
edge devices

#### FR-LLM-002: Model Selection Support

The system shall support loading of qwen3:0.6b (default) or equivalent
lightweight open-source models through Ollama's unified interface, optimized for
CPU inference.

**Priority:** High\
**Input:** Model type identifier\
**Output:** Loaded model instance via Ollama\
**Rationale:** Flexibility to select optimal model for edge hardware constraints

#### FR-LLM-003: Linguistic Input Processing

The system shall format linguistic sensor descriptions and natural language
rules into appropriate prompts for LLM consumption.

**Priority:** High\
**Input:** Linguistic descriptions, user-defined rules\
**Output:** Formatted prompt text\
**Rationale:** LLM performance depends on prompt structure

#### FR-LLM-004: Inference Execution

The system shall execute LLM inference on formatted prompts and return generated
text responses.

**Priority:** High\
**Input:** Formatted prompt\
**Output:** LLM-generated text response\
**Rationale:** Core LLM functionality

#### FR-LLM-005: Response Parsing

The system shall extract structured information from LLM text responses to
identify intended device actions.

**Priority:** High\
**Input:** LLM text response\
**Output:** Structured action specifications\
**Rationale:** Bridge between natural language output and device commands

#### FR-LLM-006: Model Optimization

The system shall support quantized model formats to reduce memory footprint and
improve inference speed.

**Priority:** Medium\
**Input:** Quantized model files\
**Output:** Optimized model instance\
**Rationale:** Edge device resource constraints

#### FR-LLM-007: Inference Timeout

The system shall enforce configurable timeout limits on LLM inference to prevent
indefinite blocking.

**Priority:** Medium\
**Input:** Timeout duration setting\
**Output:** Response within timeout or timeout error\
**Rationale:** Real-time control requires bounded response times

#### FR-LLM-008: Context Management

The system shall maintain conversation context across multiple rule evaluations
when explicitly configured.

**Priority:** Low\
**Input:** Previous interaction history, context retention setting\
**Output:** Context-aware LLM responses\
**Rationale:** Enables complex multi-step reasoning

### 3.3 Rule Interpretation System

#### FR-RI-001: Natural Language Rule Input

The system shall accept control rules expressed in free-form natural language
text.

**Priority:** High\
**Input:** Natural language rule text\
**Output:** Stored rule for processing\
**Rationale:** Core user interaction method

#### FR-RI-002: Rule Storage

The system shall persistently store user-defined rules for repeated evaluation.

**Priority:** High\
**Input:** Natural language rule\
**Output:** Confirmation of successful storage\
**Rationale:** Rules must survive system restarts

#### FR-RI-003: Condition Matching

The system shall match current linguistic sensor descriptions against conditions
specified in natural language rules.

**Priority:** High\
**Input:** Current sensor states, stored rules\
**Output:** Set of applicable rules\
**Rationale:** Determines which rules activate

#### FR-RI-004: Action Extraction

The system shall extract device control actions from LLM responses and map them
to specific device commands.

**Priority:** High\
**Input:** LLM-generated response\
**Output:** Device identifier and command parameters\
**Rationale:** Translation from natural language to executable commands

#### FR-RI-005: Multi-Device Commands

The system shall support rules that generate control commands for multiple
devices simultaneously.

**Priority:** Medium\
**Input:** Rule affecting multiple devices\
**Output:** Set of device-specific commands\
**Rationale:** Realistic scenarios involve coordinated device control

#### FR-RI-006: Conflict Resolution

The system shall detect and resolve conflicts when multiple rules produce
contradictory commands for the same device.

**Priority:** Medium\
**Input:** Multiple conflicting commands\
**Output:** Single resolved command or conflict notification\
**Rationale:** Prevents undefined system behavior

#### FR-RI-007: Rule Priority

The system shall support optional priority levels for rules to facilitate
conflict resolution.

**Priority:** Low\
**Input:** Rule with assigned priority\
**Output:** Priority-aware rule execution\
**Rationale:** User control over conflict resolution

#### FR-RI-008: Rule Validation

The system shall validate natural language rules for basic coherence and provide
feedback on ambiguous or incomplete specifications.

**Priority:** Medium\
**Input:** Natural language rule\
**Output:** Validation feedback or acceptance confirmation\
**Rationale:** Improves user experience and system reliability

### 3.4 Device Control Interface

#### FR-DC-001: Sensor Data Acquisition

The system shall acquire numerical data from configured IoT sensors through
standard communication protocols.

**Priority:** High\
**Input:** Sensor configuration\
**Output:** Current sensor readings\
**Rationale:** Primary data source for system operation

#### FR-DC-002: Actuator Command Execution

The system shall transmit control commands to IoT actuators through appropriate
communication interfaces.

**Priority:** High\
**Input:** Device identifier, command parameters\
**Output:** Command execution confirmation or error\
**Rationale:** System output mechanism

#### FR-DC-003: Device Registration

The system shall maintain a registry of available sensors and actuators with
their capabilities and communication parameters.

**Priority:** High\
**Input:** Device specification\
**Output:** Updated device registry\
**Rationale:** Dynamic device discovery and management

#### FR-DC-004: Communication Protocol Support

The system shall support MQTT as the primary IoT communication protocol via
Eclipse Mosquitto broker (thesis prototype). HTTP REST APIs and serial
communication are supported as extensibility options for future work.

**Priority:** High (MQTT), Low (HTTP REST, serial)\
**Input:** Protocol-specific configuration\
**Output:** Established communication channels\
**Rationale:** MQTT is the de facto standard for IoT device communication

#### FR-DC-005: Polling and Events

The system shall support both periodic sensor polling and event-driven sensor
updates.

**Priority:** Medium\
**Input:** Polling interval or event subscription configuration\
**Output:** Timely sensor data updates\
**Rationale:** Different sensors require different update mechanisms

#### FR-DC-006: Device Health Monitoring

The system shall monitor communication health with registered devices and report
failures.

**Priority:** Low\
**Input:** Device communication attempts\
**Output:** Device availability status\
**Rationale:** System reliability and diagnostics

#### FR-DC-007: Command Logging

The system shall log all executed device commands with timestamps for audit and
debugging purposes.

**Priority:** Low\
**Input:** Executed commands\
**Output:** Persistent command log\
**Rationale:** Troubleshooting and system analysis

### 3.5 Configuration Management

#### FR-CM-001: JSON Schema Definition

The system shall provide JSON schema specifications for membership functions,
linguistic variables, and device configurations.

**Priority:** High\
**Input:** Schema documentation\
**Output:** Valid JSON configuration files\
**Rationale:** Standardized configuration format

#### FR-CM-002: Configuration File Loading

The system shall load all configuration files at system startup and validate
their contents.

**Priority:** High\
**Input:** Configuration file paths\
**Output:** Loaded and validated configuration data\
**Rationale:** System initialization

#### FR-CM-003: Configuration Export

The system shall export current configuration to JSON files for backup and
replication purposes.

**Priority:** Medium\
**Input:** Export request\
**Output:** JSON configuration files\
**Rationale:** Configuration portability

#### FR-CM-004: Default Configurations

The system shall provide default configuration templates for common IoT
scenarios.

**Priority:** Low\
**Input:** Scenario type selection\
**Output:** Pre-configured membership functions and device settings\
**Rationale:** Simplified initial setup

### 3.6 User Interface

#### FR-UI-001: Rule Definition Interface

The system shall provide an interface for users to input, edit, and delete
natural language control rules.

**Priority:** High\
**Input:** User interaction\
**Output:** Updated rule set\
**Rationale:** Primary user interaction

#### FR-UI-002: System Status Display

The system shall display current sensor states in both numerical and linguistic
formats.

**Priority:** Medium\
**Input:** Current system state\
**Output:** Formatted status information\
**Rationale:** System transparency

#### FR-UI-003: Rule Execution Feedback

The system shall provide feedback on rule evaluation results and executed
actions.

**Priority:** Medium\
**Input:** Rule evaluation events\
**Output:** User-readable feedback messages\
**Rationale:** User understanding of system behavior

#### FR-UI-004: Configuration Interface

The system shall provide an interface for technical users to modify fuzzy logic
configurations.

**Priority:** Low\
**Input:** Configuration modification requests\
**Output:** Updated configuration and confirmation\
**Rationale:** Advanced system tuning

______________________________________________________________________

## 4. Non-Functional Requirements

### 4.1 Performance Requirements

#### NFR-PERF-001: Response Time

The system shall generate device control commands within 5 seconds of sensor
data acquisition for typical scenarios.

**Priority:** High\
**Measurement:** Time from sensor reading to command execution\
**Rationale:** Real-time control expectations

#### NFR-PERF-002: LLM Inference Latency

The system shall complete LLM inference within 3 seconds for prompts up to 500
tokens on target hardware.

**Priority:** High\
**Measurement:** Time from prompt submission to response generation\
**Rationale:** User experience and control loop timing

#### NFR-PERF-003: Fuzzy Logic Processing

The system shall compute linguistic descriptions for up to 20 sensors within 100
milliseconds.

**Priority:** Medium\
**Measurement:** Processing time for fuzzy transformations\
**Rationale:** Minimal overhead for preprocessing

#### NFR-PERF-004: Concurrent Rule Evaluation

The system shall support evaluation of up to 50 concurrent rules without
performance degradation.

**Priority:** Medium\
**Measurement:** Rule processing throughput\
**Rationale:** Complex automation scenarios

#### NFR-PERF-005: Memory Footprint

The system shall operate within 2GB RAM (minimum) to 4GB RAM (recommended)
including loaded LLM model on target edge hardware.

**Priority:** High\
**Measurement:** Peak memory usage\
**Rationale:** Edge/embedded device constraints

### 4.2 Reliability Requirements

#### NFR-REL-001: Availability

The system shall achieve 99% uptime during continuous operation excluding
planned maintenance.

**Priority:** High\
**Measurement:** Operational time / total time\
**Rationale:** Critical infrastructure control

#### NFR-REL-002: Error Recovery

The system shall recover from transient device communication failures without
manual intervention.

**Priority:** Medium\
**Measurement:** Successful recovery rate\
**Rationale:** Unattended operation

#### NFR-REL-003: Data Integrity

The system shall prevent corruption of configuration files and rule definitions
through atomic write operations.

**Priority:** High\
**Measurement:** Configuration corruption incidents\
**Rationale:** System consistency

### 4.3 Usability Requirements

#### NFR-USE-001: Rule Interpretation Accuracy

The system shall correctly interpret at least 85% of well-formed natural
language rules without ambiguity.

**Priority:** High\
**Measurement:** Correct interpretations / total rules tested\
**Rationale:** Core value proposition

#### NFR-USE-002: Setup Time

A non-technical user shall configure a basic automation scenario within 30
minutes using provided templates.

**Priority:** Medium\
**Measurement:** Time to functional configuration\
**Rationale:** Accessibility to target users

#### NFR-USE-003: Error Messages

The system shall provide clear, actionable error messages for common user
mistakes.

**Priority:** Medium\
**Measurement:** User comprehension in testing\
**Rationale:** Reduced support burden

### 4.4 Security Requirements

#### NFR-SEC-001: Data Privacy

The system shall not transmit any sensor data, rules, or device commands to
external networks.

**Priority:** High\
**Measurement:** Network traffic analysis\
**Rationale:** Privacy requirement

#### NFR-SEC-002: Configuration Access Control

The system shall restrict modification of fuzzy logic configurations to
authorized users.

**Priority:** Medium\
**Measurement:** Access control enforcement\
**Rationale:** Prevent accidental misconfiguration

#### NFR-SEC-003: Command Validation

The system shall validate all device commands against device capability
specifications before execution.

**Priority:** Medium\
**Measurement:** Invalid command rejection rate\
**Rationale:** Prevent device damage

### 4.5 Maintainability Requirements

#### NFR-MAIN-001: Modular Architecture

The system shall implement clear interfaces between fuzzy logic, LLM, and device
control components.

**Priority:** High\
**Measurement:** Component coupling metrics\
**Rationale:** Independent component evolution

#### NFR-MAIN-002: Logging

The system shall log all significant events including rule evaluations, device
commands, and errors with configurable verbosity.

**Priority:** Medium\
**Measurement:** Log completeness\
**Rationale:** Debugging and analysis

#### NFR-MAIN-003: Code Documentation

All public APIs and configuration formats shall include comprehensive
documentation with examples.

**Priority:** Medium\
**Measurement:** Documentation coverage\
**Rationale:** Developer productivity

### 4.6 Portability Requirements

#### NFR-PORT-001: Python Version

The system shall operate on Python 3.9 or later.

**Priority:** High\
**Measurement:** Successful execution on target versions\
**Rationale:** Platform compatibility

#### NFR-PORT-002: Hardware Independence

The system shall function on x86-64 and ARM64 processor architectures.

**Priority:** Medium\
**Measurement:** Successful deployment on multiple architectures\
**Rationale:** Diverse edge device landscape

#### NFR-PORT-003: Operating System Support

The system shall operate on Linux-based operating systems commonly used for edge
computing.

**Priority:** Medium\
**Measurement:** Successful deployment on target OS distributions\
**Rationale:** Edge device prevalence

______________________________________________________________________

## 5. System Interfaces

### 5.1 Hardware Interfaces

#### HW-INT-001: Sensor Interface

The system shall interface with sensors through standard GPIO, I2C, SPI, or
network protocols depending on sensor type.

**Input Format:** Protocol-specific numerical data\
**Output Format:** Not applicable\
**Error Handling:** Communication timeout detection and retry logic

#### HW-INT-002: Actuator Interface

The system shall interface with actuators through GPIO, PWM, relay control, or
network protocols.

**Input Format:** Not applicable\
**Output Format:** Protocol-specific control signals\
**Error Handling:** Command acknowledgment verification

### 5.2 Software Interfaces

#### SW-INT-001: LLM Model Interface

The system shall interface with LLM models through Ollama's REST API for local
inference.

**Input Format:** JSON request with prompt text\
**Output Format:** JSON response with generated text\
**Error Handling:** Inference timeout and service unavailability handling

#### SW-INT-002: JSON Parser

The system shall use Python's standard json library for configuration file
parsing.

**Input Format:** UTF-8 encoded JSON files\
**Output Format:** Python dictionaries and lists\
**Error Handling:** Syntax error reporting with line numbers

#### SW-INT-003: MQTT Broker

The system shall optionally interface with MQTT brokers for device communication
using the paho-mqtt library.

**Input Format:** MQTT messages with JSON payloads\
**Output Format:** MQTT publish messages\
**Error Handling:** Connection loss recovery

### 5.3 Communication Interfaces

#### COM-INT-001: Device Communication Protocol

The system shall communicate with devices using standardized message formats
defined in JSON schemas.

**Protocol:** Device-dependent (MQTT, HTTP, serial)\
**Data Format:** JSON for structured data\
**Authentication:** Device-specific credential handling

______________________________________________________________________

## 6. Data Requirements

### 6.1 Data Structures

#### DATA-001: Sensor Reading

Structure representing a single sensor measurement.

**Fields:**

- sensor_id: String identifier
- timestamp: ISO 8601 datetime
- value: Floating point number
- unit: String (e.g., "celsius", "percent")
- quality: Optional quality indicator

#### DATA-002: Linguistic Description

Structure representing fuzzified sensor data.

**Fields:**

- sensor_id: String identifier
- linguistic_terms: List of (term, membership_degree) tuples
- timestamp: ISO 8601 datetime
- raw_value: Original numerical value

#### DATA-003: Natural Language Rule

Structure representing a user-defined control rule.

**Fields:**

- rule_id: Unique identifier
- rule_text: Natural language specification
- priority: Integer priority level
- enabled: Boolean activation flag
- created_timestamp: ISO 8601 datetime
- last_triggered: ISO 8601 datetime or null

#### DATA-004: Device Command

Structure representing a control action.

**Fields:**

- device_id: String identifier
- command_type: String (e.g., "set_value", "toggle")
- parameters: Dictionary of command-specific parameters
- timestamp: ISO 8601 datetime
- rule_id: Originating rule identifier

#### DATA-005: Membership Function Definition

JSON structure defining a fuzzy membership function.

**Fields:**

- function_type: String ("triangular", "trapezoidal", "gaussian", "sigmoid")
- parameters: Dictionary of type-specific parameters
- linguistic_term: String label
- universe_min: Minimum value in universe of discourse
- universe_max: Maximum value in universe of discourse

### 6.2 Data Persistence

#### DATA-PERS-001: Configuration Storage

All configuration data shall persist in JSON files on local filesystem with
atomic write operations.

**Location:** Configurable directory path\
**Format:** JSON with schema validation\
**Backup:** Optional automatic backup on modification

#### DATA-PERS-002: Rule Storage

Natural language rules shall persist in a structured file format supporting
efficient retrieval.

**Location:** Configurable file path\
**Format:** JSON array or line-delimited JSON\
**Indexing:** In-memory index for active rules

#### DATA-PERS-003: Event Logging

System events shall persist in structured log files with rotation.

**Location:** Configurable log directory\
**Format:** Line-delimited JSON or standard logging format\
**Rotation:** Size-based or time-based rotation

______________________________________________________________________

## 7. External Interface Requirements

### 7.1 User Interfaces

The system shall provide the following user interface modes:

#### UI-MODE-001: Command-Line Interface (Required for Thesis)

A command-line interface for system administration, configuration, and rule
management.

**Capabilities:**

- System startup and shutdown
- Rule addition, modification, deletion
- Status monitoring
- Configuration validation
- Log viewing

#### UI-MODE-002: Web Interface (Optional — Future Work)

An optional web-based interface for user-friendly rule management and system
monitoring. **Not required for thesis evaluation.**

**Capabilities:**

- Visual rule editor
- Real-time sensor status display
- Rule execution history
- Device status visualization

#### UI-MODE-003: API Interface (Optional — Future Work)

A programmatic API for integration with external systems or custom interfaces.
**Not required for thesis evaluation.**

**Protocol:** REST API over HTTP or Python API for embedded use\
**Authentication:** Token-based authentication for network API\
**Endpoints:** Rule management, status queries, device control

______________________________________________________________________

## 8. System Features by Priority

### 8.1 High Priority (Required for Thesis — MVP)

- FR-FL-001: Numerical Data Processing (Semantic Bridge)
- FR-FL-002: JSON Configuration Loading
- FR-FL-003: Multiple Sensor Support
- FR-FL-005: Linguistic Term Generation
- FR-LLM-001: Offline Model Loading (via Ollama)
- FR-LLM-002: Model Selection Support
- FR-LLM-003: Linguistic Input Processing
- FR-LLM-004: Inference Execution
- FR-LLM-005: Response Parsing
- FR-RI-001: Natural Language Rule Input
- FR-RI-002: Rule Storage
- FR-RI-003: Condition Matching
- FR-RI-004: Action Extraction
- FR-DC-001: Sensor Data Acquisition
- FR-DC-002: Actuator Command Execution
- FR-DC-003: Device Registration
- FR-DC-004: MQTT Communication Protocol
- FR-CM-001: JSON Schema Definition
- FR-CM-002: Configuration File Loading
- FR-UI-001: Rule Definition Interface (CLI)

### 8.2 Medium Priority (Important for Usability — Thesis Scope)

- FR-FL-004: Membership Function Types
- FR-FL-006: Configuration Validation
- FR-LLM-006: Model Optimization (quantization)
- FR-LLM-007: Inference Timeout
- FR-RI-005: Multi-Device Commands
- FR-RI-006: Conflict Resolution
- FR-RI-008: Rule Validation
- FR-DC-005: Polling and Events
- FR-CM-003: Configuration Export
- FR-UI-002: System Status Display
- FR-UI-003: Rule Execution Feedback

### 8.3 Low Priority (Enhanced Functionality — Future Work)

- FR-FL-007: Runtime Reconfiguration
- FR-LLM-008: Context Management
- FR-RI-007: Rule Priority
- FR-DC-004: HTTP REST and Serial protocols (extensibility)
- FR-DC-006: Device Health Monitoring
- FR-DC-007: Command Logging
- FR-CM-004: Default Configurations
- FR-UI-004: Configuration Interface
- UI-MODE-002: Web Interface
- UI-MODE-003: REST API Interface

______________________________________________________________________

## 9. Acceptance Criteria

The system shall be considered complete and ready for thesis evaluation when it
satisfies the following criteria:

### 9.1 Functional Completeness (Thesis MVP)

1. All high-priority functional requirements (Section 8.1) are implemented and
   tested
2. At least 80% of medium-priority requirements are implemented
3. Smart home demonstration scenario executes successfully end-to-end
4. Semantic bridge correctly transforms sensor values to linguistic descriptions
5. All documented APIs function as specified

### 9.2 Performance Validation

1. Response time requirements (NFR-PERF-001, NFR-PERF-002) met in 90% of test
   cases
2. Memory footprint (NFR-PERF-005) verified on target hardware
3. Concurrent rule evaluation (NFR-PERF-004) tested at specified load

### 9.3 Quality Assurance

1. Rule interpretation accuracy (NFR-USE-001) validated with diverse test rules
2. System achieves 95% test coverage for core components
3. No critical or high-severity defects remain unresolved
4. All configuration schemas validated against representative use cases

### 9.4 Documentation Completeness

1. All public APIs documented with examples
2. User guide covers common scenarios
3. Installation and deployment procedures verified
4. JSON schema specifications complete and validated

### 9.5 Usability Validation (Thesis Evaluation)

1. Setup time requirement (NFR-USE-002) validated with representative users
2. Error messages reviewed for clarity and actionability
3. At least three test scenarios executable by non-technical users
4. **Rule interpretation accuracy** measured and documented
5. **Response time** from sensor input to actuator control measured (target \<
   5s)
6. **End-user usability** assessment conducted as specified in thesis assignment

______________________________________________________________________

## 10. Appendices

### Appendix A: Example JSON Configuration Schema

```json
{
  "sensor_id": "temperature_sensor_01",
  "linguistic_variables": [
    {
      "term": "cold",
      "function_type": "trapezoidal",
      "parameters": {
        "a": -10,
        "b": 0,
        "c": 10,
        "d": 15
      }
    },
    {
      "term": "comfortable",
      "function_type": "triangular",
      "parameters": {
        "a": 10,
        "b": 20,
        "c": 25
      }
    },
    {
      "term": "hot",
      "function_type": "trapezoidal",
      "parameters": {
        "a": 22,
        "b": 27,
        "c": 40,
        "d": 50
      }
    }
  ],
  "universe_of_discourse": {
    "min": -10,
    "max": 50,
    "unit": "celsius"
  }
}
```

### Appendix B: Example Natural Language Rules

1. "If the temperature is hot and humidity is high, turn on the air conditioner"
2. "When the soil moisture is low, activate the irrigation system for 10
   minutes"
3. "If motion is detected at night, turn on the outdoor lights"
4. "When the room is cold and it's morning time, increase the heating to
   comfortable levels"

### Appendix C: Traceability Matrix

This section maps requirements to project objectives and success criteria:

| Requirement ID | Project Objective   | Success Criterion |
| -------------- | ------------------- | ----------------- |
| FR-RI-001      | Objective 1         | Criterion 1, 5    |
| FR-FL-001      | Objective 2         | Criterion 1       |
| FR-LLM-001     | Objective 3, 5      | Criterion 3       |
| FR-LLM-005     | Objective 4         | Criterion 1       |
| NFR-PERF-001   | Objective 4         | Criterion 2       |
| NFR-USE-001    | Success Criterion 1 | Criterion 1       |
