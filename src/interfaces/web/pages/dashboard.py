from __future__ import annotations

import streamlit as st

from src.interfaces.web.bridge import get_bridge
from src.interfaces.web.components.common import (
    render_error_message,
    render_header,
)
from src.common.utils import format_timestamp
from src.device_interface.messages import SensorReading
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
    queue = st.session_state["sensor_queue"]
    assert isinstance(queue, SensorDataQueue)
    return queue


def render() -> None:
    init_session_state()
    render_header("Dashboard", "System overview and live sensor monitoring")

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

    devices = bridge.get_devices()
    device_map = {dev["id"]: dev for dev in devices}
    locations = sorted(
        {dev.get("location", "Unknown") for dev in devices if dev.get("location")}
    )
    zones = ["All"] + list(locations)

    auto_refresh = st.toggle("Auto-refresh (1s)", value=False)
    col1, col2 = st.columns(2)
    with col1:
        zone_filter = st.selectbox("Filter by zone", zones)
    with col2:
        type_filter = st.selectbox(
            "Filter by type",
            ["All", "temperature", "humidity", "light_level", "motion"],
        )

    # Ensure zone_filter and type_filter are strings
    zone_filter_str = str(zone_filter) if zone_filter is not None else "All"
    type_filter_str = str(type_filter) if type_filter is not None else "All"

    queue = _get_sensor_queue()

    @st.fragment(run_every="1s" if auto_refresh else None)
    def _show_sensors() -> None:
        sensor_devices = [
            dev for dev in device_map.values() if dev.get("device_type") == "sensor"
        ]
        for dev in sensor_devices:
            device_id = dev.get("id", "")
            if not device_id:
                continue
            data = bridge.get_latest_reading(device_id)
            if data is not None and data.get("value") is not None:
                ts = data.get("timestamp")
                reading = SensorReading(
                    sensor_id=data["device_id"],
                    value=data["value"],
                    unit=data.get("unit"),
                    timestamp=ts.isoformat() if ts is not None else format_timestamp(),
                )
                queue.push_reading(reading)

        readings = queue.get_latest_readings()
        if not readings:
            st.info("No sensor readings yet. Start the system to begin receiving data.")
            return

        filtered_readings = {}
        for sensor_id, reading in readings.items():
            device = device_map.get(sensor_id, {})

            if zone_filter_str != "All" and device.get("location") != zone_filter_str:
                continue

            if (
                type_filter_str != "All"
                and device.get("device_class") != type_filter_str
            ):
                continue

            filtered_readings[sensor_id] = reading

        if not filtered_readings:
            st.info(
                f"No sensors match the selected filters ({zone_filter_str}, {type_filter_str})."
            )
            return

        cols = st.columns(2)
        for i, (sensor_id, reading) in enumerate(filtered_readings.items()):
            device = device_map.get(sensor_id, {})
            name = device.get("name", sensor_id)
            location = device.get("location", "Unknown")

            with cols[i % 2], st.container(border=True):
                st.subheader(f"{name}")
                st.caption(f"📍 {location} | 🏷️ {sensor_id}")

                if isinstance(reading.value, float):
                    val_str = f"{reading.value:.2f}"
                elif isinstance(reading.value, bool):
                    val_str = "Detected" if reading.value else "Clear"
                else:
                    val_str = str(reading.value)

                st.metric(
                    label="Current Value",
                    value=f"{val_str} {reading.unit or ''}".strip(),
                )

                history = queue.get_reading_history(sensor_id, limit=20)
                if history:
                    chart_data = {"time": [], "value": []}
                    for h in reversed(history):
                        chart_data["time"].append(h.timestamp)
                        try:
                            chart_data["value"].append(float(h.value))
                        except (ValueError, TypeError):
                            chart_data["value"].append(0.0)

                    st.line_chart(chart_data, x="time", y="value", height=150)

                st.caption(f"Last updated: {reading.timestamp}")

    _show_sensors()


if __name__ == "__main__":
    render()
