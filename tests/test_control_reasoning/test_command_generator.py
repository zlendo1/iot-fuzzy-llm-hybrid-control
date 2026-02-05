from __future__ import annotations

from typing import TYPE_CHECKING, Any
from unittest.mock import Mock

import pytest

if TYPE_CHECKING:
    from src.device_interface.models import Actuator, Sensor


def _create_actuator(
    device_id: str = "actuator_001",
    capabilities: tuple[str, ...] = ("turn_on", "turn_off", "set_temperature"),
) -> Actuator:
    from src.device_interface.models import Actuator, DeviceType

    return Actuator(
        id=device_id,
        name=f"Test Actuator {device_id}",
        device_type=DeviceType.ACTUATOR,
        device_class="switch",
        capabilities=capabilities,
    )


def _create_sensor(device_id: str = "sensor_001") -> Sensor:
    from src.device_interface.models import DeviceType, Sensor

    return Sensor(
        id=device_id,
        name=f"Test Sensor {device_id}",
        device_type=DeviceType.SENSOR,
        device_class="temperature",
    )


def _create_registry(
    devices: dict[str, Any] | None = None,
) -> Mock:
    registry = Mock()
    devices = devices or {}

    def get_optional(device_id: str) -> Mock | None:
        return devices.get(device_id)

    registry.get_optional = get_optional
    return registry


class TestCommandStatus:
    @pytest.mark.unit
    def test_command_status_values(self) -> None:
        from src.control_reasoning.command_generator import CommandStatus

        assert CommandStatus.PENDING.value == "pending"
        assert CommandStatus.VALIDATED.value == "validated"
        assert CommandStatus.REJECTED.value == "rejected"
        assert CommandStatus.EXECUTED.value == "executed"
        assert CommandStatus.FAILED.value == "failed"

    @pytest.mark.unit
    def test_command_status_count(self) -> None:
        from src.control_reasoning.command_generator import CommandStatus

        assert len(CommandStatus) == 5


