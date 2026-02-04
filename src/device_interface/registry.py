from __future__ import annotations

from typing import TYPE_CHECKING

from src.common.config import ConfigLoader
from src.common.exceptions import DeviceError
from src.common.logging import get_logger
from src.device_interface.models import Actuator, Device, DeviceType, Sensor

if TYPE_CHECKING:
    from collections.abc import Iterator

logger = get_logger(__name__)


class DeviceRegistry:
    def __init__(self, config_loader: ConfigLoader | None = None) -> None:
        self._config_loader = config_loader or ConfigLoader()
        self._devices: dict[str, Device] = {}
        self._loaded = False

    def load(self, config_file: str = "devices.json") -> None:
        data = self._config_loader.load(config_file)
        devices_data = data.get("devices", [])

        self._devices.clear()
        for device_data in devices_data:
            device = Device.from_dict(device_data)
            if device.id in self._devices:
                raise DeviceError(f"Duplicate device ID: {device.id}")
            self._devices[device.id] = device

        self._loaded = True
        logger.info("Loaded %d devices from %s", len(self._devices), config_file)

    def get(self, device_id: str) -> Device:
        self._ensure_loaded()
        if device_id not in self._devices:
            raise DeviceError(f"Device not found: {device_id}")
        return self._devices[device_id]

    def get_optional(self, device_id: str) -> Device | None:
        self._ensure_loaded()
        return self._devices.get(device_id)

    def exists(self, device_id: str) -> bool:
        self._ensure_loaded()
        return device_id in self._devices

    def all_devices(self) -> list[Device]:
        self._ensure_loaded()
        return list(self._devices.values())

    def sensors(self) -> list[Sensor]:
        self._ensure_loaded()
        return [d for d in self._devices.values() if isinstance(d, Sensor)]

    def actuators(self) -> list[Actuator]:
        self._ensure_loaded()
        return [d for d in self._devices.values() if isinstance(d, Actuator)]

    def by_location(self, location: str) -> list[Device]:
        self._ensure_loaded()
        return [d for d in self._devices.values() if d.location == location]

    def by_device_class(self, device_class: str) -> list[Device]:
        self._ensure_loaded()
        return [d for d in self._devices.values() if d.device_class == device_class]

    def by_type(self, device_type: DeviceType) -> list[Device]:
        self._ensure_loaded()
        return [d for d in self._devices.values() if d.device_type == device_type]

    def get_locations(self) -> set[str]:
        self._ensure_loaded()
        return {d.location for d in self._devices.values() if d.location}

    def get_device_classes(self) -> set[str]:
        self._ensure_loaded()
        return {d.device_class for d in self._devices.values()}

    def __len__(self) -> int:
        self._ensure_loaded()
        return len(self._devices)

    def __iter__(self) -> Iterator[Device]:
        self._ensure_loaded()
        return iter(self._devices.values())

    def __contains__(self, device_id: str) -> bool:
        return self.exists(device_id)

    def _ensure_loaded(self) -> None:
        if not self._loaded:
            self.load()
