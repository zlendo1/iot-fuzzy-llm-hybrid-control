# Demo Walkthrough Guide

This document provides step-by-step instructions for demonstrating the Fuzzy-LLM
Hybrid IoT Management System for thesis evaluation.

## Prerequisites

Before running the demo, ensure:

1. **Docker and Docker Compose** are installed and running
2. **System is built**: `make build`

## Quick Start

```bash
# Start all services
make up

# Verify services are healthy
make ps

# View system logs
make logs
```

## Demo Scenario Overview

The demo showcases a smart home with:

- **7 sensors**: temperature (3), humidity (1), motion (2), light level (1)
- **7 actuators**: AC (1), heaters (2), lights (2), blinds (2)
- **10 rules**: climate, lighting, heating, blind control

## Step-by-Step Demo

### Step 1: Verify System Health

```bash
# Check all containers are running
docker-compose ps
```

**Verification**: Confirm all 3 containers show `running (healthy)`:

```
NAME           STATUS
iot-mosquitto  running (healthy)
iot-ollama     running (healthy)
iot-app        running (healthy)
```

### Step 2: CLI Status Check

```bash
# Check system status via CLI
iot-fuzzy-llm status
```

**Verification**: Confirm the output shows "Connected to running application"
and component status:

```
Connected to running application

System Status
=============
State: running
Running: Yes

Statistics:
  Readings processed: 0
  Rules evaluated: 0
  Commands generated: 0
  Commands sent: 0
  Errors: 0
  Uptime: 45.2s

Components:
  config_manager:   available
  logging_manager:  available
  rule_manager:     available
  device_registry:  available
  fuzzy_pipeline:   available
  mqtt_manager:     available
  device_monitor:   available
```

> [!NOTE]
> The CLI first attempts to connect to the running application via
> `http://localhost:8080/status`. If successful, it shows live application
> state. If unreachable, it falls back to standalone mode validating
> configurations locally.

### Step 3: List Demo Rules

```bash
# List all configured rules
iot-fuzzy-llm rule list
```

**Verification**: Confirm 10 rules are displayed with their IDs, status, and
text:

```
Rules (10 total)
================

ID           Enabled  Priority  Rule Text
-----------  -------  --------  -----------------------------------------
climate_001  Yes      80        If the living room is hot and humid...
climate_002  Yes      75        If the living room temperature is...
heating_001  Yes      70        If the bedroom is cold, turn on...
heating_002  Yes      70        If the office is cold, turn on...
lighting_001 Yes      60        If motion is detected and it is dark...
lighting_002 Yes      60        If no motion detected for 10 minutes...
blinds_001   Yes      50        If the living room light level is...
blinds_002   Yes      50        If the bedroom light level is...
security_001 Yes      90        If motion detected at night when...
energy_001   Yes      40        If no one is home, turn off all...
```

### Step 4: Climate Control Demo (DEMO-004)

**Scenario**: Living room is hot (32°C) and humid (78%)

> [!NOTE]
> The `mosquitto_pub` commands below should be run from a **separate terminal**
> on the host (requires `mosquitto-clients` package), or from the mosquitto
> container using `docker exec iot-mosquitto mosquitto_pub ...`

```bash
# First, start subscribing to the AC command topic (in a separate terminal)
mosquitto_sub -h localhost -t home/living_room/ac/set

# Simulate hot temperature reading (from host or mosquitto container)
mosquitto_pub -h localhost -t home/living_room/temperature \
  -m '{"value": 32.0, "unit": "celsius"}'

# Simulate high humidity reading
mosquitto_pub -h localhost -t home/living_room/humidity \
  -m '{"value": 78.0, "unit": "percent"}'
```

**Verification**:

1. **Check application logs** (`make logs` or `docker-compose logs -f app`):

   ```
   INFO  Sensor reading received  sensor_id=temp_living_room value=32.0
   INFO  Sensor reading processed sensor_id=temp_living_room linguistic_description="temperature is hot (0.85)"
   INFO  Rules evaluated with matches  rules_evaluated=10 commands_generated=1
   INFO  Command sent  device_id=ac_living_room command_type=turn_on
   ```

2. **Check MQTT subscriber output** (from the `mosquitto_sub` terminal):

   ```json
   {"device_id": "ac_living_room", "command": "turn_on", "parameters": {"temperature": 22}}
   ```

### Step 5: Lighting Control Demo (DEMO-005)

**Scenario**: Motion detected in dark hallway

```bash
# Subscribe to hallway light command topic (in a separate terminal)
mosquitto_sub -h localhost -t home/hallway/light/set

# Simulate dark light level (50 lux)
mosquitto_pub -h localhost -t home/living_room/light_level \
  -m '{"value": 50.0}'

# Simulate motion in hallway
mosquitto_pub -h localhost -t home/hallway/motion \
  -m '{"value": 1}'
```

**Verification**:

1. **Check application logs**:

   ```
   INFO  Sensor reading processed sensor_id=light_living_room linguistic_description="light_level is dark (0.80)"
   INFO  Sensor reading processed sensor_id=motion_hallway linguistic_description="motion is detected (1.0)"
   INFO  Command sent  device_id=light_hallway command_type=turn_on
   ```

2. **Check MQTT subscriber output**:

   ```json
   {"device_id": "light_hallway", "command": "turn_on", "parameters": {}}
   ```

### Step 6: Heating Control Demo (DEMO-006)

**Scenario**: Bedroom is cold (15°C)

```bash
# Subscribe to bedroom heater command topic (in a separate terminal)
mosquitto_sub -h localhost -t home/bedroom/heater/set

# Simulate cold bedroom temperature
mosquitto_pub -h localhost -t home/bedroom/temperature \
  -m '{"value": 15.0, "unit": "celsius"}'
```

