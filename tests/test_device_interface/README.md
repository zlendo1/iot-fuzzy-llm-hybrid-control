# Device Interface Layer Tests

This directory contains tests for the Device Interface Layer components.

## Components Tested

- `test_device_registry.py` - Tests for DeviceRegistry component
- `test_mqtt_client.py` - Tests for MQTTClient component
- `test_device_monitor.py` - Tests for DeviceMonitor component
- `test_mqtt_communication_manager.py` - Tests for the layer coordinator

## Test Focus

### DeviceRegistry Tests

- Device loading from configuration
- Device lookup and query operations
- Device metadata storage and retrieval
- Device availability status tracking
- Edge cases (duplicate devices, missing devices)

### MQTTClient Tests

- Connection establishment with authentication
- Topic subscription and unsubscription
- Message publication to actuator topics
- Message reception from sensor topics
- Reconnection logic with exponential backoff
- Last Will and Testament configuration
- Connection state handling

### DeviceMonitor Tests

- Device availability tracking via LWT
- Heartbeat monitoring and timeout handling
- Device failure detection and reporting
- Status updates in registry
- Reconnection detection

### MQTTCommunicationManager Tests

- Integration of all Device Interface components
- Upward communication to Data Processing Layer
- Downward command reception
- Device state propagation
- Coordinator interface compliance

## Mocking Strategy

- **MQTT Broker**: Mock paho-mqtt client to simulate broker interactions
- **Device Messages**: Use pre-defined message fixtures for sensor readings
- **Time**: Mock time for testing reconnection delays and timeouts

## Test Configuration

Fixtures provide:

- Sample device configurations from `config/devices.json`
- Sample MQTT broker settings
- Mock sensor messages
- Mock connection states

## Running Tests

```bash
# All Device Interface tests
pytest tests/test_device_interface/

# Specific component
pytest tests/test_device_interface/test_device_registry.py

# With verbose output
pytest tests/test_device_interface/ -v
```
