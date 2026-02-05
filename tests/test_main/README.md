# Main System Tests

This directory contains tests for the main system entry point and cross-layer
integration scenarios.

## Test Files

```
test_main/
├── test_accuracy.py        # Accuracy verification tests
├── test_application.py     # Application lifecycle tests
├── test_e2e_integration.py # End-to-end integration tests
├── test_performance.py     # Performance benchmark tests
├── test_placeholder.py     # Placeholder test file
└── test_stress.py          # Stress and load tests
```

## Test Focus

### Application Tests

- Application class initialization
- System startup flow validation
- Graceful shutdown verification
- Signal handling

### End-to-End Integration Tests

- Complete sensor-to-actuator flow (MQTT -> Fuzzy -> LLM -> Command -> MQTT)
- Complete system initialization (all layers in correct order)
- System shutdown with cleanup
- Cross-layer communication verification

### Performance Tests

Verify end-to-end system targets from ADD Section 8.1:

- End-to-end (sensor change to actuator command): < 5 seconds
- System startup: < 30 seconds
- Fuzzy processing: < 50ms
- LLM inference: < 3s
- Command generation: < 100ms

### Stress Tests

- Test system limits (200 devices, 1000 rules, 100 readings/sec)
- Verify memory constraints (8GB total footprint)
- Test cache eviction under load
- Verify graceful degradation under stress

### Accuracy Tests

- Verify fuzzy logic computation accuracy
- Test rule matching correctness
- Validate command generation fidelity

## Mocking Strategy

For integration tests, use lightweight mocks for external services:

- **MQTT Broker**: In-memory MQTT broker mock
- **Ollama Service**: Mock HTTP responses with realistic timing
- **File System**: Temporary directories for config and logs

## Running Tests

```bash
# All main tests
pytest tests/test_main/

# Integration tests
pytest tests/test_main/test_e2e_integration.py

# Performance tests
pytest tests/test_main/test_performance.py

# Stress tests
pytest tests/test_main/test_stress.py

# With verbose output
pytest tests/test_main/ -v
```