class TestDeviceCommand:
    @pytest.mark.unit
    def test_device_command_creation_with_defaults(self) -> None:
        from src.control_reasoning.command_generator import (
            CommandStatus,
            DeviceCommand,
        )

        cmd = DeviceCommand(
            command_id="cmd_001",
            device_id="actuator_001",
            command_type="turn_on",
        )

        assert cmd.command_id == "cmd_001"
        assert cmd.device_id == "actuator_001"
        assert cmd.command_type == "turn_on"
        assert cmd.parameters == {}
        assert cmd.status == CommandStatus.PENDING
        assert cmd.rule_id is None
        assert cmd.rejection_reason is None
        assert cmd.created_at > 0

    @pytest.mark.unit
    def test_device_command_creation_with_all_fields(self) -> None:
        from src.control_reasoning.command_generator import (
            CommandStatus,
            DeviceCommand,
        )

        cmd = DeviceCommand(
            command_id="cmd_002",
            device_id="ac_living_room",
            command_type="set_temperature",
            parameters={"temperature": 22, "mode": "cool"},
            status=CommandStatus.VALIDATED,
            created_at=1234567890.0,
            rule_id="rule_001",
            rejection_reason=None,
        )

        assert cmd.command_id == "cmd_002"
        assert cmd.device_id == "ac_living_room"
        assert cmd.command_type == "set_temperature"
        assert cmd.parameters == {"temperature": 22, "mode": "cool"}
        assert cmd.status == CommandStatus.VALIDATED
        assert cmd.created_at == 1234567890.0
        assert cmd.rule_id == "rule_001"

    @pytest.mark.unit
    def test_device_command_to_mqtt_payload(self) -> None:
        from src.control_reasoning.command_generator import DeviceCommand

        cmd = DeviceCommand(
            command_id="cmd_003",
            device_id="light_001",
            command_type="set_brightness",
            parameters={"brightness": 75},
            created_at=1234567890.0,
        )

        payload = cmd.to_mqtt_payload()

        assert payload == {
            "command": "set_brightness",
            "parameters": {"brightness": 75},
            "command_id": "cmd_003",
            "timestamp": 1234567890.0,
        }

    @pytest.mark.unit
    def test_device_command_to_mqtt_payload_empty_parameters(self) -> None:
        from src.control_reasoning.command_generator import DeviceCommand

        cmd = DeviceCommand(
            command_id="cmd_004",
            device_id="fan_001",
            command_type="turn_off",
            created_at=1000000.0,
        )

        payload = cmd.to_mqtt_payload()

        assert payload["command"] == "turn_off"
        assert payload["parameters"] == {}
        assert payload["command_id"] == "cmd_004"

    @pytest.mark.unit
    def test_device_command_mark_validated(self) -> None:
        from src.control_reasoning.command_generator import (
            CommandStatus,
            DeviceCommand,
        )

        cmd = DeviceCommand(
            command_id="cmd_005",
            device_id="device_001",
            command_type="turn_on",
        )
        assert cmd.status == CommandStatus.PENDING

        cmd.mark_validated()

        assert cmd.status == CommandStatus.VALIDATED

    @pytest.mark.unit
    def test_device_command_mark_rejected(self) -> None:
        from src.control_reasoning.command_generator import (
            CommandStatus,
            DeviceCommand,
        )

        cmd = DeviceCommand(
            command_id="cmd_006",
            device_id="device_001",
            command_type="turn_on",
        )

        cmd.mark_rejected("Device offline")

        assert cmd.status == CommandStatus.REJECTED
        assert cmd.rejection_reason == "Device offline"

    @pytest.mark.unit
    def test_device_command_mark_executed(self) -> None:
        from src.control_reasoning.command_generator import (
            CommandStatus,
            DeviceCommand,
        )

        cmd = DeviceCommand(
            command_id="cmd_007",
            device_id="device_001",
            command_type="turn_on",
        )
        cmd.mark_validated()

        cmd.mark_executed()

        assert cmd.status == CommandStatus.EXECUTED

    @pytest.mark.unit
    def test_device_command_mark_failed(self) -> None:
        from src.control_reasoning.command_generator import (
            CommandStatus,
            DeviceCommand,
        )

        cmd = DeviceCommand(
            command_id="cmd_008",
            device_id="device_001",
            command_type="turn_on",
        )

        cmd.mark_failed("MQTT publish failed")

        assert cmd.status == CommandStatus.FAILED
        assert cmd.rejection_reason == "MQTT publish failed"

    @pytest.mark.unit
    def test_device_command_is_mutable(self) -> None:
        from src.control_reasoning.command_generator import DeviceCommand

        cmd = DeviceCommand(
            command_id="cmd_009",
            device_id="device_001",
            command_type="turn_on",
        )

        cmd.parameters["new_param"] = "value"
        assert cmd.parameters["new_param"] == "value"


class TestGenerationResult:
    @pytest.mark.unit
    def test_generation_result_ok(self) -> None:
        from src.control_reasoning.command_generator import (
            DeviceCommand,
            GenerationResult,
        )

        cmd = DeviceCommand(
            command_id="cmd_001",
            device_id="device_001",
            command_type="turn_on",
        )

        result = GenerationResult.ok(cmd)

        assert result.success is True
        assert result.command is cmd
        assert result.error is None

    @pytest.mark.unit
    def test_generation_result_fail(self) -> None:
        from src.control_reasoning.command_generator import GenerationResult

        result = GenerationResult.fail("Device not found")

        assert result.success is False
        assert result.command is None
        assert result.error == "Device not found"

    @pytest.mark.unit
    def test_generation_result_is_frozen(self) -> None:
        from dataclasses import FrozenInstanceError

        from src.control_reasoning.command_generator import GenerationResult

        result = GenerationResult.fail("Error")

        with pytest.raises(FrozenInstanceError):
            result.success = True  # type: ignore[misc]

    @pytest.mark.unit
    def test_generation_result_direct_creation(self) -> None:
        from src.control_reasoning.command_generator import GenerationResult

        result = GenerationResult(success=True, command=None, error="test")

        assert result.success is True
        assert result.command is None
        assert result.error == "test"


