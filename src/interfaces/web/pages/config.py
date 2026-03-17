"""Configuration page - Edit system configuration."""

from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from src.interfaces.web.bridge import get_bridge
from src.interfaces.web.components.common import render_error_message, render_header
from src.interfaces.web.session import init_session_state


def _load_config_file(filename: str) -> dict | None:
    """Load config file by name."""
    config_path = Path("config") / f"{filename}.json"
    if not config_path.exists():
        return None
    try:
        with config_path.open(encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def _save_config_file(filename: str, data: dict) -> bool:
    """Save config file by name."""
    config_path = Path("config") / f"{filename}.json"
    try:
        config_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return True
    except (OSError, json.JSONDecodeError):
        return False


def _render_config_editor(
    title: str,
    config_name: str,
    save_label: str,
) -> None:
    st.subheader(title)
    config_data = _load_config_file(config_name)

    if config_data is None:
        st.error(f"Failed to load {config_name} configuration")
        return

    edited_text = st.text_area(
        label="Edit JSON",
        value=json.dumps(config_data, indent=2),
        height=400,
        key=f"config_editor_{config_name}",
    )

    if st.button(save_label, key=f"save_{config_name}"):
        try:
            parsed = json.loads(edited_text)
        except json.JSONDecodeError as exc:
            st.error(f"Invalid JSON: {exc}")
            return

        if _save_config_file(config_name, parsed):
            st.success(f"Saved {config_name} configuration.")
        else:
            st.error(f"Failed to save {config_name} configuration")


def render() -> None:
    init_session_state()
    render_header("Configuration")

    try:
        bridge = get_bridge()
    except RuntimeError as exc:
        render_error_message(str(exc))
        return

    devices_tab, mqtt_tab, llm_tab = st.tabs(["Devices", "MQTT", "LLM"])
    with devices_tab:
        _render_config_editor("Devices", "devices", "Save devices")
    with mqtt_tab:
        _render_config_editor("MQTT", "mqtt_config", "Save mqtt")
    with llm_tab:
        _render_config_editor("LLM", "llm_config", "Save llm")


if __name__ == "__main__":
    render()
