from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from src.interfaces.web.bridge import get_bridge
from src.interfaces.web.components.common import (
    render_error_message,
    render_header,
    render_status_badge,
)
from src.interfaces.web.session import init_session_state


def _load_devices() -> list[dict] | None:
    """Load devices from config file."""
    config_path = Path("config") / "devices.json"
    if not config_path.exists():
        return None
    try:
        with config_path.open(encoding="utf-8") as f:
            data = json.load(f)
            return data.get("devices", [])
    except (OSError, json.JSONDecodeError):
        return None


def render() -> None:
    init_session_state()
    render_header("Devices")

    try:
        get_bridge()
    except RuntimeError as exc:
        render_error_message(str(exc))
        return

    devices = _load_devices()
    if devices is None:
        st.warning("Device configuration not found.")
        return

    locations = sorted(
        {t for t in {d.get("location") for d in devices} if t is not None}
    )
    device_types = sorted(
        {t for t in {d.get("device_type") for d in devices} if t is not None}
    )

    col1, col2 = st.columns(2)
    with col1:
        type_filter = st.selectbox("Filter by type", ["All"] + device_types)
    with col2:
        location_filter = st.selectbox("Filter by zone", ["All"] + locations)

    filtered = devices
    if type_filter != "All":
        filtered = [d for d in filtered if d.get("device_type") == type_filter]
    if location_filter != "All":
        filtered = [d for d in filtered if d.get("location") == location_filter]

    st.write(f"Showing {len(filtered)} of {len(devices)} devices")

    if not filtered:
        st.info("No devices match the current filter.")
        return

    for device in filtered:
        device_id = device.get("id", "unknown")
        device_name = device.get("name", "Unknown")
        with st.expander(f"{device_name} ({device_id})", expanded=False):
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.write(f"**Type:** {device.get('device_type', 'unknown')}")
                st.write(f"**Class:** {device.get('device_class', 'unknown')}")
            with col_b:
                st.write(f"**Zone:** {device.get('location', 'unknown')}")
            with col_c:
                render_status_badge("unknown")


if __name__ == "__main__":
    render()
