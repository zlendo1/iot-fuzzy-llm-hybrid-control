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
docker compose ps
```

**Verification**: Confirm all 4 containers show `running (healthy)`:

```
NAME           STATUS
iot-mosquitto  running (healthy)
iot-ollama     running (healthy)
iot-app        running (healthy)
iot-web        running (healthy)
```

### Step 2: CLI Status Check

```bash
# Check system status via CLI
iot-fuzzy-llm status
```

**Verification**: Confirm the output shows "Connected to running application"
and system status:

```
✓ Connected to running application.
System State: RUNNING
Ready: Yes
Uptime (seconds): 10
Version: 0.1.0
```

> [!NOTE]
> The CLI connects to the running application via gRPC on `localhost:50051`. If
> successful, it shows live application state. If unreachable, it falls back to
> standalone mode validating configurations locally.

### Step 3: List Demo Rules

```bash
# List all configured rules
iot-fuzzy-llm rule list
```

**Verification**: Confirm 10 rules are displayed with their IDs, status, and
text:

```
ID           | Enabled | Text
-------------+---------+----------------------------------------------------
climate_001  | Yes     | If the living room temperature is hot and humidity 
             |         | is high, turn on the air conditioner and set it to 
             |         | cooling mode at 22 degrees                         
-------------+---------+----------------------------------------------------
climate_002  | Yes     | If the living room temperature is warm and         
             |         | humidity is comfortable, no action is needed       
-------------+---------+----------------------------------------------------
lighting_001 | Yes     | When motion is detected in the hallway and the     
             |         | light level is dark, turn on the hallway light     
-------------+---------+----------------------------------------------------
lighting_002 | Yes     | If motion is detected in the living room and it is 
             |         | dark, turn on the living room light                
-------------+---------+----------------------------------------------------
heating_001  | Yes     | If the bedroom is cold, turn on the heater         
-------------+---------+----------------------------------------------------
heating_002  | Yes     | If the office is cold, turn on the office heater   
-------------+---------+----------------------------------------------------
blinds_001   | Yes     | If the living room is very bright, close the blinds
-------------+---------+----------------------------------------------------
blinds_002   | Yes     | If the living room is dark, open the blinds        
-------------+---------+----------------------------------------------------
energy_001   | Yes     | If no motion in living room for 1 hour, turn off AC
-------------+---------+----------------------------------------------------
comfort_001  | Yes     | If living room is comfortable, turn off AC         
-------------+---------+----------------------------------------------------

Total: 10 rule(s)
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

1. **Check application logs** (`make logs` or `docker compose logs -f app`):

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
iot-fuzzy-llm rule add \
  "If no motion detected for 30 minutes after 11pm, turn off all lights"
```

**Verification**: Confirm rule was added:

```
✓ Rule added with ID: rule_a1b2c3d4e5f6
```

> [!IMPORTANT]
> Although the CLI accepts `--id`, `--priority`, and `-t/--tag` options, these
> are not currently passed to the server in the gRPC implementation. The system
> automatically generates a unique ID for every new rule.

```bash
# Disable a rule
iot-fuzzy-llm rule disable climate_002
```

**Verification**: Confirm rule was disabled:

```
✓ Rule climate_002 disabled.
```

```bash
# Enable a rule
iot-fuzzy-llm rule enable climate_002
```

**Verification**: Confirm rule was enabled:

```
✓ Rule climate_002 enabled.
```

```bash
# Show rule details
iot-fuzzy-llm rule show climate_001
```

**Verification**: Confirm rule details are displayed:

```
Rule ID: climate_001
Text: If the living room temperature is hot and humidity is high, turn on the air conditioner
Enabled: Yes
```

```bash
# Delete a rule
iot-fuzzy-llm rule delete climate_002
```

**Verification**: Confirm rule was deleted:

```
Are you sure you want to delete rule 'climate_002'? [y/N]: y
✓ Rule climate_002 deleted.
```

### Step 9: Sensor Status Demo

```bash
# Show current sensor readings
iot-fuzzy-llm sensor status
```

**Verification**: Confirm sensors are displayed with their registration status:

```
Living Room Temperature Sensor (temp_living_room)
  Class: N/A
  Location: living_room
  Unit: N/A
  Status: registered

Living Room Humidity Sensor (humidity_living_room)
  Class: N/A
  Location: living_room
  Unit: N/A
  Status: registered

Bedroom Temperature Sensor (temp_bedroom)
  Class: N/A
  Location: bedroom
  Unit: N/A
  Status: registered

Hallway Motion Sensor (motion_hallway)
  Class: N/A
  Location: hallway
  Unit: N/A
  Status: registered

Living Room Motion Sensor (motion_living_room)
  Class: N/A
  Location: living_room
  Unit: N/A
  Status: registered

Living Room Light Level Sensor (light_level_living_room)
  Class: N/A
  Location: living_room
  Unit: N/A
  Status: registered

Office Temperature Sensor (temp_office)
  Class: N/A
  Location: office
  Unit: N/A
  Status: registered
```

**Verification**: Confirm sensors are displayed with their configuration:

```
Living Room Temperature Sensor (temp_living_room)
  Class: temperature
  Location: living_room
  Unit: N/A
  Status: registered

Living Room Humidity Sensor (humidity_living_room)
  Class: humidity
  Location: living_room
  Unit: N/A
  Status: registered

Bedroom Temperature Sensor (temp_bedroom)
  Class: temperature
  Location: bedroom
  Unit: N/A
  Status: registered
...
```

### Step 10: Configuration Validation

```bash
# Validate all configuration files
iot-fuzzy-llm config validate
```

**Verification**: Confirm all configurations pass validation:

```
ℹ Validating configuration files...
✓ All configuration files are valid.

Loaded configurations:
  ✓ devices
  ✓ llm_config
  ✓ mqtt_config
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

During the demo, observe these performance targets (as defined in `AGENTS.md`):

| Metric               | Target  | How to Verify                    |
| -------------------- | ------- | -------------------------------- |
| Fuzzy processing     | < 50ms  | Check application logs           |
| Sensor → description | < 100ms | Check application logs           |
| LLM inference        | < 3s    | Observe response time            |
| Command generation   | < 100ms | Check application logs           |
| End-to-end latency   | < 5s    | Time from sensor pub to command  |
| System startup       | < 30s   | Time `make up` to healthy status |

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
