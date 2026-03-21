"""Command Line Interface for the Fuzzy-LLM Hybrid IoT Management System.

This module provides a CLI for system administration, rule management,
device monitoring, and configuration management.
"""

from __future__ import annotations

import json
import typing
import sys
import textwrap
from pathlib import Path
from typing import Any

import click

from src.common.exceptions import ConfigurationError, IoTFuzzyLLMError, RuleError
from src.common.logging import get_logger


class _GrpcClientFallback:
    def __init__(self, host: str = "localhost", port: int = 50051) -> None:
        self._host = host
        self._port = port

    def __enter__(self) -> _GrpcClientFallback:
        raise IoTFuzzyLLMError("gRPC server unavailable")

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        return None

    def start(self) -> dict[str, Any]:
        raise IoTFuzzyLLMError("gRPC server unavailable")

    def stop(self) -> dict[str, Any]:
        raise IoTFuzzyLLMError("gRPC server unavailable")

    def get_status(self) -> dict[str, Any]:
        raise IoTFuzzyLLMError("gRPC server unavailable")

    def reload_config(self) -> dict[str, Any]:
        raise IoTFuzzyLLMError("gRPC server unavailable")


GrpcClient: type[Any]
try:
    from src.interfaces.rpc.client import GrpcClient as _RealGrpcClient

    GrpcClient = typing.cast(type[Any], _RealGrpcClient)
except ModuleNotFoundError:
    GrpcClient = _GrpcClientFallback


logger = get_logger(__name__)


class OutputFormatter:
    """Handles consistent output formatting for CLI commands."""

    def __init__(self, output_format: str = "table") -> None:
        self._format = output_format

    def set_format(self, output_format: str) -> None:
        self._format = output_format

    def format_table(
        self,
        headers: list[str],
        rows: list[list[Any]],
        *,
        min_widths: list[int] | None = None,
        max_widths: list[int] | None = None,
        row_separator: bool = False,
    ) -> str:
        """Format data as a table with optional text wrapping for long cells.

        Args:
            headers: Column header names.
            rows: List of rows, each row is a list of cell values.
            min_widths: Minimum width for each column (optional).
            max_widths: Maximum width for each column - text will wrap (optional).
            row_separator: If True, add a separator line between logical rows.

        Returns:
            Formatted table string.
        """
        if not rows:
            return "No data to display."

        widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                widths[i] = max(widths[i], len(str(cell)))

        if min_widths:
            for i, min_w in enumerate(min_widths):
                if i < len(widths):
                    widths[i] = max(widths[i], min_w)

        if max_widths:
            for i, max_w in enumerate(max_widths):
                if i < len(widths) and max_w > 0:
                    widths[i] = min(widths[i], max_w)

        header_line = " | ".join(h.ljust(widths[i]) for i, h in enumerate(headers))
        separator = "-+-".join("-" * w for w in widths)

        data_lines: list[str] = []
        for row_idx, row in enumerate(rows):
            wrapped_cells: list[list[str]] = []
            for i, cell in enumerate(row):
                cell_str = str(cell)
                if max_widths and i < len(max_widths) and max_widths[i] > 0:
                    wrapped = textwrap.wrap(
                        cell_str, width=max_widths[i], break_long_words=True
                    )
                    wrapped_cells.append(wrapped if wrapped else [""])
                else:
                    wrapped_cells.append([cell_str])

            max_lines = max(len(wc) for wc in wrapped_cells)

            for line_idx in range(max_lines):
                line_parts = []
                for i, wrapped in enumerate(wrapped_cells):
                    if line_idx < len(wrapped):
                        line_parts.append(wrapped[line_idx].ljust(widths[i]))
                    else:
                        line_parts.append(" " * widths[i])
                data_lines.append(" | ".join(line_parts))

            if row_separator and row_idx < len(rows) - 1:
                data_lines.append(separator)

        return "\n".join([header_line, separator] + data_lines)

    def format_json(self, data: Any) -> str:
        """Format data as JSON."""
        return json.dumps(data, indent=2, default=str)

    def format_dict(self, data: dict[str, Any], *, indent: int = 0) -> str:
        """Format a dictionary for display."""
        lines = []
        prefix = "  " * indent
        for key, value in data.items():
            if isinstance(value, dict):
                lines.append(f"{prefix}{key}:")
                lines.append(self.format_dict(value, indent=indent + 1))
            else:
                lines.append(f"{prefix}{key}: {value}")
        return "\n".join(lines)

    def success(self, message: str) -> str:
        """Format a success message."""
        return click.style(f"✓ {message}", fg="green")

    def error(self, message: str) -> str:
        """Format an error message."""
        return click.style(f"✗ {message}", fg="red")

    def warning(self, message: str) -> str:
        """Format a warning message."""
        return click.style(f"⚠ {message}", fg="yellow")

    def info(self, message: str) -> str:
        """Format an info message."""
        return click.style(f"ℹ {message}", fg="blue")


