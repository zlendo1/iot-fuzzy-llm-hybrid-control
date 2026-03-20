from __future__ import annotations

from importlib import import_module
from typing import Any
from unittest.mock import MagicMock

import grpc
import pytest

from src.device_interface.device_monitor import DeviceState, DeviceStatus
from src.device_interface.messages import CommandType, DeviceCommand, SensorReading
from src.device_interface.models import Actuator, DeviceType, Sensor
from src.interfaces.rpc.generated import devices_pb2


@pytest.fixture
def devices_servicer_cls() -> Any:
    module = import_module("src.interfaces.rpc.servicers.devices_servicer")
    return module.DevicesServicer


@pytest.fixture
def mock_orchestrator() -> MagicMock:
    orchestrator = MagicMock()
    orchestrator.device_registry = MagicMock()
    orchestrator._mqtt_manager = MagicMock()
    return orchestrator


@pytest.fixture
def mock_context() -> MagicMock:
    return MagicMock()


@pytest.fixture
def sample_sensor() -> Sensor:
    return Sensor(
        id="temp_1",
        name="Temperature Sensor",
        device_type=DeviceType.SENSOR,
        device_class="temperature",
        location="living_room",
        unit="celsius",
    )


@pytest.fixture
def sample_actuator() -> Actuator:
    return Actuator(
        id="ac_1",
        name="AC Unit",
        device_type=DeviceType.ACTUATOR,
        device_class="ac",
        location="living_room",
        capabilities=("turn_on", "turn_off", "set_temp"),
    )


