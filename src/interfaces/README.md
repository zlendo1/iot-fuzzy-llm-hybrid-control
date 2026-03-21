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

### Web UI

- **Purpose**: Browser-based interface for visual interaction
- **Features**:
  - Real-time sensor status dashboard with auto-refresh
  - Visual rule editor with natural language input
  - Execution history viewer with timestamps
  - Configuration file editor with validation
  - Membership function editor with visual graphs
  - Device monitoring and health display
  - Log viewer with filtering and search
- **Implementation**: Streamlit dashboard
- **Access**: Web browser at `http://localhost:8501`
- **Note**: Uses gRPC to communicate with the running application

### gRPC RPC Interface

- **Purpose**: Unified RPC layer for programmatic access
- **Services**:
  - LifecycleService: Start, stop, status, system info
  - RulesService: Rule CRUD, enable/disable, evaluation
  - DevicesService: Device listing, status, commands
  - ConfigService: Configuration get/update/validate/reload
  - LogsService: Log retrieval and filtering
  - MembershipService: Fuzzy membership function access
- **Implementation**: grpcio server with Protocol Buffers
- **Access**: gRPC on port 50051 (configurable)
- **Use Cases**: CLI commands, Web UI bridge, automation scripts, custom clients

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
3. **gRPC Interface** - Unified RPC for CLI, Web UI, and third-party access

## Design Principles

- **Minimal overhead**: UIs remain lightweight and responsive
- **Privacy**: All UI data stays on-device, no external connections
- **Accessibility**: CLI works over SSH on edge devices
- **Consistency**: All interfaces expose the same core functionality
- **Fail-safe**: Input validation before executing any action

## Resource Impact

- CLI: Minimal (< 50MB memory overhead)
- Web UI: ~150MB for Streamlit and dependencies
- gRPC Server: ~30MB additional for grpcio runtime

## Security Considerations

- CLI: Requires local shell access or SSH authentication
- Web UI: Local access by default; can add Streamlit authentication
- gRPC: Binds to all interfaces (`[::]`) by default; TLS not currently
  implemented
- All interfaces validate inputs before passing to system

## Architecture Note

This is the only layer without a coordinator since it only communicates downward
to the Configuration & Management Layer. Multiple UI components can coexist and
are all optional except for the CLI which provides essential system
administration capabilities.
