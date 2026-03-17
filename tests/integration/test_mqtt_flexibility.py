from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from src.device_interface.messages import SensorReading
from src.device_interface.models import PayloadSchema, Sensor, TopicPattern
from src.device_interface.topic_resolver import TopicPatternResolver


def _write_devices_config(path: Path, devices: dict[str, dict[str, Any]]) -> None:
    path.write_text(json.dumps({"devices": devices}))


def _load_sensors(path: Path) -> list[Sensor]:
    data = json.loads(path.read_text())
    return [Sensor.from_dict(device) for _, device in data["devices"].items()]


class TestMQTTFlexibilityIntegration:
    @pytest.mark.integration
    def test_custom_payload_schema_extracts_reading(self, tmp_path: Path) -> None:
        devices_path = tmp_path / "devices.json"
        _write_devices_config(
            devices_path,
            {
                "temp-001": {
                    "id": "temp-001",
                    "name": "Lab Temp",
                    "type": "sensor",
                    "device_class": "temperature",
                    "location": "lab",
                    "unit": "celsius",
                    "mqtt": {
                        "payload_mapping": {
                            "value_field": "temperature",
                            "unit_field": "unit",
                            "timestamp_field": "ts",
                        }
                    },
                }
            },
        )

        sensor = _load_sensors(devices_path)[0]
        payload = json.dumps(
            {"temperature": 22.5, "unit": "celsius", "ts": "2026-01-01T10:00:00"}
        ).encode("utf-8")

        assert sensor.mqtt is not None
        assert sensor.mqtt.payload_mapping is not None

        reading = SensorReading.from_mqtt_payload(
            sensor.id,
            payload,
            "home/lab/temperature",
            unit=sensor.unit,
            payload_schema=sensor.mqtt.payload_mapping,
        )

        assert reading.value == 22.5
        assert reading.unit == "celsius"
        assert reading.timestamp == "2026-01-01T10:00:00"

    @pytest.mark.integration
    def test_custom_topic_pattern_resolves_sensor_topic(self) -> None:
        pattern = TopicPattern(
            pattern="site/{location}/{device_class}/sensor",
            variables=("location", "device_class"),
        )
        resolver = TopicPatternResolver(patterns={"sensors": pattern})
        sensor = Sensor.from_dict(
            {
                "id": "temp-002",
                "name": "Warehouse Temp",
                "type": "sensor",
                "device_class": "temperature",
                "location": "warehouse",
            }
        )

        topic = resolver.resolve_sensor_topic(sensor)

        assert topic == "site/warehouse/temperature/sensor"

    @pytest.mark.integration
    def test_backward_compatibility_explicit_topic_and_legacy_payload(self) -> None:
        pattern = TopicPattern(
            pattern="home/{location}/{device_class}",
            variables=("location", "device_class"),
        )
        resolver = TopicPatternResolver(patterns={"sensors": pattern})
        sensor = Sensor.from_dict(
            {
                "id": "temp-legacy",
                "name": "Legacy Temp",
                "type": "sensor",
                "device_class": "temperature",
                "location": "legacy",
                "mqtt": {"topic": "legacy/home/temp"},
            }
        )

        assert resolver.resolve_sensor_topic(sensor) == "legacy/home/temp"

        payload = json.dumps({"reading": 19.0}).encode("utf-8")
        assert sensor.mqtt is not None
        assert sensor.mqtt.topic is not None

        reading = SensorReading.from_mqtt_payload(
            sensor.id,
            payload,
            sensor.mqtt.topic,
            payload_schema=None,
        )

        assert reading.value == 19.0

    @pytest.mark.integration
    def test_mixed_device_config_resolves_custom_and_default_topics(
        self, tmp_path: Path
    ) -> None:
        devices_path = tmp_path / "devices.json"
        _write_devices_config(
            devices_path,
            {
                "temp-default": {
                    "id": "temp-default",
                    "name": "Default Sensor",
                    "type": "sensor",
                    "device_class": "temperature",
                    "location": "kitchen",
                },
                "temp-explicit": {
                    "id": "temp-explicit",
                    "name": "Explicit Sensor",
                    "type": "sensor",
                    "device_class": "temperature",
                    "location": "office",
                    "mqtt": {"topic": "custom/office/temperature"},
                },
            },
        )

        sensors = {sensor.id: sensor for sensor in _load_sensors(devices_path)}
        resolver = TopicPatternResolver(
            patterns={
                "sensors": TopicPattern(
                    pattern="custom/{location}/{device_class}",
                    variables=("location", "device_class"),
                )
            }
        )

        default_topic = resolver.resolve_sensor_topic(sensors["temp-default"])
        explicit_topic = resolver.resolve_sensor_topic(sensors["temp-explicit"])

        assert default_topic == "custom/kitchen/temperature"
        assert explicit_topic == "custom/office/temperature"
