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

    if not bridge.is_app_running():
        st.warning("⚠️ Application is not running. Start the system to see live data.")
        st.info("Run `docker compose up -d` or `python -m src.main` to start.")
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
