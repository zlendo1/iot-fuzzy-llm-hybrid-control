"""Configuration page - Edit system configuration."""

from __future__ import annotations

import json
from typing import Any

import streamlit as st

from src.interfaces.web.bridge import get_bridge
from src.interfaces.web.components.common import render_error_message, render_header
from src.interfaces.web.session import init_session_state


def _render_config_editor(
    title: str,
    config_name: str,
    save_label: str,
    bridge: Any,
) -> None:
    st.subheader(title)
    config_data = bridge.get_config(config_name)

    if config_data is None:
        st.error(f"Failed to load {config_name} configuration")
        return

    content = config_data.get("content")
    version = config_data.get("version", "")

    if content is None:
        st.error(f"Invalid {config_name} configuration format")
        return

    edited_text = st.text_area(
        label="Edit JSON",
        value=json.dumps(content, indent=2),
        height=400,
        key=f"config_editor_{config_name}",
    )

    if st.button(save_label, key=f"save_{config_name}"):
        try:
            parsed = json.loads(edited_text)
        except json.JSONDecodeError as exc:
            st.error(f"Invalid JSON: {exc}")
            return

        result = bridge.update_config(config_name, parsed, version)
        if result is not None and result.get("success") or result is not None and "new_version" in result:
            st.success(f"Saved {config_name} configuration.")
        else:
            error_msg = (
                result.get("message", "Unknown error")
                if result is not None
                else "Failed to save configuration"
            )
            st.error(f"Failed to save {config_name} configuration: {error_msg}")


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
        _render_config_editor("Devices", "devices", "Save devices", bridge)
    with mqtt_tab:
        _render_config_editor("MQTT", "mqtt_config", "Save mqtt", bridge)
    with llm_tab:
        _render_config_editor("LLM", "llm_config", "Save llm", bridge)


if __name__ == "__main__":
    render()
