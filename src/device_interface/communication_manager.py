"""MQTT Communication Manager - Layer Coordinator for Device Interface.

This is the sole interface between the Device Interface layer and the
Data Processing layer above. It orchestrates the MQTTClient, DeviceRegistry,
and DeviceMonitor components.
"""

from __future__ import annotations

import threading
from abc import ABC, abstractmethod
from collections.abc import Callable

from src.common.config import ConfigLoader
from src.common.exceptions import DeviceError, MQTTError
from src.common.logging import get_logger
from src.device_interface.device_monitor import DeviceMonitor, DeviceStatus
from src.device_interface.messages import (
    DeviceCommand,
    SensorReading,
)
from src.device_interface.models import Actuator, Sensor
from src.device_interface.mqtt_client import (
    MessageCallback,
    MQTTClient,
    MQTTClientConfig,
)
from src.device_interface.registry import DeviceRegistry

logger = get_logger(__name__)

SensorReadingCallback = Callable[[SensorReading], None]
DeviceStatusCallback = Callable[[str, DeviceStatus, DeviceStatus], None]


class DeviceInterfaceProtocol(ABC):
    """Abstract interface for upper layer (Data Processing) interaction."""

    @abstractmethod
    def get_latest_reading(self, sensor_id: str) -> SensorReading | None:
        """Get the most recent reading for a sensor."""
        ...

    @abstractmethod
    def get_all_latest_readings(self) -> dict[str, SensorReading]:
        """Get the most recent readings for all sensors."""
        ...

    @abstractmethod
    def send_command(self, command: DeviceCommand) -> bool:
        """Send a command to an actuator. Returns True on success."""
        ...

    @abstractmethod
    def get_device_status(self, device_id: str) -> DeviceStatus:
        """Get the availability status of a device."""
        ...

    @abstractmethod
    def add_reading_callback(self, callback: SensorReadingCallback) -> None:
        """Register callback for new sensor readings."""
        ...

    @abstractmethod
    def remove_reading_callback(self, callback: SensorReadingCallback) -> None:
        """Unregister a reading callback."""
        ...


