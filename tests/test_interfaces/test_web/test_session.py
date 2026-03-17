"""Tests for Session State Management helpers."""

from __future__ import annotations

from unittest.mock import patch


def test_init_session_state_sets_defaults() -> None:
    """Test that init_session_state sets default keys if not present."""
    fake_state: dict = {}
    with patch("src.interfaces.web.session.st") as mock_st:
        mock_st.session_state = fake_state
        from src.interfaces.web.session import init_session_state

        init_session_state()

    assert fake_state["selected_device"] is None
    assert fake_state["ui_preferences"] == {}


def test_init_session_state_preserves_existing_values() -> None:
    """Test that init_session_state doesn't overwrite existing keys."""
    fake_state = {"selected_device": "device_123", "ui_preferences": {"theme": "dark"}}
    with patch("src.interfaces.web.session.st") as mock_st:
        mock_st.session_state = fake_state
        from src.interfaces.web.session import init_session_state

        init_session_state()

    assert fake_state["selected_device"] == "device_123"
    assert fake_state["ui_preferences"] == {"theme": "dark"}


def test_get_selected_device_returns_none_when_not_set() -> None:
    """Test get_selected_device returns None when key is missing."""
    fake_state: dict = {}
    with patch("src.interfaces.web.session.st") as mock_st:
        mock_st.session_state = fake_state
        from src.interfaces.web.session import get_selected_device

        result = get_selected_device()

    assert result is None


def test_get_selected_device_returns_device_id() -> None:
    """Test get_selected_device returns the stored device ID."""
    fake_state = {"selected_device": "device_xyz"}
    with patch("src.interfaces.web.session.st") as mock_st:
        mock_st.session_state = fake_state
        from src.interfaces.web.session import get_selected_device

        result = get_selected_device()

    assert result == "device_xyz"


def test_set_selected_device_updates_state() -> None:
    """Test set_selected_device updates session state."""
    fake_state: dict = {}
    with patch("src.interfaces.web.session.st") as mock_st:
        mock_st.session_state = fake_state
        from src.interfaces.web.session import set_selected_device

        set_selected_device("device_abc")

    assert fake_state["selected_device"] == "device_abc"


def test_set_selected_device_overwrites_existing() -> None:
    """Test set_selected_device overwrites previous value."""
    fake_state = {"selected_device": "device_old"}
    with patch("src.interfaces.web.session.st") as mock_st:
        mock_st.session_state = fake_state
        from src.interfaces.web.session import set_selected_device

        set_selected_device("device_new")

    assert fake_state["selected_device"] == "device_new"


def test_get_ui_preferences_returns_empty_dict_when_missing() -> None:
    """Test get_ui_preferences returns empty dict when key is missing."""
    fake_state: dict = {}
    with patch("src.interfaces.web.session.st") as mock_st:
        mock_st.session_state = fake_state
        from src.interfaces.web.session import get_ui_preferences

        result = get_ui_preferences()

    assert result == {}


def test_get_ui_preferences_returns_preferences() -> None:
    """Test get_ui_preferences returns stored preferences."""
    fake_state = {"ui_preferences": {"theme": "dark", "font_size": 14}}
    with patch("src.interfaces.web.session.st") as mock_st:
        mock_st.session_state = fake_state
        from src.interfaces.web.session import get_ui_preferences

        result = get_ui_preferences()

    assert result == {"theme": "dark", "font_size": 14}


def test_set_ui_preference_creates_dict_if_missing() -> None:
    """Test set_ui_preference creates ui_preferences dict if not present."""
    fake_state: dict = {}
    with patch("src.interfaces.web.session.st") as mock_st:
        mock_st.session_state = fake_state
        from src.interfaces.web.session import set_ui_preference

        set_ui_preference("theme", "light")

    assert fake_state["ui_preferences"]["theme"] == "light"


def test_set_ui_preference_adds_to_existing_dict() -> None:
    """Test set_ui_preference adds to existing ui_preferences dict."""
    fake_state = {"ui_preferences": {"theme": "dark"}}
    with patch("src.interfaces.web.session.st") as mock_st:
        mock_st.session_state = fake_state
        from src.interfaces.web.session import set_ui_preference

        set_ui_preference("font_size", 16)

    assert fake_state["ui_preferences"]["theme"] == "dark"
    assert fake_state["ui_preferences"]["font_size"] == 16


def test_set_ui_preference_overwrites_existing_key() -> None:
    """Test set_ui_preference overwrites existing key in ui_preferences."""
    fake_state = {"ui_preferences": {"theme": "dark"}}
    with patch("src.interfaces.web.session.st") as mock_st:
        mock_st.session_state = fake_state
        from src.interfaces.web.session import set_ui_preference

        set_ui_preference("theme", "light")

    assert fake_state["ui_preferences"]["theme"] == "light"


def test_get_selected_device_type_hint() -> None:
    """Test get_selected_device has correct return type."""
    from src.interfaces.web.session import get_selected_device

    assert callable(get_selected_device)


def test_set_selected_device_type_hint() -> None:
    """Test set_selected_device has correct parameter type."""
    from src.interfaces.web.session import set_selected_device

    assert callable(set_selected_device)


def test_get_ui_preferences_type_hint() -> None:
    """Test get_ui_preferences has correct return type."""
    from src.interfaces.web.session import get_ui_preferences

    assert callable(get_ui_preferences)


def test_set_ui_preference_type_hint() -> None:
    """Test set_ui_preference has correct parameter types."""
    from src.interfaces.web.session import set_ui_preference

    assert callable(set_ui_preference)


def test_init_session_state_type_hint() -> None:
    """Test init_session_state has correct return type."""
    from src.interfaces.web.session import init_session_state

    assert callable(init_session_state)
