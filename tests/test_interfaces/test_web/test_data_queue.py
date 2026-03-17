from __future__ import annotations

from src.device_interface.messages import SensorReading
from src.interfaces.web.data_queue import SensorDataQueue


def test_get_latest_readings_empty_returns_empty_dict() -> None:
    queue = SensorDataQueue()

    assert queue.get_latest_readings() == {}


def test_push_reading_updates_latest() -> None:
    queue = SensorDataQueue()
    reading = SensorReading(sensor_id="sensor-1", value=21.5)

    queue.push_reading(reading)

    assert queue.get_latest_readings() == {"sensor-1": reading}


def test_push_reading_multiple_sensors_tracks_independently() -> None:
    queue = SensorDataQueue()
    first = SensorReading(sensor_id="sensor-1", value=12.3)
    second = SensorReading(sensor_id="sensor-2", value=19.8)

    queue.push_reading(first)
    queue.push_reading(second)

    latest = queue.get_latest_readings()
    assert latest["sensor-1"] is first
    assert latest["sensor-2"] is second


def test_get_reading_history_returns_most_recent_first() -> None:
    queue = SensorDataQueue()
    older = SensorReading(sensor_id="sensor-1", value=1.0)
    newer = SensorReading(sensor_id="sensor-1", value=2.0)

    queue.push_reading(older)
    queue.push_reading(newer)

    history = queue.get_reading_history("sensor-1")

    assert history == [newer, older]


def test_get_reading_history_respects_limit() -> None:
    queue = SensorDataQueue()
    readings = [SensorReading(sensor_id="sensor-1", value=value) for value in range(5)]

    for reading in readings:
        queue.push_reading(reading)

    history = queue.get_reading_history("sensor-1", limit=3)

    assert history == list(reversed(readings[-3:]))


def test_push_reading_caps_history_at_max_history() -> None:
    queue = SensorDataQueue(max_history=2)
    readings = [SensorReading(sensor_id="sensor-1", value=value) for value in range(3)]

    for reading in readings:
        queue.push_reading(reading)

    history = queue.get_reading_history("sensor-1")

    assert history == [readings[-1], readings[-2]]


def test_get_reading_history_unknown_device_returns_empty_list() -> None:
    queue = SensorDataQueue()

    assert queue.get_reading_history("missing-sensor") == []
