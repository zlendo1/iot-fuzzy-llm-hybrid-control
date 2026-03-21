# New Additions — 21 March 2026

Three planned features added to the thesis scope. Details in the documents
linked below.

______________________________________________________________________

## Features

### 1. Streamlit Web UI

Browser-based dashboard running **in parallel with the CLI**.

- **Architecture**: [add.md — Section 3.3.5](add.md)
- **Requirements**: [srs.md — UI-MODE-002](srs.md)
- **Usage guide**: [user/user-guide.md — Section 11](../user/user-guide.md)
- **Full documentation**: [user/web-ui-guide.md](../user/web-ui-guide.md)
- **API reference**:
  [user/api-reference.md — Web Interface Layer](../user/api-reference.md)

### 2. MQTT Flexibility Refactor

Custom payload schemas and topic patterns per device.

- **Architecture**: [add.md — Section 11.1](add.md)
- **Requirements**: [srs.md — FR-DC-008, FR-DC-009, FR-DC-010](srs.md)
- **Migration guide**:
  [user/configuration-guide.md — Section 8](../user/configuration-guide.md)
- **Full documentation**:
  [user/mqtt-flexibility-guide.md](../user/mqtt-flexibility-guide.md)

### 3. gRPC Interface

Unified RPC layer for CLI and Web UI communication (port 50051).

- **Architecture**:
  [add.md — Section 11.2](add.md#112-grpc-interface-architecture)
- **Requirements**: [srs.md — UI-MODE-003](srs.md#ui-mode-003)
- **API reference**:
  [user/api-reference.md — gRPC Interface Layer](../user/api-reference.md#grpc-interface-layer)
