# Configuration & Management Layer

This directory contains the system's management layer responsible for lifecycle,
configuration, rules, and logging.

## Coordinator

- **SystemOrchestrator** - The central coordinator managing the full system
  lifecycle and orchestrating initialization, runtime, and shutdown across all
  layers.

## Components

### ConfigurationManager

- Loads all JSON configuration files from `config/` directory
- Performs schema validation on all configurations
- Provides async configuration access to other components
- Supports runtime configuration updates
- Implements atomic write-rename operations
- Creates timestamped backups before modifications

### RuleManager

- Provides persistent storage for natural language rules
- Full CRUD operations (Create, Read, Update, Delete)
- Rule enabling/disabling without deletion
- Metadata tracking (created_timestamp, last_triggered, trigger_count)
- Import/export capabilities for backup and sharing
- Maintains `rules/active_rules.json`

### LoggingManager

- Centralized structured logging for all system events
- JSON format for machine readability
- Log rotation (max 100MB per file)
- 30-day retention period
- Multiple log categories:
  - System events (startup, shutdown, config changes)
  - Commands sent to devices
  - Sensor readings and processing
  - Error messages with stack traces
  - Rule evaluation history

## System Orchestrator Responsibilities

As specified in Section 4.3, manages startup sequence:

01. Load and validate all configuration files
02. Initialize LoggingManager
03. Populate DeviceRegistry from device configuration
04. Connect MQTT client and subscribe to sensor topics
05. Verify Ollama connectivity and model availability
06. Load and validate membership functions
07. Load all persisted rules and index them
08. Start DeviceMonitor for tracking device availability
09. Initialize user interfaces
10. Enter ready state and begin normal operation

Also handles:

- Graceful shutdown procedures
- Cross-layer communication coordination
- Error handling and fail-safe defaults
- Component lifecycle management

## Communication Flow

**Downward** (to Control & Reasoning Layer):

- System state and configuration data
- Rule database access
- Logging services

**Upward** (from Control & Reasoning Layer):

- Command validation requests
- Rule history updates

**Horizontal** (to all layers):

- Configuration updates
- Logging services
- Lifecycle control signals

## Design Pattern

This layer uses the **Singleton** pattern for Configuration Manager and Logging
Manager (per Appendix D), ensuring single instances accessible system-wide for
efficiency and consistency.

## Resource Management

- Configuration tree cached to avoid repeated file I/O
- Cache invalidated on file modification or explicit reload
- Automatic backup before configuration changes
- Thread-safe configuration access for multi-threaded operations

## Integration

This is the central management layer sitting at the heart of the architecture.
It configures and coordinates all other layers, providing the foundation upon
which the system operates. It maintains strict layered communication patterns,
only interfacing directly with the Control & Reasoning Layer.
