"""Integration tests for CLI commands using gRPC server.

Tests CLI functionality end-to-end through the gRPC interface.
Uses real gRPC server (not mocked) with mocked MQTT and Ollama backends.
"""

from __future__ import annotations

import socket
import time
from pathlib import Path

import pytest
from click.testing import CliRunner

from src.application import Application, ApplicationConfig, ApplicationState
from src.interfaces.cli import cli

try:
    import grpc  # noqa: F401

    HAS_GRPC = True
except ImportError:
    HAS_GRPC = False

pytestmark = pytest.mark.skipif(not HAS_GRPC, reason="grpc module not installed")


def _find_free_port() -> int:
    """Find an available port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_for_state(
    app: Application, expected: ApplicationState, timeout: float = 6
) -> bool:
    """Wait for application to reach expected state."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if app.state == expected:
            return True
        time.sleep(0.1)
    return app.state == expected


@pytest.fixture
def grpc_port() -> int:
    """Provide a free port for gRPC server."""
    return _find_free_port()


@pytest.fixture
def running_app(
    config_directory: Path,
    rules_directory: Path,
    logs_directory: Path,
    grpc_port: int,
) -> Application:
    """Start Application with gRPC server for integration tests."""
    app = Application(
        ApplicationConfig(
            config_dir=config_directory,
            rules_dir=rules_directory,
            logs_dir=logs_directory,
            grpc_port=grpc_port,
            skip_mqtt=True,
            skip_ollama=True,
            evaluation_interval=0.1,
        )
    )

    assert app.start() is True
    assert _wait_for_state(app, ApplicationState.RUNNING)
    time.sleep(0.2)  # Allow server to fully initialize

    yield app

    # Cleanup
    app.stop()
    assert _wait_for_state(app, ApplicationState.STOPPED)


@pytest.mark.integration
def test_cli_status_via_grpc(
    config_directory: Path,
    rules_directory: Path,
    logs_directory: Path,
    grpc_port: int,
) -> None:
    """Test CLI status command connects via gRPC."""
    app = Application(
        ApplicationConfig(
            config_dir=config_directory,
            rules_dir=rules_directory,
            logs_dir=logs_directory,
            grpc_port=grpc_port,
            skip_mqtt=True,
            skip_ollama=True,
        )
    )

    assert app.start() is True
    assert _wait_for_state(app, ApplicationState.RUNNING)
    time.sleep(0.2)

    try:
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "--grpc-host",
                "localhost",
                "--grpc-port",
                str(grpc_port),
                "status",
            ],
        )

        assert result.exit_code == 0
        # Status output should be JSON-like
        assert "running" in result.output.lower() or "state" in result.output.lower()

    finally:
        app.stop()
        assert _wait_for_state(app, ApplicationState.STOPPED)


@pytest.mark.integration
def test_cli_list_devices_via_grpc(
    config_directory: Path,
    rules_directory: Path,
    logs_directory: Path,
    grpc_port: int,
) -> None:
    """Test CLI list devices command via gRPC."""
    app = Application(
        ApplicationConfig(
            config_dir=config_directory,
            rules_dir=rules_directory,
            logs_dir=logs_directory,
            grpc_port=grpc_port,
            skip_mqtt=True,
            skip_ollama=True,
        )
    )

    assert app.start() is True
    assert _wait_for_state(app, ApplicationState.RUNNING)
    time.sleep(0.2)

    try:
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "--grpc-host",
                "localhost",
                "--grpc-port",
                str(grpc_port),
                "device",
                "list",
            ],
        )

        assert result.exit_code == 0
        # Should list devices (empty or populated from config)
        assert "device" in result.output.lower() or "sensor" in result.output.lower()

    finally:
        app.stop()
        assert _wait_for_state(app, ApplicationState.STOPPED)


@pytest.mark.integration
def test_cli_list_rules_via_grpc(
    config_directory: Path,
    rules_directory: Path,
    logs_directory: Path,
    grpc_port: int,
) -> None:
    """Test CLI list rules command via gRPC."""
    app = Application(
        ApplicationConfig(
            config_dir=config_directory,
            rules_dir=rules_directory,
            logs_dir=logs_directory,
            grpc_port=grpc_port,
            skip_mqtt=True,
            skip_ollama=True,
        )
    )

    assert app.start() is True
    assert _wait_for_state(app, ApplicationState.RUNNING)
    time.sleep(0.2)

    try:
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "--grpc-host",
                "localhost",
                "--grpc-port",
                str(grpc_port),
                "rule",
                "list",
            ],
        )

        assert result.exit_code == 0
        # Should list rules output
        assert "rule" in result.output.lower() or "id" in result.output.lower()

    finally:
        app.stop()
        assert _wait_for_state(app, ApplicationState.STOPPED)


@pytest.mark.integration
def test_cli_add_rule_via_grpc(
    config_directory: Path,
    rules_directory: Path,
    logs_directory: Path,
    grpc_port: int,
) -> None:
    """Test CLI add rule command via gRPC."""
    app = Application(
        ApplicationConfig(
            config_dir=config_directory,
            rules_dir=rules_directory,
            logs_dir=logs_directory,
            grpc_port=grpc_port,
            skip_mqtt=True,
            skip_ollama=True,
        )
    )

    assert app.start() is True
    assert _wait_for_state(app, ApplicationState.RUNNING)
    time.sleep(0.2)

    try:
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "--grpc-host",
                "localhost",
                "--grpc-port",
                str(grpc_port),
                "rule",
                "add",
                "If temperature is high, turn on AC",
            ],
        )

        assert result.exit_code == 0
        assert "added" in result.output.lower() or "success" in result.output.lower()

    finally:
        app.stop()
        assert _wait_for_state(app, ApplicationState.STOPPED)


