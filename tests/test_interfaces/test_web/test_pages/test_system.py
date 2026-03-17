from __future__ import annotations

from unittest.mock import MagicMock, patch

from streamlit.testing.v1 import AppTest


def test_system_module_importable() -> None:
    import src.interfaces.web.pages.system_control as m

    assert hasattr(m, "render")


def test_render_is_callable() -> None:
    from src.interfaces.web.pages.system_control import render

    assert callable(render)


def test_system_apptest_no_exception() -> None:
    at = AppTest.from_file("src/interfaces/web/pages/system_control.py")
    with patch("src.interfaces.web.bridge.get_bridge") as mock_bridge:
        mock_orch = MagicMock()
        mock_orch.state.value = "ready"
        mock_orch.is_ready = True
        mock_orch.get_system_status.return_value = {
            "state": "ready",
            "is_ready": True,
            "initialization_steps": [],
            "components": {"config_manager": True, "mqtt_manager": False},
        }
        mock_bridge.return_value.get_orchestrator.return_value = mock_orch
        at.run(timeout=10)
    assert not at.exception


def test_system_shows_title() -> None:
    at = AppTest.from_file("src/interfaces/web/pages/system_control.py")
    with patch("src.interfaces.web.bridge.get_bridge") as mock_bridge:
        mock_orch = MagicMock()
        mock_orch.state.value = "ready"
        mock_orch.is_ready = True
        mock_orch.get_system_status.return_value = {
            "state": "ready",
            "is_ready": True,
            "initialization_steps": [],
            "components": {},
        }
        mock_bridge.return_value.get_orchestrator.return_value = mock_orch
        at.run(timeout=10)
    titles = [t.value for t in at.title]
    assert any("System" in str(t) for t in titles)


def test_system_shows_status() -> None:
    at = AppTest.from_file("src/interfaces/web/pages/system_control.py")
    with patch("src.interfaces.web.bridge.get_bridge") as mock_bridge:
        mock_orch = MagicMock()
        mock_orch.state.value = "error"
        mock_orch.is_ready = False
        mock_orch.get_system_status.return_value = {
            "state": "error",
            "is_ready": False,
            "initialization_steps": [
                {
                    "name": "step1",
                    "description": "Load config",
                    "completed": True,
                    "error": None,
                }
            ],
            "components": {"config_manager": True},
        }
        mock_bridge.return_value.get_orchestrator.return_value = mock_orch
        at.run(timeout=10)
    assert not at.exception