class CLIContext:
    """Context object holding shared CLI state."""

    def __init__(self) -> None:
        self.config_dir: Path = Path("config")
        self.rules_dir: Path = Path("rules")
        self.logs_dir: Path = Path("logs")
        self.output_format: str = "table"
        self.verbose: bool = False
        self.formatter: OutputFormatter = OutputFormatter()
        self.grpc_host: str = "localhost"
        self.grpc_port: int = 50051


pass_context = click.make_pass_decorator(CLIContext, ensure=True)


def handle_errors(func: Any) -> Any:
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        ctx = args[0] if args and isinstance(args[0], CLIContext) else None
        formatter = ctx.formatter if ctx else OutputFormatter()
        try:
            return func(*args, **kwargs)
        except ConfigurationError as e:
            click.echo(formatter.error(f"Configuration error: {e}"))
            sys.exit(1)
        except RuleError as e:
            click.echo(formatter.error(f"Rule error: {e}"))
            sys.exit(1)
        except IoTFuzzyLLMError as e:
            click.echo(formatter.error(str(e)))
            sys.exit(1)
        except FileNotFoundError as e:
            click.echo(formatter.error(f"File not found: {e}"))
            sys.exit(1)
        except Exception as e:
            click.echo(formatter.error(f"Unexpected error: {e}"))
            if ctx and ctx.verbose:
                import traceback

                click.echo(traceback.format_exc())
            sys.exit(1)

    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    return wrapper


@click.group()
@click.option(
    "--config-dir",
    type=click.Path(exists=False, file_okay=False, path_type=Path),
    default=Path("config"),
    help="Configuration directory path.",
)
@click.option(
    "--rules-dir",
    type=click.Path(exists=False, file_okay=False, path_type=Path),
    default=Path("rules"),
    help="Rules directory path.",
)
@click.option(
    "--logs-dir",
    type=click.Path(exists=False, file_okay=False, path_type=Path),
    default=Path("logs"),
    help="Logs directory path.",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json", "plain"]),
    default="table",
    help="Output format.",
)
@click.option("--grpc-host", default="localhost", help="gRPC server host")
@click.option("--grpc-port", default=50051, type=int, help="gRPC server port")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output.")
@click.version_option(version="0.1.0", prog_name="iot-fuzzy-llm")
@click.pass_context
def cli(
    ctx: click.Context,
    config_dir: Path,
    rules_dir: Path,
    logs_dir: Path,
    output_format: str,
    grpc_host: str,
    grpc_port: int,
    verbose: bool,
) -> None:
    """Fuzzy-LLM Hybrid IoT Management System CLI.

    Manage IoT devices using natural language rules processed by a local LLM.
    """
    ctx.ensure_object(CLIContext)
    cli_ctx = ctx.obj
    cli_ctx.config_dir = config_dir
    cli_ctx.rules_dir = rules_dir
    cli_ctx.logs_dir = logs_dir
    cli_ctx.output_format = output_format
    cli_ctx.grpc_host = grpc_host
    cli_ctx.grpc_port = grpc_port
    cli_ctx.verbose = verbose
    cli_ctx.formatter.set_format(output_format)


@cli.command()
@click.option("--skip-mqtt", is_flag=True, help="Skip MQTT connection.")
@click.option("--skip-ollama", is_flag=True, help="Skip Ollama verification.")
@pass_context
@handle_errors
def start(ctx: CLIContext, skip_mqtt: bool, skip_ollama: bool) -> None:
    """Start the IoT management system."""
    click.echo(ctx.formatter.info("Starting Fuzzy-LLM IoT Management System..."))

    if skip_mqtt or skip_ollama:
        logger.debug(
            "gRPC lifecycle start ignores local skip flags",
            extra={"skip_mqtt": skip_mqtt, "skip_ollama": skip_ollama},
        )

    with GrpcClient(ctx.grpc_host, ctx.grpc_port) as client:
        result = client.start()

    if result.get("success", False):
        click.echo(ctx.formatter.success("System started successfully."))
    else:
        message = result.get("message", "System failed to start.")
        click.echo(ctx.formatter.error(f"Failed: {message}"))
        sys.exit(1)


