from __future__ import annotations

import importlib
import socket
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner
from streamlit.testing.v1 import AppTest

from src.application import Application, ApplicationConfig, ApplicationState
from src.interfaces.cli import cli
from src.interfaces.web.bridge import OrchestratorBridge

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
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _status_reachable(port: int) -> bool:
    try:
        with urllib.request.urlopen(f"http://localhost:{port}/status", timeout=1):
            return True
    except (OSError, urllib.error.URLError):
        return False


def _wait_for_state(
    app: Application, expected: ApplicationState, timeout: float = 6
) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if app.state == expected:
            return True
        time.sleep(0.1)
    return app.state == expected


@pytest.mark.integration
def test_cli_stop_via_http_endpoint(
    config_directory: Path,
    rules_directory: Path,
    logs_directory: Path,
) -> None:
    port = _find_free_port()

    app = Application(
        ApplicationConfig(
            config_dir=config_directory,
            rules_dir=rules_directory,
            logs_dir=logs_directory,
            skip_mqtt=True,
            skip_ollama=True,
            evaluation_interval=0.1,
        )
    )

    with patch.dict("os.environ", {"IOT_STATUS_PORT": str(port)}, clear=False):
        assert app.start() is True
        assert _status_reachable(port) is True

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "--config-dir",
                str(config_directory),
                "--rules-dir",
                str(rules_directory),
                "--logs-dir",
                str(logs_directory),
                "stop",
            ],
        )

        assert result.exit_code == 0
        assert "stopped" in result.output.lower()
        assert _wait_for_state(app, ApplicationState.STOPPED)
        assert _status_reachable(port) is False


@pytest.mark.integration
def test_web_ui_no_mqtt_connection() -> None:
    sys.modules.pop("src.interfaces.web.bridge", None)
    sys.modules.pop("paho.mqtt", None)
    sys.modules.pop("paho.mqtt.client", None)

    bridge_module = importlib.import_module("src.interfaces.web.bridge")
    bridge = bridge_module.OrchestratorBridge(grpc_host="127.0.0.1", grpc_port=9999)

    assert bridge._grpc_host == "127.0.0.1"
    assert bridge._grpc_port == 9999
    assert "paho.mqtt.client" not in sys.modules


@pytest.mark.integration
def test_bridge_handles_app_not_running() -> None:
    bridge = OrchestratorBridge(grpc_host="127.0.0.1", grpc_port=9999)

    assert bridge.is_app_running() is False
    assert bridge.get_system_status() is None
    assert bridge.shutdown() is False
    assert isinstance(bridge.get_devices(), list)
    assert isinstance(bridge.get_rules(), list)


@pytest.mark.integration
@pytest.mark.parametrize("page_file", PAGE_FILES)
def test_web_pages_render_in_http_only_mode_when_app_not_running(
    page_file: str,
) -> None:
    at = AppTest.from_file(page_file)

    fake_bridge = type(
        "FakeBridge",
        (),
        {
            "is_app_running": lambda _: False,
            "get_system_status": lambda _: None,
            "get_devices": lambda _: [],
            "get_rules": lambda _: [],
            "shutdown": lambda _: False,
        },
    )()

    with patch("src.interfaces.web.bridge.get_bridge", return_value=fake_bridge):
        at.run(timeout=10)

    assert not at.exception


@pytest.mark.integration
@pytest.mark.parametrize("page_file", PAGE_FILES)
def test_web_pages_render_in_http_only_mode_when_app_running(page_file: str) -> None:
    at = AppTest.from_file(page_file)

    fake_bridge = type(
        "FakeBridge",
        (),
        {
            "is_app_running": lambda _: True,
            "get_system_status": lambda _: {
                "state": "running",
                "is_running": True,
                "orchestrator": {"is_ready": True, "components": {}},
            },
            "get_devices": lambda _: [],
            "get_rules": lambda _: [],
            "shutdown": lambda _: True,
        },
    )()

    with patch("src.interfaces.web.bridge.get_bridge", return_value=fake_bridge):
        at.run(timeout=10)

    assert not at.exception
