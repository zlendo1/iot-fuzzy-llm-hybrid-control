# gRPC RPC Layer

<!-- Generated: 2026-03-22 | Parent: src/interfaces/AGENTS.md -->

> Unified gRPC interface providing typed RPC methods for all system operations.
> CLI and Web UI both use this as their backend.

## Purpose

Single point of access for all system functionality. The gRPC server exposes 6
services on port 50051, and the typed `GrpcClient` provides Python-native method
calls that abstract away protobuf serialization.

## Directory Structure

```
rpc/
├── server.py          # GrpcServer — registers all 6 services
├── client.py          # GrpcClient — typed Python wrapper (581 lines)
├── servicers/         # 6 service implementations
│   ├── lifecycle_servicer.py
│   ├── rules_servicer.py
│   ├── devices_servicer.py
│   ├── config_servicer.py
│   ├── logs_servicer.py
│   └── membership_servicer.py
├── generated/         # Auto-generated protobuf code (DO NOT EDIT)
│   ├── *_pb2.py       # Message classes
│   └── *_pb2_grpc.py  # Service stubs
└── __init__.py
```

## 6 gRPC Services

| Service    | Proto File         | Key Methods                                                            |
| ---------- | ------------------ | ---------------------------------------------------------------------- |
| Lifecycle  | `lifecycle.proto`  | Start, Stop, GetStatus, GetSystemInfo                                  |
| Rules      | `rules.proto`      | AddRule, RemoveRule, ListRules, GetRule, Enable/Disable, EvaluateRules |
| Devices    | `devices.proto`    | ListDevices, GetDevice, GetDeviceStatus, GetLatestReading, SendCommand |
| Config     | `config.proto`     | GetConfig, UpdateConfig, ValidateConfig, ReloadConfig, ListConfigs     |
| Logs       | `logs.proto`       | GetLogEntries, GetLogCategories, GetLogStats                           |
| Membership | `membership.proto` | GetMembershipFunctions, UpdateMembershipFunction, ListSensorTypes      |

Shared types defined in `common.proto`.

## Servicer Pattern

Each servicer receives the `SystemOrchestrator` (or a specific manager) and
delegates all logic:

```python
class RulesServicer(RulesServiceServicer):
    def __init__(self, orchestrator: SystemOrchestrator) -> None:
        self._orchestrator = orchestrator

    def AddRule(self, request, context):
        result = self._orchestrator.rule_manager.add_rule(request.rule_text)
        return AddRuleResponse(success=True, rule_id=result.id)
```

**Servicers are thin** — no business logic, just proto ↔ Python conversion.

## Common Tasks

### Adding a New gRPC Method to an Existing Service

1. Edit the `.proto` file in `protos/`
2. Run `make proto` to regenerate Python code
3. Run `scripts/fix_protobuf_imports.py` (auto-fixes relative imports)
4. Implement the method in the corresponding servicer
5. Add typed wrapper method in `client.py`
6. Add tests in `tests/test_interfaces/test_rpc/`

### Adding a New gRPC Service

1. Create new `.proto` file in `protos/`
2. Import shared types from `common.proto`
3. Run `make proto`
4. Create servicer in `rpc/servicers/`
5. Register service in `server.py`
6. Add client methods in `client.py`
7. Add tests

### Proto Regeneration Workflow

```bash
make proto  # Runs protoc + fix_protobuf_imports.py
```

The `fix_protobuf_imports.py` script post-processes generated files to fix
Python import paths (protoc generates absolute imports that don't work with the
project's package structure).

## DO NOT

- **Edit files in `generated/`** — they are overwritten by `make proto`
- **Put business logic in servicers** — servicers are pure delegation
- **Skip `fix_protobuf_imports.py`** after proto regeneration — imports will
  break
- **Add new proto files without `common.proto` imports** — shared types must be
  consistent
- **Change the port (50051)** without updating all connection points (CLI, Web
  bridge, Docker compose)
