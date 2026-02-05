# Configuration & Management Layer Tests

This directory contains tests for the Configuration & Management Layer
components.

## Test Files

```
test_configuration/
├── test_config_manager.py       # Tests for ConfigurationManager
├── test_logging_manager.py      # Tests for LoggingManager
├── test_rule_manager.py         # Tests for RuleManager
└── test_system_orchestrator.py  # Tests for SystemOrchestrator
```

## Test Focus

### ConfigurationManager Tests

- Loading all JSON configuration files from config directory
- Schema validation for all configuration types
- Configuration file parsing with error handling
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
- Multiple log category support (system, commands, sensors, errors, rules)
- Log level filtering

### SystemOrchestrator Tests

- System startup sequence
- Component initialization order
- Graceful shutdown procedures
- Error handling and fail-safe defaults
- Component lifecycle management

## Running Tests

```bash
# All Configuration & Management tests
pytest tests/test_configuration/

# Specific component
pytest tests/test_configuration/test_config_manager.py

# With coverage
pytest tests/test_configuration/ --cov=src/configuration
```
