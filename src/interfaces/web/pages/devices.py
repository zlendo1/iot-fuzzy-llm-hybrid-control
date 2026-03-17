from __future__ import annotations

import streamlit as st

from src.interfaces.web.bridge import get_bridge
from src.interfaces.web.components.common import (
    render_error_message,
    render_header,
    render_status_badge,
)
from src.interfaces.web.session import init_session_state


def render() -> None:
    init_session_state()
    render_header("Devices")

    try:
        bridge = get_bridge()
    except RuntimeError as exc:
        render_error_message(str(exc))
        return

    registry = bridge.get_device_registry()
    if registry is None:
        st.warning("Device registry not available. Start the system first.")
        return

    all_devices = registry.all_devices()

    col1, col2 = st.columns(2)
    with col1:
        type_filter = st.selectbox("Filter by type", ["All", "sensor", "actuator"])
    with col2:
        location_filter = st.selectbox(
            "Filter by zone",
            ["All"] + sorted(registry.get_locations()),
        )

    filtered = all_devices
    if type_filter != "All":
        filtered = [
            device for device in filtered if device.device_type.value == type_filter
        ]
    if location_filter != "All":
        filtered = [device for device in filtered if device.location == location_filter]

    st.write(f"Showing {len(filtered)} of {len(all_devices)} devices")

    if not filtered:
        st.info("No devices match the current filter.")
        return

    for device in filtered:
        with st.expander(f"{device.name} ({device.id})", expanded=False):
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.write(f"**Type:** {device.device_type.value}")
                st.write(f"**Class:** {device.device_class}")
            with col_b:
                st.write(f"**Zone:** {device.location}")
            with col_c:
                render_status_badge("unknown")


if __name__ == "__main__":
    render()
