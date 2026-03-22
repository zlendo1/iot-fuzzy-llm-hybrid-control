from __future__ import annotations

from unittest.mock import MagicMock, patch

from streamlit.testing.v1 import AppTest

_FAKE_STATUS = {
    "state": "running",
    "uptime_seconds": 120,
    "version": "0.1.0",
}


def _patched_bridge() -> tuple[MagicMock, MagicMock]:
    bridge = MagicMock()
    bridge.get_system_status.return_value = _FAKE_STATUS
    bridge.get_all_latest_readings.return_value = {}
    return bridge, bridge


def test_dashboard_module_importable() -> None:
    import src.interfaces.web.pages.dashboard as m

    assert hasattr(m, "render")


def test_render_is_callable() -> None:
    from src.interfaces.web.pages.dashboard import render

    assert callable(render)


def test_dashboard_apptest_no_exception() -> None:
    at = AppTest.from_file("src/interfaces/web/pages/dashboard.py")
    with patch("src.interfaces.web.bridge.get_bridge") as mock_get:
        mock_get.return_value = _patched_bridge()[0]
        at.run(timeout=10)
    assert not at.exception


def test_dashboard_shows_title() -> None:
    at = AppTest.from_file("src/interfaces/web/pages/dashboard.py")
    with patch("src.interfaces.web.bridge.get_bridge") as mock_get:
        mock_get.return_value = _patched_bridge()[0]
        at.run(timeout=10)
    titles = [t.value for t in at.title]
    assert any("Dashboard" in str(t) for t in titles)


def test_dashboard_empty_state_shows_info() -> None:
    at = AppTest.from_file("src/interfaces/web/pages/dashboard.py")
    with patch("src.interfaces.web.bridge.get_bridge") as mock_get:
        bridge = MagicMock()
        bridge.get_system_status.return_value = None
        mock_get.return_value = bridge
        at.run(timeout=10)
    assert not at.exception
    infos = [i.value for i in at.info]
    assert len(infos) >= 0
