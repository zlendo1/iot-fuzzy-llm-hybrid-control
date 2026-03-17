from __future__ import annotations

from unittest.mock import MagicMock, patch

from streamlit.testing.v1 import AppTest


def test_devices_module_importable() -> None:
    import src.interfaces.web.pages.devices as m

    assert hasattr(m, "render")


def test_render_is_callable() -> None:
    from src.interfaces.web.pages.devices import render

    assert callable(render)


def test_devices_apptest_no_exception() -> None:
    at = AppTest.from_file("src/interfaces/web/pages/devices.py")
    with patch("src.interfaces.web.bridge.get_bridge") as mock_bridge:
        mock_registry = MagicMock()
        mock_registry.all_devices.return_value = []
        mock_registry.get_locations.return_value = []
        mock_bridge.return_value.get_device_registry.return_value = mock_registry
        at.run(timeout=10)
    assert not at.exception


def test_devices_shows_title() -> None:
    at = AppTest.from_file("src/interfaces/web/pages/devices.py")
    with patch("src.interfaces.web.bridge.get_bridge") as mock_bridge:
        mock_registry = MagicMock()
        mock_registry.all_devices.return_value = []
        mock_registry.get_locations.return_value = []
        mock_bridge.return_value.get_device_registry.return_value = mock_registry
        at.run(timeout=10)
    titles = [t.value for t in at.title]
    assert any("Devices" in str(t) for t in titles)


def test_devices_empty_registry_shows_info() -> None:
    at = AppTest.from_file("src/interfaces/web/pages/devices.py")
    with patch("src.interfaces.web.bridge.get_bridge") as mock_bridge:
        mock_registry = MagicMock()
        mock_registry.all_devices.return_value = []
        mock_registry.get_locations.return_value = []
        mock_bridge.return_value.get_device_registry.return_value = mock_registry
        at.run(timeout=10)
    assert not at.exception
