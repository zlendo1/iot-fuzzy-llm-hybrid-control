from __future__ import annotations

from unittest.mock import MagicMock, patch

from streamlit.testing.v1 import AppTest


def test_rules_module_importable() -> None:
    import src.interfaces.web.pages.rules as m

    assert hasattr(m, "render")


def test_render_is_callable() -> None:
    from src.interfaces.web.pages.rules import render

    assert callable(render)


def test_rules_apptest_no_exception() -> None:
    at = AppTest.from_file("src/interfaces/web/pages/rules.py")
    with patch("src.interfaces.web.bridge.get_bridge") as mock_bridge:
        mock_rule_mgr = MagicMock()
        mock_rule_mgr.get_all_rules.return_value = []
        mock_bridge.return_value.get_rule_manager.return_value = mock_rule_mgr
        at.run(timeout=10)
    assert not at.exception


def test_rules_shows_title() -> None:
    at = AppTest.from_file("src/interfaces/web/pages/rules.py")
    with patch("src.interfaces.web.bridge.get_bridge") as mock_bridge:
        mock_rule_mgr = MagicMock()
        mock_rule_mgr.get_all_rules.return_value = []
        mock_bridge.return_value.get_rule_manager.return_value = mock_rule_mgr
        at.run(timeout=10)
    titles = [t.value for t in at.title]
    assert any("Rules" in str(t) for t in titles)


def test_rules_empty_list_shows_info() -> None:
    at = AppTest.from_file("src/interfaces/web/pages/rules.py")
    with patch("src.interfaces.web.bridge.get_bridge") as mock_bridge:
        mock_rule_mgr = MagicMock()
        mock_rule_mgr.get_all_rules.return_value = []
        mock_bridge.return_value.get_rule_manager.return_value = mock_rule_mgr
        at.run(timeout=10)
    assert not at.exception
