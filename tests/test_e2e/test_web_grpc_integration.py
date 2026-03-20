"""Integration tests for Web UI pages using gRPC server.

Tests Web UI functionality end-to-end through the gRPC interface.
Uses Streamlit AppTest with real gRPC server (not mocked MQTT/Ollama).
"""

from __future__ import annotations

import socket
import time
from pathlib import Path
from unittest.mock import patch

import pytest
from streamlit.testing.v1 import AppTest

from src.application import Application, ApplicationConfig, ApplicationState

try:
    import grpc  # noqa: F401

    HAS_GRPC = True
except ImportError:
    HAS_GRPC = False

pytestmark = pytest.mark.skipif(not HAS_GRPC, reason="grpc module not installed")

PAGE_FILES = [
    "src/interfaces/web/pages/dashboard.py",
    "src/interfaces/web/pages/devices.py",
    "src/interfaces/web/pages/rules.py",
    "src/interfaces/web/pages/config.py",
    "src/interfaces/web/pages/membership_editor.py",
    "src/interfaces/web/pages/logs.py",
    "src/interfaces/web/pages/system_control.py",
]


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
    time.sleep(0.2)

    yield app

    app.stop()
    assert _wait_for_state(app, ApplicationState.STOPPED)


@pytest.mark.integration
def test_web_dashboard_loads_via_grpc(
    config_directory: Path,
    rules_directory: Path,
    logs_directory: Path,
    grpc_port: int,
) -> None:
    """Test dashboard page loads and connects via gRPC."""
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
        at = AppTest.from_file("src/interfaces/web/pages/dashboard.py")
        with patch.dict(
            "os.environ", {"STREAMLIT_GRPC_PORT": str(grpc_port)}, clear=False
        ):
            at.run(timeout=10)

        assert not at.exception, f"Streamlit error: {at.exception}"

    finally:
        app.stop()
        assert _wait_for_state(app, ApplicationState.STOPPED)


@pytest.mark.integration
def test_web_devices_page_loads_via_grpc(
    config_directory: Path,
    rules_directory: Path,
    logs_directory: Path,
    grpc_port: int,
) -> None:
    """Test devices page loads via gRPC."""
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
        at = AppTest.from_file("src/interfaces/web/pages/devices.py")
        with patch.dict(
            "os.environ", {"STREAMLIT_GRPC_PORT": str(grpc_port)}, clear=False
        ):
            at.run(timeout=10)

        assert not at.exception, f"Streamlit error: {at.exception}"

    finally:
        app.stop()
        assert _wait_for_state(app, ApplicationState.STOPPED)


@pytest.mark.integration
def test_web_rules_page_loads_via_grpc(
    config_directory: Path,
    rules_directory: Path,
    logs_directory: Path,
    grpc_port: int,
) -> None:
    """Test rules page loads via gRPC."""
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
        at = AppTest.from_file("src/interfaces/web/pages/rules.py")
        with patch.dict(
            "os.environ", {"STREAMLIT_GRPC_PORT": str(grpc_port)}, clear=False
        ):
            at.run(timeout=10)

        assert not at.exception, f"Streamlit error: {at.exception}"

    finally:
        app.stop()
        assert _wait_for_state(app, ApplicationState.STOPPED)


@pytest.mark.integration
def test_web_config_page_loads_via_grpc(
    config_directory: Path,
    rules_directory: Path,
    logs_directory: Path,
    grpc_port: int,
) -> None:
    """Test config page loads via gRPC."""
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
        at = AppTest.from_file("src/interfaces/web/pages/config.py")
        with patch.dict(
            "os.environ", {"STREAMLIT_GRPC_PORT": str(grpc_port)}, clear=False
        ):
            at.run(timeout=10)

        assert not at.exception, f"Streamlit error: {at.exception}"

    finally:
        app.stop()
        assert _wait_for_state(app, ApplicationState.STOPPED)


@pytest.mark.integration
def test_web_logs_page_loads_via_grpc(
    config_directory: Path,
    rules_directory: Path,
    logs_directory: Path,
    grpc_port: int,
) -> None:
    """Test logs page loads via gRPC."""
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
        at = AppTest.from_file("src/interfaces/web/pages/logs.py")
        with patch.dict(
            "os.environ", {"STREAMLIT_GRPC_PORT": str(grpc_port)}, clear=False
        ):
            at.run(timeout=10)

        assert not at.exception, f"Streamlit error: {at.exception}"

    finally:
        app.stop()
        assert _wait_for_state(app, ApplicationState.STOPPED)


@pytest.mark.integration
def test_web_membership_editor_page_loads_via_grpc(
    config_directory: Path,
    rules_directory: Path,
    logs_directory: Path,
    grpc_port: int,
) -> None:
    """Test membership editor page loads via gRPC."""
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
        at = AppTest.from_file("src/interfaces/web/pages/membership_editor.py")
        with patch.dict(
            "os.environ", {"STREAMLIT_GRPC_PORT": str(grpc_port)}, clear=False
        ):
            at.run(timeout=10)

        assert not at.exception, f"Streamlit error: {at.exception}"

    finally:
        app.stop()
        assert _wait_for_state(app, ApplicationState.STOPPED)


@pytest.mark.integration
def test_web_system_control_page_loads_via_grpc(
    config_directory: Path,
    rules_directory: Path,
    logs_directory: Path,
    grpc_port: int,
) -> None:
    """Test system control page loads via gRPC."""
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
        at = AppTest.from_file("src/interfaces/web/pages/system_control.py")
        with patch.dict(
            "os.environ", {"STREAMLIT_GRPC_PORT": str(grpc_port)}, clear=False
        ):
            at.run(timeout=10)

        assert not at.exception, f"Streamlit error: {at.exception}"

    finally:
        app.stop()
        assert _wait_for_state(app, ApplicationState.STOPPED)


@pytest.mark.integration
def test_web_all_pages_with_same_grpc_server(
    config_directory: Path,
    rules_directory: Path,
    logs_directory: Path,
    grpc_port: int,
) -> None:
    """Test all pages load with same gRPC server instance."""
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
        page_files = [
            "src/interfaces/web/pages/dashboard.py",
            "src/interfaces/web/pages/devices.py",
            "src/interfaces/web/pages/rules.py",
        ]

        for page_file in page_files:
            at = AppTest.from_file(page_file)
            with patch.dict(
                "os.environ", {"STREAMLIT_GRPC_PORT": str(grpc_port)}, clear=False
            ):
                at.run(timeout=10)

            assert not at.exception, f"Page {page_file} error: {at.exception}"

    finally:
        app.stop()
        assert _wait_for_state(app, ApplicationState.STOPPED)


@pytest.mark.integration
def test_web_page_graceful_error_when_grpc_unavailable(
    config_directory: Path,
    rules_directory: Path,
    logs_directory: Path,
) -> None:
    """Test web pages show graceful error when gRPC server is unavailable."""
    at = AppTest.from_file("src/interfaces/web/pages/dashboard.py")
    with patch.dict("os.environ", {"STREAMLIT_GRPC_PORT": "9999"}, clear=False):
        at.run(timeout=10)

    assert not at.exception, f"Streamlit error: {at.exception}"
