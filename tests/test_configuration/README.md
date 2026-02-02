# Configuration & Management Layer Tests

This directory contains tests for the Configuration & Management Layer
components.

## Components Tested

- `test_configuration_manager.py` - Tests for Configuration Manager
- `test_rule_manager.py` - Tests for Rule Manager
- `test_logging_manager.py` - Tests for Logging Manager
- `test_system_orchestrator.py` - Tests for the layer coordinator

## Test Focus

### ConfigurationManager Tests

- Loading all JSON configuration files from config directory
- Schema validation for all configuration types
- Configuration file parsing with error handling
- Runtime configuration updates
- Atomic write-rename operations
- Timestamped backup creation
- Configuration access and retrieval
- Invalid configuration rejection

### RuleManager Tests

- Rule CRUD operations (Create, Read, Update, Delete)
- Rule enabling/disabling without deletion
- Metadata tracking (created_timestamp, last_triggered, trigger_count)
- Import/export functionality
- Rule file persistence (rules/active_rules.json)
- Duplicate rule handling
- Invalid rule rejection

### LoggingManager Tests

- Centralized logging initialization
- JSON format log output
- Log rotation (max size triggering)
- Log retention cleanup
- Multiple log category support (system, commands, sensors, errors, rules)
- Log level filtering
- Concurrent logging safety

### SystemOrchestrator Tests

- System startup sequence (per ADD Section 4.3):
  01. Configuration loading and validation
  02. LoggingManager initialization
  03. DeviceRegistry population
  04. MQTT client connection and subscription
  05. Ollama connectivity verification
  06. Membership function loading
  07. Rule loading and indexing
  08. DeviceMonitor startup
  09. User interface initialization
  10. Ready state entry
- Graceful shutdown procedures
- Error handling and fail-safe defaults
- Cross-layer communication coordination
- Component lifecycle management

## Integration Tests

Test the complete system initialization flow:

- Verify all layers initialize in correct order
- Verify all components receive necessary configuration
- Verify coordinator communication paths
- Verify error handling at each stage

## Performance Tests

Verify latency targets from ADD Section 8.1:

- System startup: < 30 seconds
- Configuration loading: < 5 seconds total
- Logging overhead: < 1ms per log entry

## Mocking Strategy

- **File System**: Use tmp_path fixture for isolated config testing
- **Time**: Mock time for testing backups and log rotation
- **MQTT Client**: Mock for testing initialization without broker
- **Ollama Client**: Mock for testing connectivity verification

## Test Configuration

Fixtures provide:

- Sample configuration files (all JSON types)
- Sample rules file
- Temporary directories for file operations
- Mock device registry data
- Mock logger instances

## Running Tests

```bash
# All Configuration & Management tests
pytest tests/test_configuration/

# Specific component
pytest tests/test_configuration/test_configuration_manager.py

# With coverage
pytest tests/test_configuration/ --cov=src/configuration

# Integration tests
pytest tests/test_configuration/test_system_orchestrator.py -v
```
