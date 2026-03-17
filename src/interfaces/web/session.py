"""Session State Management helpers for Streamlit web interface."""

from __future__ import annotations

import streamlit as st


def init_session_state() -> None:
    """Initialize session state with default values.

    Sets these keys if not already present:
    - "selected_device": None
    - "ui_preferences": {}
    """
    if "selected_device" not in st.session_state:
        st.session_state["selected_device"] = None
    if "ui_preferences" not in st.session_state:
        st.session_state["ui_preferences"] = {}


def get_selected_device() -> str | None:
    """Get the currently selected device ID.

    Returns:
        Device ID string or None if no device is selected.
    """
    return st.session_state.get("selected_device")


def set_selected_device(device_id: str) -> None:
    """Set the currently selected device ID.

    Args:
        device_id: Device ID to select.
    """
    st.session_state["selected_device"] = device_id


def get_ui_preferences() -> dict[str, object]:
    """Get all UI preference settings.

    Returns:
        Dictionary of UI preferences, empty dict if none set.
    """
    return st.session_state.get("ui_preferences", {})


def set_ui_preference(key: str, value: object) -> None:
    """Set a UI preference value.

    Args:
        key: Preference key.
        value: Preference value.
    """
    st.session_state.setdefault("ui_preferences", {})[key] = value
