"""Command Line Interface for the Fuzzy-LLM Hybrid IoT Management System.

This module provides a CLI for system administration, rule management,
device monitoring, and configuration management.
"""

from __future__ import annotations

import json
import os
import sys
import textwrap
import urllib.error
import urllib.request
from pathlib import Path
from typing import TYPE_CHECKING, Any

import click

from src.common.exceptions import ConfigurationError, RuleError
from src.common.logging import get_logger

if TYPE_CHECKING:
    from src.configuration.system_orchestrator import SystemOrchestrator

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
        self._orchestrator: SystemOrchestrator | None = None

    @property
    def orchestrator(self) -> SystemOrchestrator:
        """Get or create the system orchestrator."""
        if self._orchestrator is None:
            from src.configuration.system_orchestrator import SystemOrchestrator

            self._orchestrator = SystemOrchestrator(
                config_dir=self.config_dir,
                rules_dir=self.rules_dir,
                logs_dir=self.logs_dir,
            )
        return self._orchestrator

    def get_initialized_orchestrator(self) -> SystemOrchestrator | None:
        """Get orchestrator only if it's been initialized."""
        if self._orchestrator is None:
            return None
        if not self._orchestrator.is_ready:
            return None
        return self._orchestrator


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
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output.")
@click.version_option(version="0.1.0", prog_name="iot-fuzzy-llm")
@click.pass_context
def cli(
    ctx: click.Context,
    config_dir: Path,
    rules_dir: Path,
    logs_dir: Path,
    output_format: str,
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

    orchestrator = ctx.orchestrator
    result = orchestrator.initialize(skip_mqtt=skip_mqtt, skip_ollama=skip_ollama)

    if result:
        click.echo(ctx.formatter.success("System started successfully."))
        # Show initialization steps
        steps = orchestrator.initialization_steps
        if ctx.verbose:
            click.echo("\nInitialization steps:")
            for step in steps:
                status = "✓" if step.completed else "✗"
                click.echo(f"  {status} {step.name}: {step.description}")
    else:
        click.echo(ctx.formatter.error("System failed to start."))
        # Show failed steps
        steps = orchestrator.initialization_steps
        for step in steps:
            if step.error:
                click.echo(f"  ✗ {step.name}: {step.error}")
        sys.exit(1)


@cli.command()
@pass_context
@handle_errors
def stop(ctx: CLIContext) -> None:
    """Stop the IoT management system."""
    click.echo(ctx.formatter.info("Stopping system..."))

    orchestrator = ctx.get_initialized_orchestrator()
    if orchestrator is None:
        click.echo(ctx.formatter.warning("System is not running."))
        return

    result = orchestrator.shutdown()
    if result:
        click.echo(ctx.formatter.success("System stopped successfully."))
    else:
        click.echo(ctx.formatter.error("Failed to stop system."))
        sys.exit(1)


@cli.command()
@pass_context
@handle_errors
def status(ctx: CLIContext) -> None:
    """Display system status."""
    status_port = os.getenv("IOT_STATUS_PORT", "8080")
    status_url = f"http://localhost:{status_port}/status"
    status_data: dict[str, Any] | None = None
    status_source = "standalone"

    try:
        with urllib.request.urlopen(status_url, timeout=2) as response:
            if response.status == 200:
                status_data = json.loads(response.read().decode("utf-8"))
                status_source = "running"
    except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
        logger.debug("Status endpoint unavailable", extra={"error": str(exc)})

    if status_data is None:
        orchestrator = ctx.orchestrator
        status_data = orchestrator.get_system_status()

    if ctx.output_format == "json":
        if status_source == "running":
            status_data = {"source": "running", **status_data}
        else:
            status_data = {"source": "standalone", **status_data}
        click.echo(ctx.formatter.format_json(status_data))
        return

    if status_source == "running":
        click.echo(ctx.formatter.success("Connected to running application."))
    else:
        click.echo(ctx.formatter.warning("Running in standalone status mode."))

    # Display status - handle both remote and standalone response shapes
    state = status_data.get("state", "unknown")
    is_ready = status_data.get("is_ready")
    if is_ready is None:
        # Remote response has is_ready nested under orchestrator
        is_ready = status_data.get("orchestrator", {}).get("is_ready", False)

    click.echo(f"System State: {state.upper()}")
    click.echo(f"Ready: {'Yes' if is_ready else 'No'}")

    # Component status - handle both response shapes
    click.echo("\nComponents:")
    components = status_data.get("components")
    if components is None:
        components = status_data.get("orchestrator", {}).get("components", {})
    for name, available in components.items():
        status_icon = "✓" if available else "✗"
        status_color = "green" if available else "red"
        click.echo(
            f"  {status_icon} {name}: "
            + click.style("available" if available else "unavailable", fg=status_color)
        )

    # Initialization steps (if any)
    steps = status_data.get("initialization_steps")
    if steps is None:
        steps = status_data.get("orchestrator", {}).get("initialization_steps", [])

    if steps and ctx.verbose:
        click.echo("\nInitialization Steps:")
        for step in steps:
            status_icon = "✓" if step["completed"] else "✗"
            click.echo(f"  {status_icon} {step['name']}: {step['description']}")
            if step.get("error"):
                click.echo(click.style(f"      Error: {step['error']}", fg="red"))


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
    import uuid

    from src.configuration.rule_manager import RuleManager

    rules_file = ctx.rules_dir / "active_rules.json"
    manager = RuleManager(rules_file=rules_file, auto_save=True)

    if rule_id is None:
        rule_id = f"rule_{uuid.uuid4().hex[:8]}"

    metadata: dict[str, Any] = {}
    if tag:
        metadata["tags"] = list(tag)

    rule_obj = manager.add_rule(
        rule_id=rule_id,
        rule_text=text,
        priority=priority,
        enabled=True,
        metadata=metadata,
    )

    if ctx.output_format == "json":
        click.echo(ctx.formatter.format_json(rule_obj.to_dict()))
    else:
        click.echo(ctx.formatter.success(f"Rule added with ID: {rule_obj.rule_id}"))
        click.echo(f"  Text: {rule_obj.rule_text}")
        click.echo(f"  Priority: {rule_obj.priority}")
        tags = rule_obj.metadata.get("tags", [])
        if tags:
            click.echo(f"  Tags: {', '.join(tags)}")


@rule.command("list")
@click.option("--enabled-only", is_flag=True, help="Show only enabled rules.")
@click.option("--tag", "-t", help="Filter by tag.")
@pass_context
@handle_errors
def rule_list(ctx: CLIContext, enabled_only: bool, tag: str | None) -> None:
    """List all rules."""
    from src.configuration.rule_manager import RuleManager

    rules_file = ctx.rules_dir / "active_rules.json"
    manager = RuleManager(rules_file=rules_file, auto_save=False)

    rules = manager.get_enabled_rules() if enabled_only else manager.get_all_rules()

    if tag:
        rules = [r for r in rules if tag in r.metadata.get("tags", [])]

    if ctx.output_format == "json":
        click.echo(ctx.formatter.format_json([r.to_dict() for r in rules]))
        return

    if not rules:
        click.echo("No rules found.")
        return

    headers = ["ID", "Enabled", "Priority", "Text", "Tags"]
    rows = []
    for r in rules:
        tags = r.metadata.get("tags", [])
        tags_str = ", ".join(tags) if tags else ""
        rows.append(
            [
                r.rule_id,
                "Yes" if r.enabled else "No",
                str(r.priority),
                r.rule_text,
                tags_str,
            ]
        )

    text_column_wrap_width = 50
    max_widths = [0, 0, 0, text_column_wrap_width, 0]
    click.echo(
        ctx.formatter.format_table(
            headers, rows, max_widths=max_widths, row_separator=True
        )
    )
    click.echo(f"\nTotal: {len(rules)} rule(s)")


@rule.command("show")
@click.argument("rule_id")
@pass_context
@handle_errors
def rule_show(ctx: CLIContext, rule_id: str) -> None:
    """Show detailed information about a rule."""
    from src.configuration.rule_manager import RuleManager

    rules_file = ctx.rules_dir / "active_rules.json"
    manager = RuleManager(rules_file=rules_file, auto_save=False)

    rule_obj = manager.get_rule_optional(rule_id)
    if rule_obj is None:
        click.echo(ctx.formatter.error(f"Rule not found: {rule_id}"))
        sys.exit(1)

    if ctx.output_format == "json":
        click.echo(ctx.formatter.format_json(rule_obj.to_dict()))
        return

    tags = rule_obj.metadata.get("tags", [])
    click.echo(f"Rule ID: {rule_obj.rule_id}")
    click.echo(f"Text: {rule_obj.rule_text}")
    click.echo(f"Enabled: {'Yes' if rule_obj.enabled else 'No'}")
    click.echo(f"Priority: {rule_obj.priority}")
    click.echo(f"Tags: {', '.join(tags) if tags else 'None'}")
    click.echo(f"Created: {rule_obj.created_timestamp or 'N/A'}")
    click.echo(f"Trigger Count: {rule_obj.trigger_count}")
    if rule_obj.last_triggered:
        click.echo(f"Last Triggered: {rule_obj.last_triggered}")


@rule.command("enable")
@click.argument("rule_id")
@pass_context
@handle_errors
def rule_enable(ctx: CLIContext, rule_id: str) -> None:
    """Enable a rule."""
    from src.configuration.rule_manager import RuleManager

    rules_file = ctx.rules_dir / "active_rules.json"
    manager = RuleManager(rules_file=rules_file, auto_save=True)

    if not manager.contains(rule_id):
        click.echo(ctx.formatter.error(f"Rule not found: {rule_id}"))
        sys.exit(1)

    manager.enable_rule(rule_id)
    click.echo(ctx.formatter.success(f"Rule {rule_id} enabled."))


@rule.command("disable")
@click.argument("rule_id")
@pass_context
@handle_errors
def rule_disable(ctx: CLIContext, rule_id: str) -> None:
    """Disable a rule."""
    from src.configuration.rule_manager import RuleManager

    rules_file = ctx.rules_dir / "active_rules.json"
    manager = RuleManager(rules_file=rules_file, auto_save=True)

    if not manager.contains(rule_id):
        click.echo(ctx.formatter.error(f"Rule not found: {rule_id}"))
        sys.exit(1)

    manager.disable_rule(rule_id)
    click.echo(ctx.formatter.success(f"Rule {rule_id} disabled."))


@rule.command("delete")
@click.argument("rule_id")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation.")
@pass_context
@handle_errors
def rule_delete(ctx: CLIContext, rule_id: str, yes: bool) -> None:
    """Delete a rule."""
    from src.configuration.rule_manager import RuleManager

    rules_file = ctx.rules_dir / "active_rules.json"
    manager = RuleManager(rules_file=rules_file, auto_save=True)

    rule_obj = manager.get_rule_optional(rule_id)
    if rule_obj is None:
        click.echo(ctx.formatter.error(f"Rule not found: {rule_id}"))
        sys.exit(1)

    if not yes:
        text_preview = (
            rule_obj.rule_text[:50] + "..."
            if len(rule_obj.rule_text) > 50
            else rule_obj.rule_text
        )
        click.echo(f"Rule to delete: {text_preview}")
        if not click.confirm("Are you sure you want to delete this rule?"):
            click.echo("Cancelled.")
            return

    result = manager.delete_rule(rule_id)
    if result:
        click.echo(ctx.formatter.success(f"Rule {rule_id} deleted."))
    else:
        click.echo(ctx.formatter.error(f"Failed to delete rule: {rule_id}"))
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
    from src.common.config import ConfigLoader
    from src.device_interface.registry import DeviceRegistry

    config_loader = ConfigLoader(config_dir=ctx.config_dir)
    registry = DeviceRegistry(config_loader=config_loader)

    try:
        registry.load("devices.json")
    except FileNotFoundError:
        click.echo(ctx.formatter.error("devices.json not found in config directory."))
        sys.exit(1)

    sensors = registry.sensors()

    if ctx.output_format == "json":
        data = [
            {
                "id": s.id,
                "name": s.name,
                "device_class": s.device_class,
                "location": s.location,
                "unit": s.unit,
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
                s.id,
                s.name[:25] if len(s.name) > 25 else s.name,
                s.device_class,
                s.location or "-",
                s.unit or "-",
            ]
        )

    click.echo(ctx.formatter.format_table(headers, rows))
    click.echo(f"\nTotal: {len(sensors)} sensor(s)")


@sensor.command("status")
@click.argument("sensor_id", required=False)
@pass_context
@handle_errors
def sensor_status(ctx: CLIContext, sensor_id: str | None) -> None:
    """Show sensor status and readings.

    If SENSOR_ID is not provided, shows status for all sensors.
    """
    from src.common.config import ConfigLoader
    from src.device_interface.registry import DeviceRegistry

    config_loader = ConfigLoader(config_dir=ctx.config_dir)
    registry = DeviceRegistry(config_loader=config_loader)

    try:
        registry.load("devices.json")
    except FileNotFoundError:
        click.echo(ctx.formatter.error("devices.json not found in config directory."))
        sys.exit(1)

    sensors = registry.sensors()

    if sensor_id:
        sensors = [s for s in sensors if s.id == sensor_id]
        if not sensors:
            click.echo(ctx.formatter.error(f"Sensor not found: {sensor_id}"))
            sys.exit(1)

    if ctx.output_format == "json":
        data = [
            {
                "id": s.id,
                "name": s.name,
                "device_class": s.device_class,
                "location": s.location,
                "unit": s.unit,
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
        click.echo(f"\n{s.name} ({s.id})")
        click.echo(f"  Class: {s.device_class}")
        click.echo(f"  Location: {s.location or 'N/A'}")
        click.echo(f"  Unit: {s.unit or 'N/A'}")
        click.echo("  Status: registered")
        if s.mqtt:
            click.echo(f"  MQTT Topic: {s.mqtt.topic}")


@cli.group()
def device() -> None:
    """View device information and status."""
    pass


@device.command("list")
@pass_context
@handle_errors
def device_list(ctx: CLIContext) -> None:
    """List all registered devices."""
    from src.common.config import ConfigLoader
    from src.device_interface.registry import DeviceRegistry

    config_loader = ConfigLoader(config_dir=ctx.config_dir)
    registry = DeviceRegistry(config_loader=config_loader)

    try:
        registry.load("devices.json")
    except FileNotFoundError:
        click.echo(ctx.formatter.error("devices.json not found in config directory."))
        sys.exit(1)

    devices = list(registry)

    if ctx.output_format == "json":
        data = [
            {
                "id": d.id,
                "name": d.name,
                "type": d.device_type.value,
                "device_class": d.device_class,
                "location": d.location,
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
                d.id,
                d.name[:25] if len(d.name) > 25 else d.name,
                d.device_type.value,
                d.device_class,
                d.location or "-",
            ]
        )

    click.echo(ctx.formatter.format_table(headers, rows))
    click.echo(f"\nTotal: {len(devices)} device(s)")


@device.command("status")
@click.argument("device_id", required=False)
@pass_context
@handle_errors
def device_status(ctx: CLIContext, device_id: str | None) -> None:
    """Show device status and capabilities.

    If DEVICE_ID is not provided, shows status for all devices.
    """
    from src.common.config import ConfigLoader
    from src.device_interface.models import Actuator
    from src.device_interface.registry import DeviceRegistry

    config_loader = ConfigLoader(config_dir=ctx.config_dir)
    registry = DeviceRegistry(config_loader=config_loader)

    try:
        registry.load("devices.json")
    except FileNotFoundError:
        click.echo(ctx.formatter.error("devices.json not found in config directory."))
        sys.exit(1)

    devices = list(registry)

    if device_id:
        devices = [d for d in devices if d.id == device_id]
        if not devices:
            click.echo(ctx.formatter.error(f"Device not found: {device_id}"))
            sys.exit(1)

    if ctx.output_format == "json":
        data: list[dict[str, Any]] = []
        for d in devices:
            item: dict[str, Any] = {
                "id": d.id,
                "name": d.name,
                "type": d.device_type.value,
                "device_class": d.device_class,
                "location": d.location,
                "status": "registered",
            }
            if isinstance(d, Actuator):
                item["capabilities"] = list(d.capabilities)
            data.append(item)
        click.echo(ctx.formatter.format_json(data))
        return

    if not devices:
        click.echo("No devices found.")
        return

    for d in devices:
        click.echo(f"\n{d.name} ({d.id})")
        click.echo(f"  Type: {d.device_type.value}")
        click.echo(f"  Class: {d.device_class}")
        click.echo(f"  Location: {d.location or 'N/A'}")
        click.echo("  Status: registered")
        if isinstance(d, Actuator):
            click.echo(f"  Capabilities: {', '.join(d.capabilities)}")
        if d.mqtt:
            click.echo(f"  MQTT Topic: {d.mqtt.topic}")
            if d.mqtt.command_topic:
                click.echo(f"  Command Topic: {d.mqtt.command_topic}")


@cli.group()
def config() -> None:
    """Manage configuration files."""
    pass


@config.command("validate")
@pass_context
@handle_errors
def config_validate(ctx: CLIContext) -> None:
    """Validate all configuration files."""
    from src.configuration.config_manager import ConfigurationManager

    click.echo(ctx.formatter.info("Validating configuration files..."))

    try:
        manager = ConfigurationManager(config_dir=ctx.config_dir)
        configs = manager.get_all_configs()

        click.echo(ctx.formatter.success("All configuration files are valid."))
        click.echo("\nLoaded configurations:")
        for name in configs:
            click.echo(f"  ✓ {name}")

    except ConfigurationError as e:
        click.echo(ctx.formatter.error(f"Validation failed: {e}"))
        sys.exit(1)


@config.command("reload")
@pass_context
@handle_errors
def config_reload(ctx: CLIContext) -> None:
    """Reload configuration at runtime."""
    orchestrator = ctx.get_initialized_orchestrator()
    if orchestrator is None:
        click.echo(ctx.formatter.warning("System is not running. Nothing to reload."))
        return

    config_manager = orchestrator.config_manager
    if config_manager is None:
        click.echo(ctx.formatter.error("Configuration manager not available."))
        sys.exit(1)

    config_manager.reload()
    click.echo(ctx.formatter.success("Configuration reloaded successfully."))


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
    log_file = ctx.logs_dir / f"{category}.log"

    if not log_file.exists():
        click.echo(ctx.formatter.warning(f"Log file not found: {log_file}"))
        return

    # Read last N lines
    with open(log_file) as f:
        all_lines = f.readlines()
        recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines

    if not recent_lines:
        click.echo("No log entries found.")
        return

    click.echo(f"Last {len(recent_lines)} entries from {category}.log:\n")
    for line in recent_lines:
        # Try to parse as JSON for better formatting
        try:
            entry = json.loads(line.strip())
            timestamp = entry.get("timestamp", "")
            level = entry.get("level", "INFO")
            message = entry.get("message", line.strip())

            level_color = {
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
            }.get(level, "white")

            click.echo(f"{timestamp} [{click.style(level, fg=level_color)}] {message}")
        except json.JSONDecodeError:
            click.echo(line.strip())


def main() -> None:
    """Main entry point for the CLI."""
    cli(obj=CLIContext())


if __name__ == "__main__":
    main()
