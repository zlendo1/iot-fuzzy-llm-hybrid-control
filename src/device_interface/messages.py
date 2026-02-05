"""Data models for sensor readings and device commands.

This module defines the data structures used for communication between
the Device Interface layer and upper layers.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any

from src.common.utils import format_timestamp, generate_id


class ReadingQuality(Enum):
    """Quality indicator for sensor readings."""

    GOOD = "good"
    UNCERTAIN = "uncertain"
    BAD = "bad"
    STALE = "stale"


class CommandType(Enum):
    """Type of command sent to an actuator."""

    SET = "set"
    TOGGLE = "toggle"
    INCREASE = "increase"
    DECREASE = "decrease"
    RESET = "reset"


@dataclass(frozen=True)
class SensorReading:
    """Represents a single sensor reading from an MQTT message.

    Attributes:
        sensor_id: Unique identifier of the sensor that produced the reading.
        value: The measured value (type depends on sensor).
        timestamp: When the reading was taken (ISO 8601 format).
        unit: Optional unit of measurement (e.g., "celsius", "percent").
        quality: Data quality indicator.
        raw_topic: Original MQTT topic the reading came from.
        reading_id: Unique identifier for this reading.
    """

    sensor_id: str
    value: float | int | bool | str
    timestamp: str = field(default_factory=lambda: format_timestamp())
    unit: str | None = None
    quality: ReadingQuality = ReadingQuality.GOOD
    raw_topic: str | None = None
    reading_id: str = field(default_factory=lambda: generate_id("reading"))

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data["quality"] = self.quality.value
        return data

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SensorReading:
        """Create a SensorReading from a dictionary."""
        quality = data.get("quality", "good")
        if isinstance(quality, str):
            quality = ReadingQuality(quality)

        return cls(
            sensor_id=data["sensor_id"],
            value=data["value"],
            timestamp=data.get("timestamp", format_timestamp()),
            unit=data.get("unit"),
            quality=quality,
            raw_topic=data.get("raw_topic"),
            reading_id=data.get("reading_id", generate_id("reading")),
        )

    @classmethod
    def from_json(cls, json_str: str) -> SensorReading:
        """Create a SensorReading from a JSON string."""
        return cls.from_dict(json.loads(json_str))

    @classmethod
    def from_mqtt_payload(
        cls,
        sensor_id: str,
        payload: bytes,
        topic: str,
        unit: str | None = None,
    ) -> SensorReading:
        """Create a SensorReading from raw MQTT payload.

        Attempts to parse the payload as JSON first, falling back to
        treating it as a simple value.
        """
        payload_str = payload.decode("utf-8").strip()

        try:
            data = json.loads(payload_str)
            if isinstance(data, dict):
                raw_value = data.get("value", data.get("reading", data.get("v")))
                value: float | int | bool | str = (
                    raw_value if raw_value is not None else payload_str
                )
                raw_timestamp = data.get("timestamp", data.get("time"))
                timestamp: str = (
                    raw_timestamp
                    if isinstance(raw_timestamp, str)
                    else format_timestamp()
                )
                unit = data.get("unit", unit)
                quality_str = data.get("quality", "good")
            else:
                value = data if isinstance(data, (float, int, bool, str)) else str(data)
                timestamp = format_timestamp()
                quality_str = "good"
        except json.JSONDecodeError:
            value = cls._parse_simple_value(payload_str)
            timestamp = format_timestamp()
            quality_str = "good"

        return cls(
            sensor_id=sensor_id,
            value=value,
            timestamp=timestamp,
            unit=unit,
            quality=ReadingQuality(quality_str),
            raw_topic=topic,
        )

    @staticmethod
    def _parse_simple_value(value_str: str) -> float | int | bool | str:
        """Parse a simple string value to appropriate type."""
        lower = value_str.lower()
        if lower in ("true", "on", "1"):
            return True
        if lower in ("false", "off", "0"):
            return False

        try:
            if "." in value_str:
                return float(value_str)
            return int(value_str)
        except ValueError:
            return value_str


@dataclass(frozen=True)
class DeviceCommand:
    """Represents a command to be sent to an actuator.

    Attributes:
        device_id: Unique identifier of the target actuator.
        command_type: Type of command (set, toggle, etc.).
        parameters: Command-specific parameters.
        timestamp: When the command was created (ISO 8601 format).
        command_id: Unique identifier for this command.
        source: Origin of the command (e.g., "rule_engine", "user").
    """

    device_id: str
    command_type: CommandType
    parameters: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: format_timestamp())
    command_id: str = field(default_factory=lambda: generate_id("cmd"))
    source: str = "system"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data["command_type"] = self.command_type.value
        return data

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict())

    def to_mqtt_payload(self) -> bytes:
        """Convert to MQTT payload bytes."""
        return self.to_json().encode("utf-8")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DeviceCommand:
        """Create a DeviceCommand from a dictionary."""
        command_type = data.get("command_type", "set")
        if isinstance(command_type, str):
            command_type = CommandType(command_type)

        return cls(
            device_id=data["device_id"],
            command_type=command_type,
            parameters=data.get("parameters", {}),
            timestamp=data.get("timestamp", format_timestamp()),
            command_id=data.get("command_id", generate_id("cmd")),
            source=data.get("source", "system"),
        )

    @classmethod
    def from_json(cls, json_str: str) -> DeviceCommand:
        """Create a DeviceCommand from a JSON string."""
        return cls.from_dict(json.loads(json_str))

    @classmethod
    def set_value(
        cls,
        device_id: str,
        value: Any,
        source: str = "system",
    ) -> DeviceCommand:
        """Factory method to create a SET command."""
        return cls(
            device_id=device_id,
            command_type=CommandType.SET,
            parameters={"value": value},
            source=source,
        )

    @classmethod
    def toggle(cls, device_id: str, source: str = "system") -> DeviceCommand:
        """Factory method to create a TOGGLE command."""
        return cls(
            device_id=device_id,
            command_type=CommandType.TOGGLE,
            source=source,
        )

    @property
    def value(self) -> Any:
        """Get the 'value' parameter if present."""
        return self.parameters.get("value")
