# Tests Directory

This directory contains all test code for the Fuzzy-LLM Hybrid IoT Management
System.

## Purpose

Comprehensive testing suite to ensure system reliability, correctness, and
performance across all components and layers.

## Test Framework

- **pytest** - Primary testing framework for unit and integration tests
- Test discovery: All `test_*.py` files are automatically discovered
- Fixtures: Shared test setup and teardown across tests
- Coverage: Use pytest-cov for code coverage reporting

## Test Organization

Tests mirror the source directory structure for clear mapping between code and
tests:

```
tests/
├── test_main.py                          # System startup and orchestrator tests
├── test_device_interface/                # Device Interface Layer tests
│   ├── test_device_registry.py
│   ├── test_mqtt_client.py
│   ├── test_device_monitor.py
│   └── test_mqtt_communication_manager.py
├── test_data_processing/                 # Data Processing Layer tests
│   ├── test_fuzzy_engine.py
│   ├── test_membership_functions.py
│   ├── test_linguistic_descriptor_buider.py
│   └── test_fuzzy_processing_pipeline.py
├── test_control_reasoning/               # Control & Reasoning Layer tests
│   ├── test_rule_interpreter.py
│   ├── test_ollama_client.py
│   ├── test_command_generator.py
│   └── test_rule_processing_pipeline.py
├── test_configuration/                   # Configuration & Management Layer tests
│   ├── test_configuration_manager.py
│   ├── test_rule_manager.py
│   ├── test_logging_manager.py
│   └── test_system_orchestrator.py
└── test_interfaces/                     # User Interface Layer tests
    ├── test_cli.py
    ├── test_web_ui.py                   # Optional
    └── test_rest_api.py                 # Optional
```

## Test Categories

### Unit Tests

- Test individual components in isolation
- Mock external dependencies (MQTT broker, Ollama service)
- Fast execution (< 1 second per test)
- Focus on logic correctness and edge cases

### Integration Tests

- Test interaction between components within a layer
- Test communication between adjacent layers
- Use lightweight mocks for external services
- Verify data flow across boundaries

### End-to-End Tests

- Test complete sensor-to-actuator flow
- Test system startup and initialization
- Test system shutdown gracefully
- May use a local MQTT broker test instance

### Performance Tests

- Verify latency targets from Section 8.1 of ADD:
  - Fuzzy logic processing < 50ms
  - Sensor reading to description < 100ms
  - LLM inference < 3s
  - Command generation < 100ms
  - End-to-end flow < 5s
  - System startup < 30s

### Stress Tests

- Test system limits (200 devices, 1000 rules, 100 readings/sec)
- Verify memory constraints (8GB total footprint)
- Test cache eviction under load
- Verify graceful degradation under stress

## Mocking Strategy

- **MQTT Client**: Mock paho-mqtt to simulate broker without external dependency
- **Ollama Client**: Mock HTTP responses for fast, deterministic testing
- **File System**: Use tmp_path fixture for isolated config file testing
- **Device Registry**: Mock device states for edge case testing

## Test Data

Fixtures provide reusable test data:

- Sample configurations (mqtt_config.json, llm_config.json, etc.)
- Sample rules
- Sample device definitions
- Sample membership functions
- Mock sensor readings

## Running Tests

```bash
# Run all tests
pytest

# Run specific directory
pytest tests/test_device_interface/

# Run specific test file
pytest tests/test_fuzzy_engine.py

# Run with coverage
pytest --cov=src --cov-report=html

# Run performance tests only
pytest -m performance

# Run with verbose output
pytest -v
```

## Continuous Integration

Tests should run automatically on:

- Every push to the repository
- Every pull request
- Scheduled builds (daily)
- Before every release

## Coverage Goals

- Overall code coverage: > 80%
- Critical path coverage: > 95%
- Edge case coverage: Include all failure modes
- Layer boundary coverage: All inter-layer calls tested

## Test Maintenance

- Tests should be updated when component interfaces change
- Mocks should reflect actual service behavior
- Test data should be representative of real-world scenarios
- Legacy tests should be reviewed and updated periodically

## Design Philosophy

Following the ADD's layered architecture principles, tests respect layer
boundaries:

- Unit tests test components in isolation
- Integration tests test layer-internal communication
- E2E tests test full system flow through all layers
- No component is tested through a non-adjacent layer
