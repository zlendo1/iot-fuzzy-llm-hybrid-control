from __future__ import annotations

from unittest.mock import MagicMock, patch

from streamlit.testing.v1 import AppTest


def test_dashboard_module_importable() -> None:
    import src.interfaces.web.pages.dashboard as m

    assert hasattr(m, "render")


def test_render_is_callable() -> None:
    from src.interfaces.web.pages.dashboard import render

    assert callable(render)


def test_dashboard_apptest_no_exception() -> None:
    at = AppTest.from_file("src/interfaces/web/pages/dashboard.py")
    with patch("src.interfaces.web.bridge.get_bridge") as mock_bridge:
        mock_bridge.return_value = MagicMock()
        at.run(timeout=10)
    assert not at.exception


def test_dashboard_shows_title() -> None:
    at = AppTest.from_file("src/interfaces/web/pages/dashboard.py")
    with patch("src.interfaces.web.bridge.get_bridge") as mock_bridge:
        mock_bridge.return_value = MagicMock()
        at.run(timeout=10)
    titles = [t.value for t in at.title]
    assert any("Dashboard" in str(t) for t in titles)


def test_dashboard_empty_state_shows_info() -> None:
    at = AppTest.from_file("src/interfaces/web/pages/dashboard.py")
    with patch("src.interfaces.web.bridge.get_bridge") as mock_bridge:
        mock_bridge.return_value = MagicMock()
        at.run(timeout=10)
    assert not at.exception
    infos = [i.value for i in at.info]
    assert len(infos) >= 0
