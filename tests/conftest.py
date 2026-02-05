from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def sample_mqtt_config() -> dict[str, Any]:
    return {
        "broker": {
            "host": "localhost",
            "port": 1883,
            "keepalive": 60,
        },
        "client": {
            "id_prefix": "iot_test",
            "clean_session": True,
        },
        "auth": {
            "username": None,
            "password": None,
        },
    }


@pytest.fixture
def sample_llm_config() -> dict[str, Any]:
    return {
        "llm": {
            "provider": "ollama",
            "connection": {"host": "localhost", "port": 11434},
            "model": {"name": "qwen3:0.6b", "fallback": ["llama3.2", "phi3"]},
            "inference": {
                "temperature": 0.1,
                "max_tokens": 256,
                "top_p": 0.9,
            },
        },
    }


@pytest.fixture
def sample_devices_config() -> dict[str, Any]:
    return {
        "devices": [
            {
                "id": "temp_living_room",
                "name": "Living Room Temperature Sensor",
                "type": "sensor",
                "device_class": "temperature",
                "unit": "celsius",
                "mqtt": {"topic": "home/living_room/temperature"},
            },
            {
                "id": "humidity_living_room",
                "name": "Living Room Humidity Sensor",
                "type": "sensor",
                "device_class": "humidity",
                "unit": "percent",
                "mqtt": {"topic": "home/living_room/humidity"},
            },
            {
                "id": "motion_living_room",
                "name": "Living Room Motion Sensor",
                "type": "sensor",
                "device_class": "motion",
                "mqtt": {"topic": "home/living_room/motion"},
            },
            {
                "id": "ac_living_room",
                "name": "Living Room AC",
                "type": "actuator",
                "device_class": "thermostat",
                "capabilities": ["turn_on", "turn_off", "set_temperature"],
                "constraints": {"min_temp": 16, "max_temp": 30},
                "mqtt": {
                    "topic": "home/living_room/ac/state",
                    "command_topic": "home/living_room/ac/set",
                },
            },
            {
                "id": "light_living_room",
                "name": "Living Room Light",
                "type": "actuator",
                "device_class": "light",
                "capabilities": ["turn_on", "turn_off", "set_brightness"],
                "constraints": {"min_brightness": 0, "max_brightness": 100},
                "mqtt": {
                    "topic": "home/living_room/light/state",
                    "command_topic": "home/living_room/light/set",
                },
            },
        ],
    }


@pytest.fixture
def sample_temperature_mf() -> dict[str, Any]:
    return {
        "sensor_type": "temperature",
        "unit": "celsius",
        "universe_of_discourse": {"min": -10.0, "max": 50.0},
        "confidence_threshold": 0.1,
        "linguistic_variables": [
            {"term": "cold", "function_type": "trapezoidal", "parameters": {"a": -10.0, "b": -10.0, "c": 10.0, "d": 18.0}},
            {"term": "comfortable", "function_type": "triangular", "parameters": {"a": 16.0, "b": 22.0, "c": 26.0}},
            {"term": "warm", "function_type": "triangular", "parameters": {"a": 24.0, "b": 28.0, "c": 32.0}},
            {"term": "hot", "function_type": "trapezoidal", "parameters": {"a": 30.0, "b": 35.0, "c": 50.0, "d": 50.0}},
        ],
    }


@pytest.fixture
def sample_humidity_mf() -> dict[str, Any]:
    return {
        "sensor_type": "humidity",
        "unit": "percent",
        "universe_of_discourse": {"min": 0.0, "max": 100.0},
        "confidence_threshold": 0.1,
        "linguistic_variables": [
            {"term": "dry", "function_type": "trapezoidal", "parameters": {"a": 0.0, "b": 0.0, "c": 20.0, "d": 35.0}},
            {"term": "comfortable", "function_type": "triangular", "parameters": {"a": 30.0, "b": 50.0, "c": 70.0}},
            {"term": "humid", "function_type": "trapezoidal", "parameters": {"a": 65.0, "b": 80.0, "c": 100.0, "d": 100.0}},
        ],
    }


@pytest.fixture
def sample_mf_schema() -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "membership_functions.schema.json",
        "title": "Membership Function Configuration",
        "type": "object",
        "required": ["sensor_type", "unit", "universe_of_discourse", "linguistic_variables"],
        "properties": {
            "sensor_type": {"type": "string"},
            "unit": {"type": "string"},
            "universe_of_discourse": {
                "type": "object",
                "required": ["min", "max"],
                "properties": {"min": {"type": "number"}, "max": {"type": "number"}},
            },
            "confidence_threshold": {"type": "number"},
            "linguistic_variables": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["term", "function_type", "parameters"],
                    "properties": {
                        "term": {"type": "string"},
                        "function_type": {"type": "string"},
                        "parameters": {"type": "object"},
                    },
                },
            },
        },
    }


