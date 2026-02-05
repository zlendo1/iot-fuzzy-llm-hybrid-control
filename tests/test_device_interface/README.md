# Device Interface Layer Tests

This directory contains tests for the Device Interface Layer components.

## Test Files

```
test_device_interface/
├── test_communication_manager.py  # Tests for MQTTCommunicationManager
├── test_device_monitor.py         # Tests for DeviceMonitor
├── test_messages.py               # Tests for message parsing/formatting
├── test_models.py                 # Tests for device data models
├── test_mqtt_client.py            # Tests for MQTTClient
└── test_registry.py               # Tests for DeviceRegistry
```

## Test Focus

### MQTTClient Tests

- Connection establishment with authentication
- Topic subscription and unsubscription
- Message publication to actuator topics
- Message reception from sensor topics
- Reconnection logic with exponential backoff
- Connection state handling

### DeviceRegistry Tests

- Device loading from configuration
- Device lookup and query operations
- Device metadata storage and retrieval
- Device availability status tracking
- Edge cases (duplicate devices, missing devices)

### DeviceMonitor Tests

- Device availability tracking
- Heartbeat monitoring and timeout handling
- Device failure detection and reporting
- Status updates in registry

### Models Tests

- Device data class validation
- Sensor and actuator type definitions
- Capability specification validation

### Messages Tests

- Incoming sensor message parsing
- Outgoing command message formatting
- JSON payload handling

### CommunicationManager Tests

- Integration of all Device Interface components
- Upward communication to Data Processing Layer
- Downward command reception
- Device state propagation

## Mocking Strategy

- **MQTT Broker**: Mock paho-mqtt client to simulate broker interactions
- **Device Messages**: Use pre-defined message fixtures for sensor readings
- **Time**: Mock time for testing reconnection delays and timeouts

## Running Tests

```bash
# All Device Interface tests
pytest tests/test_device_interface/

# Specific component
pytest tests/test_device_interface/test_mqtt_client.py

# With verbose output
pytest tests/test_device_interface/ -v
```