@cli.command()
@pass_context
@handle_errors
def stop(ctx: CLIContext) -> None:
    """Stop the IoT management system."""
    click.echo(ctx.formatter.info("Stopping system..."))

    with GrpcClient(ctx.grpc_host, ctx.grpc_port) as client:
        result = client.stop()

    if result.get("success", False):
        click.echo(ctx.formatter.success("✓ System stopped successfully."))
    else:
        message = result.get("message", "Failed to stop system.")
        click.echo(ctx.formatter.error(f"Failed: {message}"))
        sys.exit(1)


@cli.command()
@pass_context
@handle_errors
def status(ctx: CLIContext) -> None:
    """Display system status."""
    with GrpcClient(ctx.grpc_host, ctx.grpc_port) as client:
        status_data = client.get_status()

    if ctx.output_format == "json":
        click.echo(ctx.formatter.format_json({"source": "running", **status_data}))
        return

    click.echo(ctx.formatter.success("Connected to running application."))

    state = str(status_data.get("status", "unknown"))
    is_ready = state.upper() in {"RUNNING", "READY"}

    click.echo(f"System State: {state.upper()}")
    click.echo(f"Ready: {'Yes' if is_ready else 'No'}")
    click.echo(f"Uptime (seconds): {status_data.get('uptime_seconds', 0)}")
    click.echo(f"Version: {status_data.get('version', 'unknown')}")


@cli.group()
def rule() -> None:
    """Manage natural language rules."""
    pass


@rule.command("add")
@click.argument("text")
@click.option(
    "--id", "rule_id", default=None, help="Rule ID (auto-generated if not provided)."
)
@click.option(
    "--priority",
    type=int,
    default=50,
    help="Rule priority (1-100, higher = more important).",
)
@click.option(
    "--tag", "-t", multiple=True, help="Tags for the rule (stored in metadata)."
)
@pass_context
@handle_errors
def rule_add(
    ctx: CLIContext, text: str, rule_id: str | None, priority: int, tag: tuple[str, ...]
) -> None:
    """Add a new natural language rule.

    TEXT is the natural language rule text.
    """
    with GrpcClient(ctx.grpc_host, ctx.grpc_port) as client:
        try:
            result = client.add_rule(text)
            rule = result.get("rule", {})

            if ctx.output_format == "json":
                click.echo(ctx.formatter.format_json(rule))
            else:
                click.echo(ctx.formatter.success(f"Rule added with ID: {rule['id']}"))
                click.echo(f"  Text: {rule['text']}")
                click.echo(f"  Enabled: {'Yes' if rule.get('enabled', True) else 'No'}")
        except Exception as e:
            click.echo(ctx.formatter.error(f"Failed to add rule: {e}"), err=True)
            sys.exit(1)


@rule.command("list")
@click.option("--enabled-only", is_flag=True, help="Show only enabled rules.")
@click.option("--tag", "-t", help="Filter by tag.")
@pass_context
@handle_errors
def rule_list(ctx: CLIContext, enabled_only: bool, tag: str | None) -> None:
    """List all rules."""
    with GrpcClient(ctx.grpc_host, ctx.grpc_port) as client:
        try:
            result = client.list_rules()
            rules = result.get("rules", [])

            if enabled_only:
                rules = [r for r in rules if r.get("enabled", True)]

            if ctx.output_format == "json":
                click.echo(ctx.formatter.format_json(rules))
                return

            if not rules:
                click.echo("No rules found.")
                return

            headers = ["ID", "Enabled", "Text"]
            rows = []
            for r in rules:
                rows.append(
                    [
                        r["id"],
                        "Yes" if r.get("enabled", True) else "No",
                        r["text"],
                    ]
                )

            text_column_wrap_width = 50
            max_widths = [0, 0, text_column_wrap_width]
            click.echo(
                ctx.formatter.format_table(
                    headers, rows, max_widths=max_widths, row_separator=True
                )
            )
            click.echo(f"\nTotal: {len(rules)} rule(s)")
        except Exception as e:
            click.echo(ctx.formatter.error(f"Failed to list rules: {e}"), err=True)
            sys.exit(1)


