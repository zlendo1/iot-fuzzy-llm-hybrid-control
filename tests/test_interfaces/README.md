# User Interface Layer Tests

This directory contains tests for the User Interface Layer components.

## Test Files

```
test_interfaces/
└── test_cli.py    # Tests for CLI Interface
```

## Note on Scope

The User Interface Layer currently implements only the CLI interface. The CLI is
the primary interaction tool for system administration.

## Test Focus

### CLI Tests

- System lifecycle commands (start, stop, status)
- Rule management commands (add, list, delete, enable, disable)
- Status monitoring queries (device status, sensor readings)
- Configuration management (reload, view, validate)
- Log viewing and filtering
- Command argument parsing and validation
- Help command output
- Error message formatting

## Mocking Strategy

- **Configuration Layer**: Mock SystemOrchestrator and Manager responses
- **User Input**: Mock command-line arguments
- **Output Streams**: Capture and verify CLI output

## Running Tests

```bash
# All User Interface tests
pytest tests/test_interfaces/

# CLI tests
pytest tests/test_interfaces/test_cli.py

# With verbose output
pytest tests/test_interfaces/ -v
```
