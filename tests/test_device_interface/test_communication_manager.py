
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
