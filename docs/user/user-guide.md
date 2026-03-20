# User Guide

## Fuzzy-LLM Hybrid IoT Management System

**Document Status:** Active\
**Last Updated:** 2026-02-05

This guide provides comprehensive instructions for using the Fuzzy-LLM Hybrid
IoT Management System through its command-line interface.

______________________________________________________________________

## Table of Contents

01. [Getting Started](#1-getting-started)
02. [CLI Overview](#2-cli-overview)
03. [System Management](#3-system-management)
04. [Rule Management](#4-rule-management)
05. [Device Management](#5-device-management)
06. [Sensor Management](#6-sensor-management)
07. [Configuration Management](#7-configuration-management)
08. [Log Viewing](#8-log-viewing)
09. [Common Workflows](#9-common-workflows)
10. [Output Formats](#10-output-formats)
11. [Web Interface](#11-web-interface)

______________________________________________________________________

## 1. Getting Started

### Prerequisites

Before using the CLI, ensure:

1. The system is installed (see [Installation Guide](installation-guide.md))
2. Configuration files are in place (`config/` directory)
3. Ollama is running with a model installed
4. MQTT broker is accessible (optional, can skip)

### First Run

```bash
# Check system status
iot-fuzzy-llm status

# Start the system
iot-fuzzy-llm start

# Verify system is running
iot-fuzzy-llm status
```

### Getting Help

```bash
# Show all commands
iot-fuzzy-llm --help

# Show help for a specific command
iot-fuzzy-llm start --help
iot-fuzzy-llm rule --help
iot-fuzzy-llm rule add --help
```

______________________________________________________________________

## 2. CLI Overview

### Basic Syntax

```bash
iot-fuzzy-llm [OPTIONS] COMMAND [SUBCOMMAND] [ARGS]
```

### Global Options

| Option              | Description                                 |
| ------------------- | ------------------------------------------- |
| `--config-dir PATH` | Configuration directory (default: `config`) |
| `--rules-dir PATH`  | Rules directory (default: `rules`)          |
| `--logs-dir PATH`   | Logs directory (default: `logs`)            |
| `--grpc-host HOST`  | gRPC server host (default: `localhost`)     |
| `--grpc-port PORT`  | gRPC server port (default: `50051`)         |
| `--format FORMAT`   | Output format: `table`, `json`, `plain`     |
| `-v, --verbose`     | Enable verbose output                       |
| `--version`         | Show version and exit                       |
| `--help`            | Show help and exit                          |

### Command Groups

| Command  | Description                     |
| -------- | ------------------------------- |
| `start`  | Start the IoT management system |
| `stop`   | Stop the IoT management system  |
| `status` | Display system status           |
| `rule`   | Manage natural language rules   |
| `sensor` | View sensor information         |
| `device` | View device information         |
| `config` | Manage configuration            |
| `log`    | View system logs                |

______________________________________________________________________

## 3. System Management

### Starting the System

```bash
# Normal start
iot-fuzzy-llm start

# Start without MQTT (for testing)
iot-fuzzy-llm start --skip-mqtt

# Start without Ollama verification
iot-fuzzy-llm start --skip-ollama

# Start with verbose output
iot-fuzzy-llm -v start
```

**Start Options:**

| Option          | Description                      |
| --------------- | -------------------------------- |
| `--skip-mqtt`   | Skip MQTT broker connection      |
| `--skip-ollama` | Skip Ollama service verification |

### Stopping the System

```bash
iot-fuzzy-llm stop
```

### Checking System Status

```bash
# Basic status
iot-fuzzy-llm status

# Detailed status with initialization steps
iot-fuzzy-llm -v status

# JSON output for scripting
iot-fuzzy-llm --format json status

# Connect to custom gRPC server
iot-fuzzy-llm --grpc-host localhost --grpc-port 50051 status
```

> [!NOTE]
> The `status` command connects to a running application via the gRPC interface
> (default: `localhost:50051`). The gRPC port can be customized with
> `--grpc-port` or by setting the `GRPC_PORT` environment variable.

**Status Output (after start):**

```
System State: RUNNING
Ready: Yes

Components:
  ✓ config_manager: available
  ✓ device_registry: available
  ✓ fuzzy_engine: available
  ✓ ollama_client: available
  ✓ mqtt_client: available
```

______________________________________________________________________

## 4. Rule Management

Rules are natural language statements that define how the system responds to
sensor conditions.

### Listing Rules

```bash
# List all rules
iot-fuzzy-llm rule list

# List only enabled rules
iot-fuzzy-llm rule list --enabled-only

# Filter by tag
iot-fuzzy-llm rule list --tag comfort

# JSON output
iot-fuzzy-llm --format json rule list
```

**Example Output:**

```
ID           | Enabled | Priority | Text                                               | Tags
-------------+---------+----------+----------------------------------------------------+-----------------------------
climate_001  | Yes     | 1        | If the living room temperature is hot and humidity | climate, cooling, comfort
             |         |          | is high, turn on the air conditioner and set it to |
             |         |          | cooling mode at 22 degrees                         |
-------------+---------+----------+----------------------------------------------------+-----------------------------
climate_002  | Yes     | 2        | If the living room temperature is warm and         | climate, comfort
             |         |          | humidity is comfortable, no action is needed       |
-------------+---------+----------+----------------------------------------------------+-----------------------------
lighting_001 | Yes     | 1        | When motion is detected in the hallway and the     | lighting, motion, safety
             |         |          | light level is dark, turn on the hallway light     |

Total: 3 rule(s)
```

### Adding Rules

```bash
# Basic rule
iot-fuzzy-llm rule add "When living room temperature is hot, turn on the AC"

# With custom ID
iot-fuzzy-llm rule add --id my_rule "When humidity is high, turn on ventilation"

# With priority (1-100, higher = more important)
iot-fuzzy-llm rule add --priority 90 "When motion detected, turn on lights"

# With tags
iot-fuzzy-llm rule add -t comfort -t climate "When temperature is cold, turn on heater"
```

**Add Options:**

| Option          | Description                                     |
| --------------- | ----------------------------------------------- |
| `--id ID`       | Custom rule ID (auto-generated if not provided) |
| `--priority N`  | Priority 1-100 (default: 50)                    |
| `-t, --tag TAG` | Add tag (can be used multiple times)            |

### Viewing Rule Details

```bash
iot-fuzzy-llm rule show <rule_id>
```

**Example Output:**

```
Rule ID: rule_001
Text: When living room temperature is hot, turn on the AC and set it to 22 degrees
Enabled: Yes
Priority: 80
Tags: comfort, climate
Created: 2026-02-05T10:30:00
Trigger Count: 15
Last Triggered: 2026-02-05T14:22:00
```

### Enabling and Disabling Rules

```bash
# Enable a rule
iot-fuzzy-llm rule enable <rule_id>

# Disable a rule
iot-fuzzy-llm rule disable <rule_id>
```

### Deleting Rules

```bash
# Delete with confirmation
iot-fuzzy-llm rule delete <rule_id>

# Delete without confirmation
iot-fuzzy-llm rule delete <rule_id> --yes
```

______________________________________________________________________

## 5. Device Management

### Listing Devices

```bash
# List all devices (sensors and actuators)
iot-fuzzy-llm device list

# JSON output
iot-fuzzy-llm --format json device list
```

**Example Output:**

```
ID                      | Name                           | Type     | Class       | Location
------------------------+--------------------------------+----------+-------------+------------
temp_living_room        | Living Room Temperature Sensor | sensor   | temperature | living_room
motion_hallway          | Hallway Motion Sensor          | sensor   | motion      | hallway
ac_living_room          | Living Room Air Conditioner    | actuator | thermostat  | living_room
light_hallway           | Hallway Light                  | actuator | light       | hallway

Total: 4 device(s)
```

### Viewing Device Status

```bash
# Status for all devices
iot-fuzzy-llm device status

# Status for a specific device
iot-fuzzy-llm device status living_room_ac
```

**Example Output:**

```
Living Room AC (living_room_ac)
  Type: actuator
  Class: thermostat
  Location: Living Room
  Status: registered
  Capabilities: turn_on, turn_off, set_temperature
  MQTT Topic: home/living_room/ac/status
  Command Topic: home/living_room/ac/set
```

______________________________________________________________________

## 6. Sensor Management

### Listing Sensors

```bash
# List all sensors
iot-fuzzy-llm sensor list

# JSON output
iot-fuzzy-llm --format json sensor list
```

**Example Output:**

```
ID                      | Name                           | Class       | Location    | Unit
------------------------+--------------------------------+-------------+-------------+-----
temp_living_room        | Living Room Temperature Sensor | temperature | living_room | °C
humidity_living_room    | Living Room Humidity Sensor    | humidity    | living_room | %
motion_hallway          | Hallway Motion Sensor          | motion      | hallway     | -

Total: 3 sensor(s)
```

### Viewing Sensor Status

```bash
# Status for all sensors
iot-fuzzy-llm sensor status

# Status for a specific sensor
iot-fuzzy-llm sensor status living_room_temp
```

**Example Output:**

```
Living Room Temp (living_room_temp)
  Class: temperature
  Location: Living Room
  Unit: celsius
  Status: registered
  MQTT Topic: home/living_room/temperature
```

______________________________________________________________________

## 7. Configuration Management

### Validating Configuration

```bash
iot-fuzzy-llm config validate
```

**Example Output:**

```
ℹ Validating configuration files...
✓ All configuration files are valid.

Loaded configurations:
  ✓ devices
  ✓ mqtt
  ✓ llm
  ✓ membership_functions
```

### Reloading Configuration

Reload configuration at runtime without restarting:

```bash
iot-fuzzy-llm config reload
```

______________________________________________________________________

## 8. Log Viewing

### Viewing Recent Logs

```bash
# Default: last 20 lines from system log
iot-fuzzy-llm log tail

# Last 50 lines
iot-fuzzy-llm log tail -n 50

# Different log category
iot-fuzzy-llm log tail --category errors
iot-fuzzy-llm log tail --category commands
iot-fuzzy-llm log tail --category sensors
iot-fuzzy-llm log tail --category rules
```

**Log Categories:**

| Category   | Description                     |
| ---------- | ------------------------------- |
| `system`   | General system events (default) |
| `commands` | Actuator commands executed      |
| `sensors`  | Sensor readings received        |
| `errors`   | Error messages                  |
| `rules`    | Rule evaluation results         |

**Example Output:**

```
Last 5 entries from system.log:

2026-02-05T14:20:00 [INFO] System initialized successfully
2026-02-05T14:20:01 [INFO] Connected to MQTT broker
2026-02-05T14:22:00 [INFO] Rule rule_001 triggered
2026-02-05T14:22:01 [INFO] Command sent: living_room_ac turn_on
2026-02-05T14:22:02 [INFO] Actuator confirmed: living_room_ac
```

______________________________________________________________________

## 9. Common Workflows

### Initial Setup

```bash
# 1. Validate configuration
iot-fuzzy-llm config validate

# 2. Check devices are registered
iot-fuzzy-llm device list

# 3. Start system
iot-fuzzy-llm start

# 4. Verify status
iot-fuzzy-llm status
```

### Adding a New Automation Rule

```bash
# 1. Check current rules
iot-fuzzy-llm rule list

# 2. Add new rule
iot-fuzzy-llm rule add --priority 75 -t automation \
    "When bedroom temperature is cold, turn on the bedroom heater"

# 3. Verify rule was added
iot-fuzzy-llm rule list

# 4. Check rule details
iot-fuzzy-llm rule show <new_rule_id>
```

### Debugging Issues

```bash
# 1. Check system status
iot-fuzzy-llm -v status

# 2. View error logs
iot-fuzzy-llm log tail --category errors -n 50

# 3. Check if devices are registered
iot-fuzzy-llm device list

# 4. Validate configuration
iot-fuzzy-llm config validate

# 5. Check sensor status
iot-fuzzy-llm sensor status
```

### Temporarily Disabling a Rule

```bash
# Disable rule
iot-fuzzy-llm rule disable <rule_id>

# Later, re-enable it
iot-fuzzy-llm rule enable <rule_id>
```

### Testing Without External Services

```bash
# Start without MQTT and Ollama
iot-fuzzy-llm start --skip-mqtt --skip-ollama

# Check device configuration is correct
iot-fuzzy-llm device list
iot-fuzzy-llm sensor list

# Validate rules
iot-fuzzy-llm rule list
```

______________________________________________________________________

## 10. Output Formats

The CLI supports three output formats:

### Table Format (Default)

Human-readable tabular output:

```bash
iot-fuzzy-llm device list
```

```
ID                      | Name                           | Type     | Class       | Location
------------------------+--------------------------------+----------+-------------+------------
temp_living_room        | Living Room Temperature Sensor | sensor   | temperature | living_room
```

### JSON Format

Machine-readable JSON for scripting:

```bash
iot-fuzzy-llm --format json device list
```

```json
[
  {
    "id": "living_room_temp",
    "name": "Living Room Temp",
    "type": "sensor",
    "device_class": "temperature",
    "location": "Living Room"
  }
]
```

### Plain Format

Minimal output without formatting:

```bash
iot-fuzzy-llm --format plain status
```

### Using JSON Output in Scripts

```bash
# Get all device IDs
iot-fuzzy-llm --format json device list | jq -r '.[].id'

# Get enabled rule count
iot-fuzzy-llm --format json rule list --enabled-only | jq 'length'

# Check if system is ready
iot-fuzzy-llm --format json status | jq '.is_ready'
```

______________________________________________________________________

## See Also

- [Installation Guide](installation-guide.md) - System installation
- [Configuration Guide](configuration-guide.md) - Configuration options
- [Schema Reference](schema-reference.md) - Configuration file schemas
- [Demo Walkthrough](demo-walkthrough.md) - Step-by-step demo
- [Troubleshooting](demo-troubleshooting.md) - Common issues and solutions

______________________________________________________________________

## 11. Web Interface

> See [Web UI Guide](web-ui-guide.md) for full documentation.

The web interface is a **Streamlit-based browser dashboard** that operates **in
parallel with the CLI** — it is an additional interface, not a replacement. Both
interfaces are supported simultaneously.

The dashboard is accessible at `http://localhost:8501` by default.

### 11.1 Overview

Launch the web interface with:

```bash
streamlit run src/interfaces/web/streamlit_app.py
```

Or, when using Docker:

```bash
docker compose up -d
# Web UI available at http://localhost:8501
```

### 11.2 Real-Time Monitoring

The monitoring dashboard displays live updates for:

- **Sensor Readings** — Current values and fuzzy membership scores for all
  configured sensors, updated in real time as MQTT messages arrive.
- **Rule Evaluations** — Which rules are currently active, their condition
  evaluation results, and LLM reasoning output.
- **Device Commands** — Recent commands sent to actuators with timestamps and
  execution status.
- **System Health** — Connection status for MQTT broker and Ollama service,
  memory usage, and processing latency.

### 11.3 System Control

The control panel allows you to:

- Start and stop the IoT management system
- Trigger manual rule evaluation cycles
- Reload configuration without restarting
- View and manage active MQTT subscriptions

### 11.4 Rule Management

The rule management interface provides:

- A table view of all rules (enabled/disabled status, creation date, last
  triggered)
- Add new natural language rules via a text input
- Enable, disable, or delete existing rules with one click
- View the LLM interpretation and action extracted for each rule

### 11.5 Configuration Editing

The configuration editor allows **direct JSON editing in-browser**:

- Edit `devices.json`, `mqtt_config.json`, `llm_config.json` in a syntax-
  highlighted JSON editor
- Automatic schema validation before saving
- One-click configuration reload after saving
- Revision history with restore capability

### 11.6 Visual Membership Function Editor

The membership function editor provides a **drag-point graph interface** for
adjusting fuzzy sets:

- Visual graph showing all linguistic terms for a sensor type (e.g., cold,
  comfortable, hot for temperature)
- Drag control points to reshape membership function curves
- Live preview of how a specific sensor value maps to each linguistic term
- Save changes directly to the membership functions JSON file without manual
  editing

### 11.7 Log Viewing

The log viewer provides:

- Live-streaming log output with colour-coded severity levels
- Filtering by log level (DEBUG, INFO, WARNING, ERROR)
- Filtering by component (fuzzy engine, LLM client, MQTT, rule interpreter)
- Full-text search across log history
- Export logs to a file
