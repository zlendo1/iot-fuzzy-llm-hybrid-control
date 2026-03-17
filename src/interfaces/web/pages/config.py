"""Configuration page - Edit system configuration."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import streamlit as st

from src.interfaces.web.bridge import get_bridge
from src.interfaces.web.components.common import render_error_message, render_header
from src.interfaces.web.session import init_session_state

if TYPE_CHECKING:
    from src.configuration.config_manager import ConfigurationManager


def _render_config_editor(
    cfg_mgr: ConfigurationManager,
    title: str,
    config_name: str,
    save_label: str,
) -> None:
    st.subheader(title)
    try:
        config_data = cfg_mgr.load_config(config_name)
    except Exception as exc:
        st.error(f"Failed to load {config_name} configuration: {exc}")
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

        try:
            cfg_mgr.save_config(config_name, parsed, validate=False, backup=True)
        except Exception as exc:
            st.error(f"Failed to save {config_name} configuration: {exc}")
        else:
            st.success(f"Saved {config_name} configuration.")


def render() -> None:
    init_session_state()
    render_header("Configuration")

    try:
        bridge = get_bridge()
    except RuntimeError as exc:
        render_error_message(str(exc))
        return

    cfg_mgr = bridge.get_config_manager()
    if cfg_mgr is None:
        st.warning("Configuration manager not available. Start the system first.")
        return

    devices_tab, mqtt_tab, llm_tab = st.tabs(["Devices", "MQTT", "LLM"])
    with devices_tab:
        _render_config_editor(cfg_mgr, "Devices", "devices", "Save devices")
    with mqtt_tab:
        _render_config_editor(cfg_mgr, "MQTT", "mqtt_config", "Save mqtt")
    with llm_tab:
        _render_config_editor(cfg_mgr, "LLM", "llm_config", "Save llm")


if __name__ == "__main__":
    render()