**Verification**:

1. **Check application logs**:

   ```
   INFO  Sensor reading processed sensor_id=temp_bedroom linguistic_description="temperature is cold (0.75)"
   INFO  Command sent  device_id=heater_bedroom command_type=turn_on
   ```

2. **Check MQTT subscriber output**:

   ```json
   {"device_id": "heater_bedroom", "command": "turn_on", "parameters": {"temperature": 21}}
   ```

### Step 7: Blind Control Demo (DEMO-007)

**Scenario**: Very bright sunlight (40000 lux)

```bash
# Subscribe to blinds command topic (in a separate terminal)
mosquitto_sub -h localhost -t home/living_room/blinds/set

# Simulate very bright light
mosquitto_pub -h localhost -t home/living_room/light_level \
  -m '{"value": 40000.0, "unit": "lux"}'
```

**Verification**:

1. **Check application logs**:

   ```
   INFO  Sensor reading processed sensor_id=light_living_room linguistic_description="light_level is very_bright (0.90)"
   INFO  Command sent  device_id=blinds_living_room command_type=set_position
   ```

2. **Check MQTT subscriber output**:

   ```json
   {"device_id": "blinds_living_room", "command": "set_position", "parameters": {"position": 50}}
   ```

### Step 8: Rule Management Demo

```bash
# Add a new rule
iot-fuzzy-llm rule add --id night_mode \
  "If no motion detected for 30 minutes after 11pm, turn off all lights"
```

**Verification**: Confirm rule was added:

```
Rule added successfully.
  ID: night_mode
  Text: If no motion detected for 30 minutes after 11pm, turn off all lights
  Priority: 50
  Enabled: Yes
```

```bash
# Disable a rule
iot-fuzzy-llm rule disable climate_002
```

**Verification**: Confirm rule was disabled:

```
Rule 'climate_002' disabled.
```

```bash
# Enable a rule
iot-fuzzy-llm rule enable climate_002
```

**Verification**: Confirm rule was enabled:

```
Rule 'climate_002' enabled.
```

```bash
# Show rule details
iot-fuzzy-llm rule show climate_001
```

**Verification**: Confirm rule details are displayed:

```
Rule: climate_001
=================
Text: If the living room is hot and humid, turn on the air conditioner
Enabled: Yes
Priority: 80
Created: 2026-02-05T10:00:00
Trigger Count: 3
Last Triggered: 2026-02-05T14:22:00
```

### Step 9: Sensor Status Demo

```bash
# Show current sensor readings
iot-fuzzy-llm sensor status
```

**Verification**: Confirm 7 sensors are displayed with their configuration:

```
Sensors (7 total)
=================

ID                  Type         Location      Unit     MQTT Topic
------------------  -----------  ------------  -------  --------------------------
temp_living_room    temperature  Living Room   celsius  home/living_room/temperature
temp_bedroom        temperature  Bedroom       celsius  home/bedroom/temperature
temp_office         temperature  Office        celsius  home/office/temperature
humidity_living     humidity     Living Room   percent  home/living_room/humidity
motion_hallway      motion       Hallway       -        home/hallway/motion
motion_living       motion       Living Room   -        home/living_room/motion
light_living        light_level  Living Room   lux      home/living_room/light_level
```

### Step 10: Configuration Validation

```bash
# Validate all configuration files
iot-fuzzy-llm config validate
```

**Verification**: Confirm all configurations pass validation:

```
Configuration Validation
========================

Validating configuration files...

  ✓ devices.json         Valid (14 devices)
  ✓ mqtt_config.json     Valid
  ✓ llm_config.json      Valid
  ✓ membership_functions Valid (4 sensor types)

All configuration files are valid.
```

## Expected Outputs

### Fuzzy Logic Output Example

```
Sensor: temp_living_room
Raw Value: 32.0°C
Linguistic Description: temperature is hot (0.85), warm (0.15)
```

### LLM Response Example

```
Based on the current sensor state:
- temperature is hot (0.85)
- humidity is humid (0.76)

The rule "If the living room temperature is hot and humidity is high,
turn on the air conditioner" applies.

ACTION: ac_living_room, turn_on, temperature=22
```

### Command Output Example

```json
{
  "device_id": "ac_living_room",
  "command": "turn_on",
  "parameters": {
    "temperature": 22,
    "mode": "cooling"
  },
  "timestamp": "2025-02-05T14:00:05Z",
  "triggered_by": "climate_001"
}
```

## Performance Metrics

During the demo, observe these performance targets:

| Metric             | Target  | How to Verify                    |
| ------------------ | ------- | -------------------------------- |
| Fuzzy processing   | < 100ms | Check logs for timing            |
| LLM inference      | < 3s    | Observe response time            |
| End-to-end latency | < 5s    | Time from sensor pub to command  |
| System startup     | < 30s   | Time `make up` to healthy status |

## Cleanup

```bash
# Stop all services
make down

# Remove all data (fresh start)
make clean-docker
```

## Demo Tips

1. **Use multiple terminals**: One for publishing sensors, one for subscribing
   to actuator commands, one for viewing logs

2. **Log verbosity**: Set `LOG_LEVEL=DEBUG` for detailed processing info

3. **Slow down LLM**: If LLM responses are too fast to observe, reduce inference
   speed with `temperature=0.7`

4. **Reset between demos**: Use `make restart` to clear state

## Recording the Demo

For thesis documentation:

1. **Screen recording**: Record terminal sessions showing:

   - System startup
   - Sensor simulation
   - Rule triggering
   - Command generation

2. **Log capture**: Save logs showing:

   - Fuzzy logic transformations
   - LLM prompts and responses
   - Command validation

3. **Timing measurements**: Document actual latencies observed