@rule.command("show")
@click.argument("rule_id")
@pass_context
@handle_errors
def rule_show(ctx: CLIContext, rule_id: str) -> None:
    """Show detailed information about a rule."""
    with GrpcClient(ctx.grpc_host, ctx.grpc_port) as client:
        try:
            rule = client.get_rule(rule_id)

            if ctx.output_format == "json":
                click.echo(ctx.formatter.format_json(rule))
                return

            click.echo(f"Rule ID: {rule['id']}")
            click.echo(f"Text: {rule['text']}")
            click.echo(f"Enabled: {'Yes' if rule.get('enabled', True) else 'No'}")
        except Exception as e:
            click.echo(ctx.formatter.error(f"Failed to get rule: {e}"), err=True)
            sys.exit(1)


@rule.command("enable")
@click.argument("rule_id")
@pass_context
@handle_errors
def rule_enable(ctx: CLIContext, rule_id: str) -> None:
    """Enable a rule."""
    with GrpcClient(ctx.grpc_host, ctx.grpc_port) as client:
        try:
            result = client.enable_rule(rule_id)
            if result.get("success", False):
                click.echo(ctx.formatter.success(f"Rule {rule_id} enabled."))
            else:
                click.echo(ctx.formatter.error(f"Failed to enable rule: {rule_id}"))
                sys.exit(1)
        except Exception as e:
            click.echo(ctx.formatter.error(f"Failed to enable rule: {e}"), err=True)
            sys.exit(1)


@rule.command("disable")
@click.argument("rule_id")
@pass_context
@handle_errors
def rule_disable(ctx: CLIContext, rule_id: str) -> None:
    """Disable a rule."""
    with GrpcClient(ctx.grpc_host, ctx.grpc_port) as client:
        try:
            result = client.disable_rule(rule_id)
            if result.get("success", False):
                click.echo(ctx.formatter.success(f"Rule {rule_id} disabled."))
            else:
                click.echo(ctx.formatter.error(f"Failed to disable rule: {rule_id}"))
                sys.exit(1)
        except Exception as e:
            click.echo(ctx.formatter.error(f"Failed to disable rule: {e}"), err=True)
            sys.exit(1)


@rule.command("delete")
@click.argument("rule_id")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation.")
@pass_context
@handle_errors
def rule_delete(ctx: CLIContext, rule_id: str, yes: bool) -> None:
    """Delete a rule."""
    with GrpcClient(ctx.grpc_host, ctx.grpc_port) as client:
        try:
            if not yes:
                try:
                    rule = client.get_rule(rule_id)
                    text_preview = (
                        rule["text"][:50] + "..."
                        if len(rule["text"]) > 50
                        else rule["text"]
                    )
                    click.echo(f"Rule to delete: {text_preview}")
                    if not click.confirm("Are you sure you want to delete this rule?"):
                        click.echo("Cancelled.")
                        return
                except Exception:
                    pass

            result = client.remove_rule(rule_id)
            if result.get("success", False):
                click.echo(ctx.formatter.success(f"Rule {rule_id} deleted."))
            else:
                click.echo(ctx.formatter.error(f"Failed to delete rule: {rule_id}"))
                sys.exit(1)
        except Exception as e:
            click.echo(ctx.formatter.error(f"Failed to delete rule: {e}"), err=True)
            sys.exit(1)


@cli.group()
def sensor() -> None:
    """View sensor information and readings."""
    pass


