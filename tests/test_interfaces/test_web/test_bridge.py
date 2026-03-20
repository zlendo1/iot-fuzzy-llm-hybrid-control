from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from src.interfaces.web.bridge import OrchestratorBridge


def test_get_system_status_returns_http_status_payload() -> None:
    bridge = OrchestratorBridge()
    expected = {"state": "running", "is_running": True, "orchestrator": {}}

    with patch.object(
        bridge._http_client, "get_status", return_value=expected
    ) as mocked:
        result = bridge.get_system_status()

    assert result == expected
    mocked.assert_called_once_with()


def test_is_app_running_proxies_http_client() -> None:
    bridge = OrchestratorBridge()

    with patch.object(
        bridge._http_client,
        "is_app_running",
        return_value=False,
    ) as mocked:
        assert bridge.is_app_running() is False

    mocked.assert_called_once_with()


def test_get_devices_prefers_status_orchestrator_devices() -> None:
    bridge = OrchestratorBridge()
    expected_devices = [{"id": "temp_1"}, {"id": "ac_1"}]

    with patch.object(
        bridge,
        "get_system_status",
        return_value={"orchestrator": {"devices": expected_devices}},
    ):
        result = bridge.get_devices()

    assert result == expected_devices


def test_get_devices_falls_back_to_devices_file(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    config_dir.mkdir(parents=True)
    devices_path = config_dir / "devices.json"
    payload = {"devices": [{"id": "from_config"}]}
    devices_path.write_text(json.dumps(payload), encoding="utf-8")

    bridge = OrchestratorBridge()
    bridge._config_dir = config_dir

    with patch.object(bridge, "get_system_status", return_value=None):
        result = bridge.get_devices()

    assert result == payload["devices"]


def test_get_rules_reads_active_rules_file(tmp_path: Path) -> None:
    rules_dir = tmp_path / "rules"
    rules_dir.mkdir(parents=True)
    rules_path = rules_dir / "active_rules.json"
    payload = {"rules": [{"rule_id": "r1", "rule_text": "If hot, turn on AC"}]}
    rules_path.write_text(json.dumps(payload), encoding="utf-8")

    bridge = OrchestratorBridge()
    bridge._rules_dir = rules_dir

    assert bridge.get_rules() == payload["rules"]


def test_shutdown_calls_http_client_shutdown() -> None:
    bridge = OrchestratorBridge()

    with patch.object(bridge._http_client, "shutdown", return_value=True) as mocked:
        result = bridge.shutdown()

    assert result is True
    mocked.assert_called_once_with()


def test_graceful_when_app_not_running() -> None:
    bridge = OrchestratorBridge()

    with patch.object(bridge._http_client, "is_app_running", return_value=False):
        assert bridge.is_app_running() is False

    with patch.object(bridge, "get_system_status", return_value=None):
        devices = bridge.get_devices()

    assert isinstance(devices, list)


def test_get_bridge_returns_cached_instance() -> None:
    from src.interfaces.web import bridge as bridge_module

    bridge_module.get_bridge.clear()
    with patch.object(bridge_module, "OrchestratorBridge") as mocked_bridge:
        first = bridge_module.get_bridge()
        second = bridge_module.get_bridge()

    assert first is second
    mocked_bridge.assert_called_once_with()
