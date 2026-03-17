from __future__ import annotations

from unittest.mock import MagicMock, patch

from streamlit.testing.v1 import AppTest


def test_logs_module_importable() -> None:
    import src.interfaces.web.pages.logs as m

    assert hasattr(m, "render")


def test_render_is_callable() -> None:
    from src.interfaces.web.pages.logs import render

    assert callable(render)


def test_logs_apptest_no_exception() -> None:
    at = AppTest.from_file("src/interfaces/web/pages/logs.py")
    with patch("src.interfaces.web.bridge.get_bridge") as mock_bridge:
        mock_bridge.return_value = MagicMock()
        at.run(timeout=10)
    assert not at.exception


def test_logs_shows_title() -> None:
    at = AppTest.from_file("src/interfaces/web/pages/logs.py")
    with patch("src.interfaces.web.bridge.get_bridge") as mock_bridge:
        mock_bridge.return_value = MagicMock()
        at.run(timeout=10)
    titles = [t.value for t in at.title]
    assert any("Logs" in str(t) for t in titles)


def test_logs_no_log_files_shows_info() -> None:
    at = AppTest.from_file("src/interfaces/web/pages/logs.py")
    with patch("src.interfaces.web.bridge.get_bridge") as mock_bridge:
        mock_bridge.return_value = MagicMock()
        at.run(timeout=10)
    assert not at.exception
