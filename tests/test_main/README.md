# Main System Tests

This directory contains tests for the main system entry point and cross-layer
integration scenarios.

## Test Files

- `test_main.py` - Tests for system main entry point and integration scenarios

## Test Focus

### Main System Tests

- System entry point initialization (main.py)
- Command-line argument parsing for main.py
- System startup flow validation
- Graceful shutdown verification
- Signal handling (SIGTERM, SIGINT)

### Integration Tests

- End-to-end sensor data flow (MQTT -> Fuzzy -> LLM -> Command -> MQTT)
- Complete system initialization (all layers in correct order)
- System shutdown with cleanup
- State persistence across system restarts
- Cross-layer communication verification

### System Health Tests

- Overall system status reporting
- Component health checks
- Resource usage monitoring
- Error recovery scenarios

## Performance Tests

Verify end-to-end system targets from ADD Section 8.1:

- End-to-end (sensor change to actuator command): < 5 seconds
- System startup: < 30 seconds

## Mocking Strategy

For integration tests, use lightweight mocks for external services:

- **MQTT Broker**: In-memory MQTT broker mock or test instance
- **Ollama Service**: Mock HTTP responses with realistic timing
- **File System**: Temporary directories for config and logs

## Test Configuration

Fixtures provide:

- Complete system configuration (all config files)
- Sample devices (sensors and actuators)
- Sample rules
- Mock MQTT broker and Ollama service
- Temporary test directories

## Running Tests

```bash
# Main system tests
pytest tests/test_main.py

# With verbose output
pytest tests/test_main.py -v

# Integration tests
pytest tests/test_main.py -k integration

# Performance tests
pytest tests/test_main.py -m performance

# With system integration (requires external services)
pytest tests/test_main.py --integration
```

## Integration Test Scenarios

1. **Happy Path**: Complete sensor-to-actuator flow
2. **Rule Firing**: Verify rule triggers correctly
3. **Conflict Resolution**: Test priority-based conflict handling
4. **Command Validation**: Verify validation pipeline works
5. **Device Failure**: Test behavior when device goes offline
6. **Ollama Failure**: Test graceful degradation if LLM unavailable
7. **Configuration Update**: Test hot-reloading configuration changes
8. **Startup/Shutdown**: Complete lifecycle test

## Deployment Tests

Test system deployment scenarios:

- Fresh installation and first startup
- Restart with persisted state
- Upgrade from previous version
- Recovery from crash

## Coverage Goals

- System entry point: 100%
- Main initialization flow: 100%
- Cross-layer integration points: > 90%
- Error handling paths: > 90%
