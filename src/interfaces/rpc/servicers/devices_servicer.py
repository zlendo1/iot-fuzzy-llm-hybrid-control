from __future__ import annotations

from datetime import UTC, datetime

import grpc
from google.protobuf.timestamp_pb2 import Timestamp

from src.common.logging import get_logger
from src.configuration.system_orchestrator import SystemOrchestrator
from src.device_interface.device_monitor import DeviceStatus
from src.device_interface.messages import CommandType, DeviceCommand, SensorReading
from src.device_interface.models import Actuator, Device
from src.interfaces.rpc.error_mapping import handle_grpc_errors
from src.interfaces.rpc.generated import devices_pb2, devices_pb2_grpc

logger = get_logger(__name__)


class DevicesServicer(devices_pb2_grpc.DevicesServiceServicer):
    def __init__(self, orchestrator: SystemOrchestrator) -> None:
        self._orchestrator = orchestrator

    @handle_grpc_errors
    def ListDevices(
        self,
        request: devices_pb2.ListDevicesRequest,
        context: grpc.ServicerContext,
    ) -> devices_pb2.ListDevicesResponse:
        del request, context
        registry = self._require_registry()
        devices = [self._to_proto_device(device) for device in registry.all_devices()]
        return devices_pb2.ListDevicesResponse(devices=devices)

    @handle_grpc_errors
    def GetDevice(
        self,
        request: devices_pb2.GetDeviceRequest,
        context: grpc.ServicerContext,
    ) -> devices_pb2.GetDeviceResponse:
        registry = self._require_registry()
        device = registry.get_optional(request.device_id)
        if device is None:
            context.abort(grpc.StatusCode.NOT_FOUND, "Device not found")
            return devices_pb2.GetDeviceResponse()
        return devices_pb2.GetDeviceResponse(device=self._to_proto_device(device))

    @handle_grpc_errors
    def GetDeviceStatus(
        self,
        request: devices_pb2.GetDeviceStatusRequest,
        context: grpc.ServicerContext,
    ) -> devices_pb2.GetDeviceStatusResponse:
        registry = self._require_registry()
        if not registry.exists(request.device_id):
            context.abort(grpc.StatusCode.NOT_FOUND, "Device not found")
            return devices_pb2.GetDeviceStatusResponse()

        manager = self._require_mqtt_manager()
        status = manager.get_device_status(request.device_id)
        online = status == DeviceStatus.ONLINE
        last_seen = self._last_seen_for_device(request.device_id)

        return devices_pb2.GetDeviceStatusResponse(
            device_id=request.device_id,
            online=online,
            last_seen=last_seen,
        )

    @handle_grpc_errors
    def GetLatestReading(
        self,
        request: devices_pb2.GetLatestReadingRequest,
        context: grpc.ServicerContext,
    ) -> devices_pb2.GetLatestReadingResponse:
        registry = self._require_registry()
        if not registry.exists(request.device_id):
            context.abort(grpc.StatusCode.NOT_FOUND, "Device not found")
            return devices_pb2.GetLatestReadingResponse()

        manager = self._require_mqtt_manager()
        reading = manager.get_latest_reading(request.device_id)
        if reading is None:
            context.abort(grpc.StatusCode.NOT_FOUND, "No reading available for device")
            return devices_pb2.GetLatestReadingResponse()

        return devices_pb2.GetLatestReadingResponse(
            reading=self._to_proto_reading(reading)
        )

    @handle_grpc_errors
    def SendCommand(
        self,
        request: devices_pb2.SendCommandRequest,
        context: grpc.ServicerContext,
    ) -> devices_pb2.SendCommandResponse:
        del context
        manager = self._require_mqtt_manager()
        command = self._to_domain_command(request.command)

        success = manager.send_command(command)
        if success:
            return devices_pb2.SendCommandResponse(success=True, message="Command sent")

        return devices_pb2.SendCommandResponse(
            success=False,
            message="Failed to send command",
        )

    def _require_registry(self):
        registry = self._orchestrator.device_registry
        if registry is None:
            raise RuntimeError("Device registry unavailable")
        return registry

    def _require_mqtt_manager(self):
        manager = self._orchestrator._mqtt_manager
        if manager is None:
            raise RuntimeError("MQTT communication manager unavailable")
        return manager

    def _last_seen_for_device(self, device_id: str) -> Timestamp:
        manager = self._require_mqtt_manager()
        monitor = getattr(manager, "_device_monitor", None)
        if monitor is None:
            return Timestamp()

        state = monitor.get_state(device_id)
        if state is None or state.last_seen is None:
            return Timestamp()
        return self._timestamp_from_iso(state.last_seen)

    @staticmethod
    def _to_proto_device(device: Device) -> devices_pb2.Device:
        capabilities: list[str] = []
        if isinstance(device, Actuator):
            capabilities = list(device.capabilities)

        return devices_pb2.Device(
            id=device.id,
            name=device.name,
            type=device.device_type.value,
            location=device.location or "",
            capabilities=capabilities,
        )

    @staticmethod
    def _to_proto_reading(reading: SensorReading) -> devices_pb2.SensorReading:
        value = reading.value
        if isinstance(value, bool):
            numeric_value = float(int(value))
        elif isinstance(value, (int, float)):
            numeric_value = float(value)
        else:
            numeric_value = 0.0

        return devices_pb2.SensorReading(
            device_id=reading.sensor_id,
            value=numeric_value,
            unit=reading.unit or "",
            timestamp=DevicesServicer._timestamp_from_iso(reading.timestamp),
        )

    @staticmethod
    def _to_domain_command(command: devices_pb2.DeviceCommand) -> DeviceCommand:
        action = command.action.lower().strip()
        command_type = (
            CommandType.SET if action == CommandType.SET.value else CommandType.TOGGLE
        )
        return DeviceCommand(
            device_id=command.device_id,
            command_type=command_type,
            parameters=dict(command.parameters),
        )

    @staticmethod
    def _timestamp_from_iso(timestamp_str: str) -> Timestamp:
        normalized = timestamp_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(normalized)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)

        ts = Timestamp()
        ts.FromDatetime(dt)
        return ts