class TestCommandGeneratorInit:
    @pytest.mark.unit
    def test_command_generator_init_without_registry(self) -> None:
        from src.control_reasoning.command_generator import CommandGenerator

        generator = CommandGenerator()

        assert generator.registry is None

    @pytest.mark.unit
    def test_command_generator_init_with_registry(self) -> None:
        from src.control_reasoning.command_generator import CommandGenerator

        registry = _create_registry()

        generator = CommandGenerator(registry=registry)

        assert generator.registry is registry

    @pytest.mark.unit
    def test_command_generator_set_registry(self) -> None:
        from src.control_reasoning.command_generator import CommandGenerator

        generator = CommandGenerator()
        registry = _create_registry()

        generator.set_registry(registry)

        assert generator.registry is registry


class TestCommandGeneratorGenerate:
    @pytest.mark.unit
    def test_generate_fails_without_registry(self) -> None:
        from src.control_reasoning.command_generator import CommandGenerator
        from src.control_reasoning.response_parser import ActionSpec

        generator = CommandGenerator()
        action = ActionSpec(device_id="device_001", command="turn_on")

        result = generator.generate(action)

        assert result.success is False
        assert result.error == "No device registry configured"

    @pytest.mark.unit
    def test_generate_fails_device_not_found(self) -> None:
        from src.control_reasoning.command_generator import CommandGenerator
        from src.control_reasoning.response_parser import ActionSpec

        registry = _create_registry({})
        generator = CommandGenerator(registry=registry)
        action = ActionSpec(device_id="unknown_device", command="turn_on")

        result = generator.generate(action)

        assert result.success is False
        assert "Device 'unknown_device' not found" in result.error  # type: ignore[operator]

    @pytest.mark.unit
    def test_generate_fails_device_is_sensor(self) -> None:
        from src.control_reasoning.command_generator import CommandGenerator
        from src.control_reasoning.response_parser import ActionSpec

        sensor = _create_sensor("temp_sensor")
        registry = _create_registry({"temp_sensor": sensor})
        generator = CommandGenerator(registry=registry)
        action = ActionSpec(device_id="temp_sensor", command="turn_on")

        result = generator.generate(action)

        assert result.success is False
        assert "not an actuator" in result.error  # type: ignore[operator]

    @pytest.mark.unit
    def test_generate_fails_missing_capability(self) -> None:
        from src.control_reasoning.command_generator import CommandGenerator
        from src.control_reasoning.response_parser import ActionSpec

        actuator = _create_actuator(
            device_id="light_001",
            capabilities=("turn_on", "turn_off"),
        )
        registry = _create_registry({"light_001": actuator})
        generator = CommandGenerator(registry=registry)
        action = ActionSpec(device_id="light_001", command="set_color")

        result = generator.generate(action)

        assert result.success is False
        assert "does not support command 'set_color'" in result.error  # type: ignore[operator]

    @pytest.mark.unit
    def test_generate_success_basic(self) -> None:
        from src.control_reasoning.command_generator import (
            CommandGenerator,
            CommandStatus,
        )
        from src.control_reasoning.response_parser import ActionSpec

        actuator = _create_actuator(
            device_id="ac_001",
            capabilities=("turn_on", "turn_off", "set_temperature"),
        )
        registry = _create_registry({"ac_001": actuator})
        generator = CommandGenerator(registry=registry)
        action = ActionSpec(device_id="ac_001", command="turn_on")

        result = generator.generate(action)

        assert result.success is True
        assert result.command is not None
        assert result.command.device_id == "ac_001"
        assert result.command.command_type == "turn_on"
        assert result.command.status == CommandStatus.PENDING

    @pytest.mark.unit
    def test_generate_success_with_parameters(self) -> None:
        from src.control_reasoning.command_generator import CommandGenerator
        from src.control_reasoning.response_parser import ActionSpec

        actuator = _create_actuator(
            device_id="ac_001",
            capabilities=("set_temperature",),
        )
        registry = _create_registry({"ac_001": actuator})
        generator = CommandGenerator(registry=registry)
        action = ActionSpec(
            device_id="ac_001",
            command="set_temperature",
            parameters={"temperature": 22, "mode": "cool"},
        )

        result = generator.generate(action)

        assert result.success is True
        assert result.command is not None
        assert result.command.parameters == {"temperature": 22, "mode": "cool"}

    @pytest.mark.unit
    def test_generate_success_with_rule_id(self) -> None:
        from src.control_reasoning.command_generator import CommandGenerator
        from src.control_reasoning.response_parser import ActionSpec

        actuator = _create_actuator(device_id="fan_001", capabilities=("turn_on",))
        registry = _create_registry({"fan_001": actuator})
        generator = CommandGenerator(registry=registry)
        action = ActionSpec(device_id="fan_001", command="turn_on")

        result = generator.generate(action, rule_id="rule_hot_weather")

        assert result.success is True
        assert result.command is not None
        assert result.command.rule_id == "rule_hot_weather"

    @pytest.mark.unit
    def test_generate_increments_command_id(self) -> None:
        from src.control_reasoning.command_generator import CommandGenerator
        from src.control_reasoning.response_parser import ActionSpec

        actuator = _create_actuator(device_id="light_001", capabilities=("turn_on",))
        registry = _create_registry({"light_001": actuator})
        generator = CommandGenerator(registry=registry)
        action = ActionSpec(device_id="light_001", command="turn_on")

        result1 = generator.generate(action)
        result2 = generator.generate(action)
        result3 = generator.generate(action)

        assert result1.command is not None
        assert result2.command is not None
        assert result3.command is not None
        assert result1.command.command_id == "cmd_000001"
        assert result2.command.command_id == "cmd_000002"
        assert result3.command.command_id == "cmd_000003"

    @pytest.mark.unit
    def test_generate_copies_parameters(self) -> None:
        from src.control_reasoning.command_generator import CommandGenerator
        from src.control_reasoning.response_parser import ActionSpec

        actuator = _create_actuator(device_id="ac_001", capabilities=("set_temp",))
        registry = _create_registry({"ac_001": actuator})
        generator = CommandGenerator(registry=registry)
        original_params = {"temp": 22}
        action = ActionSpec(
            device_id="ac_001",
            command="set_temp",
            parameters=original_params,
        )

        result = generator.generate(action)

        assert result.command is not None
        result.command.parameters["temp"] = 30
        assert action.parameters["temp"] == 22


