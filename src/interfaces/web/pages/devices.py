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
    render_header("Devices", "Manage and monitor connected IoT devices")

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

    st.divider()
    st.markdown(
        f"**Device Summary:** Showing {len(filtered)} of {len(devices)} devices"
    )

    if not filtered:
        st.info("No devices match the current filter.")
        return

    device_statuses = {}
    device_readings = {}
    for dev in filtered:
        did = dev.get("id", "")
        if not did:
            continue
        status = bridge.get_device_status(did)
        if status is not None:
            device_statuses[did] = status
        if dev.get("device_type") == "sensor":
            reading_data = bridge.get_latest_reading(did)
            if reading_data is not None:
                device_readings[did] = reading_data

    for device in filtered:
        device_id = device.get("id", "unknown")
        device_name = device.get("name", "Unknown")
        device_type = device.get("device_type", "unknown")
        device_class = device.get("device_class", "unknown")
        location = device.get("location", "unknown")
        capabilities = device.get("capabilities", [])
        unit = device.get("unit", "")

        status_info = device_statuses.get(device_id)
        is_online = status_info.get("online", False) if status_info else False
        status_icon = "\U0001f7e2" if is_online else "\U0001f534"

        with st.expander(f"{status_icon} {device_name} ({device_id})", expanded=False):
            col_status, col_type, col_zone, col_class = st.columns(4)
            with col_status:
                st.caption("Status")
                render_status_badge("online" if is_online else "offline")
            with col_type:
                st.metric(
                    "Type",
                    str(device_type).replace("_", " ").title(),
                )
            with col_zone:
                st.metric("Zone", str(location).title())
            with col_class:
                st.caption("Class")
                render_status_badge(device_class)

            if status_info and status_info.get("last_seen"):
                st.caption(f"Last seen: {status_info['last_seen']}")

            if capabilities:
                st.markdown(
                    f"**Capabilities:** {', '.join(str(c) for c in capabilities)}"
                )

            if unit:
                st.markdown(f"**Unit:** {unit}")

            if device_type == "sensor":
                st.divider()
                reading_data = device_readings.get(device_id)
                if reading_data and reading_data.get("value") is not None:
                    val = reading_data["value"]
                    unit_str = reading_data.get("unit", "")
                    ts = reading_data.get("timestamp")
                    val_display = f"{val:.2f}" if isinstance(val, float) else str(val)
                    st.metric(
                        "Latest Reading",
                        f"{val_display} {unit_str}".strip(),
                    )
                    if ts:
                        st.caption(f"Reading at: {ts}")
                else:
                    st.info("No reading available")

            if device_type == "actuator" and capabilities:
                st.divider()
                st.markdown("**Send Command**")
                cmd_col1, cmd_col2 = st.columns([2, 1])
                with cmd_col1:
                    action = st.selectbox(
                        "Action",
                        options=capabilities,
                        key=f"cmd_action_{device_id}",
                    )
                with cmd_col2:
                    if st.button("Send", key=f"cmd_send_{device_id}", type="primary"):
                        result = bridge.send_command(device_id, str(action))
                        if result and result.get("success"):
                            st.success(f"Command sent: {action}")
                        else:
                            msg = (
                                result.get("message", "Unknown error")
                                if result
                                else "Failed to send"
                            )
                            st.error(f"Failed: {msg}")


if __name__ == "__main__":
    render()
