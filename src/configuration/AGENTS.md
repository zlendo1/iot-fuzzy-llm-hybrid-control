# Configuration & Management Layer

<!-- Generated: 2026-03-22 | Parent: src/AGENTS.md -->

> System orchestration, configuration management, structured logging, and rule
> persistence.

## Purpose

Top-level coordination layer. The **SystemOrchestrator** is the system's brain —
it initializes all components in order, manages lifecycle (start/stop), and
provides the single entry point for the interfaces layer above.

## Key Files

| File                     | Lines | Role                                                                    |
| ------------------------ | ----- | ----------------------------------------------------------------------- |
| `system_orchestrator.py` | 486   | **Layer coordinator**. 10-step init, lifecycle, wiring                  |
| `config_manager.py`      | 372   | Config loading with schema validation, TTL cache, atomic writes         |
| `logging_manager.py`     | 373   | Structured JSON logging, rotation, category-based handlers              |
| `rule_manager.py`        | 306   | Rule CRUD with atomic persistence, metadata tracking                    |
| `__init__.py`            |       | Exports: SystemOrchestrator, ConfigManager, LoggingManager, RuleManager |

## Architecture

```
Interfaces Layer (above)
        ↓
SystemOrchestrator  ←── THE coordinator
   ├── ConfigManager      (config/ JSON files)
   ├── LoggingManager     (structured logging setup)
   └── RuleManager        (rules/ persistence)
        ↓
Control & Reasoning Layer (below)
```

### Orchestrator Initialization Sequence (10 steps)

The `initialize()` method runs these steps **in order** — sequence matters:

01. Load system configuration
02. Initialize logging manager
03. Load device configuration
04. Initialize device registry
05. Initialize MQTT communication
06. Load membership functions
07. Initialize fuzzy pipeline
08. Initialize rule pipeline
09. Initialize LLM client
10. Wire components together

**Do not reorder steps.** Each depends on prior steps completing.

## Patterns

### Atomic Config Writes

```python
# ConfigManager uses write-rename for crash safety
def _atomic_write(self, path: Path, data: dict) -> None:
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2))
    tmp.rename(path)  # atomic on POSIX
```

### Schema Validation

All JSON configs validated against `config/schemas/*.json` before use.
ConfigManager caches validated configs with TTL.

### Logging Convention

```python
from src.common.logging import get_logger
logger = get_logger(__name__)
logger.info("Component initialized", extra={"component": "mqtt"})
```

LoggingManager sets up: console handler, rotating file handler, JSON formatter.
Categories: `system`, `mqtt`, `rules`, `fuzzy`, `llm`.

## Common Tasks

### Adding a New Configuration Section

1. Create JSON schema in `config/schemas/`
2. Add default config file in `config/`
3. Load via `ConfigManager.load("new_config.json")`
4. Add initialization step in `SystemOrchestrator.initialize()` if needed

### Modifying the Init Sequence

1. Add step in `SystemOrchestrator.initialize()`
2. Add corresponding cleanup in `shutdown()` (reverse order)
3. Update the step count and docstring

## DO NOT

- **Skip schema validation** when loading any JSON config
- **Modify config files without atomic write-rename** — risk of corruption on
  crash
- **Import from non-adjacent layers** — this layer talks only to interfaces
  (above) and control_reasoning (below)
- **Add direct file I/O** — use ConfigManager for all config operations
- **Break init order** — components depend on prior steps

## Known Architecture Notes

- SystemOrchestrator imports from `data_processing` and `device_interface`
  directly (bypassing control_reasoning). This is a known pragmatic deviation
  from strict layer adjacency, as the orchestrator needs to initialize all
  system components.
- RuleManager uses file-based persistence (not a database) — intentional for
  offline/embedded use case.
