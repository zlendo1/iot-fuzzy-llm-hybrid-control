# User Interface Layer

This directory contains all user interfaces for interacting with the Fuzzy-LLM
Hybrid IoT Management System.

## Components

### CLI Interface

- **Purpose**: Primary interaction tool for system administration
- **Features**:
  - System lifecycle control (start, stop, restart, status)
  - Rule management (add, list, delete, enable, disable)
  - Status monitoring (device status, sensor readings, rule history)
  - Configuration management (reload, view, validate)
  - Log viewing and filtering
- **Implementation**: Python CLI using argparse or Click
- **Access**: Command line terminal

### Web UI (Optional)

- **Purpose**: Browser-based interface for visual interaction
- **Features**:
  - Visual rule editor with natural language input
  - Real-time sensor status dashboard
  - Execution history viewer with timestamps
  - Configuration file editor with validation
  - Device monitoring and health display
  - Log viewer with filtering
- **Implementation**: Flask web server (port 5000)
- **Access**: Web browser at `http://localhost:5000`
- **Note**: Can be disabled if not needed (lightweight deployment)

### REST API (Optional)

- **Purpose**: Programmatic access for third-party integration
- **Endpoints**:
  - Rule CRUD operations
  - Device status queries
  - Sensor reading retrieval
  - System health checks
  - Configuration management
  - Log access
- **Implementation**: Flask with RESTful endpoints
- **Access**: HTTP API calls
- **Use Cases**: Automation scripts, external monitoring tools, custom
  dashboards

## Communication Flow

**Downward** (to Configuration & Management Layer):

- User commands and queries
- Administrative actions
- Rule modifications

**Upward** (from Configuration & Management Layer):

- System status and health data
- Device telemetry
- Rule evaluation results
- Log entries

## Implementation Priority

1. **CLI Interface** - Implemented first for basic system administration
2. **Web UI** - Added later for improved usability and visual monitoring
3. **REST API** - Added last for programmatic access and integration

## Design Principles

- **Minimal overhead**: UIs remain lightweight and responsive
- **Privacy**: All UI data stays on-device, no external connections
- **Accessibility**: CLI works over SSH on edge devices
- **Consistency**: All interfaces expose the same core functionality
- **Fail-safe**: Input validation before executing any action

## Resource Impact

- CLI: Minimal (< 50MB memory overhead)
- Web UI: Additional ~100MB for Flask and static assets
- REST API: Leverages Web UI Flask server, no additional overhead

## Security Considerations

- CLI: Requires local shell access or SSH authentication
- Web UI: Can add basic authentication (username/password)
- REST API: Can use API keys or token-based authentication
- All interfaces validate inputs before passing to system

## Architecture Note

This is the only layer without a coordinator since it only communicates downward
to the Configuration & Management Layer. Multiple UI components can coexist and
are all optional except for the CLI which provides essential system
administration capabilities.