class TestCommandGeneratorBatch:
    @pytest.mark.unit
    def test_generate_batch_empty_list(self) -> None:
        from src.control_reasoning.command_generator import CommandGenerator

        registry = _create_registry({})
        generator = CommandGenerator(registry=registry)

        results = generator.generate_batch([])

        assert results == []

    @pytest.mark.unit
    def test_generate_batch_all_success(self) -> None:
        from src.control_reasoning.command_generator import CommandGenerator
        from src.control_reasoning.response_parser import ActionSpec

        actuator1 = _create_actuator(device_id="light_001", capabilities=("turn_on",))
        actuator2 = _create_actuator(device_id="fan_001", capabilities=("turn_off",))
        registry = _create_registry(
            {
                "light_001": actuator1,
                "fan_001": actuator2,
            }
        )
        generator = CommandGenerator(registry=registry)
        actions = [
            ActionSpec(device_id="light_001", command="turn_on"),
            ActionSpec(device_id="fan_001", command="turn_off"),
        ]

        results = generator.generate_batch(actions)

        assert len(results) == 2
        assert all(r.success for r in results)

    @pytest.mark.unit
    def test_generate_batch_mixed_results(self) -> None:
        from src.control_reasoning.command_generator import CommandGenerator
        from src.control_reasoning.response_parser import ActionSpec

        actuator = _create_actuator(device_id="light_001", capabilities=("turn_on",))
        registry = _create_registry({"light_001": actuator})
        generator = CommandGenerator(registry=registry)
        actions = [
            ActionSpec(device_id="light_001", command="turn_on"),  # Success
            ActionSpec(device_id="unknown", command="turn_on"),  # Fail: not found
            ActionSpec(device_id="light_001", command="set_color"),  # Fail: no cap
        ]

        results = generator.generate_batch(actions)

        assert len(results) == 3
        assert results[0].success is True
        assert results[1].success is False
        assert results[2].success is False

    @pytest.mark.unit
    def test_generate_batch_with_rule_id(self) -> None:
        from src.control_reasoning.command_generator import CommandGenerator
        from src.control_reasoning.response_parser import ActionSpec

        actuator = _create_actuator(device_id="ac_001", capabilities=("turn_on",))
        registry = _create_registry({"ac_001": actuator})
        generator = CommandGenerator(registry=registry)
        actions = [ActionSpec(device_id="ac_001", command="turn_on")]

        results = generator.generate_batch(actions, rule_id="batch_rule")

        assert results[0].command is not None
        assert results[0].command.rule_id == "batch_rule"


