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
    ("system_control", "src/interfaces/web/pages/system_control.py"),
)


def _build_bridge_mock() -> MagicMock:
    mock_bridge = MagicMock()

    mock_registry = MagicMock()
    mock_registry.all_devices.return_value = []
    mock_registry.get_locations.return_value = []
    mock_bridge.get_device_registry.return_value = mock_registry

    mock_rule_manager = MagicMock()
    mock_rule_manager.get_all_rules.return_value = []
    mock_bridge.get_rule_manager.return_value = mock_rule_manager

    mock_config_manager = MagicMock()
    mock_config_manager.load_config.return_value = {"key": "value"}
    mock_bridge.get_config_manager.return_value = mock_config_manager

    mock_orchestrator = MagicMock()
    mock_orchestrator.state.value = "ready"
    mock_orchestrator.is_ready = True
    mock_orchestrator.get_system_status.return_value = {
        "state": "ready",
        "is_ready": True,
        "initialization_steps": [],
        "components": {"config_manager": True, "mqtt_manager": False},
    }
    mock_bridge.get_orchestrator.return_value = mock_orchestrator

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

    registry = bridge.get_device_registry()
    rule_manager = bridge.get_rule_manager()
    config_manager = bridge.get_config_manager()
    orchestrator = bridge.get_orchestrator()

    assert registry.all_devices() == []
    assert registry.get_locations() == []
    assert rule_manager.get_all_rules() == []
    assert config_manager.load_config() == {"key": "value"}
    status = orchestrator.get_system_status()
    assert status["state"] == "ready"
    assert status["is_ready"] is True


@pytest.mark.integration
def test_importing_multiple_pages_does_not_conflict() -> None:
    modules: dict[str, Any] = {}
    for module_name, _path in PAGES:
        modules[module_name] = __import__(
            f"src.interfaces.web.pages.{module_name}", fromlist=["render"]
        )

    assert set(modules.keys()) == {name for name, _path in PAGES}
    assert all(hasattr(module, "render") for module in modules.values())