@sensor.command("list")
@pass_context
@handle_errors
def sensor_list(ctx: CLIContext) -> None:
    """List all registered sensors."""
    from src.interfaces.rpc.client import GrpcClient

    with GrpcClient(ctx.grpc_host, ctx.grpc_port) as client:
        try:
            all_devices = client.list_devices()
            # Filter to sensors only (type == "sensor")
            sensors = [d for d in all_devices if d.get("type") == "sensor"]

            if ctx.output_format == "json":
                data = [
                    {
                        "id": s["id"],
                        "name": s["name"],
                        "device_class": s.get("capabilities", [""])[0]
                        if s.get("capabilities")
                        else "",
                        "location": s.get("location", ""),
                        "unit": "",  # Not available from gRPC response
                    }
                    for s in sensors
                ]
                click.echo(ctx.formatter.format_json(data))
                return

            if not sensors:
                click.echo("No sensors registered.")
                return

            headers = ["ID", "Name", "Class", "Location", "Unit"]
            rows = []
            for s in sensors:
                rows.append(
                    [
                        s["id"],
                        s["name"],
                        s.get("capabilities", [""])[0]
                        if s.get("capabilities")
                        else "-",
                        s.get("location") or "-",
                        "-",  # Unit not available from gRPC response
                    ]
                )

            click.echo(ctx.formatter.format_table(headers, rows))
            click.echo(f"\nTotal: {len(sensors)} sensor(s)")

        except Exception as e:
            click.echo(ctx.formatter.error(f"Failed to list sensors: {e}"), err=True)
            sys.exit(1)


@sensor.command("status")
@click.argument("sensor_id", required=False)
@pass_context
@handle_errors
def sensor_status(ctx: CLIContext, sensor_id: str | None) -> None:
    """Show sensor status and readings.

    If SENSOR_ID is not provided, shows status for all sensors.
    """
    from src.interfaces.rpc.client import GrpcClient

    with GrpcClient(ctx.grpc_host, ctx.grpc_port) as client:
        try:
            if sensor_id:
                device = client.get_device(sensor_id)
                if device.get("type") != "sensor":
                    click.echo(
                        ctx.formatter.error(f"Device {sensor_id} is not a sensor")
                    )
                    sys.exit(1)
                sensors = [device]
            else:
                all_devices = client.list_devices()
                sensors = [d for d in all_devices if d.get("type") == "sensor"]

            if ctx.output_format == "json":
                data = [
                    {
                        "id": s["id"],
                        "name": s["name"],
                        "device_class": s.get("capabilities", [""])[0]
                        if s.get("capabilities")
                        else "",
                        "location": s.get("location", ""),
                        "unit": "",
                        "status": "registered",
                    }
                    for s in sensors
                ]
                click.echo(ctx.formatter.format_json(data))
                return

            if not sensors:
                click.echo("No sensors found.")
                return

            for s in sensors:
                click.echo(f"\n{s['name']} ({s['id']})")
                click.echo(
                    f"  Class: {s.get('capabilities', [''])[0] if s.get('capabilities') else 'N/A'}"
                )
                click.echo(f"  Location: {s.get('location') or 'N/A'}")
                click.echo("  Unit: N/A")
                click.echo("  Status: registered")

        except Exception as e:
            click.echo(
                ctx.formatter.error(f"Failed to get sensor status: {e}"), err=True
            )
            sys.exit(1)


@cli.group()
def device() -> None:
    """View device information and status."""
    pass


@device.command("list")
@pass_context
@handle_errors
def device_list(ctx: CLIContext) -> None:
    """List all registered devices."""
    from src.interfaces.rpc.client import GrpcClient

    with GrpcClient(ctx.grpc_host, ctx.grpc_port) as client:
        try:
            devices = client.list_devices()

            if ctx.output_format == "json":
                data = [
                    {
                        "id": d["id"],
                        "name": d["name"],
                        "type": d.get("type", ""),
                        "device_class": d.get("capabilities", [""])[0]
                        if d.get("capabilities")
                        else "",
                        "location": d.get("location", ""),
                    }
                    for d in devices
                ]
                click.echo(ctx.formatter.format_json(data))
                return

            if not devices:
                click.echo("No devices registered.")
                return

            headers = ["ID", "Name", "Type", "Class", "Location"]
            rows = []
            for d in devices:
                rows.append(
                    [
                        d["id"],
                        d["name"],
                        d.get("type", "-"),
                        d.get("capabilities", [""])[0]
                        if d.get("capabilities")
                        else "-",
                        d.get("location") or "-",
                    ]
                )

            click.echo(ctx.formatter.format_table(headers, rows))
            click.echo(f"\nTotal: {len(devices)} device(s)")

        except Exception as e:
            click.echo(ctx.formatter.error(f"Failed to list devices: {e}"), err=True)
            sys.exit(1)


