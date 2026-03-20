from __future__ import annotations

from unittest.mock import MagicMock, patch

from streamlit.testing.v1 import AppTest


def test_config_module_importable() -> None:
    import src.interfaces.web.pages.config as m

    assert hasattr(m, "render")


def test_render_is_callable() -> None:
    from src.interfaces.web.pages.config import render

    assert callable(render)


def test_config_apptest_no_exception() -> None:
    at = AppTest.from_file("src/interfaces/web/pages/config.py")
    with patch("src.interfaces.web.bridge.get_bridge") as mock_get_bridge:
        mock_bridge = MagicMock()
        mock_bridge.get_config.return_value = {
            "content": {"devices": []},
            "version": "abc123",
        }
        mock_get_bridge.return_value = mock_bridge
        at.run(timeout=10)
    assert not at.exception


def test_config_shows_title() -> None:
    at = AppTest.from_file("src/interfaces/web/pages/config.py")
    with patch("src.interfaces.web.bridge.get_bridge") as mock_get_bridge:
        mock_bridge = MagicMock()
        mock_bridge.get_config.return_value = {
            "content": {"devices": []},
            "version": "abc123",
        }
        mock_get_bridge.return_value = mock_bridge
        at.run(timeout=10)
    titles = [t.value for t in at.title]
    assert any("Config" in str(t) for t in titles)


def test_config_shows_tabs() -> None:
    at = AppTest.from_file("src/interfaces/web/pages/config.py")
    with patch("src.interfaces.web.bridge.get_bridge") as mock_get_bridge:
        mock_bridge = MagicMock()
        mock_bridge.get_config.return_value = {
            "content": {"devices": []},
            "version": "abc123",
        }
        mock_get_bridge.return_value = mock_bridge
        at.run(timeout=10)
    assert not at.exception
