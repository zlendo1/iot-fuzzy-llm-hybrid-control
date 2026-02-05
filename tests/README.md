# Tests Directory

This directory contains all test code for the Fuzzy-LLM Hybrid IoT Management
System.

## Test Statistics

- **806 tests** passing
- **83% code coverage**
- All performance targets verified

## Test Framework

- **pytest** - Primary testing framework for unit and integration tests
- Test discovery: All `test_*.py` files are automatically discovered
- Fixtures: Shared test setup in `conftest.py`
- Coverage: Use pytest-cov for code coverage reporting

## Test Organization

Tests mirror the source directory structure:

```
tests/
├── conftest.py                           # Shared fixtures and configuration
├── test_common/                          # Tests for common utilities
├── test_configuration/                   # Configuration & Management Layer
│   ├── test_config_manager.py
│   ├── test_logging_manager.py
│   ├── test_rule_manager.py
│   └── test_system_orchestrator.py
├── test_control_reasoning/               # Control & Reasoning Layer
│   ├── test_command_generator.py
│   ├── test_command_validator.py
│   ├── test_conflict_resolver.py
│   ├── test_ollama_client.py
│   ├── test_prompt_builder.py
│   ├── test_response_parser.py
│   ├── test_rule_interpreter.py
│   └── test_rule_pipeline.py
├── test_data_processing/                 # Data Processing Layer
│   ├── test_fuzzy_engine.py
│   ├── test_fuzzy_pipeline.py
│   ├── test_linguistic_descriptor.py
│   └── test_membership_functions.py
├── test_device_interface/                # Device Interface Layer
│   ├── test_communication_manager.py
│   ├── test_device_monitor.py
│   ├── test_messages.py
│   ├── test_models.py
│   ├── test_mqtt_client.py
│   └── test_registry.py
├── test_interfaces/                      # User Interface Layer
│   └── test_cli.py
└── test_main/                            # Integration and E2E tests
    ├── test_accuracy.py
    ├── test_application.py
    ├── test_e2e_integration.py
    ├── test_performance.py
    └── test_stress.py
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

### Accuracy Tests

- Verify fuzzy logic computation accuracy
- Test LLM response parsing correctness
- Validate command generation fidelity

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Quick check
pytest --tb=line -q

# Run specific directory
pytest tests/test_control_reasoning/

# Run specific test file
pytest tests/test_control_reasoning/test_ollama_client.py

# Run with verbose output
pytest -v

# Run performance tests only
pytest -m performance
```

## Coverage Goals

- Overall code coverage: > 80% (currently 83%)
- Critical path coverage: > 95%
- Edge case coverage: Include all failure modes
- Layer boundary coverage: All inter-layer calls tested

## Design Philosophy

Following the ADD's layered architecture principles, tests respect layer
boundaries:

- Unit tests test components in isolation
- Integration tests test layer-internal communication
- E2E tests test full system flow through all layers
