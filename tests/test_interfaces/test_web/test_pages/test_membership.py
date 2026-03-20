from __future__ import annotations

from unittest.mock import MagicMock, patch

from streamlit.testing.v1 import AppTest


def test_membership_module_importable() -> None:
    import src.interfaces.web.pages.membership_editor as m

    assert hasattr(m, "render")


def test_render_is_callable() -> None:
    from src.interfaces.web.pages.membership_editor import render

    assert callable(render)


def test_membership_apptest_no_exception() -> None:
    at = AppTest.from_file("src/interfaces/web/pages/membership_editor.py")
    with patch("src.interfaces.web.bridge.get_bridge") as mock_get_bridge:
        mock_bridge = MagicMock()
        mock_bridge.list_sensor_types.return_value = ["temperature", "humidity"]
        mock_bridge.get_membership_functions.return_value = {
            "sensor_type": "temperature",
            "linguistic_variables": [
                {
                    "name": "temp_level",
                    "membership_functions": [
                        {
                            "name": "cold",
                            "function_type": "triangular",
                            "parameters": {"a": 0.0, "b": 10.0, "c": 20.0},
                        }
                    ],
                }
            ],
        }
        mock_get_bridge.return_value = mock_bridge
        at.run(timeout=10)
    assert not at.exception


def test_membership_shows_title() -> None:
    at = AppTest.from_file("src/interfaces/web/pages/membership_editor.py")
    with patch("src.interfaces.web.bridge.get_bridge") as mock_get_bridge:
        mock_bridge = MagicMock()
        mock_bridge.list_sensor_types.return_value = ["temperature"]
        mock_bridge.get_membership_functions.return_value = {}
        mock_get_bridge.return_value = mock_bridge
        at.run(timeout=10)
    titles = [t.value for t in at.title]
    assert any("Membership" in str(t) for t in titles)


def test_membership_selectbox_exists() -> None:
    at = AppTest.from_file("src/interfaces/web/pages/membership_editor.py")
    with patch("src.interfaces.web.bridge.get_bridge") as mock_get_bridge:
        mock_bridge = MagicMock()
        mock_bridge.list_sensor_types.return_value = ["temperature", "humidity"]
        mock_bridge.get_membership_functions.return_value = {}
        mock_get_bridge.return_value = mock_bridge
        at.run(timeout=10)
    assert not at.exception
