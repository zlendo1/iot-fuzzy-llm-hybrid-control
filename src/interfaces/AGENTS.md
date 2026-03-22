# Interfaces Layer

<!-- Generated: 2026-03-22 | Parent: src/AGENTS.md -->

> User-facing interfaces: CLI, gRPC RPC services, and Streamlit Web UI. All
> three use the same gRPC backend for consistency.

## Purpose

Provides all user interaction surfaces. Every interface communicates with the
system through the **gRPC client** — ensuring CLI, Web UI, and any future
interface have identical functionality.

## Sub-directories

| Directory | Purpose                        | Details                            |
| --------- | ------------------------------ | ---------------------------------- |
| `rpc/`    | gRPC server, servicers, client | See [rpc/AGENTS.md](rpc/AGENTS.md) |
| `web/`    | Streamlit dashboard            | See [web/AGENTS.md](web/AGENTS.md) |

## Key Files (this level)

| File          | Lines | Role                                            |
| ------------- | ----- | ----------------------------------------------- |
| `cli.py`      | 1009  | Click-based CLI with 4 command groups           |
| `__init__.py` |       | Exports: CLIContext, OutputFormatter, cli, main |

## Architecture

```
                    ┌── CLI (cli.py) ──────────┐
User ──────────────►│                           │
                    ├── Web UI (streamlit) ─────┤──► GrpcClient ──► gRPC Server ──► SystemOrchestrator
                    │                           │        (port 50051)
                    └── Future interfaces ──────┘
```

**Key insight**: CLI and Web UI are **equivalent thin clients**. Neither
contains business logic — all operations go through gRPC.

## CLI Structure (`cli.py`)

The CLI uses Click command groups:

```
cli (root)
├── system      # start, stop, status
├── rule        # add, list, enable, disable, delete
├── device      # list, status
├── sensor      # list, readings
├── config      # validate, reload, migrate
└── logs        # tail, categories, stats
```

### CLI → gRPC Flow

```python
# CLI commands use GrpcClient for ALL operations
@cli.command()
@click.argument("rule_text")
def add(ctx, rule_text):
    client = ctx.obj["client"]  # GrpcClient instance
    result = client.add_rule(rule_text)
    # Format and display result
```

### Running the CLI

```bash
python -m src.interfaces [command] [subcommand] [args]
# e.g.
python -m src.interfaces rule add "If bedroom is cold, turn on heater"
python -m src.interfaces system status
python -m src.interfaces device list
```

## Common Tasks

### Adding a New CLI Command

1. Add Click command function in `cli.py` under appropriate group
2. Use `ctx.obj["client"]` (GrpcClient) for all operations
3. Format output with `OutputFormatter`
4. If new gRPC method needed, add it in `rpc/` first (see rpc/AGENTS.md)

### Adding a New Interface Type

1. Use `GrpcClient` from `src/interfaces/rpc/client.py`
2. Connect to `localhost:50051`
3. All system operations available via typed client methods
4. No direct imports from other layers needed

## DO NOT

- **Put business logic in interfaces** — interfaces are thin clients only
- **Import from configuration/control_reasoning/data_processing/device_interface
  directly** — always use gRPC
- **Add CLI commands without corresponding gRPC methods** — CLI must go through
  gRPC for consistency
- **Skip error handling** — gRPC calls can fail (server down, timeout)