@device.command("status")
@click.argument("device_id", required=False)
@pass_context
@handle_errors
def device_status(ctx: CLIContext, device_id: str | None) -> None:
    """Show device status and capabilities.

    If DEVICE_ID is not provided, shows status for all devices.
    """
    from src.interfaces.rpc.client import GrpcClient

    with GrpcClient(ctx.grpc_host, ctx.grpc_port) as client:
        try:
            if device_id:
                device = client.get_device(device_id)
                devices = [device]
            else:
                devices = client.list_devices()

            if ctx.output_format == "json":
                data: list[dict[str, Any]] = []
                for d in devices:
                    item: dict[str, Any] = {
                        "id": d["id"],
                        "name": d["name"],
                        "type": d.get("type", ""),
                        "device_class": d.get("capabilities", [""])[0]
                        if d.get("capabilities")
                        else "",
                        "location": d.get("location", ""),
                        "status": "registered",
                    }
                    if d.get("type") == "actuator" and d.get("capabilities"):
                        item["capabilities"] = d["capabilities"]
                    data.append(item)
                click.echo(ctx.formatter.format_json(data))
                return

            if not devices:
                click.echo("No devices found.")
                return

            for d in devices:
                click.echo(f"\n{d['name']} ({d['id']})")
                click.echo(f"  Type: {d.get('type', 'N/A')}")
                click.echo(
                    f"  Class: {d.get('capabilities', [''])[0] if d.get('capabilities') else 'N/A'}"
                )
                click.echo(f"  Location: {d.get('location') or 'N/A'}")
                click.echo("  Status: registered")
                if d.get("type") == "actuator" and d.get("capabilities"):
                    click.echo(f"  Capabilities: {', '.join(d['capabilities'])}")

        except Exception as e:
            click.echo(
                ctx.formatter.error(f"Failed to get device status: {e}"), err=True
            )
            sys.exit(1)


@cli.group()
def config() -> None:
    """Manage configuration files."""
    pass


@config.command("validate")
@pass_context
@handle_errors
def config_validate(ctx: CLIContext) -> None:
    """Validate all configuration files."""
    from src.interfaces.rpc.client import GrpcClient

    click.echo(ctx.formatter.info("Validating configuration files..."))

    with GrpcClient(ctx.grpc_host, ctx.grpc_port) as client:
        try:
            config_names = client.list_configs()
            all_valid = True
            validated_configs: list[str] = []

            for name in config_names:
                config_data = client.get_config(name)
                result = client.validate_config(name, config_data["content"])
                if result["valid"]:
                    validated_configs.append(name)
                else:
                    all_valid = False
                    click.echo(ctx.formatter.error(f"Validation failed for {name}:"))
                    for error in result["errors"]:
                        click.echo(f"  - {error}")

            if all_valid:
                click.echo(ctx.formatter.success("All configuration files are valid."))
                click.echo("\nLoaded configurations:")
                for name in validated_configs:
                    click.echo(f"  ✓ {name}")
            else:
                sys.exit(1)

        except Exception as e:
            click.echo(ctx.formatter.error(f"Validation failed: {e}"))
            sys.exit(1)


