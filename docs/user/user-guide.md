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

The CLI can be accessed using the `iot-fuzzy-llm` command (if installed via
`pip install -e .`) or by running the module directly:

```bash
# Using installed command
iot-fuzzy-llm status

# Using python module (if not installed)
python3 -m src.interfaces status

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

# JSON output for scripting
iot-fuzzy-llm --format json status

# Connect to custom gRPC server
iot-fuzzy-llm --grpc-host localhost --grpc-port 50051 status
```

> [!NOTE]
> The `status` command connects to a running application via the gRPC interface
> (default: `localhost:50051`). The gRPC port can be customized with
> `--grpc-port` or by setting the `IOT_GRPC_PORT` environment variable.

**Status Output (after start):**

```
✓ Connected to running application.
System State: RUNNING
Ready: Yes
Uptime (seconds): 124
Version: 0.1.0
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
ID            | Enabled | Text
--------------+---------+----------------------------------------------------
climate_001   | Yes     | If the living room temperature is hot and humidity
              |         | is high, turn on the air conditioner and set it to
              |         | cooling mode at 22 degrees
--------------+---------+----------------------------------------------------
climate_002   | Yes     | If the living room temperature is warm and
              |         | humidity is comfortable, no action is needed
--------------+---------+----------------------------------------------------
lighting_001  | Yes     | When motion is detected in the hallway and the
              |         | light level is dark, turn on the hallway light
...

Total: 10 rule(s)
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

> [!NOTE]
> The `--id`, `--priority`, and `--tag` options are accepted by the CLI but not
> currently passed to the gRPC `AddRule` call. The rule will receive an
> auto-generated ID regardless of `--id`. These options may be implemented in a
> future release.

### Viewing Rule Details

```bash
iot-fuzzy-llm rule show climate_001
```

**Example Output:**

```
Rule ID: climate_001
Text: If the living room temperature is hot and humidity is high, turn on the air conditioner and set it to cooling mode at 22 degrees
Enabled: Yes
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
ID                      | Name                              | Type     | Class           | Location
------------------------+-----------------------------------+----------+-----------------+-------------
temp_living_room        | Living Room Temperature Sensor    | sensor   | -               | living_room
humidity_living_room    | Living Room Humidity Sensor       | sensor   | -               | living_room
ac_living_room          | Living Room Air Conditioner       | actuator | set_temperature | living_room
light_hallway           | Hallway Light                     | actuator | turn_on         | hallway

Total: 14 device(s)
```

### Viewing Device Status

```bash
# Status for all devices
iot-fuzzy-llm device status

# Status for a specific device
iot-fuzzy-llm device status ac_living_room
```

**Example Output:**

```
Living Room Air Conditioner (ac_living_room)
  Type: actuator
  Class: set_temperature
  Location: living_room
  Status: registered
  Capabilities: set_temperature, set_mode, turn_on, turn_off
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
ID                      | Name                              | Class | Location    | Unit
------------------------+-----------------------------------+-------+-------------+-----
temp_living_room        | Living Room Temperature Sensor    | -     | living_room | -
humidity_living_room    | Living Room Humidity Sensor       | -     | living_room | -
motion_hallway          | Hallway Motion Sensor             | -     | hallway     | -

Total: 7 sensor(s)
```

### Viewing Sensor Status

```bash
# Status for all sensors
iot-fuzzy-llm sensor status

# Status for a specific sensor
iot-fuzzy-llm sensor status temp_living_room
```

**Example Output:**

```
Living Room Temperature Sensor (temp_living_room)
  Class: N/A
  Location: living_room
  Unit: N/A
  Status: registered
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
  ✓ llm_config
  ✓ mqtt_config
```

### Reloading Configuration

Reload configuration at runtime without restarting:

```bash
iot-fuzzy-llm config reload
```

### Migrating Configuration

Migrate configuration files to the latest schema format:

```bash
iot-fuzzy-llm config migrate

# Preview changes without modifying files
iot-fuzzy-llm config migrate --dry-run
```

The migration command detects missing required fields in `devices.json` and
`mqtt_config.json` and adds them with default values. It creates `.bak` backups
before modifying any file.

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
Last 5 entries from category:

2026-03-22 21:35:50.548869 [INFO] ConfigurationManager initialized
2026-03-22 21:35:50.551329 [INFO] MQTT manager initialized
2026-03-22 21:35:51.102844 [INFO] Ollama client initialized
2026-03-22 21:35:51.103102 [INFO] System initialized successfully
2026-03-22 21:35:51.103298 [INFO] System started
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
ID                      | Name                              | Type     | Class           | Location
------------------------+-----------------------------------+----------+-----------------+-------------
temp_living_room        | Living Room Temperature Sensor    | sensor   | -               | living_room
```

### JSON Format

Machine-readable JSON for scripting:

```bash
iot-fuzzy-llm --format json device list
```

```json
[
  {
    "id": "temp_living_room",
    "name": "Living Room Temperature Sensor",
    "type": "sensor",
    "device_class": "-",
    "location": "living_room"
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

### 11.2 Dashboard

The main dashboard page provides:

- **System Status** — Current state (Running/Stopped), readiness, version, and
  uptime displayed as metric tiles.
- **System Control** — Start and stop buttons for the IoT management system.
- **Auto-Refresh** — Toggle for automatic page refresh to show updated sensor
  readings.
- **Sensor Readings** — Current values for all configured sensors with zone and
  type filters.

### 11.3 Rule Management

The rule management page provides:

- A text input form to add new natural language rules
- Expandable cards for each rule showing full rule text
- Enable/disable toggle for each rule
- Delete button with confirmation for removing rules

### 11.4 Configuration Editing

The configuration editor supports **direct JSON editing in-browser**:

- Three tabs for `devices.json`, `mqtt_config.json`, and `llm_config.json`
- JSON text area editor for each configuration file
- Save button to persist changes with automatic backup

### 11.5 Membership Function Editor

The membership function editor provides a **JSON-based editor** for adjusting
fuzzy membership functions:

- Sensor type selector dropdown to choose which membership functions to edit
- JSON viewer showing the current membership function configuration
- Text area editor for modifying the JSON directly
- Save button to persist changes to the membership functions file

### 11.6 Log Viewing

The log viewer provides:

- Category selector (system, commands, sensors, errors, rules)
- Log level filter
- Text search across log entries
- Manual refresh button to load latest entries
- Tabular log display using a dataframe view
