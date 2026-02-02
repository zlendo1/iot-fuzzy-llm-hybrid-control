# User Interface Layer Tests

This directory contains tests for the User Interface Layer components.

## Note on Scope

The User Interface Layer differs from other layers - it only communicates
downward to the Configuration & Management Layer. Tests focus on user
interaction, command processing, and response formatting.

## Components Tested

- `test_cli.py` - Tests for CLI Interface
- `test_web_ui.py` - Tests for Web UI (Optional)
- `test_rest_api.py` - Tests for REST API (Optional)

## Test Focus

### CLI Tests

- System lifecycle commands (start, stop, restart, status)
- Rule management commands (add, list, delete, enable, disable)
- Status monitoring queries (device status, sensor readings, rule history)
- Configuration management (reload, view, validate)
- Log viewing and filtering
- Command argument parsing and validation
- Help command output
- Error message formatting

### Web UI Tests (Optional)

- Visual rule editor functionality
- Dashboard rendering and real-time updates
- Configuration file editing
- Device status display
- Sensor reading visualization
- History viewer with filters
- Form validation and error handling
- Authentication (if implemented)

### REST API Tests (Optional)

- Rule CRUD endpoints (POST, GET, PUT, DELETE /api/rules)
- Device status endpoints (GET /api/devices)
- Sensor reading endpoints (GET /api/sensors)
- System health endpoints (GET /api/health)
- Configuration endpoints (GET/PUT /api/config)
- Log access endpoints (GET /api/logs)
- Request validation and error handling
- API authentication (if implemented)

## Mocking Strategy

- **Configuration Layer**: Mock SystemOrchestrator and Manager responses
- **User Input**: Mock command-line arguments or HTTP requests
- **Output Streams**: Capture and verify CLI output
- **HTTP Responses**: Mock Flask responses for Web UI and API tests

## Test Configuration

Fixtures provide:

- Mock system state data
- Sample rule configurations
- Sample device and sensor data
- Sample log entries
- Mock CLI arguments
- Mock HTTP requests and responses

## Integration Tests

Test UI communication with Configuration Layer:

- Verify commands are correctly passed to SystemOrchestrator
- Verify responses are correctly formatted for display
- Verify error conditions are properly handled and reported

## Running Tests

```bash
# All User Interface tests
pytest tests/test_interfaces/

# CLI tests only
pytest tests/test_interfaces/test_cli.py

# Web UI tests (if implemented)
pytest tests/test_interfaces/test_web_ui.py

# REST API tests (if implemented)
pytest tests/test_interfaces/test_rest_api.py

# With verbose output
pytest tests/test_interfaces/ -v
```

## Testing Priority

1. **CLI Tests** - Critical for system administration and debugging
2. **REST API Tests** - Important for third-party integration and automation
3. **Web UI Tests** - Lower priority (optional feature)

## Test Data

Test fixtures should include:

- Rule manipulation scenarios (add, modify, delete, enable, disable)
- Configuration update scenarios
- Status query scenarios
- Error conditions and edge cases
- Malformed input validation tests
