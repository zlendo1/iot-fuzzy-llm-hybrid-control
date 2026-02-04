import json
from pathlib import Path

import pytest


@pytest.fixture
def sample_devices_config(tmp_path: Path) -> Path:
    config = {
        "devices": [
            {
                "id": "temp_sensor_1",
                "name": "Temperature Sensor 1",
                "type": "sensor",
                "device_class": "temperature",
                "location": "living_room",
                "unit": "°C",
                "value_type": "float",
                "mqtt": {"topic": "home/living_room/temperature", "qos": 1},
                "constraints": {"min": -40, "max": 85},
            },
            {
                "id": "humidity_sensor_1",
                "name": "Humidity Sensor 1",
                "type": "sensor",
                "device_class": "humidity",
                "location": "living_room",
                "unit": "%",
                "mqtt": {"topic": "home/living_room/humidity"},
            },
            {
                "id": "ac_unit_1",
                "name": "AC Unit 1",
                "type": "actuator",
                "device_class": "thermostat",
                "location": "living_room",
                "capabilities": ["set_temperature", "turn_on", "turn_off"],
                "mqtt": {
                    "topic": "home/living_room/ac/state",
                    "command_topic": "home/living_room/ac/set",
                },
                "constraints": {"min": 16, "max": 30},
            },
            {
                "id": "light_1",
                "name": "Light 1",
                "type": "actuator",
                "device_class": "light",
                "location": "bedroom",
                "capabilities": ["turn_on", "turn_off"],
                "mqtt": {"topic": "home/bedroom/light/state"},
            },
        ]
    }
    config_file = tmp_path / "devices.json"
    config_file.write_text(json.dumps(config))
    return tmp_path


@pytest.mark.unit
def test_registry_loads_devices(sample_devices_config: Path) -> None:
    from src.common.config import ConfigLoader
    from src.device_interface.registry import DeviceRegistry

    loader = ConfigLoader(sample_devices_config)
    registry = DeviceRegistry(loader)
    registry.load()

    assert len(registry) == 4


@pytest.mark.unit
def test_registry_get_device_by_id(sample_devices_config: Path) -> None:
    from src.common.config import ConfigLoader
    from src.device_interface.registry import DeviceRegistry

    loader = ConfigLoader(sample_devices_config)
    registry = DeviceRegistry(loader)
    registry.load()

    device = registry.get("temp_sensor_1")

    assert device.id == "temp_sensor_1"
    assert device.name == "Temperature Sensor 1"


@pytest.mark.unit
def test_registry_get_raises_for_unknown_device(sample_devices_config: Path) -> None:
    from src.common.config import ConfigLoader
    from src.common.exceptions import DeviceError
    from src.device_interface.registry import DeviceRegistry

    loader = ConfigLoader(sample_devices_config)
    registry = DeviceRegistry(loader)
    registry.load()

    with pytest.raises(DeviceError, match="Device not found"):
        registry.get("nonexistent")


@pytest.mark.unit
def test_registry_get_optional_returns_none(sample_devices_config: Path) -> None:
    from src.common.config import ConfigLoader
    from src.device_interface.registry import DeviceRegistry

    loader = ConfigLoader(sample_devices_config)
    registry = DeviceRegistry(loader)
    registry.load()

    assert registry.get_optional("nonexistent") is None


@pytest.mark.unit
def test_registry_sensors_returns_only_sensors(sample_devices_config: Path) -> None:
    from src.common.config import ConfigLoader
    from src.device_interface.models import Sensor
    from src.device_interface.registry import DeviceRegistry

    loader = ConfigLoader(sample_devices_config)
    registry = DeviceRegistry(loader)
    registry.load()

    sensors = registry.sensors()

    assert len(sensors) == 2
    assert all(isinstance(s, Sensor) for s in sensors)


@pytest.mark.unit
def test_registry_actuators_returns_only_actuators(sample_devices_config: Path) -> None:
    from src.common.config import ConfigLoader
    from src.device_interface.models import Actuator
    from src.device_interface.registry import DeviceRegistry

    loader = ConfigLoader(sample_devices_config)
    registry = DeviceRegistry(loader)
    registry.load()

    actuators = registry.actuators()

    assert len(actuators) == 2
    assert all(isinstance(a, Actuator) for a in actuators)


@pytest.mark.unit
def test_registry_by_location(sample_devices_config: Path) -> None:
    from src.common.config import ConfigLoader
    from src.device_interface.registry import DeviceRegistry

    loader = ConfigLoader(sample_devices_config)
    registry = DeviceRegistry(loader)
    registry.load()

    living_room_devices = registry.by_location("living_room")

    assert len(living_room_devices) == 3


@pytest.mark.unit
def test_registry_by_device_class(sample_devices_config: Path) -> None:
    from src.common.config import ConfigLoader
    from src.device_interface.registry import DeviceRegistry

    loader = ConfigLoader(sample_devices_config)
    registry = DeviceRegistry(loader)
    registry.load()

    lights = registry.by_device_class("light")

    assert len(lights) == 1
    assert lights[0].id == "light_1"


@pytest.mark.unit
def test_registry_get_locations(sample_devices_config: Path) -> None:
    from src.common.config import ConfigLoader
    from src.device_interface.registry import DeviceRegistry

    loader = ConfigLoader(sample_devices_config)
    registry = DeviceRegistry(loader)
    registry.load()

    locations = registry.get_locations()

    assert locations == {"living_room", "bedroom"}


@pytest.mark.unit
def test_registry_contains(sample_devices_config: Path) -> None:
    from src.common.config import ConfigLoader
    from src.device_interface.registry import DeviceRegistry

    loader = ConfigLoader(sample_devices_config)
    registry = DeviceRegistry(loader)
    registry.load()

    assert "temp_sensor_1" in registry
    assert "nonexistent" not in registry


@pytest.mark.unit
def test_registry_iteration(sample_devices_config: Path) -> None:
    from src.common.config import ConfigLoader
    from src.device_interface.registry import DeviceRegistry

    loader = ConfigLoader(sample_devices_config)
    registry = DeviceRegistry(loader)
    registry.load()

    device_ids = [d.id for d in registry]

    assert len(device_ids) == 4
    assert "temp_sensor_1" in device_ids
