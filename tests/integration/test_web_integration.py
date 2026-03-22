from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from streamlit.testing.v1 import AppTest

PAGES: tuple[tuple[str, str], ...] = (
    ("dashboard", "src/interfaces/web/pages/dashboard.py"),
    ("devices", "src/interfaces/web/pages/devices.py"),
    ("rules", "src/interfaces/web/pages/rules.py"),
    ("config", "src/interfaces/web/pages/config.py"),
    ("membership_editor", "src/interfaces/web/pages/membership_editor.py"),
    ("logs", "src/interfaces/web/pages/logs.py"),
)


def _build_bridge_mock() -> MagicMock:
    mock_bridge = MagicMock()

    mock_bridge.is_app_running.return_value = True
    mock_bridge.get_devices.return_value = []
    mock_bridge.get_rules.return_value = []
    mock_bridge.get_config.return_value = {"key": "value"}
    mock_bridge.list_configs.return_value = []
    mock_bridge.validate_config.return_value = {"valid": True, "errors": []}
    mock_bridge.reload_config.return_value = {"success": True}
    mock_bridge.get_system_status.return_value = {
        "state": "running",
        "is_running": True,
        "orchestrator": {"is_ready": True, "components": {}},
    }
    mock_bridge.get_status.return_value = {
        "status": "RUNNING",
        "uptime_seconds": 10,
        "version": "0.1.0",
    }
    mock_bridge.shutdown.return_value = True
    mock_bridge.list_sensor_types.return_value = []
    mock_bridge.get_membership_functions.return_value = {}
    mock_bridge.update_membership_function.return_value = {"success": True}
    mock_bridge.get_log_entries.return_value = {"entries": [], "total_count": 0}
    mock_bridge.get_log_categories.return_value = []
    mock_bridge.get_log_stats.return_value = {}
    mock_bridge.add_rule.return_value = {"id": "r1", "text": "test", "enabled": True}
    mock_bridge.remove_rule.return_value = True
    mock_bridge.enable_rule.return_value = True
    mock_bridge.disable_rule.return_value = True
    mock_bridge.update_config.return_value = {"success": True}

    return mock_bridge


@pytest.mark.integration
@pytest.mark.parametrize("module_name,_path", PAGES)
def test_page_modules_importable(module_name: str, _path: str) -> None:
    module = __import__(f"src.interfaces.web.pages.{module_name}", fromlist=["render"])
    assert hasattr(module, "render")


@pytest.mark.integration
@pytest.mark.parametrize("module_name,_path", PAGES)
def test_page_render_callable(module_name: str, _path: str) -> None:
    module = __import__(f"src.interfaces.web.pages.{module_name}", fromlist=["render"])
    assert callable(module.render)


@pytest.mark.integration
@pytest.mark.parametrize("module_name,path", PAGES)
def test_page_apptest_runs_without_exception(module_name: str, path: str) -> None:
    at = AppTest.from_file(path)
    with patch("src.interfaces.web.bridge.get_bridge") as mock_bridge:
        mock_bridge.return_value = _build_bridge_mock()
        at.run(timeout=10)
    assert not at.exception, f"AppTest failed for {module_name}"


@pytest.mark.integration
def test_bridge_returns_expected_types_from_mock() -> None:
    with patch("src.interfaces.web.bridge.get_bridge") as mock_bridge:
        mock_bridge.return_value = _build_bridge_mock()
        bridge = mock_bridge.return_value

    assert bridge.get_devices() == []
    assert bridge.get_rules() == []
    assert bridge.get_config() == {"key": "value"}
    assert bridge.is_app_running() is True
    status = bridge.get_system_status()
    assert status["state"] == "running"
    assert status["is_running"] is True


@pytest.mark.integration
def test_importing_multiple_pages_does_not_conflict() -> None:
    modules: dict[str, Any] = {}
    for module_name, _path in PAGES:
        modules[module_name] = __import__(
            f"src.interfaces.web.pages.{module_name}", fromlist=["render"]
        )

    assert set(modules.keys()) == {name for name, _path in PAGES}
    assert all(hasattr(module, "render") for module in modules.values())