class MQTTCommunicationManager(DeviceInterfaceProtocol):
    """Layer coordinator for Device Interface.

    Orchestrates:
    - DeviceRegistry: device configuration and metadata
    - MQTTClient: MQTT broker communication
    - DeviceMonitor: device availability tracking
    """

    def __init__(
        self,
        config_loader: ConfigLoader | None = None,
        mqtt_config_file: str = "mqtt_config.json",
        devices_config_file: str = "devices.json",
    ) -> None:
        self._config_loader = config_loader or ConfigLoader()
        self._mqtt_config_file = mqtt_config_file
        self._devices_config_file = devices_config_file

        self._registry: DeviceRegistry | None = None
        self._mqtt_client: MQTTClient | None = None
        self._device_monitor: DeviceMonitor | None = None

        self._latest_readings: dict[str, SensorReading] = {}
        self._reading_callbacks: list[SensorReadingCallback] = []
        self._lock = threading.RLock()
        self._started = False

    @property
    def is_started(self) -> bool:
        return self._started

    @property
    def is_connected(self) -> bool:
        return self._mqtt_client is not None and self._mqtt_client.is_connected

    @property
    def registry(self) -> DeviceRegistry:
        if self._registry is None:
            raise DeviceError("Manager not started - registry unavailable")
        return self._registry

    def start(self, connect_timeout: float = 10.0) -> None:
        if self._started:
            logger.warning("Manager already started")
            return

        logger.info("Starting MQTT Communication Manager")

        self._registry = DeviceRegistry(self._config_loader)
        self._registry.load(self._devices_config_file)

        mqtt_config_data = self._config_loader.load(self._mqtt_config_file)
        mqtt_config = MQTTClientConfig.from_dict(mqtt_config_data)
        self._mqtt_client = MQTTClient(mqtt_config)

        self._device_monitor = DeviceMonitor()
        for device in self._registry:
            self._device_monitor.register_device(device.id)

        self._mqtt_client.connect(timeout=connect_timeout)
        self._subscribe_to_sensors()
        self._device_monitor.start_monitoring()

        self._started = True
        logger.info(
            "MQTT Communication Manager started with %d devices",
            len(self._registry),
        )

    def stop(self) -> None:
        if not self._started:
            return

        logger.info("Stopping MQTT Communication Manager")

        if self._device_monitor:
            self._device_monitor.stop_monitoring()

        if self._mqtt_client:
            self._mqtt_client.disconnect()

        self._started = False
        logger.info("MQTT Communication Manager stopped")

    def get_latest_reading(self, sensor_id: str) -> SensorReading | None:
        with self._lock:
            return self._latest_readings.get(sensor_id)

    def get_all_latest_readings(self) -> dict[str, SensorReading]:
        with self._lock:
            return dict(self._latest_readings)

    def send_command(self, command: DeviceCommand) -> bool:
        if not self.is_connected:
            logger.error("Cannot send command - not connected")
            return False

        if self._registry is None:
            logger.error("Registry not initialized")
            return False

        device = self._registry.get_optional(command.device_id)
        if device is None:
            logger.error("Unknown device: %s", command.device_id)
            return False

        if not isinstance(device, Actuator):
            logger.error("Device %s is not an actuator", command.device_id)
            return False

        if device.mqtt is None or device.mqtt.command_topic is None:
            logger.error("No command topic for device %s", command.device_id)
            return False

        if (
            device.constraints
            and command.value is not None
            and not device.constraints.validate(command.value)
        ):
            logger.error(
                "Command value %s violates constraints for %s",
                command.value,
                command.device_id,
            )
            return False

        try:
            self._mqtt_client.publish(  # type: ignore[union-attr]
                device.mqtt.command_topic,
                command.to_mqtt_payload(),
                qos=device.mqtt.qos,
                retain=device.mqtt.retain,
            )
            logger.info(
                "Sent command to %s: %s",
                command.device_id,
                command.command_type.value,
            )
            return True
        except MQTTError:
            logger.exception("Failed to send command to %s", command.device_id)
            return False

    def get_device_status(self, device_id: str) -> DeviceStatus:
        if self._device_monitor is None:
            return DeviceStatus.UNKNOWN
        return self._device_monitor.get_status(device_id)

    def add_reading_callback(self, callback: SensorReadingCallback) -> None:
        with self._lock:
            self._reading_callbacks.append(callback)

    def remove_reading_callback(self, callback: SensorReadingCallback) -> None:
        with self._lock:
            if callback in self._reading_callbacks:
                self._reading_callbacks.remove(callback)

    def add_status_callback(self, callback: DeviceStatusCallback) -> None:
        if self._device_monitor:
            self._device_monitor.add_status_callback(callback)

    def _subscribe_to_sensors(self) -> None:
        if self._mqtt_client is None or self._registry is None:
            return

        sensors = self._registry.sensors()
        for sensor in sensors:
            if sensor.mqtt is None:
                logger.warning("Sensor %s has no MQTT config", sensor.id)
                continue

            self._mqtt_client.subscribe(
                sensor.mqtt.topic,
                self._create_sensor_callback(sensor),
                qos=sensor.mqtt.qos,
            )
            logger.debug("Subscribed to sensor %s on %s", sensor.id, sensor.mqtt.topic)

        logger.info("Subscribed to %d sensor topics", len(sensors))

    def _create_sensor_callback(self, sensor: Sensor) -> MessageCallback:
        def callback(topic: str, payload: bytes, qos: int) -> None:
            self._handle_sensor_message(sensor, topic, payload, qos)

        return callback

    def _handle_sensor_message(
        self,
        sensor: Sensor,
        topic: str,
        payload: bytes,
        _qos: int,
    ) -> None:
        try:
            reading = SensorReading.from_mqtt_payload(
                sensor_id=sensor.id,
                payload=payload,
                topic=topic,
                unit=sensor.unit,
            )

            with self._lock:
                self._latest_readings[sensor.id] = reading
                callbacks = list(self._reading_callbacks)

            if self._device_monitor:
                self._device_monitor.record_activity(sensor.id, topic)

            for callback in callbacks:
                try:
                    callback(reading)
                except Exception:
                    logger.exception("Error in reading callback")

            logger.debug(
                "Received reading from %s: %s %s",
                sensor.id,
                reading.value,
                reading.unit or "",
            )

        except Exception:
            logger.exception("Error processing message from %s", topic)
