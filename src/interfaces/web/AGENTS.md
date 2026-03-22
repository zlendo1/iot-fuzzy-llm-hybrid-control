# Web UI Layer (Streamlit)

<!-- Generated: 2026-03-22 | Parent: src/interfaces/AGENTS.md -->

> Streamlit-based web dashboard for system monitoring and management. Connects
> to the system via gRPC through the OrchestratorBridge.

## Purpose

Visual dashboard providing real-time system monitoring, device management, rule
editing, configuration, and fuzzy membership function visualization. Uses the
same gRPC backend as the CLI.

## Directory Structure

```
web/
├── streamlit_app.py     # Main app entry with navigation
├── bridge.py            # OrchestratorBridge (482 lines) — gRPC wrapper
├── pages/               # 7 page implementations
│   ├── dashboard.py     # System overview, sensor readings
│   ├── devices.py       # Device list, status, commands
│   ├── rules.py         # Rule CRUD, enable/disable
│   ├── config.py        # Configuration viewer/editor
│   ├── membership_editor.py  # Fuzzy MF visual editor
│   ├── logs.py          # Log viewer with filtering
│   └── system_control.py    # Start/stop, system info
├── components/          # Shared UI components
└── __init__.py
```

## Architecture

```
Browser
   ↓
Streamlit App (streamlit_app.py)
   ↓
Page Components (pages/*.py)
   ↓
OrchestratorBridge (bridge.py)  ← cached Streamlit resource
   ↓
GrpcClient (rpc/client.py)
   ↓
gRPC Server (:50051)
```

### OrchestratorBridge Pattern

The bridge wraps `GrpcClient` with Streamlit-specific concerns:

```python
@st.cache_resource
def get_bridge() -> OrchestratorBridge:
    return OrchestratorBridge(host="localhost", port=50051)
```

- Cached as Streamlit resource (lives across reruns)
- Handles connection errors with user-friendly messages
- Provides 20+ typed methods mirroring GrpcClient

## Running the Web UI

```bash
# Development
streamlit run src/interfaces/web/streamlit_app.py

# Docker
make docker-up  # web service on port 8501
```

## Common Tasks

### Adding a New Page

1. Create `pages/new_page.py` with page rendering function
2. Add navigation entry in `streamlit_app.py`
3. Use `get_bridge()` for all data operations
4. Add tests using AppTest pattern (see testing section)

### Modifying an Existing Page

Pages are standalone functions. Edit directly in `pages/`. Use `get_bridge()`
for data, Streamlit components for UI.

### Adding Shared Components

Place reusable UI widgets in `components/`. Import in pages as needed.

## Testing Pattern

Web tests use Streamlit's `AppTest` framework:

```python
# tests/test_interfaces/test_web/conftest.py provides:
@pytest.fixture
def app_test():
    return AppTest.from_file("src/interfaces/web/streamlit_app.py")
```

Mock the bridge for unit tests — don't require a running gRPC server.

## DO NOT

- **Import system components directly** — always go through OrchestratorBridge
- **Skip `@st.cache_resource`** for the bridge — creates new connection every
  rerun otherwise
- **Put business logic in pages** — pages are display-only, bridge handles data
- **Use `st.experimental_*`** deprecated APIs — use current Streamlit API
- **Hardcode the gRPC port** — use bridge configuration
