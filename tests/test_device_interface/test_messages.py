import pytest


@pytest.mark.unit
def test_sensor_reading_creation() -> None:
    from src.device_interface.messages import ReadingQuality, SensorReading

    reading = SensorReading(
        sensor_id="temp-001",
        value=23.5,
        unit="celsius",
    )

    assert reading.sensor_id == "temp-001"
    assert reading.value == 23.5
    assert reading.unit == "celsius"
    assert reading.quality == ReadingQuality.GOOD
    assert reading.reading_id.startswith("reading_")


@pytest.mark.unit
def test_sensor_reading_to_dict() -> None:
    from src.device_interface.messages import ReadingQuality, SensorReading

    reading = SensorReading(
        sensor_id="temp-001",
        value=23.5,
        quality=ReadingQuality.UNCERTAIN,
    )

    data = reading.to_dict()

    assert data["sensor_id"] == "temp-001"
    assert data["value"] == 23.5
    assert data["quality"] == "uncertain"


@pytest.mark.unit
def test_sensor_reading_from_dict() -> None:
    from src.device_interface.messages import ReadingQuality, SensorReading

    data = {
        "sensor_id": "hum-001",
        "value": 65,
        "quality": "good",
        "unit": "percent",
    }

    reading = SensorReading.from_dict(data)

    assert reading.sensor_id == "hum-001"
    assert reading.value == 65
    assert reading.quality == ReadingQuality.GOOD
    assert reading.unit == "percent"


@pytest.mark.unit
def test_sensor_reading_from_mqtt_payload_json() -> None:
    from src.device_interface.messages import SensorReading

    payload = b'{"value": 28.5, "timestamp": "2024-01-15T10:30:00Z"}'

    reading = SensorReading.from_mqtt_payload(
        sensor_id="temp-001",
        payload=payload,
        topic="home/living/temp",
        unit="celsius",
    )

    assert reading.sensor_id == "temp-001"
    assert reading.value == 28.5
    assert reading.unit == "celsius"
    assert reading.raw_topic == "home/living/temp"


@pytest.mark.unit
def test_sensor_reading_from_mqtt_payload_simple() -> None:
    from src.device_interface.messages import SensorReading

    payload = b"42.0"

    reading = SensorReading.from_mqtt_payload(
        sensor_id="temp-001",
        payload=payload,
        topic="home/living/temp",
    )

    assert reading.value == 42.0


@pytest.mark.unit
def test_sensor_reading_parse_simple_value_bool() -> None:
    from src.device_interface.messages import SensorReading

    assert SensorReading._parse_simple_value("true") is True
    assert SensorReading._parse_simple_value("on") is True
    assert SensorReading._parse_simple_value("false") is False
    assert SensorReading._parse_simple_value("off") is False


@pytest.mark.unit
def test_sensor_reading_parse_simple_value_numbers() -> None:
    from src.device_interface.messages import SensorReading

    assert SensorReading._parse_simple_value("42") == 42
    assert SensorReading._parse_simple_value("3.14") == 3.14
    assert SensorReading._parse_simple_value("hello") == "hello"


@pytest.mark.unit
def test_device_command_creation() -> None:
    from src.device_interface.messages import CommandType, DeviceCommand

    command = DeviceCommand(
        device_id="ac-001",
        command_type=CommandType.SET,
        parameters={"value": 22},
    )

    assert command.device_id == "ac-001"
    assert command.command_type == CommandType.SET
    assert command.parameters["value"] == 22
    assert command.command_id.startswith("cmd_")


@pytest.mark.unit
def test_device_command_to_dict() -> None:
    from src.device_interface.messages import CommandType, DeviceCommand

    command = DeviceCommand(
        device_id="light-001",
        command_type=CommandType.TOGGLE,
    )

    data = command.to_dict()

    assert data["device_id"] == "light-001"
    assert data["command_type"] == "toggle"


@pytest.mark.unit
def test_device_command_set_value_factory() -> None:
    from src.device_interface.messages import CommandType, DeviceCommand

    command = DeviceCommand.set_value("ac-001", 24, source="rule_engine")

    assert command.device_id == "ac-001"
    assert command.command_type == CommandType.SET
    assert command.value == 24
    assert command.source == "rule_engine"


@pytest.mark.unit
def test_device_command_toggle_factory() -> None:
    from src.device_interface.messages import CommandType, DeviceCommand

    command = DeviceCommand.toggle("light-001")

    assert command.device_id == "light-001"
    assert command.command_type == CommandType.TOGGLE


@pytest.mark.unit
def test_device_command_to_mqtt_payload() -> None:
    import json

    from src.device_interface.messages import CommandType, DeviceCommand

    command = DeviceCommand(
        device_id="ac-001",
        command_type=CommandType.SET,
        parameters={"value": 22},
    )

    payload = command.to_mqtt_payload()
    data = json.loads(payload.decode("utf-8"))

    assert data["device_id"] == "ac-001"
    assert data["command_type"] == "set"