class TestDevicesServicer:
    def test_list_devices_returns_all_devices(
        self,
        devices_servicer_cls: Any,
        mock_orchestrator: MagicMock,
        mock_context: MagicMock,
        sample_sensor: Sensor,
        sample_actuator: Actuator,
    ) -> None:
        servicer = devices_servicer_cls(mock_orchestrator)
        mock_orchestrator.device_registry.all_devices.return_value = [
            sample_sensor,
            sample_actuator,
        ]

        response = servicer.ListDevices(devices_pb2.ListDevicesRequest(), mock_context)

        assert len(response.devices) == 2
        assert response.devices[0].id == "temp_1"
        assert response.devices[0].type == "sensor"
        assert response.devices[0].capabilities == []
        assert response.devices[1].id == "ac_1"
        assert response.devices[1].type == "actuator"
        assert list(response.devices[1].capabilities) == [
            "turn_on",
            "turn_off",
            "set_temp",
        ]

    def test_get_device_returns_device_when_found(
        self,
        devices_servicer_cls: Any,
        mock_orchestrator: MagicMock,
        mock_context: MagicMock,
        sample_sensor: Sensor,
    ) -> None:
        servicer = devices_servicer_cls(mock_orchestrator)
        mock_orchestrator.device_registry.get_optional.return_value = sample_sensor

        response = servicer.GetDevice(
            devices_pb2.GetDeviceRequest(device_id="temp_1"),
            mock_context,
        )

        assert response.device.id == "temp_1"
        assert response.device.name == "Temperature Sensor"
        assert response.device.type == "sensor"

    def test_get_device_aborts_not_found(
        self,
        devices_servicer_cls: Any,
        mock_orchestrator: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        servicer = devices_servicer_cls(mock_orchestrator)
        mock_orchestrator.device_registry.get_optional.return_value = None

        servicer.GetDevice(
            devices_pb2.GetDeviceRequest(device_id="unknown"), mock_context
        )

        mock_context.abort.assert_called_once_with(
            grpc.StatusCode.NOT_FOUND,
            "Device not found",
        )

    def test_get_device_status_returns_online_and_last_seen(
        self,
        devices_servicer_cls: Any,
        mock_orchestrator: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        servicer = devices_servicer_cls(mock_orchestrator)
        mock_orchestrator.device_registry.exists.return_value = True
        mock_orchestrator._mqtt_manager.get_device_status.return_value = (
            DeviceStatus.ONLINE
        )
        mock_orchestrator._mqtt_manager._device_monitor.get_state.return_value = (
            DeviceState(
                device_id="temp_1",
                status=DeviceStatus.ONLINE,
                last_seen="2026-03-19T10:20:30Z",
            )
        )

        response = servicer.GetDeviceStatus(
            devices_pb2.GetDeviceStatusRequest(device_id="temp_1"),
            mock_context,
        )

        assert response.device_id == "temp_1"
        assert response.online is True
        assert response.last_seen.seconds > 0

    def test_get_device_status_aborts_not_found(
        self,
        devices_servicer_cls: Any,
        mock_orchestrator: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        servicer = devices_servicer_cls(mock_orchestrator)
        mock_orchestrator.device_registry.exists.return_value = False

        servicer.GetDeviceStatus(
            devices_pb2.GetDeviceStatusRequest(device_id="missing"),
            mock_context,
        )

        mock_context.abort.assert_called_once_with(
            grpc.StatusCode.NOT_FOUND,
            "Device not found",
        )

    def test_get_latest_reading_returns_reading(
        self,
        devices_servicer_cls: Any,
        mock_orchestrator: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        servicer = devices_servicer_cls(mock_orchestrator)
        mock_orchestrator.device_registry.exists.return_value = True
        mock_orchestrator._mqtt_manager.get_latest_reading.return_value = SensorReading(
            sensor_id="temp_1",
            value=23.5,
            unit="celsius",
            timestamp="2026-03-19T11:00:00Z",
        )

        response = servicer.GetLatestReading(
            devices_pb2.GetLatestReadingRequest(device_id="temp_1"),
            mock_context,
        )

        assert response.reading.device_id == "temp_1"
        assert response.reading.value == pytest.approx(23.5)
        assert response.reading.unit == "celsius"
        assert response.reading.timestamp.seconds > 0

    def test_get_latest_reading_aborts_not_found(
        self,
        devices_servicer_cls: Any,
        mock_orchestrator: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        servicer = devices_servicer_cls(mock_orchestrator)
        mock_orchestrator.device_registry.exists.return_value = False

        servicer.GetLatestReading(
            devices_pb2.GetLatestReadingRequest(device_id="missing"),
            mock_context,
        )

        mock_context.abort.assert_called_once_with(
            grpc.StatusCode.NOT_FOUND,
            "Device not found",
        )

    def test_get_latest_reading_aborts_when_missing_data(
        self,
        devices_servicer_cls: Any,
        mock_orchestrator: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        servicer = devices_servicer_cls(mock_orchestrator)
        mock_orchestrator.device_registry.exists.return_value = True
        mock_orchestrator._mqtt_manager.get_latest_reading.return_value = None

        servicer.GetLatestReading(
            devices_pb2.GetLatestReadingRequest(device_id="temp_1"),
            mock_context,
        )

        mock_context.abort.assert_called_once_with(
            grpc.StatusCode.NOT_FOUND,
            "No reading available for device",
        )

    def test_send_command_sends_via_communication_manager(
        self,
        devices_servicer_cls: Any,
        mock_orchestrator: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        servicer = devices_servicer_cls(mock_orchestrator)
        mock_orchestrator._mqtt_manager.send_command.return_value = True

        response = servicer.SendCommand(
            devices_pb2.SendCommandRequest(
                command=devices_pb2.DeviceCommand(
                    device_id="ac_1",
                    action="set",
                    parameters={"value": "24"},
                )
            ),
            mock_context,
        )

        sent_command = mock_orchestrator._mqtt_manager.send_command.call_args[0][0]
        assert isinstance(sent_command, DeviceCommand)
        assert sent_command.device_id == "ac_1"
        assert sent_command.command_type == CommandType.SET
        assert sent_command.parameters == {"value": "24"}
        assert response.success is True

    def test_send_command_returns_failure_response_on_send_failure(
        self,
        devices_servicer_cls: Any,
        mock_orchestrator: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        servicer = devices_servicer_cls(mock_orchestrator)
        mock_orchestrator._mqtt_manager.send_command.return_value = False

        response = servicer.SendCommand(
            devices_pb2.SendCommandRequest(
                command=devices_pb2.DeviceCommand(device_id="ac_1", action="toggle")
            ),
            mock_context,
        )

        assert response.success is False
        assert response.message == "Failed to send command"

    def test_send_command_maps_non_set_action_to_toggle(
        self,
        devices_servicer_cls: Any,
        mock_orchestrator: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        servicer = devices_servicer_cls(mock_orchestrator)
        mock_orchestrator._mqtt_manager.send_command.return_value = True

        servicer.SendCommand(
            devices_pb2.SendCommandRequest(
                command=devices_pb2.DeviceCommand(device_id="ac_1", action="toggle")
            ),
            mock_context,
        )

        sent_command = mock_orchestrator._mqtt_manager.send_command.call_args[0][0]
        assert sent_command.command_type == CommandType.TOGGLE

    def test_all_methods_are_wrapped_with_handle_grpc_errors(
        self,
        devices_servicer_cls: Any,
        mock_orchestrator: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        servicer = devices_servicer_cls(mock_orchestrator)
        mock_orchestrator.device_registry.all_devices.side_effect = RuntimeError("boom")

        servicer.ListDevices(devices_pb2.ListDevicesRequest(), mock_context)

        mock_context.abort.assert_called_once_with(grpc.StatusCode.INTERNAL, "boom")
