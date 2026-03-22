# Device Interface Layer

<!-- Generated: 2026-03-22 | Parent: src/AGENTS.md -->

> MQTT communication, device registry, monitoring, and message handling for IoT
> devices.

## Purpose

The bottom layer. Manages physical device communication via MQTT, maintains a
registry of known devices, monitors device availability, and defines the core
data models (`SensorReading`, `DeviceCommand`) used throughout the system.

## Key Files

| File                       | Lines | Role                                                    |
| -------------------------- | ----- | ------------------------------------------------------- |
| `communication_manager.py` | 319   | **Layer coordinator**. MQTT ops, registry, callbacks    |
| `mqtt_client.py`           | 308   | MQTT client with reconnection logic, topic management   |
| `registry.py`              |       | Device registration, lookup, capability tracking        |
| `device_monitor.py`        | 219   | Availability monitoring via LWT, status tracking        |
| `messages.py`              | 251   | Core dataclasses: `SensorReading`, `DeviceCommand`      |
| `models.py`                |       | Device/Sensor/Actuator dataclasses                      |
| `payload_formatter.py`     |       | MQTT payload serialization/deserialization              |
| `topic_resolver.py`        |       | MQTT topic construction from device/sensor config       |
| `__init__.py`              |       | Exports: MQTTCommunicationManager, DeviceRegistry, etc. |

## Architecture

```
Data Processing Layer (above)
        ↓
┌─ MQTTCommunicationManager ────────────────┐
│  ├── MQTTClient          (protocol layer)  │
│  ├── DeviceRegistry      (device catalog)  │
│  └── DeviceMonitor       (availability)    │
└────────────────────────────────────────────┘
        ↓
    MQTT Broker (Mosquitto)
        ↓
    Physical IoT Devices
```

### Coordinator Methods

```python
manager.start()                              # Connect MQTT, start monitoring
manager.stop()                               # Disconnect, cleanup
manager.send_command(command: DeviceCommand)  # Send to device
manager.get_latest_reading(device_id)         # Last sensor value
manager.add_reading_callback(callback)        # Register sensor listener
```

## Core Data Models

These dataclasses are used across **all layers** — they're the system's lingua
franca:

```python
@dataclass
class SensorReading:
    device_id: str
    sensor_type: str
    value: float
    unit: str
    timestamp: datetime
    # + MQTT payload parsing classmethod

@dataclass
class DeviceCommand:
    device_id: str
    command_type: str
    parameters: dict
    source: str          # Which rule triggered this
    timestamp: datetime
```

## MQTT Patterns

### Topic Structure

```
iot/{device_id}/sensors/{sensor_type}    # Sensor readings (subscribe)
iot/{device_id}/commands                  # Device commands (publish)
iot/{device_id}/status                    # LWT / availability
```

### Reconnection Logic

`MQTTClient` implements automatic reconnection with exponential backoff. Uses
`paho-mqtt` library. Connection state tracked internally.

### Callback Wiring

Sensor readings flow upward via callbacks registered in `application.py`:

```python
# In Application._wire_components():
mqtt_manager.add_reading_callback(fuzzy_pipeline.process_reading)
```

## Common Tasks

### Adding a New Device Type

1. Add device definition to `config/devices.json`
2. Define its sensors and actuators with capabilities
3. DeviceRegistry auto-loads on initialization

### Adding a New Command Type

1. Define command structure in device config (capabilities)
2. CommandValidator (control_reasoning) will check against capabilities
3. MQTT payload format defined by the device's protocol

### Monitoring Device Health

DeviceMonitor uses MQTT Last Will and Testament (LWT) messages. When a device
disconnects unexpectedly, the broker publishes the LWT, and DeviceMonitor
updates status.

## DO NOT

- **Import from data_processing or above** — this is the bottom layer, it only
  provides data upward via callbacks
- **Hardcode MQTT topics** — use the topic structure from config
- **Skip reconnection handling** — always use MQTTClient's built-in reconnection
- **Modify SensorReading/DeviceCommand without updating all layers** — these
  dataclasses are used system-wide
- **Use QoS 0 for commands** — commands should use QoS 1+ for delivery guarantee

## Configuration Files

- `config/mqtt_config.json` — Broker host, port, credentials, QoS settings
- `config/devices.json` — Device definitions, sensors, actuators, capabilities
