from __future__ import annotations

import streamlit as st

from src.interfaces.web.bridge import get_bridge
from src.interfaces.web.components.common import (
    render_error_message,
    render_header,
)
from src.interfaces.web.data_queue import SensorDataQueue
from src.interfaces.web.session import (
    clear_shutdown_initiated,
    init_session_state,
    is_shutdown_initiated,
    set_shutdown_initiated,
)


def _get_sensor_queue() -> SensorDataQueue:
    if "sensor_queue" not in st.session_state:
        st.session_state["sensor_queue"] = SensorDataQueue()
    return st.session_state["sensor_queue"]  # type: ignore[return-value]


def render() -> None:
    init_session_state()
    render_header("Dashboard")

    try:
        bridge = get_bridge()
    except RuntimeError as exc:
        render_error_message(str(exc))
        return

    status = bridge.get_system_status()

    if status is None:
        if is_shutdown_initiated():
            clear_shutdown_initiated()
            st.info("System is shutting down...")
            st.info("Refresh the page in a few seconds to see updated status.")
        else:
            st.warning(
                "⚠️ Application is not running. Start the system to see live data."
            )
            st.info("Run `docker compose up -d` or `python -m src.main` to start.")
        st.stop()

    current_state = status.get("state", "unknown")

    st.subheader("System Overview")

    uptime_seconds = status.get("uptime_seconds", 0)
    version = status.get("version", "unknown")

    hours, remainder = divmod(int(uptime_seconds), 3600)
    minutes, seconds = divmod(remainder, 60)
    uptime_str = f"{hours}h {minutes}m {seconds}s"

    col_state, col_version, col_uptime = st.columns(3)
    with col_state:
        if current_state == "running":
            st.metric("Status", "RUNNING")
        elif current_state == "stopped":
            st.metric("Status", "STOPPED")
        else:
            st.metric("Status", current_state.upper())
    with col_version:
        st.metric("Version", version)
    with col_uptime:
        st.metric("Uptime", uptime_str)

    if current_state == "stopped":
        if st.button("▶️ Start System", type="primary"):
            if bridge.start():
                st.success("System started!")
                st.rerun()
            else:
                st.error("Failed to start system")
    elif current_state == "running":  # noqa: SIM102
        if st.button("⏹️ Stop System", type="secondary"):
            if bridge.shutdown():
                st.success("Shutdown initiated!")
                set_shutdown_initiated()
                st.rerun()
            else:
                st.error("Failed to stop system")

    st.divider()

    if current_state != "running":
        st.info("Start the system to see live sensor data.")
        st.stop()

    auto_refresh = st.toggle("Auto-refresh (1s)", value=False)
    col1, col2 = st.columns(2)
    with col1:
        st.selectbox("Filter by zone", ["All"])
    with col2:
        st.selectbox(
            "Filter by type",
            ["All", "temperature", "humidity", "light_level", "motion"],
        )

    queue = _get_sensor_queue()

    @st.fragment(run_every="1s" if auto_refresh else None)
    def _show_sensors() -> None:
        readings = queue.get_latest_readings()
        if not readings:
            st.info("No sensor readings yet. Start the system to begin receiving data.")
            return
        cols = st.columns(3)
        for i, (sensor_id, reading) in enumerate(readings.items()):
            with cols[i % 3]:
                st.metric(
                    label=sensor_id,
                    value=f"{reading.value:.2f} {reading.unit or ''}".strip(),
                )
                st.caption(f"Updated: {reading.timestamp}")

    _show_sensors()


if __name__ == "__main__":
    render()
