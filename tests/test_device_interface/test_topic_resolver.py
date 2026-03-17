from importlib import import_module

import pytest

from src.device_interface.models import (
    Actuator,
    DeviceType,
    MQTTConfig,
    Sensor,
    TopicPattern,
)

TopicPatternResolver = import_module(
    "src.device_interface.topic_resolver"
).TopicPatternResolver


@pytest.mark.unit
class TestTopicPatternResolver:
    def _make_sensor(
        self,
        *,
        location: str | None = "living_room",
        device_class: str = "temperature",
        mqtt: MQTTConfig | None = None,
    ) -> Sensor:
        return Sensor(
            id="temp_1",
            name="Temperature Sensor",
            device_type=DeviceType.SENSOR,
            device_class=device_class,
            location=location,
            mqtt=mqtt,
        )

    def _make_actuator(
        self,
        *,
        location: str | None = "living_room",
        device_class: str = "thermostat",
        mqtt: MQTTConfig | None = None,
    ) -> Actuator:
        return Actuator(
            id="ac_1",
            name="AC Unit",
            device_type=DeviceType.ACTUATOR,
            device_class=device_class,
            location=location,
            mqtt=mqtt,
        )

    def test_resolve_sensor_topic_default_pattern(self) -> None:
        resolver = TopicPatternResolver()
        device = self._make_sensor(location="living_room", device_class="temperature")

        assert resolver.resolve_sensor_topic(device) == "home/living_room/temperature"

    def test_resolve_actuator_topic_default_pattern(self) -> None:
        resolver = TopicPatternResolver()
        device = self._make_actuator(
            location="living_room",
            device_class="thermostat",
        )

        assert resolver.resolve_actuator_topic(device) == "home/living_room/thermostat"

    def test_resolve_command_topic_default_pattern(self) -> None:
        resolver = TopicPatternResolver()
        device = self._make_actuator(
            location="living_room",
            device_class="thermostat",
        )

        assert (
            resolver.resolve_command_topic(device) == "home/living_room/thermostat/set"
        )

    def test_explicit_mqtt_topic_takes_precedence(self) -> None:
        resolver = TopicPatternResolver()
        mqtt = MQTTConfig(topic="custom/topic")
        device = self._make_sensor(mqtt=mqtt)

        assert resolver.resolve_sensor_topic(device) == "custom/topic"

    def test_custom_sensor_pattern(self) -> None:
        patterns = {
            "sensors": TopicPattern(
                pattern="custom/{location}/{device_class}",
                variables=("location", "device_class"),
            )
        }
        resolver = TopicPatternResolver(patterns=patterns)
        device = self._make_sensor(location="living_room", device_class="temperature")

        assert resolver.resolve_sensor_topic(device) == "custom/living_room/temperature"

    def test_custom_actuator_pattern(self) -> None:
        patterns = {
            "actuators": TopicPattern(
                pattern="act/{location}/{device_class}",
                variables=("location", "device_class"),
            )
        }
        resolver = TopicPatternResolver(patterns=patterns)
        device = self._make_actuator(location="living_room", device_class="thermostat")

        assert resolver.resolve_actuator_topic(device) == "act/living_room/thermostat"

    def test_custom_command_pattern(self) -> None:
        patterns = {
            "commands": TopicPattern(
                pattern="cmd/{location}/{device_class}/set",
                variables=("location", "device_class"),
            )
        }
        resolver = TopicPatternResolver(patterns=patterns)
        device = self._make_actuator(location="living_room", device_class="thermostat")

        assert (
            resolver.resolve_command_topic(device) == "cmd/living_room/thermostat/set"
        )

    def test_device_without_location(self) -> None:
        resolver = TopicPatternResolver()
        device = self._make_sensor(location=None)

        assert resolver.resolve_sensor_topic(device) == "home//temperature"

    def test_resolve_with_device_id_variable(self) -> None:
        patterns = {
            "sensors": TopicPattern(
                pattern="devices/{id}/readings",
                variables=("id",),
            )
        }
        resolver = TopicPatternResolver(patterns=patterns)
        device = self._make_sensor()

        assert resolver.resolve_sensor_topic(device) == "devices/temp_1/readings"

    def test_resolve_with_device_name_variable(self) -> None:
        patterns = {
            "sensors": TopicPattern(
                pattern="devices/{name}/readings",
                variables=("name",),
            )
        }
        resolver = TopicPatternResolver(patterns=patterns)
        device = self._make_sensor()

        assert (
            resolver.resolve_sensor_topic(device)
            == "devices/Temperature Sensor/readings"
        )

    def test_no_patterns_uses_defaults(self) -> None:
        resolver = TopicPatternResolver()
        device = self._make_sensor(location="living_room", device_class="temperature")

        assert resolver.resolve_sensor_topic(device) == "home/living_room/temperature"

    def test_resolver_with_empty_patterns_dict(self) -> None:
        resolver = TopicPatternResolver(patterns={})
        device = self._make_sensor(location="living_room", device_class="temperature")

        assert resolver.resolve_sensor_topic(device) == "home/living_room/temperature"
