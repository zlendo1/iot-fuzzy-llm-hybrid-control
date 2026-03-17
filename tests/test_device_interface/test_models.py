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

    data = {
        "topic": "test/topic",
        "command_topic": "test/cmd",
        "qos": 2,
        "retain": True,
    }

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


# PayloadSchema tests
@pytest.mark.unit
def test_payload_schema_default() -> None:
    from src.device_interface.models import PayloadSchema

    schema = PayloadSchema.default()

    assert schema.value_field == "value"
    assert schema.timestamp_field is None
    assert schema.unit_field is None


@pytest.mark.unit
def test_payload_schema_custom_fields() -> None:
    from src.device_interface.models import PayloadSchema

    schema = PayloadSchema(
        value_field="reading",
        timestamp_field="ts",
        unit_field="unit",
    )

    assert schema.value_field == "reading"
    assert schema.timestamp_field == "ts"
    assert schema.unit_field == "unit"


@pytest.mark.unit
def test_payload_schema_empty_value_field_raises_validation_error() -> None:
    from src.common.exceptions import ValidationError
    from src.device_interface.models import PayloadSchema

    with pytest.raises(ValidationError):
        PayloadSchema(value_field="", timestamp_field=None, unit_field=None)


@pytest.mark.unit
def test_payload_schema_is_frozen() -> None:
    from src.device_interface.models import PayloadSchema

    schema = PayloadSchema.default()

    with pytest.raises(AttributeError):
        schema.value_field = "new_value"  # type: ignore[misc]


# TopicPattern tests
@pytest.mark.unit
def test_topic_pattern_valid() -> None:
    from src.device_interface.models import TopicPattern

    pattern = TopicPattern(
        pattern="home/{zone}/{device}",
        variables=("zone", "device"),
    )

    assert pattern.pattern == "home/{zone}/{device}"
    assert pattern.variables == ("zone", "device")


@pytest.mark.unit
def test_topic_pattern_single_variable() -> None:
    from src.device_interface.models import TopicPattern

    pattern = TopicPattern(
        pattern="devices/{id}/status",
        variables=("id",),
    )

    assert pattern.pattern == "devices/{id}/status"
    assert pattern.variables == ("id",)


@pytest.mark.unit
def test_topic_pattern_no_variables() -> None:
    from src.device_interface.models import TopicPattern

    pattern = TopicPattern(
        pattern="global/status",
        variables=(),
    )

    assert pattern.pattern == "global/status"
    assert pattern.variables == ()


@pytest.mark.unit
def test_topic_pattern_missing_variable_in_pattern_raises_validation_error() -> None:
    from src.common.exceptions import ValidationError
    from src.device_interface.models import TopicPattern

    with pytest.raises(ValidationError):
        TopicPattern(
            pattern="home/{zone}/status",
            variables=("zone", "device"),
        )


@pytest.mark.unit
def test_topic_pattern_is_frozen() -> None:
    from src.device_interface.models import TopicPattern

    pattern = TopicPattern(
        pattern="home/{zone}/{device}",
        variables=("zone", "device"),
    )

    with pytest.raises(AttributeError):
        pattern.pattern = "new/pattern"  # type: ignore[misc]


# LEGACY_VALUE_FIELDS constant tests
@pytest.mark.unit
def test_legacy_value_fields_constant() -> None:
    from src.device_interface.models import LEGACY_VALUE_FIELDS

    assert LEGACY_VALUE_FIELDS == ["value", "reading", "v"]
    assert isinstance(LEGACY_VALUE_FIELDS, list)
