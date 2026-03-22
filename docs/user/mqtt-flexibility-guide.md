# MQTT Flexibility Guide

## Fuzzy-LLM Hybrid IoT Management System

**Document Status:** Active\
**Last Updated:** 2026-03-17

This guide explains how to configure custom MQTT payload schemas and topic
patterns to integrate the system with any MQTT-based IoT device, regardless of
its message format.

______________________________________________________________________

## Table of Contents

1. [Overview](#1-overview)
2. [Payload Mapping Configuration](#2-payload-mapping-configuration)
3. [Topic Pattern Configuration](#3-topic-pattern-configuration)
4. [Migration Guide](#4-migration-guide)
5. [Device Format Examples](#5-device-format-examples)
6. [Backward Compatibility](#6-backward-compatibility)
7. [Troubleshooting](#7-troubleshooting)

______________________________________________________________________

## 1. Overview

### What Is MQTT Flexibility?

By default, the system expects sensor readings in a simple JSON format:

```json
{"value": 25.0}
```

In practice, IoT devices rarely publish data in this format. A Zigbee2MQTT
gateway publishes temperature as `{"temperature": 22.5, "humidity": 60}`. A
Tasmota device uses `{"StatusSNS": {"DS18B20": {"Temperature": 23.1}}}`. A
commercial sensor might use `{"v": 23.1, "u": "C", "ts": 1700000000}`.

**MQTT Flexibility** solves this by letting you configure:

- **Payload mapping** — which field in an incoming MQTT message contains the
  sensor value, unit, and timestamp.
- **Topic patterns** — reusable topic templates using substitution variables so
  you don't repeat `{location}/{name}` in every device entry.

This means you can integrate the system with virtually any MQTT device ecosystem
without writing custom code.

### Why It Matters

| Without MQTT Flexibility                                 | With MQTT Flexibility                                  |
| -------------------------------------------------------- | ------------------------------------------------------ |
| All sensors must publish `{"value": N}`                  | Each sensor declares its own payload schema            |
| Topic structure is hardcoded per device                  | Topic patterns defined once, reused across all devices |
| Adding Zigbee2MQTT requires custom adapter code          | Configure a `payload_mapping` and start receiving data |
| Changing your topic hierarchy means editing every device | Update the pattern in `mqtt_config.json` once          |

______________________________________________________________________

## 2. Payload Mapping Configuration

**Location:** `config/devices.json` — inside the `mqtt` block of each sensor
device.

### Schema

```json
"payload_mapping": {
  "value_field": "temperature",
  "unit_field": "unit",
  "timestamp_field": "time"
}
```

### Field Reference

| Field             | Type   | Required | Description                                    |
| ----------------- | ------ | -------- | ---------------------------------------------- |
| `value_field`     | string | **Yes**  | JSON key containing the sensor reading         |
| `unit_field`      | string | No       | JSON key containing the unit string (optional) |
| `timestamp_field` | string | No       | JSON key containing the timestamp (optional)   |

> **Note:** The `payload_mapping` block itself is optional. If omitted entirely,
> the system reads `{"value": N}` for backward compatibility. However, when
> `payload_mapping` is present, `value_field` is required. See
> [Section 6](#6-backward-compatibility) for details.
>
> The schema enforces `additionalProperties: false` — only the three fields
> above are accepted.

### Nested Field Access

Use dot notation to reach values inside nested JSON objects:

```json
"value_field": "StatusSNS.DS18B20.Temperature"
```

This reads `payload["StatusSNS"]["DS18B20"]["Temperature"]` from the incoming
MQTT message.

### Complete Sensor Example with Payload Mapping

```json
{
  "id": "temp_living_room",
  "name": "Living Room Temperature Sensor",
  "type": "sensor",
  "device_class": "temperature",
  "location": "living_room",
  "unit": "°C",
  "value_type": "float",
  "mqtt": {
    "topic": "home/living_room/temperature",
    "qos": 1,
    "payload_mapping": {
      "value_field": "temperature",
      "unit_field": "unit",
      "timestamp_field": "time"
    }
  },
  "constraints": {
    "min": -10,
    "max": 60
  }
}
```

______________________________________________________________________

## 3. Topic Pattern Configuration

**Location:** `config/mqtt_config.json` — top-level `topic_patterns` object.

### Schema

```json
"topic_patterns": {
  "sensor": "home/{location}/{name}/sensor",
  "actuator": "home/{location}/{name}/actuator",
  "command": "home/{location}/{name}/set"
}
```

### Substitution Variables

| Variable      | Replaced With                                                |
| ------------- | ------------------------------------------------------------ |
| `{device_id}` | The device's `id` field                                      |
| `{name}`      | The device's `name` field (lowercased, spaces → underscores) |
| `{location}`  | The device's `location` field                                |

### Pattern Keys

| Key        | Used For                                    |
| ---------- | ------------------------------------------- |
| `sensor`   | Default subscribe topic for sensor devices  |
| `actuator` | Default state topic for actuator devices    |
| `command`  | Default publish topic for actuator commands |

> **Note:** Topic patterns are applied as defaults. Individual devices can still
> override topics explicitly by setting `mqtt.topic` in their device entry.
> Explicit per-device topics take precedence over patterns.

### Complete mqtt_config.json with Patterns

```json
{
  "broker": {
    "host": "localhost",
    "port": 1883,
    "keepalive": 60
  },
  "client": {
    "id": "iot-fuzzy-llm",
    "clean_session": true,
    "protocol_version": 5
  },
  "auth": {
    "username": "iot_user",
    "password": "iot_password"
  },
  "reconnect": {
    "enabled": true,
    "min_delay": 1,
    "max_delay": 60
  },
  "topic_patterns": {
    "sensor": "home/{location}/{name}",
    "actuator": "home/{location}/{name}/state",
    "command": "home/{location}/{name}/set"
  }
}
```

### Zigbee2MQTT Topic Patterns

For Zigbee2MQTT deployments where the gateway publishes to `zigbee2mqtt/{name}`:

```json
"topic_patterns": {
  "sensor": "zigbee2mqtt/{name}",
  "actuator": "zigbee2mqtt/{name}",
  "command": "zigbee2mqtt/{name}/set"
}
```

### Tasmota Topic Patterns

For Tasmota firmware devices that use `tele/{name}/SENSOR` for telemetry:

```json
"topic_patterns": {
  "sensor": "tele/{name}/SENSOR",
  "actuator": "stat/{name}/RESULT",
  "command": "cmnd/{name}/POWER"
}
```

______________________________________________________________________

## 4. Migration Guide

The `config migrate` command scans your existing configuration files for devices
and MQTT settings that are missing the new `payload_mapping` and
`topic_patterns` keys, then adds the missing defaults automatically.

### Prerequisites

Before migrating, validate your current configuration:

```bash
python -m src.interfaces config validate
```

Fix any existing validation errors before running migration.

### Dry Run (Preview Changes)

To see what the migration would change without writing anything:

```bash
python -m src.interfaces config migrate --dry-run
```

Example output:

```
DRY RUN — no files will be modified.

devices.json — 7 sensors missing payload_mapping:
  • temp_living_room: will add payload_mapping with value_field="value"
  • humidity_living_room: will add payload_mapping with value_field="value"
  • temp_bedroom: will add payload_mapping with value_field="value"
  • motion_hallway: will add payload_mapping with data_type="bool"
  • motion_living_room: will add payload_mapping with data_type="bool"
  • light_level_living_room: will add payload_mapping with value_field="value"
  • temp_office: will add payload_mapping with value_field="value"

mqtt_config.json — topic_patterns key absent: will add default patterns.

Run without --dry-run to apply changes.
```

### Apply Migration

```bash
python -m src.interfaces config migrate
```

The command automatically creates `.bak` backups before modifying any file. You
can restore a backup at any time:

```bash
cp config/devices.json.bak config/devices.json
python -m src.interfaces config validate
```

### After Migration

Validate the result, then reload the running system:

```bash
python -m src.interfaces config validate
python -m src.interfaces config reload
```

______________________________________________________________________

## 5. Device Format Examples

### Zigbee2MQTT

Zigbee2MQTT publishes combined sensor readings as a single JSON message:

```json
{
  "temperature": 22.5,
  "humidity": 60,
  "battery": 98,
  "linkquality": 85
}
```

**Topic:** `zigbee2mqtt/Living Room Sensor`

**Device configuration:**

```json
{
  "id": "temp_living_room",
  "name": "Living Room Temperature Sensor",
  "type": "sensor",
  "device_class": "temperature",
  "location": "living_room",
  "unit": "°C",
  "value_type": "float",
  "mqtt": {
    "topic": "zigbee2mqtt/Living Room Sensor",
    "qos": 0,
    "payload_mapping": {
      "value_field": "temperature"
    }
  },
  "constraints": {
    "min": -40,
    "max": 85
  }
}
```

A second device can subscribe to the **same topic** but map `humidity`:

```json
{
  "id": "humidity_living_room",
  "name": "Living Room Humidity Sensor",
  "type": "sensor",
  "device_class": "humidity",
  "location": "living_room",
  "unit": "%",
  "value_type": "float",
  "mqtt": {
    "topic": "zigbee2mqtt/Living Room Sensor",
    "qos": 0,
    "payload_mapping": {
      "value_field": "humidity"
    }
  },
  "constraints": {
    "min": 0,
    "max": 100
  }
}
```

### Tasmota

Tasmota publishes telemetry in deeply nested JSON:

```json
{
  "Time": "2026-03-17T14:30:00",
  "DS18B20": {
    "Id": "0316B91E6438",
    "Temperature": 23.1
  },
  "TempUnit": "C"
}
```

**Topic:** `tele/bedroom_sensor/SENSOR`

**Device configuration:**

```json
{
  "id": "temp_bedroom",
  "name": "Bedroom Temperature Sensor",
  "type": "sensor",
  "device_class": "temperature",
  "location": "bedroom",
  "unit": "°C",
  "value_type": "float",
  "mqtt": {
    "topic": "tele/bedroom_sensor/SENSOR",
    "qos": 0,
    "payload_mapping": {
      "value_field": "DS18B20.Temperature",
      "timestamp_field": "Time"
    }
  },
  "constraints": {
    "min": -40,
    "max": 85
  }
}
```

### Generic Custom Format

For sensors that publish a compact format with non-standard field names:

```json
{"v": 750, "u": "lux", "ts": 1700000000}
```

**Device configuration:**

```json
{
  "id": "light_level_living_room",
  "name": "Living Room Light Level Sensor",
  "type": "sensor",
  "device_class": "light_level",
  "location": "living_room",
  "unit": "lux",
  "value_type": "float",
  "mqtt": {
    "topic": "home/living_room/light_level",
    "qos": 1,
    "payload_mapping": {
      "value_field": "v",
      "unit_field": "u",
      "timestamp_field": "ts"
    }
  },
  "constraints": {
    "min": 0,
    "max": 100000
  }
}
```

______________________________________________________________________

## 6. Backward Compatibility

Existing `devices.json` and `mqtt_config.json` files that do **not** contain
`payload_mapping` or `topic_patterns` continue to work without any changes.

| Old config element                 | Behavior                                             |
| ---------------------------------- | ---------------------------------------------------- |
| No `payload_mapping` in a device   | Reads `{"value": N}` as before                       |
| No `topic_patterns` in mqtt_config | Topics used directly from each device's `mqtt.topic` |
| No `timestamp_field`               | Timestamp defaults to message arrival time           |
| No `unit_field`                    | Unit taken from device's top-level `unit` field      |

The migration command adds defaults that preserve existing behavior, so running
`config migrate --backup` is safe and reversible.

> **Note:** You do not need to run migration to keep the system working.
> Migration is only necessary if you want to add `payload_mapping` or
> `topic_patterns` to take advantage of the new flexibility features.

______________________________________________________________________

## 7. Troubleshooting

### Sensor value is always `None` or `0`

**Cause:** The `value_field` in `payload_mapping` does not match the actual key
in the incoming MQTT message.

**Fix:**

1. Subscribe to the sensor topic directly and inspect the raw payload:

   ```bash
   mosquitto_sub -t "zigbee2mqtt/Living Room Sensor" -v
   ```

2. Compare the output to your `value_field` setting. If the payload is
   `{"temperature": 22.5}` and `value_field` is `"temp"`, change it to
   `"temperature"`.

3. For nested fields, verify the dot path. A payload of
   `{"DS18B20": {"Temperature": 23.1}}` requires `"DS18B20.Temperature"`.

______________________________________________________________________

### `config migrate` fails with a validation error

**Cause:** The existing configuration already has invalid JSON or fails schema
validation before migration can run.

**Fix:**

```bash
# Check JSON syntax
python -m json.tool config/devices.json
python -m json.tool config/mqtt_config.json

# Check schema validity
python -m src.interfaces config validate
```

Fix any reported errors, then re-run `config migrate`.

______________________________________________________________________

### Topic patterns are not being applied

**Cause:** A device's explicit `mqtt.topic` field takes precedence over the
pattern.

**Fix:** If you want a device to use a pattern, remove (or do not set) its
`mqtt.topic`. Only devices without an explicit topic inherit from
`topic_patterns`.

______________________________________________________________________

### After migration, the system does not pick up the new configuration

**Fix:** Reload configuration without restarting:

```bash
python -m src.interfaces config reload
```

Or restart the system:

```bash
python -m src.interfaces stop
python -m src.interfaces start
```

______________________________________________________________________

## See Also

- [Configuration Guide](configuration-guide.md) — Device and MQTT configuration
  reference
- [User Guide](user-guide.md) — CLI command reference
- [Schema Reference](schema-reference.md) — Full JSON schema documentation
- [Demo Troubleshooting](demo-troubleshooting.md) — Common setup issues