@config.command("migrate")
@click.option(
    "--dry-run", is_flag=True, help="Show what would change without modifying files."
)
@pass_context
@handle_errors
def config_migrate(ctx: CLIContext, dry_run: bool) -> None:
    """Migrate configuration files to the latest schema format.

    Detects devices.json devices missing payload_mapping under their mqtt key
    and mqtt_config.json missing the topic_patterns key.
    Creates .bak backups before modifying any file.
    """
    from src.interfaces.rpc.client import GrpcClient

    changes_needed: list[str] = []

    with GrpcClient(ctx.grpc_host, ctx.grpc_port) as client:
        try:
            # Check devices.json for missing payload_mapping
            devices_needing_payload_mapping: list[str] = []
            try:
                devices_config = client.get_config("devices")
                devices_data: dict[str, Any] = devices_config["content"]

                for dev in devices_data.get("devices", []):
                    dev_id: str = dev.get("id", "<unknown>")
                    if "mqtt" in dev and "payload_mapping" not in dev["mqtt"]:
                        devices_needing_payload_mapping.append(dev_id)

                for dev_id in devices_needing_payload_mapping:
                    if dry_run:
                        click.echo(f"Would add payload_mapping to device: {dev_id}")
                    else:
                        click.echo(f"Added payload_mapping to device: {dev_id}")
                    changes_needed.append(dev_id)

                if not dry_run and devices_needing_payload_mapping:
                    for dev in devices_data.get("devices", []):
                        if dev.get("id") in devices_needing_payload_mapping:
                            dev["mqtt"]["payload_mapping"] = {"value_field": "value"}
                    client.update_config(
                        "devices", devices_data, devices_config["version"]
                    )

                logger.info(
                    "Checked devices.json for payload_mapping",
                    extra={
                        "count": len(devices_needing_payload_mapping),
                        "dry_run": dry_run,
                    },
                )
            except Exception:
                click.echo(
                    ctx.formatter.warning(
                        "devices.json not found — skipping device migration."
                    )
                )

            # Check mqtt_config.json for missing topic_patterns
            try:
                mqtt_config = client.get_config("mqtt_config")
                mqtt_data: dict[str, Any] = mqtt_config["content"]

                if "topic_patterns" not in mqtt_data:
                    if dry_run:
                        click.echo("Would add topic_patterns to mqtt_config.json")
                    else:
                        click.echo("Added topic_patterns to mqtt_config.json")
                    changes_needed.append("mqtt_config.json:topic_patterns")

                    if not dry_run:
                        mqtt_data["topic_patterns"] = {}
                        client.update_config(
                            "mqtt_config", mqtt_data, mqtt_config["version"]
                        )

                logger.info(
                    "Checked mqtt_config.json for topic_patterns",
                    extra={
                        "needs_migration": "topic_patterns" not in mqtt_data,
                        "dry_run": dry_run,
                    },
                )
            except Exception:
                click.echo(
                    ctx.formatter.warning(
                        "mqtt_config.json not found — skipping MQTT config migration."
                    )
                )

            if not changes_needed:
                click.echo(
                    ctx.formatter.success(
                        "All configuration files are already up-to-date. No changes needed."
                    )
                )
            elif dry_run:
                click.echo(
                    ctx.formatter.info(
                        f"Dry-run complete. {len(changes_needed)} change(s) would be applied."
                    )
                )
            else:
                click.echo(
                    ctx.formatter.success(
                        f"Migration complete. {len(changes_needed)} change(s) applied."
                    )
                )

        except Exception as e:
            click.echo(ctx.formatter.error(f"Migration failed: {e}"), err=True)
            sys.exit(1)


@config.command("reload")
@pass_context
@handle_errors
def config_reload(ctx: CLIContext) -> None:
    """Reload configuration at runtime."""
    with GrpcClient(ctx.grpc_host, ctx.grpc_port) as client:
        result = client.reload_config()

    if result.get("success", False):
        click.echo(ctx.formatter.success("Configuration reloaded successfully."))
    else:
        message = result.get("message", "Failed to reload configuration.")
        click.echo(ctx.formatter.error(message))
        sys.exit(1)


@cli.group()
def log() -> None:
    """View system logs."""
    pass


@log.command("tail")
@click.option("-n", "--lines", type=int, default=20, help="Number of lines to show.")
@click.option(
    "--category",
    type=click.Choice(["system", "commands", "sensors", "errors", "rules"]),
    default="system",
    help="Log category to show.",
)
@pass_context
@handle_errors
def log_tail(ctx: CLIContext, lines: int, category: str) -> None:
    """Show recent log entries."""
    from src.interfaces.rpc.client import GrpcClient

    with GrpcClient(ctx.grpc_host, ctx.grpc_port) as client:
        try:
            result = client.get_log_entries(
                limit=lines, category_filter=category, offset=0
            )
            entries = result["entries"]

            if not entries:
                click.echo("No log entries found.")
                return

            click.echo(f"Last {len(entries)} entries from {category} category:\n")
            for entry in entries:
                timestamp = entry.get("timestamp", "")
                level = entry.get("level", "INFO")
                message = entry.get("message", "")

                level_color = {
                    "DEBUG": "cyan",
                    "INFO": "green",
                    "WARNING": "yellow",
                    "ERROR": "red",
                }.get(level, "white")

                click.echo(
                    f"{timestamp} [{click.style(level, fg=level_color)}] {message}"
                )

        except Exception as e:
            click.echo(ctx.formatter.error(f"Failed to retrieve logs: {e}"), err=True)
            sys.exit(1)


def main() -> None:
    """Main entry point for the CLI."""
    cli(obj=CLIContext())


if __name__ == "__main__":
    main()
