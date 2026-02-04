import pytest


@pytest.mark.unit
def test_sensor_from_dict() -> None:
    from src.device_interface.models import DeviceType, Sensor, ValueType

    data = {
        "id": "temp_1",
        "name": "Temperature Sensor",
        "type": "sensor",
        "device_class": "temperature",
        "location": "living_room",
        "unit": "°C",
        "value_type": "float",
        "mqtt": {"topic": "home/temp", "qos": 1},
        "constraints": {"min": -40, "max": 85},
    }

    sensor = Sensor.from_dict(data)

    assert sensor.id == "temp_1"
    assert sensor.device_type == DeviceType.SENSOR
    assert sensor.unit == "°C"
    assert sensor.value_type == ValueType.FLOAT
    assert sensor.mqtt is not None
    assert sensor.mqtt.topic == "home/temp"
    assert sensor.constraints is not None
    assert sensor.constraints.min_value == -40


@pytest.mark.unit
def test_actuator_from_dict() -> None:
    from src.device_interface.models import Actuator, DeviceType

    data = {
        "id": "ac_1",
        "name": "AC Unit",
        "type": "actuator",
        "device_class": "thermostat",
        "capabilities": ["set_temperature", "turn_on", "turn_off"],
        "mqtt": {"topic": "home/ac/state", "command_topic": "home/ac/set"},
    }

    actuator = Actuator.from_dict(data)

    assert actuator.id == "ac_1"
    assert actuator.device_type == DeviceType.ACTUATOR
    assert actuator.capabilities == ("set_temperature", "turn_on", "turn_off")
    assert actuator.has_capability("turn_on")
    assert not actuator.has_capability("set_brightness")


@pytest.mark.unit
def test_device_from_dict_creates_sensor() -> None:
    from src.device_interface.models import Device, Sensor

    data = {
        "id": "sensor_1",
        "name": "Sensor",
        "type": "sensor",
        "device_class": "motion",
    }

    device = Device.from_dict(data)

    assert isinstance(device, Sensor)


@pytest.mark.unit
def test_device_from_dict_creates_actuator() -> None:
    from src.device_interface.models import Actuator, Device

    data = {
        "id": "actuator_1",
        "name": "Actuator",
        "type": "actuator",
        "device_class": "switch",
        "capabilities": ["turn_on"],
    }

    device = Device.from_dict(data)

    assert isinstance(device, Actuator)


@pytest.mark.unit
def test_mqtt_config_from_dict() -> None:
    from src.device_interface.models import MQTTConfig

    data = {"topic": "test/topic", "command_topic": "test/cmd", "qos": 2, "retain": True}

    config = MQTTConfig.from_dict(data)

    assert config.topic == "test/topic"
    assert config.command_topic == "test/cmd"
    assert config.qos == 2
    assert config.retain is True


@pytest.mark.unit
def test_mqtt_config_defaults() -> None:
    from src.device_interface.models import MQTTConfig

    data = {"topic": "test/topic"}

    config = MQTTConfig.from_dict(data)

    assert config.qos == 1
    assert config.retain is False
    assert config.command_topic is None


@pytest.mark.unit
def test_constraints_validate_range() -> None:
    from src.device_interface.models import Constraints

    constraints = Constraints(min_value=0, max_value=100)

    assert constraints.validate(50) is True
    assert constraints.validate(0) is True
    assert constraints.validate(100) is True
    assert constraints.validate(-1) is False
    assert constraints.validate(101) is False


@pytest.mark.unit
def test_constraints_validate_allowed_values() -> None:
    from src.device_interface.models import Constraints

    constraints = Constraints(allowed_values=("on", "off", "auto"))

    assert constraints.validate("on") is True
    assert constraints.validate("off") is True
    assert constraints.validate("invalid") is False


@pytest.mark.unit
def test_device_is_frozen() -> None:
    from src.device_interface.models import Sensor

    data = {"id": "s1", "name": "S", "type": "sensor", "device_class": "temp"}
    sensor = Sensor.from_dict(data)

    with pytest.raises(AttributeError):
        sensor.id = "new_id"  # type: ignore[misc]
