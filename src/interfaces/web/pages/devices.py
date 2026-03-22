from __future__ import annotations

import streamlit as st

from src.interfaces.web.bridge import get_bridge
from src.interfaces.web.components.common import (
    render_header,
    render_status_badge,
)
from src.interfaces.web.session import init_session_state


def render() -> None:
    init_session_state()
    render_header("Devices")

    bridge = get_bridge()

    devices = bridge.get_devices()
    if not devices:
        st.warning("No devices available or unable to retrieve device list.")
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
