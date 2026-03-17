# urllib.request HTTP Pattern for IoT System

## Pattern Overview

Used consistently across CLI and web interfaces for HTTP requests to local
status endpoints.

## Core Pattern (from src/interfaces/cli.py:319-325)

```python
try:
    with urllib.request.urlopen(status_url, timeout=2) as response:
        if response.status == 200:
            status_data = json.loads(response.read().decode("utf-8"))
            status_source = "running"
except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
    logger.debug("Status endpoint unavailable", extra={"error": str(exc)})
```

## Key Elements

- **Error Handling**: Catch OSError, urllib.error.URLError, and
  json.JSONDecodeError together
- **Timeout**: Always set timeout (2-5 seconds) to prevent indefinite blocking
- **Context Manager**: Use `with` statement for automatic resource cleanup
- **Status Check**: Always verify response.status == 200 before parsing
- **Decode**: Use response.read().decode("utf-8") for bytes to string conversion

## Implementation in http_client.py

Applied the same pattern in AppStatusClient for:

- `get_status()` - Returns dict or None
- `shutdown()` - Returns bool indicating success

This ensures consistency across the codebase for HTTP operations.


## Task 1: Shutdown Endpoint Learnings

- `_StatusRequestHandler` follows a strict path-first dispatch pattern: normalize `self.path` with `split("?", 1)[0].rstrip("/")` before route checks.
- For method-specific behavior, keep status handler logic in the request method (`do_GET`/`do_POST`) and reuse `_send_response` to keep JSON content-type/length consistent.
- Graceful shutdown works reliably when returning response before `self._app.stop()`: client gets `{"status": "shutdown_initiated"}` and then server terminates.
- Endpoint tests should isolate HTTP port with `patch.dict(os.environ, {"IOT_STATUS_PORT": ...})` to avoid flakiness from existing listeners during threaded server startup.
- GET `/shutdown` is best handled explicitly as 405 in `do_GET` to preserve `/status` behavior while making method constraints testable.

## Task 4: CLI HTTP Shutdown Integration

### Implementation Pattern
- Stop command tries HTTP POST to `/shutdown` first with 5s timeout
- Falls back to orchestrator-based shutdown if HTTP fails
- Uses `urllib.request.urlopen(url, data=b'', timeout=5)` for POST (data parameter required)
- Error handling catches OSError and urllib.error.URLError together

### Key Changes
1. **HTTP-First Pattern**: Check running app first via HTTP, only initialize orchestrator if needed
2. **Message Format**: Returns "✓ Application stopped successfully." on HTTP success, "✓ System stopped successfully." on orchestrator success
3. **Graceful Degradation**: Falls back silently - no error messages if HTTP unavailable, just tries orchestrator

### Testing (TDD Approach)
- Write failing tests first: HTTP success, fallback on error, success message display
- Use `unittest.mock.MagicMock` to mock urlopen context manager
- Mock patterns: `__enter__` and `__exit__` for context manager protocol
- All 4 new tests pass, no existing tests broken (58/58 passing)

### QA Results
- Scenario 1: HTTP shutdown works when app running → ✓ Verified
- Scenario 2: Graceful handling when app not running → ✓ Verified with "⚠ System is not running." message

### Patterns
- Port resolution: Use `os.getenv("IOT_STATUS_PORT", "8080")` consistently
- HTTP POST for shutdown, GET for status (follows REST conventions)
- Timeout values: 2s for status queries, 5s for shutdown operations


## [2026-03-17T23:31:57Z] Task 5: OrchestratorBridge HTTP-Only Refactor

### Architectural Change
- Removed all SystemOrchestrator instantiation from web bridge
- Bridge now uses AppStatusClient for HTTP queries to  and 
- Bridge reads  and  directly for file-backed data
- Zero MQTT connections from web bridge module

### Implementation Patterns
- HTTP client created in  with configurable base URL
- CWD-independent path resolution via 
- Fallback pattern for devices: use  when present, otherwise load from devices file
- Graceful degradation: missing files, invalid JSON, or offline app return safe defaults (, , )

### Verification
✓ No MQTT imports in 
✓ No MQTT modules loaded after bridge import/instantiation
✓ HTTP status query works when app is running
✓ Graceful handling when app is not running
✓ ============================= test session starts ==============================
platform linux -- Python 3.14.3, pytest-8.4.2, pluggy-1.6.0 -- /usr/bin/python
cachedir: .pytest_cache
rootdir: /home/zijad/Projects/iot-master-web-cli-fixes
configfile: pyproject.toml
plugins: asyncio-0.26.0, cov-5.0.0, mock-3.14.1, anyio-4.12.1
asyncio: mode=Mode.STRICT, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ... collected 8 items

tests/test_interfaces/test_web/test_bridge.py::test_get_system_status_returns_http_status_payload PASSED [ 12%]
tests/test_interfaces/test_web/test_bridge.py::test_is_app_running_proxies_http_client PASSED [ 25%]
tests/test_interfaces/test_web/test_bridge.py::test_get_devices_prefers_status_orchestrator_devices PASSED [ 37%]
tests/test_interfaces/test_web/test_bridge.py::test_get_devices_falls_back_to_devices_file PASSED [ 50%]
tests/test_interfaces/test_web/test_bridge.py::test_get_rules_reads_active_rules_file PASSED [ 62%]
tests/test_interfaces/test_web/test_bridge.py::test_shutdown_calls_http_client_shutdown PASSED [ 75%]
tests/test_interfaces/test_web/test_bridge.py::test_graceful_when_app_not_running PASSED [ 87%]
tests/test_interfaces/test_web/test_bridge.py::test_get_bridge_returns_cached_instance PASSED [100%]

============================== 8 passed in 0.43s =============================== passes (8/8)

### Why This Works
- Web UI no longer creates a second orchestrator/MQTT client
- Main application remains the only MQTT connection owner
- Web layer now acts as HTTP observer + local JSON reader
- Eliminates client-ID collision/disconnect storm root cause


## [2026-03-17T23:32:05Z] Task 5: OrchestratorBridge HTTP-Only Refactor

### Architectural Change
- Removed all SystemOrchestrator instantiation from web bridge
- Bridge now uses AppStatusClient for HTTP queries to /status and /shutdown
- Bridge reads config/devices.json and rules/active_rules.json directly for file-backed data
- Zero MQTT connections from web bridge module

### Implementation Patterns
- HTTP client created in OrchestratorBridge.__init__ with configurable base URL
- CWD-independent path resolution via Path(__file__).resolve().parents[3]
- Fallback pattern for devices: use status orchestrator devices when present, otherwise load from devices file
- Graceful degradation: missing files, invalid JSON, or offline app return safe defaults (None, empty list, False)

### Verification
- No MQTT imports in src/interfaces/web/bridge.py
- No MQTT modules loaded after bridge import/instantiation
- HTTP status query works when app is running
- Graceful handling when app is not running
- pytest tests/test_interfaces/test_web/test_bridge.py -v passes (8/8)

### Why This Works
- Web UI no longer creates a second orchestrator/MQTT client
- Main application remains the only MQTT connection owner
- Web layer now acts as HTTP observer plus local JSON reader
- Eliminates client-ID collision and disconnect storm root cause