class TestCommandGeneratorParsedResponse:
    @pytest.mark.unit
    def test_generate_from_parsed_response_invalid_type(self) -> None:
        from src.control_reasoning.command_generator import CommandGenerator

        registry = _create_registry({})
        generator = CommandGenerator(registry=registry)

        result = generator.generate_from_parsed_response("not a ParsedResponse")

        assert result is not None
        assert result.success is False
        assert "Invalid parsed response type" in result.error  # type: ignore[operator]

    @pytest.mark.unit
    def test_generate_from_parsed_response_no_action_type(self) -> None:
        from src.control_reasoning.command_generator import CommandGenerator
        from src.control_reasoning.response_parser import ParsedResponse, ResponseType

        registry = _create_registry({})
        generator = CommandGenerator(registry=registry)
        parsed = ParsedResponse(
            response_type=ResponseType.NO_ACTION,
            raw_text="No action needed",
            reason="Temperature is normal",
        )

        result = generator.generate_from_parsed_response(parsed)

        assert result is None

    @pytest.mark.unit
    def test_generate_from_parsed_response_malformed_type(self) -> None:
        from src.control_reasoning.command_generator import CommandGenerator
        from src.control_reasoning.response_parser import ParsedResponse, ResponseType

        registry = _create_registry({})
        generator = CommandGenerator(registry=registry)
        parsed = ParsedResponse(
            response_type=ResponseType.MALFORMED,
            raw_text="garbage",
        )

        result = generator.generate_from_parsed_response(parsed)

        assert result is None

    @pytest.mark.unit
    def test_generate_from_parsed_response_action_but_no_action_field(self) -> None:
        from src.control_reasoning.command_generator import CommandGenerator
        from src.control_reasoning.response_parser import ParsedResponse, ResponseType

        registry = _create_registry({})
        generator = CommandGenerator(registry=registry)
        parsed = ParsedResponse(
            response_type=ResponseType.ACTION,
            raw_text="ACTION: ...",
            action=None,
        )

        result = generator.generate_from_parsed_response(parsed)

        assert result is not None
        assert result.success is False
        assert "no action" in result.error  # type: ignore[operator]

    @pytest.mark.unit
    def test_generate_from_parsed_response_success(self) -> None:
        from src.control_reasoning.command_generator import CommandGenerator
        from src.control_reasoning.response_parser import (
            ActionSpec,
            ParsedResponse,
            ResponseType,
        )

        actuator = _create_actuator(device_id="ac_001", capabilities=("turn_on",))
        registry = _create_registry({"ac_001": actuator})
        generator = CommandGenerator(registry=registry)
        parsed = ParsedResponse(
            response_type=ResponseType.ACTION,
            raw_text="ACTION: turn_on(ac_001)",
            action=ActionSpec(device_id="ac_001", command="turn_on"),
            reason="It's too hot",
        )

        result = generator.generate_from_parsed_response(parsed, rule_id="heat_rule")

        assert result is not None
        assert result.success is True
        assert result.command is not None
        assert result.command.device_id == "ac_001"
        assert result.command.command_type == "turn_on"
        assert result.command.rule_id == "heat_rule"

    @pytest.mark.unit
    def test_generate_from_parsed_response_device_not_found(self) -> None:
        from src.control_reasoning.command_generator import CommandGenerator
        from src.control_reasoning.response_parser import (
            ActionSpec,
            ParsedResponse,
            ResponseType,
        )

        registry = _create_registry({})
        generator = CommandGenerator(registry=registry)
        parsed = ParsedResponse(
            response_type=ResponseType.ACTION,
            raw_text="ACTION: turn_on(nonexistent)",
            action=ActionSpec(device_id="nonexistent", command="turn_on"),
        )

        result = generator.generate_from_parsed_response(parsed)

        assert result is not None
        assert result.success is False
        assert "not found" in result.error  # type: ignore[operator]
