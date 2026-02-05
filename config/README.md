# Configuration Directory

This directory contains all configuration files for the Fuzzy-LLM Hybrid IoT
Management System. All configuration files are in JSON format as specified in
the Architecture Design Document (ADD).

## Structure

```
config/
├── devices.json           # Sensor and actuator device definitions
├── llm_config.json        # Ollama LLM service configuration
├── mqtt_config.json       # MQTT broker connection settings
├── prompt_template.txt    # Template for constructing LLM prompts
├── membership_functions/  # Fuzzy membership function definitions
│   ├── humidity.json
│   ├── light_level.json
│   ├── motion.json
│   └── temperature.json
└── schemas/               # JSON schemas for configuration validation
```

## Configuration Files

### devices.json

Defines all sensors and actuators in the system:

- Device ID, name, and type (sensor/actuator)
- MQTT topics for communication
- Sensor types (temperature, humidity, motion, light_level)
- Actuator capabilities (turn_on, turn_off, set_temperature, etc.)
- Device constraints (min/max values, allowed modes)

### llm_config.json

Ollama LLM service configuration:

- Host and port settings
- Model selection (default: qwen3:0.6b for edge deployment)
- Inference parameters (temperature, max_tokens, top_p)
- Timeout and retry settings

### mqtt_config.json

MQTT broker connection settings:

- Broker host and port
- Authentication credentials
- Client ID and connection options
- Keep-alive and reconnection settings

### prompt_template.txt

Template for constructing prompts sent to the LLM for rule evaluation.

### membership_functions/

JSON files defining fuzzy membership functions for each sensor type. See the
[membership_functions README](membership_functions/README.md) for details.

### schemas/

JSON Schema files for validating configuration files at load time.

## Configuration Principles

- All configuration is file-based with JSON schemas for validation
- Configuration Manager loads these files at system startup
- No database required - files are sufficient for the expected data scale

## Design Decision

As noted in DD-04 of the ADD, JSON was chosen because it is:

- Human-readable and universally supported
- Schema-validatable
- Does not require code execution (unlike Python config files)

## Demo Scenario MQTT Topics

The following MQTT topics are configured for the smart home demo scenario:

### Sensor Topics (Subscribe)

| Topic                          | Device               | Type        | Unit |
| ------------------------------ | -------------------- | ----------- | ---- |
| `home/living_room/temperature` | Living Room Temp     | temperature | C    |
| `home/living_room/humidity`    | Living Room Humidity | humidity    | %    |
| `home/living_room/motion`      | Living Room Motion   | motion      | bool |
| `home/living_room/light_level` | Living Room Light    | light_level | lux  |
| `home/bedroom/temperature`     | Bedroom Temp         | temperature | C    |
| `home/office/temperature`      | Office Temp          | temperature | C    |
| `home/hallway/motion`          | Hallway Motion       | motion      | bool |

### Actuator Command Topics (Publish)

| Topic                         | Device             | Capabilities                       |
| ----------------------------- | ------------------ | ---------------------------------- |
| `home/living_room/ac/set`     | Living Room AC     | turn_on, turn_off, set_temperature |
| `home/living_room/light/set`  | Living Room Light  | turn_on, turn_off, set_brightness  |
| `home/living_room/blinds/set` | Living Room Blinds | open, close, set_position          |
| `home/bedroom/heater/set`     | Bedroom Heater     | turn_on, turn_off, set_temperature |
| `home/bedroom/blinds/set`     | Bedroom Blinds     | open, close, set_position          |
| `home/office/heater/set`      | Office Heater      | turn_on, turn_off, set_temperature |
| `home/hallway/light/set`      | Hallway Light      | turn_on, turn_off                  |

### Simulating Sensor Data

To test the demo, publish sensor readings to MQTT topics:

```bash
# Temperature reading (triggers "hot" condition at 32C)
mosquitto_pub -t home/living_room/temperature -m '{"value": 32.0}'

# Humidity reading (triggers "humid" condition at 75%)
mosquitto_pub -t home/living_room/humidity -m '{"value": 75.0}'

# Motion detected (1 = motion, 0 = no motion)
mosquitto_pub -t home/hallway/motion -m '{"value": 1}'

# Light level (very bright at 35000 lux)
mosquitto_pub -t home/living_room/light_level -m '{"value": 35000}'
```
