# Schema Reference

## Fuzzy-LLM Hybrid IoT Management System

**Document Status:** Active\
**Last Updated:** 2026-02-05

This document provides a complete reference for all JSON configuration schemas
used by the system. Each schema is documented with property tables, validation
rules, and annotated examples.

______________________________________________________________________

## Table of Contents

1. [Overview](#1-overview)
2. [Device Configuration Schema](#2-device-configuration-schema)
3. [MQTT Configuration Schema](#3-mqtt-configuration-schema)
4. [LLM Configuration Schema](#4-llm-configuration-schema)
5. [Membership Functions Schema](#5-membership-functions-schema)
6. [Quick Reference](#6-quick-reference)

______________________________________________________________________

## 1. Overview

All configuration files use JSON format with JSON Schema (draft 2020-12)
validation. Configuration files are loaded at system startup by the
Configuration Manager and validated against their respective schemas.

### Schema Files

| Schema File                                       | Configuration File                   | Purpose                |
| ------------------------------------------------- | ------------------------------------ | ---------------------- |
| `config/schemas/devices.schema.json`              | `config/devices.json`                | Device registry        |
| `config/schemas/mqtt.schema.json`                 | `config/mqtt_config.json`            | MQTT broker connection |
| `config/schemas/llm.schema.json`                  | `config/llm_config.json`             | Ollama LLM settings    |
| `config/schemas/membership_functions.schema.json` | `config/membership_functions/*.json` | Fuzzy logic mappings   |

### Validation

The Configuration Manager validates all configuration files on load:

```python
from src.configuration import ConfigManager

config = ConfigManager()
config.load_all()  # Raises ValidationError if schemas fail
```

______________________________________________________________________

## 2. Device Configuration Schema

**Schema:** `config/schemas/devices.schema.json`\
**Config File:** `config/devices.json`

Defines all IoT devices (sensors and actuators) in the system.

### Root Object

| Property  | Type  | Required | Description                 |
| --------- | ----- | -------- | --------------------------- |
| `devices` | array | Yes      | Array of device definitions |

### Device Object

| Property       | Type   | Required       | Description                                                     |
| -------------- | ------ | -------------- | --------------------------------------------------------------- |
| `id`           | string | Yes            | Unique identifier. Pattern: `^[a-z0-9_-]+$`                     |
| `name`         | string | Yes            | Human-readable device name                                      |
| `type`         | string | Yes            | Device type: `"sensor"` or `"actuator"`                         |
| `device_class` | string | Yes            | Device class (e.g., `temperature`, `humidity`, `switch`)        |
| `location`     | string | No             | Physical location description                                   |
| `mqtt`         | object | No             | MQTT topic configuration                                        |
| `capabilities` | array  | Actuators only | List of supported commands                                      |
| `constraints`  | object | No             | Value constraints                                               |
| `metadata`     | object | No             | Additional custom metadata                                      |
| `unit`         | string | Sensors only   | Measurement unit                                                |
| `value_type`   | string | Sensors only   | Value type: `float`, `int`, `bool`, `string` (default: `float`) |

### MQTT Configuration (per device)

| Property        | Type    | Required | Default | Description                           |
| --------------- | ------- | -------- | ------- | ------------------------------------- |
| `topic`         | string  | Yes      | -       | MQTT topic for publishing/subscribing |
| `command_topic` | string  | No       | -       | Command topic (actuators only)        |
| `qos`           | integer | No       | 1       | Quality of Service: 0, 1, or 2        |
| `retain`        | boolean | No       | false   | Retain messages on broker             |

### Constraints Object

| Property         | Type   | Description                     |
| ---------------- | ------ | ------------------------------- |
| `min`            | number | Minimum allowed value           |
| `max`            | number | Maximum allowed value           |
| `step`           | number | Value increment step            |
| `allowed_values` | array  | List of allowed discrete values |

### Example: Sensor Device

```json
{
  "id": "living_room_temp",
  "name": "Living Room Temperature",
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
```

### Example: Actuator Device

```json
{
  "id": "living_room_ac",
  "name": "Living Room AC",
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

### Validation Rules

- `id` must be unique across all devices
- `id` must match pattern `^[a-z0-9_-]+$` (lowercase, numbers, underscores,
  hyphens)
- Actuators must have `capabilities` array
- Sensors should have `unit` for proper display

______________________________________________________________________

## 3. MQTT Configuration Schema

**Schema:** `config/schemas/mqtt.schema.json`\
**Config File:** `config/mqtt_config.json`

Configures the MQTT broker connection for device communication.

### Root Object

| Property    | Type   | Required | Description                |
| ----------- | ------ | -------- | -------------------------- |
| `broker`    | object | Yes      | Broker connection settings |
| `client`    | object | No       | Client identity settings   |
| `auth`      | object | No       | Authentication credentials |
| `tls`       | object | No       | TLS/SSL configuration      |
| `reconnect` | object | No       | Reconnection behavior      |
| `lwt`       | object | No       | Last Will and Testament    |

### Broker Object

| Property    | Type    | Required | Default | Description                   |
| ----------- | ------- | -------- | ------- | ----------------------------- |
| `host`      | string  | Yes      | -       | Broker hostname or IP         |
| `port`      | integer | No       | 1883    | Broker port (1-65535)         |
| `keepalive` | integer | No       | 60      | Keep-alive interval (seconds) |

### Client Object

| Property           | Type    | Default | Description                               |
| ------------------ | ------- | ------- | ----------------------------------------- |
| `id`               | string  | auto    | Client identifier                         |
| `clean_session`    | boolean | true    | Start with clean session                  |
| `protocol_version` | integer | 5       | MQTT version: 3 (3.1), 4 (3.1.1), 5 (5.0) |

### Auth Object

| Property   | Type   | Description             |
| ---------- | ------ | ----------------------- |
| `username` | string | Authentication username |
| `password` | string | Authentication password |

### TLS Object

| Property   | Type    | Default | Description                          |
| ---------- | ------- | ------- | ------------------------------------ |
| `enabled`  | boolean | false   | Enable TLS encryption                |
| `ca_certs` | string  | -       | Path to CA certificate file          |
| `certfile` | string  | -       | Path to client certificate           |
| `keyfile`  | string  | -       | Path to client private key           |
| `insecure` | boolean | false   | Skip server certificate verification |

### Reconnect Object

| Property    | Type    | Default | Description                              |
| ----------- | ------- | ------- | ---------------------------------------- |
| `enabled`   | boolean | true    | Enable automatic reconnection            |
| `min_delay` | number  | 1       | Minimum delay between attempts (seconds) |
| `max_delay` | number  | 60      | Maximum delay between attempts (seconds) |

### LWT Object (Last Will and Testament)

| Property  | Type    | Default   | Description                    |
| --------- | ------- | --------- | ------------------------------ |
| `topic`   | string  | -         | Topic for LWT message          |
| `payload` | string  | "offline" | Message payload                |
| `qos`     | integer | 1         | Quality of Service: 0, 1, or 2 |
| `retain`  | boolean | true      | Retain LWT message             |

### Example: Basic Configuration

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

### Example: Authenticated with TLS

```json
{
  "broker": {
    "host": "mqtt.example.com",
    "port": 8883,
    "keepalive": 60
  },
  "auth": {
    "username": "iot-controller",
    "password": "secure-password"
  },
  "tls": {
    "enabled": true,
    "ca_certs": "/etc/ssl/certs/ca-certificates.crt"
  },
  "reconnect": {
    "enabled": true,
    "min_delay": 1,
    "max_delay": 30
  },
  "lwt": {
    "topic": "home/controller/status",
    "payload": "offline",
    "retain": true
  }
}
```

______________________________________________________________________

## 4. LLM Configuration Schema

**Schema:** `config/schemas/llm.schema.json`\
**Config File:** `config/llm_config.json`

Configures the Ollama LLM service for rule interpretation.

### Root Object

| Property | Type   | Required | Description                 |
| -------- | ------ | -------- | --------------------------- |
| `llm`    | object | Yes      | LLM configuration container |

### LLM Object

| Property     | Type   | Required | Description                   |
| ------------ | ------ | -------- | ----------------------------- |
| `provider`   | string | Yes      | LLM provider: `"ollama"`      |
| `connection` | object | Yes      | Ollama service connection     |
| `model`      | object | Yes      | Model selection               |
| `inference`  | object | No       | Inference parameters          |
| `context`    | object | No       | Conversation context settings |

### Connection Object

| Property          | Type    | Required | Default | Description             |
| ----------------- | ------- | -------- | ------- | ----------------------- |
| `host`            | string  | Yes      | -       | Ollama service host     |
| `port`            | integer | Yes      | -       | Ollama service port     |
| `timeout_seconds` | number  | No       | 30      | Request timeout (1-300) |

### Model Object

| Property          | Type   | Required | Description                             |
| ----------------- | ------ | -------- | --------------------------------------- |
| `name`            | string | Yes      | Primary model name (e.g., `qwen3:0.6b`) |
| `fallback_models` | array  | No       | Fallback models if primary unavailable  |

Model name pattern: `^[a-z0-9][a-z0-9._-]*(?::[a-z0-9._-]+)?$`

### Inference Object

| Property         | Type    | Default | Range  | Description                                       |
| ---------------- | ------- | ------- | ------ | ------------------------------------------------- |
| `temperature`    | number  | 0.3     | 0-2    | Sampling temperature (lower = more deterministic) |
| `max_tokens`     | integer | 512     | 1-4096 | Maximum tokens in response                        |
| `top_p`          | number  | 0.9     | 0-1    | Nucleus sampling parameter                        |
| `top_k`          | integer | 40      | 1-100  | Top-k sampling parameter                          |
| `repeat_penalty` | number  | 1.1     | 1-2    | Repetition penalty                                |

### Context Object

| Property      | Type    | Default | Description                    |
| ------------- | ------- | ------- | ------------------------------ |
| `enabled`     | boolean | false   | Enable conversation context    |
| `max_history` | integer | 5       | Maximum history entries (0-20) |

### Example: Basic Configuration

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

### Example: Production Configuration

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
      "fallback_models": ["qwen3:1.7b", "llama3.2:1b"]
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

### Recommended Models

For edge deployment (CPU-only):

| Model         | Size   | Use Case                |
| ------------- | ------ | ----------------------- |
| `qwen3:0.6b`  | ~400MB | Default, fast inference |
| `qwen3:1.7b`  | ~1GB   | Better accuracy         |
| `llama3.2:1b` | ~700MB | Alternative option      |

______________________________________________________________________

## 5. Membership Functions Schema

**Schema:** `config/schemas/membership_functions.schema.json`\
**Config Files:** `config/membership_functions/*.json`

Defines fuzzy logic membership functions that map numerical sensor values to
linguistic terms. This is the core of the "semantic bridge" concept.

### Root Object

| Property                | Type   | Required | Default | Description                                  |
| ----------------------- | ------ | -------- | ------- | -------------------------------------------- |
| `sensor_type`           | string | Yes      | -       | Sensor type identifier. Pattern: `^[a-z_]+$` |
| `unit`                  | string | Yes      | -       | Unit of measurement                          |
| `universe_of_discourse` | object | Yes      | -       | Valid value range                            |
| `confidence_threshold`  | number | No       | 0.1     | Minimum membership degree (0-1)              |
| `linguistic_variables`  | array  | Yes      | -       | Linguistic term definitions                  |

### Universe of Discourse Object

| Property | Type   | Required | Description                   |
| -------- | ------ | -------- | ----------------------------- |
| `min`    | number | Yes      | Minimum value of the universe |
| `max`    | number | Yes      | Maximum value of the universe |

### Linguistic Variable Object

| Property        | Type   | Required | Description                                 |
| --------------- | ------ | -------- | ------------------------------------------- |
| `term`          | string | Yes      | Linguistic term label. Pattern: `^[a-z_]+$` |
| `function_type` | string | Yes      | Function type (see below)                   |
| `parameters`    | object | Yes      | Function-specific parameters                |

### Function Types and Parameters

#### Triangular Function

Three-point function forming a triangle shape.

| Parameter | Type   | Description                 |
| --------- | ------ | --------------------------- |
| `a`       | number | Left foot (membership = 0)  |
| `b`       | number | Peak (membership = 1)       |
| `c`       | number | Right foot (membership = 0) |

Constraint: `a <= b <= c`

```json
{
  "term": "comfortable",
  "function_type": "triangular",
  "parameters": { "a": 16.0, "b": 22.0, "c": 26.0 }
}
```

#### Trapezoidal Function

Four-point function with a flat top.

| Parameter | Type   | Description                           |
| --------- | ------ | ------------------------------------- |
| `a`       | number | Left foot (membership = 0)            |
| `b`       | number | Left shoulder (membership = 1 starts) |
| `c`       | number | Right shoulder (membership = 1 ends)  |
| `d`       | number | Right foot (membership = 0)           |

Constraint: `a <= b <= c <= d`

```json
{
  "term": "cold",
  "function_type": "trapezoidal",
  "parameters": { "a": -10.0, "b": -10.0, "c": 10.0, "d": 18.0 }
}
```

#### Gaussian Function

Bell-shaped curve centered at mean.

| Parameter | Type   | Description                      |
| --------- | ------ | -------------------------------- |
| `mean`    | number | Center of curve (membership = 1) |
| `sigma`   | number | Standard deviation (must be > 0) |

```json
{
  "term": "optimal",
  "function_type": "gaussian",
  "parameters": { "mean": 22.0, "sigma": 3.0 }
}
```

#### Sigmoid Function

S-shaped curve for boundary conditions.

| Parameter | Type   | Description                                          |
| --------- | ------ | ---------------------------------------------------- |
| `a`       | number | Slope (positive = increasing, negative = decreasing) |
| `c`       | number | Inflection point (membership = 0.5)                  |

Formula: `1 / (1 + exp(-a * (x - c)))`

```json
{
  "term": "high",
  "function_type": "sigmoid",
  "parameters": { "a": 0.5, "c": 30.0 }
}
```

### Example: Temperature Membership Functions

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

### How It Works

Given a temperature reading of 31.0 celsius:

1. The Fuzzy Engine evaluates all membership functions
2. Returns linguistic descriptions with membership degrees:
   - `warm: 0.33` (31 is slightly above the warm peak at 28)
   - `hot: 0.20` (31 is in the rising edge of hot)
3. Terms below `confidence_threshold` (0.1) are filtered out
4. The LLM receives: "temperature is warm (0.33), hot (0.20)"

This semantic bridge allows the LLM to understand sensor conditions in human
terms rather than raw numbers.

______________________________________________________________________

## 6. Quick Reference

### Minimal Valid Configurations

#### Minimal Device

```json
{
  "devices": [
    {
      "id": "sensor_1",
      "name": "Sensor",
      "type": "sensor",
      "device_class": "temperature"
    }
  ]
}
```

#### Minimal MQTT

```json
{
  "broker": {
    "host": "localhost"
  }
}
```

#### Minimal LLM

```json
{
  "llm": {
    "provider": "ollama",
    "connection": { "host": "localhost", "port": 11434 },
    "model": { "name": "qwen3:0.6b" }
  }
}
```

#### Minimal Membership Function

```json
{
  "sensor_type": "temperature",
  "unit": "celsius",
  "universe_of_discourse": { "min": 0, "max": 50 },
  "linguistic_variables": [
    {
      "term": "normal",
      "function_type": "triangular",
      "parameters": { "a": 15, "b": 22, "c": 30 }
    }
  ]
}
```

### Common Patterns

| Pattern          | Value                                      |
| ---------------- | ------------------------------------------ |
| Device ID        | `^[a-z0-9_-]+$`                            |
| Sensor type      | `^[a-z_]+$`                                |
| Linguistic term  | `^[a-z_]+$`                                |
| Model name       | `^[a-z0-9][a-z0-9._-]*(?::[a-z0-9._-]+)?$` |
| MQTT QoS         | 0, 1, or 2                                 |
| Protocol version | 3 (MQTT 3.1), 4 (MQTT 3.1.1), 5 (MQTT 5.0) |

### Validation Commands

```bash
# Validate all configurations
iot-fuzzy-llm config validate

# Validate specific file
iot-fuzzy-llm config validate --file config/devices.json
```

______________________________________________________________________

## See Also

- [Configuration Guide](configuration-guide.md) - How to configure the system
- [API Reference](api-reference.md) - Python API documentation
- [Architecture Design Document](../dev/add.md) - System architecture
