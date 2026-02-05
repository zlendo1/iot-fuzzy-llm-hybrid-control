# Demo Walkthrough Guide

This document provides step-by-step instructions for demonstrating the Fuzzy-LLM
Hybrid IoT Management System for thesis evaluation.

## Prerequisites

Before running the demo, ensure:

1. **Docker and Docker Compose** are installed and running
2. **System is built**: `make build`
3. **LLM model is available**: `make pull-model` (pulls qwen3:0.6b)

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

# Expected output:
# mosquitto   running (healthy)
# ollama      running (healthy)
# app         running (healthy)
```

### Step 2: CLI Status Check

```bash
# Check system status via CLI
python -m src.main status

# Expected: Shows connected devices, loaded rules, LLM status
```

### Step 3: List Demo Rules

```bash
# List all configured rules
python -m src.main rule list

# Expected: 10 rules displayed with IDs and status
```

### Step 4: Climate Control Demo (DEMO-004)

**Scenario**: Living room is hot (32°C) and humid (78%)

```bash
# Simulate hot temperature reading
mosquitto_pub -h localhost -t home/living_room/temperature \
  -m '{"value": 32.0, "unit": "celsius", "timestamp": "2025-02-05T14:00:00Z"}'

# Simulate high humidity reading
mosquitto_pub -h localhost -t home/living_room/humidity \
  -m '{"value": 78.0, "unit": "percent", "timestamp": "2025-02-05T14:00:00Z"}'

# Expected system response:
# - Fuzzy engine converts 32°C → "temperature is hot (0.85)"
# - Fuzzy engine converts 78% → "humidity is humid (0.76)"
# - Rule climate_001 triggers
# - LLM determines: ACTION: ac_living_room, turn_on, temperature=22
# - Command published to home/living_room/ac/set
```

**Verification**:

```bash
# Subscribe to AC command topic
mosquitto_sub -h localhost -t home/living_room/ac/set
```

### Step 5: Lighting Control Demo (DEMO-005)

**Scenario**: Motion detected in dark hallway

```bash
# Simulate dark light level (50 lux)
mosquitto_pub -h localhost -t home/living_room/light_level \
  -m '{"value": 50.0, "unit": "lux"}'

# Simulate motion in hallway
mosquitto_pub -h localhost -t home/hallway/motion \
  -m '{"value": 1}'

# Expected:
# - Fuzzy engine: "light_level is dark (0.80)"
# - Fuzzy engine: "motion is motion_detected (1.0)"
# - Rule lighting_001 triggers
# - LLM: ACTION: light_hallway, turn_on
```

### Step 6: Heating Control Demo (DEMO-006)

**Scenario**: Bedroom is cold (15°C)

```bash
# Simulate cold bedroom temperature
mosquitto_pub -h localhost -t home/bedroom/temperature \
  -m '{"value": 15.0, "unit": "celsius"}'

# Expected:
# - Fuzzy engine: "temperature is cold (0.75)"
# - Rule heating_001 triggers
# - LLM: ACTION: heater_bedroom, turn_on, temperature=21
```

### Step 7: Blind Control Demo (DEMO-007)

**Scenario**: Very bright sunlight (40000 lux)

```bash
# Simulate very bright light
mosquitto_pub -h localhost -t home/living_room/light_level \
  -m '{"value": 40000.0, "unit": "lux"}'

# Expected:
# - Fuzzy engine: "light_level is very_bright (0.90)"
# - Rule blinds_001 triggers
# - LLM: ACTION: blinds_living_room, set_position, position=50
```

### Step 8: Rule Management Demo

```bash
# Add a new rule
python -m src.main rule add "night_mode" \
  "If no motion detected for 30 minutes after 11pm, turn off all lights"

# Disable a rule
python -m src.main rule disable climate_002

# Enable a rule
python -m src.main rule enable climate_002

# Show rule details
python -m src.main rule show climate_001
```

### Step 9: Sensor Status Demo

```bash
# Show current sensor readings
python -m src.main sensor status

# Expected: Shows raw values and linguistic descriptions
# Example: temp_living_room: 32.0°C → "temperature is hot (0.85)"
```

### Step 10: Configuration Validation

```bash
# Validate all configuration files
python -m src.main config validate

# Expected: All configs pass validation
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