@pytest.mark.integration
def test_cli_get_config_via_grpc(
    config_directory: Path,
    rules_directory: Path,
    logs_directory: Path,
    grpc_port: int,
) -> None:
    """Test CLI get config command via gRPC."""
    app = Application(
        ApplicationConfig(
            config_dir=config_directory,
            rules_dir=rules_directory,
            logs_dir=logs_directory,
            grpc_port=grpc_port,
            skip_mqtt=True,
            skip_ollama=True,
        )
    )

    assert app.start() is True
    assert _wait_for_state(app, ApplicationState.RUNNING)
    time.sleep(0.2)

    try:
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "--grpc-host",
                "localhost",
                "--grpc-port",
                str(grpc_port),
                "config",
                "validate",
            ],
        )

        assert result.exit_code == 0
        # Should return config validation output
        assert (
            "valid" in result.output.lower()
            or "config" in result.output.lower()
            or "ok" in result.output.lower()
        )

    finally:
        app.stop()
        assert _wait_for_state(app, ApplicationState.STOPPED)


@pytest.mark.integration
def test_cli_get_logs_via_grpc(
    config_directory: Path,
    rules_directory: Path,
    logs_directory: Path,
    grpc_port: int,
) -> None:
    """Test CLI get logs command via gRPC."""
    app = Application(
        ApplicationConfig(
            config_dir=config_directory,
            rules_dir=rules_directory,
            logs_dir=logs_directory,
            grpc_port=grpc_port,
            skip_mqtt=True,
            skip_ollama=True,
        )
    )

    assert app.start() is True
    assert _wait_for_state(app, ApplicationState.RUNNING)
    time.sleep(0.2)

    try:
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "--grpc-host",
                "localhost",
                "--grpc-port",
                str(grpc_port),
                "log",
                "tail",
            ],
        )

        assert result.exit_code == 0
        # Should return logs (may be empty or populated)
        assert "log" in result.output.lower() or result.output.strip() != ""

    finally:
        app.stop()
        assert _wait_for_state(app, ApplicationState.STOPPED)


@pytest.mark.integration
def test_cli_default_grpc_host_port(
    config_directory: Path,
    rules_directory: Path,
    logs_directory: Path,
) -> None:
    """Test CLI uses default gRPC port 50051."""
    # Use default port
    app = Application(
        ApplicationConfig(
            config_dir=config_directory,
            rules_dir=rules_directory,
            logs_dir=logs_directory,
            skip_mqtt=True,
            skip_ollama=True,
        )
    )

    assert app.start() is True
    assert _wait_for_state(app, ApplicationState.RUNNING)
    time.sleep(0.2)

    try:
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "status",
            ],
        )

        # Should connect to default port 50051
        assert result.exit_code == 0

    finally:
        app.stop()
        assert _wait_for_state(app, ApplicationState.STOPPED)


@pytest.mark.integration
def test_cli_grpc_connection_error(
    config_directory: Path,
    rules_directory: Path,
    logs_directory: Path,
) -> None:
    """Test CLI gracefully handles gRPC connection error."""
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "--grpc-host",
            "localhost",
            "--grpc-port",
            "9999",  # Port with no service
            "status",
        ],
    )

    # Should fail with non-zero exit code
    assert result.exit_code != 0
    # Should show error about connection
    assert (
        "error" in result.output.lower()
        or "connection" in result.output.lower()
        or "unavailable" in result.output.lower()
    )


@pytest.mark.integration
def test_cli_multiple_commands_same_session(
    config_directory: Path,
    rules_directory: Path,
    logs_directory: Path,
    grpc_port: int,
) -> None:
    """Test multiple CLI commands work with same gRPC server."""
    app = Application(
        ApplicationConfig(
            config_dir=config_directory,
            rules_dir=rules_directory,
            logs_dir=logs_directory,
            grpc_port=grpc_port,
            skip_mqtt=True,
            skip_ollama=True,
        )
    )

    assert app.start() is True
    assert _wait_for_state(app, ApplicationState.RUNNING)
    time.sleep(0.2)

    try:
        runner = CliRunner()

        # First command
        result1 = runner.invoke(
            cli,
            [
                "--grpc-host",
                "localhost",
                "--grpc-port",
                str(grpc_port),
                "status",
            ],
        )
        assert result1.exit_code == 0

        # Second command
        result2 = runner.invoke(
            cli,
            [
                "--grpc-host",
                "localhost",
                "--grpc-port",
                str(grpc_port),
                "device",
                "list",
            ],
        )
        assert result2.exit_code == 0

        # Third command
        result3 = runner.invoke(
            cli,
            [
                "--grpc-host",
                "localhost",
                "--grpc-port",
                str(grpc_port),
                "rule",
                "list",
            ],
        )
        assert result3.exit_code == 0

    finally:
        app.stop()
        assert _wait_for_state(app, ApplicationState.STOPPED)
