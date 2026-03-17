from __future__ import annotations

from src.device_interface.models import Device, TopicPattern

DEFAULT_SENSOR_PATTERN = TopicPattern(
    pattern="home/{location}/{device_class}",
    variables=("location", "device_class"),
)
DEFAULT_ACTUATOR_PATTERN = TopicPattern(
    pattern="home/{location}/{device_class}",
    variables=("location", "device_class"),
)
DEFAULT_COMMAND_PATTERN = TopicPattern(
    pattern="home/{location}/{device_class}/set",
    variables=("location", "device_class"),
)


class TopicPatternResolver:
    def __init__(self, patterns: dict[str, TopicPattern] | None = None) -> None:
        self._patterns = patterns or {}

    def resolve_sensor_topic(self, device: Device) -> str:
        if device.mqtt and device.mqtt.topic:
            return device.mqtt.topic
        pattern = self._patterns.get("sensors", DEFAULT_SENSOR_PATTERN)
        return self._substitute(pattern, device)

    def resolve_actuator_topic(self, device: Device) -> str:
        if device.mqtt and device.mqtt.topic:
            return device.mqtt.topic
        pattern = self._patterns.get("actuators", DEFAULT_ACTUATOR_PATTERN)
        return self._substitute(pattern, device)

    def resolve_command_topic(self, device: Device) -> str:
        if device.mqtt and device.mqtt.command_topic:
            return device.mqtt.command_topic
        pattern = self._patterns.get("commands", DEFAULT_COMMAND_PATTERN)
        return self._substitute(pattern, device)

    def _substitute(self, pattern: TopicPattern, device: Device) -> str:
        attrs: dict[str, str] = {
            "id": device.id,
            "name": device.name,
            "device_class": device.device_class,
            "location": device.location or "",
            "device_type": device.device_type.value,
        }
        result = pattern.pattern
        for var in pattern.variables:
            result = result.replace(f"{{{var}}}", attrs.get(var, ""))
        return result
