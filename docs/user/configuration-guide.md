# Configuration Guide

## Fuzzy-LLM Hybrid IoT Management System

**Document Status:** Active\
**Last Updated:** 2026-02-05

This guide explains how to configure the Fuzzy-LLM Hybrid IoT Management System
for your specific deployment needs.

______________________________________________________________________

## Table of Contents

1. [Configuration Overview](#1-configuration-overview)
2. [Device Configuration](#2-device-configuration)
3. [MQTT Configuration](#3-mqtt-configuration)
4. [LLM Configuration](#4-llm-configuration)
5. [Membership Functions](#5-membership-functions)
6. [Environment Variables](#6-environment-variables)
7. [Runtime Configuration](#7-runtime-configuration)

______________________________________________________________________

## 1. Configuration Overview

### Directory Structure

```
config/
├── devices.json                    # Device registry
├── mqtt_config.json               # MQTT broker settings
├── llm_config.json                # Ollama LLM settings
├── membership_functions/          # Fuzzy logic definitions
│   ├── temperature.json
│   ├── humidity.json
│   ├── light_level.json
│   └── motion.json
└── schemas/                       # JSON schemas for validation
    ├── devices.schema.json
    ├── mqtt.schema.json
    ├── llm.schema.json
    └── membership_functions.schema.json
```

### Configuration Principles

1. **JSON Format**: All configuration uses JSON for human readability
2. **Schema Validation**: Every file is validated against its schema on load
3. **Hot Reload**: Configuration can be reloaded without restart
4. **Backup**: Changes create timestamped backups automatically
5. **No Code Changes**: Modify behavior through config, not code

### Validating Configuration

```bash
# Validate all configuration files
iot-fuzzy-llm config validate

# Check JSON syntax manually
python -m json.tool config/devices.json
```

______________________________________________________________________

## 2. Device Configuration

**File:** `config/devices.json`\
**Schema:** `config/schemas/devices.schema.json`

### Adding a Sensor

```json
{
  "devices": [
    {
      "id": "living_room_temp",
      "name": "Living Room Temperature Sensor",
      "type": "sensor",
      "device_class": "temperature",
      "location": "Living Room",
      "unit": "celsius",
      "value_type": "float",
      "mqtt": {
        "topic": "home/living_room/temperature",
        "qos": 1
      },
      "constraints": {
        "min": -10.0,
        "max": 50.0
      }
    }
  ]
}
```

### Adding an Actuator

```json
{
  "id": "living_room_ac",
  "name": "Living Room Air Conditioner",
  "type": "actuator",
  "device_class": "thermostat",
  "location": "Living Room",
  "capabilities": ["turn_on", "turn_off", "set_temperature"],
  "mqtt": {
    "topic": "home/living_room/ac/status",
    "command_topic": "home/living_room/ac/set",
    "qos": 1
  },
  "constraints": {
    "min": 16,
    "max": 30,
    "step": 0.5
  }
}
```

### Device Types and Classes

**Sensor Types:**

| Device Class  | Description             | Typical Unit        |
| ------------- | ----------------------- | ------------------- |
| `temperature` | Temperature measurement | celsius, fahrenheit |
| `humidity`    | Relative humidity       | percent             |
| `motion`      | Motion detection        | bool                |
| `light_level` | Ambient light           | lux                 |
| `pressure`    | Atmospheric pressure    | hPa                 |
| `co2`         | CO2 concentration       | ppm                 |

**Actuator Types:**

| Device Class | Description   | Typical Capabilities               |
| ------------ | ------------- | ---------------------------------- |
| `thermostat` | HVAC control  | turn_on, turn_off, set_temperature |
| `switch`     | Binary switch | turn_on, turn_off                  |
| `light`      | Light control | turn_on, turn_off, set_brightness  |
| `blinds`     | Window blinds | open, close, set_position          |
| `fan`        | Fan control   | turn_on, turn_off, set_speed       |

### ID Naming Convention

Device IDs must:

- Use only lowercase letters, numbers, underscores, and hyphens
- Be unique across all devices
- Be descriptive of location and function

**Good examples:**

- `living_room_temp`
- `bedroom-heater-01`
- `hallway_motion_sensor`

**Bad examples:**

- `LivingRoomTemp` (no uppercase)
- `temp 1` (no spaces)
- `sensor` (not descriptive)

______________________________________________________________________

## 3. MQTT Configuration

**File:** `config/mqtt_config.json`\
**Schema:** `config/schemas/mqtt.schema.json`

### Basic Configuration

```json
{
  "broker": {
    "host": "localhost",
    "port": 1883,
    "keepalive": 60
  },
  "client": {
    "id": "iot-fuzzy-llm-controller",
    "clean_session": true,
    "protocol_version": 5
  }
}
```

### With Authentication

```json
{
  "broker": {
    "host": "mqtt.example.com",
    "port": 1883
  },
  "auth": {
    "username": "iot-controller",
    "password": "your-secure-password"
  }
}
```

### With TLS Encryption

```json
{
  "broker": {
    "host": "mqtt.example.com",
    "port": 8883
  },
  "auth": {
    "username": "iot-controller",
    "password": "your-secure-password"
  },
  "tls": {
    "enabled": true,
    "ca_certs": "/etc/ssl/certs/ca-certificates.crt"
  }
}
```

### With Reconnection and LWT

```json
{
  "broker": {
    "host": "localhost",
    "port": 1883,
    "keepalive": 60
  },
  "reconnect": {
    "enabled": true,
    "min_delay": 1,
    "max_delay": 30
  },
  "lwt": {
    "topic": "home/controller/status",
    "payload": "offline",
    "qos": 1,
    "retain": true
  }
}
```

### MQTT Topic Design

**Recommended topic structure:**

```
{location}/{room}/{device_class}
{location}/{room}/{device_class}/set    # For commands
```

**Examples:**

- `home/living_room/temperature` - Sensor reading
- `home/living_room/ac/set` - Actuator command

______________________________________________________________________

## 4. LLM Configuration

**File:** `config/llm_config.json`\
**Schema:** `config/schemas/llm.schema.json`

### Basic Configuration

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
      "name": "qwen3:0.6b"
    }
  }
}
```

### With Inference Parameters

```json
{
  "llm": {
    "provider": "ollama",
    "connection": {
      "host": "localhost",
      "port": 11434,
      "timeout_seconds": 60
    },
    "model": {
      "name": "qwen3:0.6b",
      "fallback_models": ["llama3.2:1b"]
    },
    "inference": {
      "temperature": 0.3,
      "max_tokens": 512,
      "top_p": 0.9,
      "top_k": 40,
      "repeat_penalty": 1.1
    }
  }
}
```

### Model Selection Guide

| Model         | Size   | Speed  | Accuracy | Use Case              |
| ------------- | ------ | ------ | -------- | --------------------- |
| `qwen3:0.6b`  | ~400MB | Fast   | Good     | Default, edge devices |
| `qwen3:1.7b`  | ~1GB   | Medium | Better   | When accuracy matters |
| `llama3.2:1b` | ~700MB | Medium | Good     | Alternative option    |
| `llama3.2:3b` | ~2GB   | Slow   | Best     | Powerful edge devices |

### Inference Parameters

| Parameter        | Range  | Default | Description                |
| ---------------- | ------ | ------- | -------------------------- |
| `temperature`    | 0-2    | 0.3     | Lower = more deterministic |
| `max_tokens`     | 1-4096 | 512     | Maximum response length    |
| `top_p`          | 0-1    | 0.9     | Nucleus sampling           |
| `top_k`          | 1-100  | 40      | Top-k sampling             |
| `repeat_penalty` | 1-2    | 1.1     | Discourage repetition      |

**Recommendations for IoT:**

- Use low temperature (0.1-0.3) for consistent responses
- Keep max_tokens low (256-512) for fast inference
- Use repeat_penalty > 1.0 to avoid repetitive outputs

______________________________________________________________________

## 5. Membership Functions

**Directory:** `config/membership_functions/`\
**Schema:** `config/schemas/membership_functions.schema.json`

Membership functions define how numerical sensor values are translated into
linguistic terms that the LLM can understand. This is the core of the "semantic
bridge" concept.

### Creating a Membership Function

**File:** `config/membership_functions/temperature.json`

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
      "parameters": { "a": -10.0, "b": -10.0, "c": 10.0, "d": 18.0 }
    },
    {
      "term": "comfortable",
      "function_type": "triangular",
      "parameters": { "a": 16.0, "b": 22.0, "c": 26.0 }
    },
    {
      "term": "warm",
      "function_type": "triangular",
      "parameters": { "a": 24.0, "b": 28.0, "c": 32.0 }
    },
    {
      "term": "hot",
      "function_type": "trapezoidal",
      "parameters": { "a": 30.0, "b": 35.0, "c": 50.0, "d": 50.0 }
    }
  ]
}
```

### Function Types

**Triangular** - Simple three-point function:

```
    /\
   /  \
  /    \
 a  b   c
```

Parameters: `a` (left), `b` (peak), `c` (right)

**Trapezoidal** - Four-point function with flat top:

```
    ____
   /    \
  /      \
 a  b  c  d
```

Parameters: `a` (left foot), `b` (left shoulder), `c` (right shoulder), `d`
(right foot)

**Gaussian** - Bell curve:

```
     *
    * *
   *   *
  *     *
   mean
```

Parameters: `mean` (center), `sigma` (spread)

**Sigmoid** - S-curve for boundaries:

```
        ****
       *
      *
  ****
    c (inflection)
```

Parameters: `a` (slope), `c` (inflection point)

### Design Guidelines

1. **Overlapping terms**: Terms should overlap slightly for smooth transitions
2. **Complete coverage**: Ensure the entire universe is covered
3. **Meaningful labels**: Use terms natural language rules can reference
4. **Confidence threshold**: Set to 0.1 to filter out weak matches

### Example: Humidity

```json
{
  "sensor_type": "humidity",
  "unit": "percent",
  "universe_of_discourse": { "min": 0.0, "max": 100.0 },
  "confidence_threshold": 0.1,
  "linguistic_variables": [
    {
      "term": "dry",
      "function_type": "trapezoidal",
      "parameters": { "a": 0.0, "b": 0.0, "c": 25.0, "d": 40.0 }
    },
    {
      "term": "comfortable",
      "function_type": "triangular",
      "parameters": { "a": 35.0, "b": 50.0, "c": 65.0 }
    },
    {
      "term": "humid",
      "function_type": "trapezoidal",
      "parameters": { "a": 60.0, "b": 75.0, "c": 100.0, "d": 100.0 }
    }
  ]
}
```

______________________________________________________________________

## 6. Environment Variables

Environment variables override configuration file values.

### Application Variables

| Variable     | Default | Description                                 |
| ------------ | ------- | ------------------------------------------- |
| `LOG_LEVEL`  | INFO    | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `CONFIG_DIR` | config  | Configuration directory path                |
| `RULES_DIR`  | rules   | Rules directory path                        |
| `LOGS_DIR`   | logs    | Logs directory path                         |

### MQTT Variables

| Variable        | Default   | Description                  |
| --------------- | --------- | ---------------------------- |
| `MQTT_HOST`     | localhost | MQTT broker hostname         |
| `MQTT_PORT`     | 1883      | MQTT broker port             |
| `MQTT_USERNAME` | -         | MQTT authentication username |
| `MQTT_PASSWORD` | -         | MQTT authentication password |

### Ollama Variables

| Variable       | Default    | Description                |
| -------------- | ---------- | -------------------------- |
| `OLLAMA_HOST`  | localhost  | Ollama service hostname    |
| `OLLAMA_PORT`  | 11434      | Ollama service port        |
| `OLLAMA_MODEL` | qwen3:0.6b | Model to use for inference |

### Docker Compose Variables

Create a `.env` file in the project root:

```bash
# .env
MQTT_PORT=1883
OLLAMA_PORT=11434
OLLAMA_MODEL=qwen3:0.6b
OLLAMA_PULL_ON_START=true
LOG_LEVEL=INFO
```

______________________________________________________________________

## 7. Runtime Configuration

### Reloading Configuration

Reload configuration without restarting:

```bash
iot-fuzzy-llm config reload
```

### Viewing Current Configuration

```bash
# Validate and show loaded configs
iot-fuzzy-llm config validate
```

### Configuration Precedence

1. Environment variables (highest priority)
2. Configuration files
3. Default values (lowest priority)

### Backup and Recovery

Configuration changes create automatic backups:

```
config/
├── devices.json
├── devices.json.backup.20260205_143022
└── devices.json.backup.20260204_091534
```

To recover:

```bash
cp config/devices.json.backup.20260205_143022 config/devices.json
iot-fuzzy-llm config reload
```

______________________________________________________________________

## See Also

- [Schema Reference](schema-reference.md) - Complete schema documentation
- [User Guide](user-guide.md) - CLI usage instructions
- [Installation Guide](installation-guide.md) - Installation instructions
- [Example Rules](example-rules.md) - Natural language rule examples
