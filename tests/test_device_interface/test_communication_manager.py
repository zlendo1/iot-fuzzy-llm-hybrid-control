from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import Mock

import pytest


@pytest.mark.unit
def test_manager_not_started_initially() -> None:
    from src.device_interface.communication_manager import MQTTCommunicationManager

    manager = MQTTCommunicationManager()

    assert manager.is_started is False
    assert manager.is_connected is False


@pytest.mark.unit
def test_manager_registry_unavailable_before_start() -> None:
    from src.common.exceptions import DeviceError
    from src.device_interface.communication_manager import MQTTCommunicationManager

    manager = MQTTCommunicationManager()

    with pytest.raises(DeviceError, match="registry unavailable"):
        _ = manager.registry


@pytest.mark.unit
def test_manager_get_latest_reading_returns_none_when_empty() -> None:
    from src.device_interface.communication_manager import MQTTCommunicationManager

    manager = MQTTCommunicationManager()

    assert manager.get_latest_reading("temp-001") is None


@pytest.mark.unit
def test_manager_get_all_latest_readings_returns_empty() -> None:
    from src.device_interface.communication_manager import MQTTCommunicationManager

    manager = MQTTCommunicationManager()

    assert manager.get_all_latest_readings() == {}


@pytest.mark.unit
def test_manager_send_command_fails_when_not_connected() -> None:
    from src.device_interface.communication_manager import MQTTCommunicationManager
    from src.device_interface.messages import CommandType, DeviceCommand

    manager = MQTTCommunicationManager()
    command = DeviceCommand(
        device_id="ac-001",
        command_type=CommandType.SET,
        parameters={"value": 22},
    )

    result = manager.send_command(command)

    assert result is False


@pytest.mark.unit
def test_manager_get_device_status_returns_unknown_before_start() -> None:
    from src.device_interface.communication_manager import MQTTCommunicationManager
    from src.device_interface.device_monitor import DeviceStatus

    manager = MQTTCommunicationManager()

    assert manager.get_device_status("temp-001") == DeviceStatus.UNKNOWN


@pytest.mark.unit
def test_manager_add_remove_reading_callback() -> None:
    from src.device_interface.communication_manager import MQTTCommunicationManager
    from src.device_interface.messages import SensorReading

    manager = MQTTCommunicationManager()

    def callback(_reading: SensorReading) -> None:
        pass

    manager.add_reading_callback(callback)
    assert callback in manager._reading_callbacks

    manager.remove_reading_callback(callback)
    assert callback not in manager._reading_callbacks


@pytest.mark.unit
def test_device_interface_protocol_is_abstract() -> None:
    from src.device_interface.communication_manager import DeviceInterfaceProtocol

    with pytest.raises(TypeError, match="abstract"):
        DeviceInterfaceProtocol()  # type: ignore[abstract]


@pytest.mark.unit
def test_subscribe_uses_resolver_when_topic_missing() -> None:
    from src.device_interface.communication_manager import MQTTCommunicationManager
    from src.device_interface.models import Sensor

    class DummyRegistry:
        def __init__(self, sensors: list[Sensor]) -> None:
            self._sensors = sensors

        def sensors(self) -> list[Sensor]:
            return self._sensors

    class DummyMQTTClient:
        def __init__(self) -> None:
            self.subscriptions: list[tuple[str | None, object, int]] = []

        def subscribe(self, topic: str | None, callback: object, qos: int = 1) -> None:
            self.subscriptions.append((topic, callback, qos))

    manager = MQTTCommunicationManager()
    sensor = Sensor.from_dict(
        {
            "id": "temp-001",
            "name": "Temp",
            "type": "sensor",
            "device_class": "temperature",
            "location": "lab",
            "mqtt": {"qos": 1},
        }
    )
    cast(Any, manager)._registry = DummyRegistry([sensor])
    dummy_client = DummyMQTTClient()
    cast(Any, manager)._mqtt_client = dummy_client
    resolver = Mock()
    resolver.resolve_sensor_topic.return_value = "resolved/topic"
    cast(Any, manager)._topic_resolver = resolver

    manager._subscribe_to_sensors()

    assert dummy_client.subscriptions[0][0] == "resolved/topic"
    resolver.resolve_sensor_topic.assert_called_once_with(sensor)


@pytest.mark.unit
def test_handle_sensor_message_passes_payload_schema(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from src.device_interface.communication_manager import MQTTCommunicationManager
    from src.device_interface.messages import SensorReading
    from src.device_interface.models import PayloadSchema

    manager = MQTTCommunicationManager()
    payload_schema = PayloadSchema(value_field="value")
    sensor = SimpleNamespace(
        id="temp-001",
        unit="C",
        mqtt=SimpleNamespace(payload_mapping=payload_schema),
    )
    captured: dict[str, object] = {}

    def fake_from_mqtt_payload(
        cls: type[SensorReading],
        *,
        sensor_id: str,
        payload: bytes,
        topic: str,
        unit: str | None = None,
        payload_schema: object | None = None,
    ) -> SensorReading:
        captured["payload_schema"] = payload_schema
        return SensorReading(sensor_id=sensor_id, value=1.0, unit=unit, raw_topic=topic)

    monkeypatch.setattr(
        SensorReading,
        "from_mqtt_payload",
        classmethod(fake_from_mqtt_payload),
    )

    manager._handle_sensor_message(
        cast(Any, sensor),
        "topic",
        b'{"value": 1}',
        1,
    )

    assert captured["payload_schema"] is payload_schema


@pytest.mark.unit
def test_start_initializes_topic_resolver_without_patterns(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from src.device_interface.communication_manager import MQTTCommunicationManager

    class DummyRegistry:
        def __init__(self, _loader: object) -> None:
            self._devices: list[object] = []

        def load(self, _file: str) -> None:
            return None

        def __iter__(self):
            return iter(self._devices)

        def __len__(self) -> int:
            return len(self._devices)

        def sensors(self) -> list[object]:
            return []

    class DummyMQTTClient:
        def __init__(self, _config: object) -> None:
            self.is_connected = True

        def connect(self, timeout: float = 10.0) -> None:  # noqa: ARG002
            return None

    class DummyDeviceMonitor:
        def register_device(self, _device_id: str) -> None:
            return None

        def start_monitoring(self) -> None:
            return None

        def stop_monitoring(self) -> None:
            return None

    class DummyResolver:
        def __init__(self, patterns: object | None = None) -> None:
            self.patterns = patterns

    class DummyConfigLoader:
        def load(self, _file: str) -> dict[str, object]:
            return {}

    monkeypatch.setattr(
        "src.device_interface.communication_manager.DeviceRegistry",
        DummyRegistry,
    )
    monkeypatch.setattr(
        "src.device_interface.communication_manager.MQTTClient",
        DummyMQTTClient,
    )
    monkeypatch.setattr(
        "src.device_interface.communication_manager.DeviceMonitor",
        DummyDeviceMonitor,
    )
    monkeypatch.setattr(
        "src.device_interface.communication_manager.TopicPatternResolver",
        DummyResolver,
        raising=False,
    )

    manager = MQTTCommunicationManager(config_loader=cast(Any, DummyConfigLoader()))
    manager.start(connect_timeout=0.1)

    resolver = getattr(manager, "_topic_resolver", None)
    assert resolver is not None
    assert isinstance(resolver, DummyResolver)
    assert resolver.patterns in (None, {})
