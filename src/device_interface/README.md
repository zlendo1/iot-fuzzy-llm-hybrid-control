# Device Interface Layer

This directory contains the bottom layer of the architecture, responsible for
all communication with physical IoT devices.

## Structure

```
device_interface/
├── __init__.py
├── communication_manager.py   # Coordinator - manages all device I/O
├── mqtt_client.py             # MQTT client implementation
├── registry.py                # Device registry and lookup
├── device_monitor.py          # Device availability tracking
├── models.py                  # Data models for devices and sensors
└── messages.py                # Message parsing and formatting
```

## Coordinator

- **MQTTCommunicationManager** (`communication_manager.py`) - The sole interface
  between this layer and the Data Processing Layer above it. Coordinates all
  device I/O operations.

## Components

### MQTTClient

- Implements paho-mqtt client functionality
- Connects to Eclipse Mosquitto broker with authentication
- Subscribes to sensor data topics
- Publishes commands to actuator topics
- Handles reconnection (1-60s exponential backoff)
- Configures Last Will and Testament messages

### DeviceRegistry

- Maintains inventory of all configured sensors and actuators
- Stores device metadata: MQTT topics, capabilities, constraints
- Provides device lookup and query methods
- Tracks device availability status

### DeviceMonitor

- Tracks device availability using LWT messages
- Monitors periodic device heartbeats
- Reports device failures to logging system
- Updates device status in registry

### Models

- Data classes for device definitions
- Sensor and actuator type definitions
- Device capability specifications

### Messages

- Message parsing for incoming sensor data
- Message formatting for outgoing commands
- JSON payload handling

## Communication Flow

**Upward** (to Data Processing Layer):

- Raw sensor readings from MQTT topics
- Device status updates
- Connection state changes

**Downward** (from Control & Reasoning Layer):

- Actuator commands to publish to MQTT
- Device queries

## MQTT Topic Convention

Following the pattern in Appendix C of the ADD:

- `home/{zone}/{sensor_type}` - Sensor data
- `home/{zone}/{actuator}/set` - Control commands
- `home/{zone}/{actuator}/status` - Actuator status

## Integration

This layer has no dependencies on upper layers. It can be tested independently
with a mock MQTT broker, following the strict layered architecture principle
(per DD-01).
