from __future__ import annotations

import streamlit as st

from src.interfaces.web.bridge import get_bridge
from src.interfaces.web.components.common import (
    render_error_message,
    render_header,
)
from src.interfaces.web.data_queue import SensorDataQueue
from src.interfaces.web.session import init_session_state


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
        st.warning("⚠️ Application is not running. Start the system to see live data.")
        st.info("Run `docker compose up -d` or `python -m src.main` to start.")
        st.stop()

    current_state = status.get("state", "unknown")

    st.subheader("System Control")
    col_status, col_action = st.columns([2, 1])

    with col_status:
        if current_state == "running":
            st.success("🟢 System is running")
        elif current_state == "idle":
            st.info("🟡 System is idle (ready to start)")
        else:
            st.warning(f"⚪ System state: {current_state}")

    with col_action:
        if current_state == "idle":
            if st.button("▶️ Start System", type="primary", use_container_width=True):
                if bridge.start():
                    st.success("System started!")
                    st.rerun()
                else:
                    st.error("Failed to start system")
        elif current_state == "running":
            if st.button("⏹️ Stop System", type="secondary", use_container_width=True):
                if bridge.shutdown():
                    st.success("Shutdown initiated!")
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
