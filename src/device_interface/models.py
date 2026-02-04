from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class DeviceType(Enum):
    SENSOR = "sensor"
    ACTUATOR = "actuator"


class ValueType(Enum):
    FLOAT = "float"
    INT = "int"
    BOOL = "bool"
    STRING = "string"


@dataclass(frozen=True)
class MQTTConfig:
    topic: str
    command_topic: str | None = None
    qos: int = 1
    retain: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MQTTConfig:
        return cls(
            topic=data["topic"],
            command_topic=data.get("command_topic"),
            qos=data.get("qos", 1),
            retain=data.get("retain", False),
        )


@dataclass(frozen=True)
class Constraints:
    min_value: float | None = None
    max_value: float | None = None
    step: float | None = None
    allowed_values: tuple[Any, ...] | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> Constraints | None:
        if data is None:
            return None
        allowed = data.get("allowed_values")
        return cls(
            min_value=data.get("min"),
            max_value=data.get("max"),
            step=data.get("step"),
            allowed_values=tuple(allowed) if allowed else None,
        )

    def validate(self, value: Any) -> bool:
        if self.allowed_values is not None:
            return value in self.allowed_values

        if isinstance(value, (int, float)):
            if self.min_value is not None and value < self.min_value:
                return False
            if self.max_value is not None and value > self.max_value:
                return False

        return True


@dataclass(frozen=True)
class Device:
    id: str
    name: str
    device_type: DeviceType
    device_class: str
    location: str | None = None
    mqtt: MQTTConfig | None = None
    constraints: Constraints | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Device:
        device_type = DeviceType(data["type"])

        if device_type == DeviceType.SENSOR:
            return Sensor.from_dict(data)
        return Actuator.from_dict(data)


@dataclass(frozen=True)
class Sensor(Device):
    unit: str | None = None
    value_type: ValueType = ValueType.FLOAT

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Sensor:
        mqtt_data = data.get("mqtt")
        constraints_data = data.get("constraints")
        value_type_str = data.get("value_type", "float")

        return cls(
            id=data["id"],
            name=data["name"],
            device_type=DeviceType.SENSOR,
            device_class=data["device_class"],
            location=data.get("location"),
            mqtt=MQTTConfig.from_dict(mqtt_data) if mqtt_data else None,
            constraints=Constraints.from_dict(constraints_data),
            metadata=data.get("metadata", {}),
            unit=data.get("unit"),
            value_type=ValueType(value_type_str),
        )


@dataclass(frozen=True)
class Actuator(Device):
    capabilities: tuple[str, ...] = field(default_factory=tuple)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Actuator:
        mqtt_data = data.get("mqtt")
        constraints_data = data.get("constraints")
        caps = data.get("capabilities", [])

        return cls(
            id=data["id"],
            name=data["name"],
            device_type=DeviceType.ACTUATOR,
            device_class=data["device_class"],
            location=data.get("location"),
            mqtt=MQTTConfig.from_dict(mqtt_data) if mqtt_data else None,
            constraints=Constraints.from_dict(constraints_data),
            metadata=data.get("metadata", {}),
            capabilities=tuple(caps),
        )

    def has_capability(self, capability: str) -> bool:
        return capability in self.capabilities