@pytest.fixture
def config_directory(
    tmp_path: Path,
    sample_mqtt_config: dict[str, Any],
    sample_llm_config: dict[str, Any],
    sample_devices_config: dict[str, Any],
    sample_temperature_mf: dict[str, Any],
    sample_humidity_mf: dict[str, Any],
    sample_mf_schema: dict[str, Any],
) -> Path:
    config_dir = tmp_path / "config"
    config_dir.mkdir()

    schemas_dir = config_dir / "schemas"
    schemas_dir.mkdir()

    mf_dir = config_dir / "membership_functions"
    mf_dir.mkdir()

    (config_dir / "mqtt_config.json").write_text(json.dumps(sample_mqtt_config))
    (config_dir / "llm_config.json").write_text(json.dumps(sample_llm_config))
    (config_dir / "devices.json").write_text(json.dumps(sample_devices_config))

    (schemas_dir / "membership_functions.schema.json").write_text(json.dumps(sample_mf_schema))

    (mf_dir / "temperature.json").write_text(json.dumps(sample_temperature_mf))
    (mf_dir / "humidity.json").write_text(json.dumps(sample_humidity_mf))

    return config_dir


@pytest.fixture
def rules_directory(tmp_path: Path) -> Path:
    rules_dir = tmp_path / "rules"
    rules_dir.mkdir()
    return rules_dir


@pytest.fixture
def logs_directory(tmp_path: Path) -> Path:
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    return logs_dir


@pytest.fixture
def full_test_environment(
    config_directory: Path,
    rules_directory: Path,
    logs_directory: Path,
) -> dict[str, Path]:
    return {
        "config_dir": config_directory,
        "rules_dir": rules_directory,
        "logs_dir": logs_directory,
    }


@pytest.fixture
def sample_rules() -> list[dict[str, Any]]:
    return [
        {
            "rule_id": "rule_001",
            "rule_text": "If the temperature is hot, turn on the air conditioner",
            "priority": 1,
            "enabled": True,
        },
        {
            "rule_id": "rule_002",
            "rule_text": "If the temperature is cold, turn off the air conditioner",
            "priority": 1,
            "enabled": True,
        },
        {
            "rule_id": "rule_003",
            "rule_text": "If motion is detected and it's dark, turn on the living room light",
            "priority": 2,
            "enabled": True,
        },
        {
            "rule_id": "rule_004",
            "rule_text": "If no motion is detected for 10 minutes, turn off all lights",
            "priority": 3,
            "enabled": True,
        },
        {
            "rule_id": "rule_005",
            "rule_text": "If humidity is too high, activate the dehumidifier",
            "priority": 2,
            "enabled": False,
        },
    ]


@pytest.fixture
def mock_mqtt_client() -> MagicMock:
    client = MagicMock()
    client.is_connected = True
    client.connect.return_value = None
    client.disconnect.return_value = None
    client.publish.return_value = None
    client.subscribe.return_value = None
    return client


@pytest.fixture
def mock_ollama_client() -> MagicMock:
    client = MagicMock()
    client.is_healthy.return_value = True
    client.active_model = "qwen3:0.6b"

    response = MagicMock()
    response.text = "ACTION: turn_on(device_id=ac_living_room)"
    response.model = "qwen3:0.6b"
    response.done = True
    client.generate.return_value = response

    return client


def create_sensor_reading(
    sensor_id: str = "temp_living_room",
    value: float | int | bool = 28.5,
    unit: str | None = "celsius",
) -> Any:
    from src.device_interface.messages import SensorReading

    return SensorReading(
        sensor_id=sensor_id,
        value=value,
        unit=unit,
    )


def create_linguistic_description(
    sensor_id: str = "temp_living_room",
    sensor_type: str = "temperature",
    raw_value: float = 28.5,
    terms: list[tuple[str, float]] | None = None,
    unit: str | None = "celsius",
) -> Any:
    from src.data_processing.linguistic_descriptor import (
        LinguisticDescription,
        TermMembership,
    )

    if terms is None:
        terms = [("hot", 0.85), ("warm", 0.15)]

    term_memberships = tuple(TermMembership(term=t, degree=d) for t, d in terms)
    return LinguisticDescription(
        sensor_id=sensor_id,
        sensor_type=sensor_type,
        raw_value=raw_value,
        terms=term_memberships,
        unit=unit,
    )


def create_natural_language_rule(
    rule_id: str = "rule_001",
    rule_text: str = "If temperature is hot, turn on AC",
    priority: int = 1,
    enabled: bool = True,
) -> Any:
    from src.control_reasoning.rule_interpreter import NaturalLanguageRule

    return NaturalLanguageRule(
        rule_id=rule_id,
        rule_text=rule_text,
        priority=priority,
        enabled=enabled,
    )


def create_device_command(
    command_id: str = "cmd_001",
    device_id: str = "ac_living_room",
    command_type: str = "turn_on",
    parameters: dict[str, Any] | None = None,
    rule_id: str | None = None,
) -> Any:
    from src.control_reasoning.command_generator import DeviceCommand

    return DeviceCommand(
        command_id=command_id,
        device_id=device_id,
        command_type=command_type,
        parameters=parameters or {},
        rule_id=rule_id,
    )
