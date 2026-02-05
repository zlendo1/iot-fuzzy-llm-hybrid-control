from __future__ import annotations

from typing import TYPE_CHECKING, Any
from unittest.mock import Mock

import pytest

if TYPE_CHECKING:
    from src.device_interface.models import Actuator, Sensor


def _create_actuator(
    device_id: str = "actuator_001",
    capabilities: tuple[str, ...] = ("turn_on", "turn_off", "set_temperature"),
    constraints: Any | None = None,
) -> Actuator:
    from src.device_interface.models import Actuator, Constraints, DeviceType

    return Actuator(
        id=device_id,
        name=f"Test Actuator {device_id}",
        device_type=DeviceType.ACTUATOR,
        device_class="switch",
        capabilities=capabilities,
        constraints=Constraints.from_dict(constraints) if constraints else None,
    )


def _create_sensor(device_id: str = "sensor_001") -> Sensor:
    from src.device_interface.models import DeviceType, Sensor

    return Sensor(
        id=device_id,
        name=f"Test Sensor {device_id}",
        device_type=DeviceType.SENSOR,
        device_class="temperature",
    )


def _create_registry(devices: dict[str, Any] | None = None) -> Mock:
    registry = Mock()
    devices = devices or {}

    def get_optional(device_id: str) -> Any | None:
        return devices.get(device_id)

    registry.get_optional = get_optional
    return registry


def _create_command(
    command_id: str = "cmd_001",
    device_id: str = "actuator_001",
    command_type: str = "turn_on",
    parameters: dict[str, Any] | None = None,
) -> Any:
    from src.control_reasoning.command_generator import DeviceCommand

    return DeviceCommand(
        command_id=command_id,
        device_id=device_id,
        command_type=command_type,
        parameters=parameters or {},
    )


class TestValidationStep:
    @pytest.mark.unit
    def test_validation_step_values(self) -> None:
        from src.control_reasoning.command_validator import ValidationStep

        assert ValidationStep.DEVICE_EXISTS.value == "device_exists"
        assert ValidationStep.IS_ACTUATOR.value == "is_actuator"
        assert ValidationStep.CAPABILITY_CHECK.value == "capability_check"
        assert ValidationStep.CONSTRAINT_CHECK.value == "constraint_check"
        assert ValidationStep.SAFETY_WHITELIST.value == "safety_whitelist"
        assert ValidationStep.RATE_LIMIT.value == "rate_limit"
        assert ValidationStep.CRITICAL_FLAG.value == "critical_flag"

    @pytest.mark.unit
    def test_validation_step_count(self) -> None:
        from src.control_reasoning.command_validator import ValidationStep

        assert len(ValidationStep) == 7


class TestValidationError:
    @pytest.mark.unit
    def test_validation_error_creation(self) -> None:
        from src.control_reasoning.command_validator import (
            ValidationError,
            ValidationStep,
        )

        error = ValidationError(
            step=ValidationStep.DEVICE_EXISTS,
            message="Device not found",
            details={"device_id": "unknown"},
        )

        assert error.step == ValidationStep.DEVICE_EXISTS
        assert error.message == "Device not found"
        assert error.details == {"device_id": "unknown"}

    @pytest.mark.unit
    def test_validation_error_default_details(self) -> None:
        from src.control_reasoning.command_validator import (
            ValidationError,
            ValidationStep,
        )

        error = ValidationError(
            step=ValidationStep.RATE_LIMIT,
            message="Rate limit exceeded",
        )

        assert error.details == {}

    @pytest.mark.unit
    def test_validation_error_is_frozen(self) -> None:
        from dataclasses import FrozenInstanceError

        from src.control_reasoning.command_validator import (
            ValidationError,
            ValidationStep,
        )

        error = ValidationError(
            step=ValidationStep.DEVICE_EXISTS,
            message="Error",
        )

        with pytest.raises(FrozenInstanceError):
            error.message = "New message"  # type: ignore[misc]


class TestValidationResult:
    @pytest.mark.unit
    def test_validation_result_ok(self) -> None:
        from src.control_reasoning.command_validator import ValidationResult

        command = _create_command()
        result = ValidationResult.ok(command)

        assert result.valid is True
        assert result.command is command
        assert result.errors == ()
        assert result.is_critical is False

    @pytest.mark.unit
    def test_validation_result_ok_critical(self) -> None:
        from src.control_reasoning.command_validator import ValidationResult

        command = _create_command()
        result = ValidationResult.ok(command, is_critical=True)

        assert result.valid is True
        assert result.is_critical is True

    @pytest.mark.unit
    def test_validation_result_fail(self) -> None:
        from src.control_reasoning.command_validator import (
            ValidationError,
            ValidationResult,
            ValidationStep,
        )

        command = _create_command()
        errors = [
            ValidationError(step=ValidationStep.DEVICE_EXISTS, message="Not found"),
        ]
        result = ValidationResult.fail(command, errors)

        assert result.valid is False
        assert result.command is command
        assert len(result.errors) == 1
        assert result.errors[0].step == ValidationStep.DEVICE_EXISTS

    @pytest.mark.unit
    def test_validation_result_is_frozen(self) -> None:
        from dataclasses import FrozenInstanceError

        from src.control_reasoning.command_validator import ValidationResult

        command = _create_command()
        result = ValidationResult.ok(command)

        with pytest.raises(FrozenInstanceError):
            result.valid = False  # type: ignore[misc]


class TestCommandValidatorInit:
    @pytest.mark.unit
    def test_validator_init_defaults(self) -> None:
        from src.control_reasoning.command_validator import CommandValidator

        validator = CommandValidator()

        assert validator.registry is None
        assert validator.safety_whitelist == set()
        assert validator.critical_commands == set()

    @pytest.mark.unit
    def test_validator_init_with_registry(self) -> None:
        from src.control_reasoning.command_validator import CommandValidator

        registry = _create_registry()
        validator = CommandValidator(registry=registry)

        assert validator.registry is registry

    @pytest.mark.unit
    def test_validator_init_with_whitelist(self) -> None:
        from src.control_reasoning.command_validator import CommandValidator

        whitelist = {"turn_on", "turn_off"}
        validator = CommandValidator(safety_whitelist=whitelist)

        assert validator.safety_whitelist == whitelist

    @pytest.mark.unit
    def test_validator_init_with_critical_commands(self) -> None:
        from src.control_reasoning.command_validator import CommandValidator

        critical = {"emergency_stop", "reset"}
        validator = CommandValidator(critical_commands=critical)

        assert validator.critical_commands == critical

    @pytest.mark.unit
    def test_validator_set_registry(self) -> None:
        from src.control_reasoning.command_validator import CommandValidator

        validator = CommandValidator()
        registry = _create_registry()
        validator.set_registry(registry)

        assert validator.registry is registry

    @pytest.mark.unit
    def test_validator_set_safety_whitelist(self) -> None:
        from src.control_reasoning.command_validator import CommandValidator

        validator = CommandValidator()
        validator.set_safety_whitelist({"turn_on"})

        assert validator.safety_whitelist == {"turn_on"}

    @pytest.mark.unit
    def test_validator_set_critical_commands(self) -> None:
        from src.control_reasoning.command_validator import CommandValidator

        validator = CommandValidator()
        validator.set_critical_commands({"shutdown"})

        assert validator.critical_commands == {"shutdown"}


class TestCommandValidatorDeviceChecks:
    @pytest.mark.unit
    def test_validate_fails_without_registry(self) -> None:
        from src.control_reasoning.command_validator import (
            CommandValidator,
            ValidationStep,
        )

        validator = CommandValidator()
        command = _create_command()

        result = validator.validate(command)

        assert result.valid is False
        assert len(result.errors) == 1
        assert result.errors[0].step == ValidationStep.DEVICE_EXISTS

    @pytest.mark.unit
    def test_validate_fails_device_not_found(self) -> None:
        from src.control_reasoning.command_validator import (
            CommandValidator,
            ValidationStep,
        )

        registry = _create_registry({})
        validator = CommandValidator(registry=registry)
        command = _create_command(device_id="unknown")

        result = validator.validate(command)

        assert result.valid is False
        assert result.errors[0].step == ValidationStep.DEVICE_EXISTS
        assert "unknown" in result.errors[0].message

    @pytest.mark.unit
    def test_validate_fails_device_is_sensor(self) -> None:
        from src.control_reasoning.command_validator import (
            CommandValidator,
            ValidationStep,
        )

        sensor = _create_sensor("temp_sensor")
        registry = _create_registry({"temp_sensor": sensor})
        validator = CommandValidator(registry=registry)
        command = _create_command(device_id="temp_sensor")

        result = validator.validate(command)

        assert result.valid is False
        assert result.errors[0].step == ValidationStep.IS_ACTUATOR

    @pytest.mark.unit
    def test_validate_fails_missing_capability(self) -> None:
        from src.control_reasoning.command_validator import (
            CommandValidator,
            ValidationStep,
        )

        actuator = _create_actuator(capabilities=("turn_on", "turn_off"))
        registry = _create_registry({"actuator_001": actuator})
        validator = CommandValidator(registry=registry)
        command = _create_command(command_type="set_color")

        result = validator.validate(command)

        assert result.valid is False
        assert result.errors[0].step == ValidationStep.CAPABILITY_CHECK


class TestCommandValidatorConstraints:
    @pytest.mark.unit
    def test_validate_passes_no_constraints(self) -> None:
        from src.control_reasoning.command_validator import CommandValidator

        actuator = _create_actuator()
        registry = _create_registry({"actuator_001": actuator})
        validator = CommandValidator(registry=registry)
        command = _create_command(parameters={"temperature": 25})

        result = validator.validate(command)

        assert result.valid is True

    @pytest.mark.unit
    def test_validate_passes_within_constraints(self) -> None:
        from src.control_reasoning.command_validator import CommandValidator

        actuator = _create_actuator(
            constraints={"min": 16, "max": 30},
        )
        registry = _create_registry({"actuator_001": actuator})
        validator = CommandValidator(registry=registry)
        command = _create_command(parameters={"temperature": 22})

        result = validator.validate(command)

        assert result.valid is True

    @pytest.mark.unit
    def test_validate_fails_below_min_constraint(self) -> None:
        from src.control_reasoning.command_validator import (
            CommandValidator,
            ValidationStep,
        )

        actuator = _create_actuator(
            constraints={"min": 16, "max": 30},
        )
        registry = _create_registry({"actuator_001": actuator})
        validator = CommandValidator(registry=registry)
        command = _create_command(parameters={"temperature": 10})

        result = validator.validate(command)

        assert result.valid is False
        assert result.errors[0].step == ValidationStep.CONSTRAINT_CHECK

    @pytest.mark.unit
    def test_validate_fails_above_max_constraint(self) -> None:
        from src.control_reasoning.command_validator import (
            CommandValidator,
            ValidationStep,
        )

        actuator = _create_actuator(
            constraints={"min": 16, "max": 30},
        )
        registry = _create_registry({"actuator_001": actuator})
        validator = CommandValidator(registry=registry)
        command = _create_command(parameters={"temperature": 40})

        result = validator.validate(command)

        assert result.valid is False
        assert result.errors[0].step == ValidationStep.CONSTRAINT_CHECK

    @pytest.mark.unit
    def test_validate_fails_not_in_allowed_values(self) -> None:
        from src.control_reasoning.command_validator import (
            CommandValidator,
            ValidationStep,
        )

        actuator = _create_actuator(
            constraints={"allowed_values": ["low", "medium", "high"]},
        )
        registry = _create_registry({"actuator_001": actuator})
        validator = CommandValidator(registry=registry)
        command = _create_command(parameters={"mode": "turbo"})

        result = validator.validate(command)

        assert result.valid is False
        assert result.errors[0].step == ValidationStep.CONSTRAINT_CHECK


class TestCommandValidatorSafetyWhitelist:
    @pytest.mark.unit
    def test_validate_passes_empty_whitelist(self) -> None:
        from src.control_reasoning.command_validator import CommandValidator

        actuator = _create_actuator()
        registry = _create_registry({"actuator_001": actuator})
        validator = CommandValidator(registry=registry)
        command = _create_command()

        result = validator.validate(command)

        assert result.valid is True

    @pytest.mark.unit
    def test_validate_passes_command_in_whitelist(self) -> None:
        from src.control_reasoning.command_validator import CommandValidator

        actuator = _create_actuator()
        registry = _create_registry({"actuator_001": actuator})
        validator = CommandValidator(
            registry=registry,
            safety_whitelist={"turn_on", "turn_off"},
        )
        command = _create_command(command_type="turn_on")

        result = validator.validate(command)

        assert result.valid is True

    @pytest.mark.unit
    def test_validate_fails_command_not_in_whitelist(self) -> None:
        from src.control_reasoning.command_validator import (
            CommandValidator,
            ValidationStep,
        )

        actuator = _create_actuator()
        registry = _create_registry({"actuator_001": actuator})
        validator = CommandValidator(
            registry=registry,
            safety_whitelist={"turn_off"},
        )
        command = _create_command(command_type="turn_on")

        result = validator.validate(command)

        assert result.valid is False
        assert result.errors[0].step == ValidationStep.SAFETY_WHITELIST


class TestCommandValidatorRateLimit:
    @pytest.mark.unit
    def test_validate_passes_under_rate_limit(self) -> None:
        from src.control_reasoning.command_validator import CommandValidator

        actuator = _create_actuator()
        registry = _create_registry({"actuator_001": actuator})
        validator = CommandValidator(registry=registry, rate_limit=5)

        for i in range(5):
            command = _create_command(command_id=f"cmd_{i:03d}")
            result = validator.validate(command)
            assert result.valid is True

    @pytest.mark.unit
    def test_validate_fails_at_rate_limit(self) -> None:
        from src.control_reasoning.command_validator import (
            CommandValidator,
            ValidationStep,
        )

        actuator = _create_actuator()
        registry = _create_registry({"actuator_001": actuator})
        validator = CommandValidator(registry=registry, rate_limit=3)

        for i in range(3):
            command = _create_command(command_id=f"cmd_{i:03d}")
            validator.validate(command)

        command = _create_command(command_id="cmd_003")
        result = validator.validate(command)

        assert result.valid is False
        assert result.errors[0].step == ValidationStep.RATE_LIMIT

    @pytest.mark.unit
    def test_validate_rate_limit_per_device(self) -> None:
        from src.control_reasoning.command_validator import CommandValidator

        actuator1 = _create_actuator(device_id="actuator_001")
        actuator2 = _create_actuator(device_id="actuator_002")
        registry = _create_registry(
            {
                "actuator_001": actuator1,
                "actuator_002": actuator2,
            }
        )
        validator = CommandValidator(registry=registry, rate_limit=2)

        for i in range(2):
            command = _create_command(command_id=f"cmd1_{i}", device_id="actuator_001")
            validator.validate(command)

        command = _create_command(command_id="cmd2_0", device_id="actuator_002")
        result = validator.validate(command)

        assert result.valid is True

    @pytest.mark.unit
    def test_clear_rate_limit_history_all(self) -> None:
        from src.control_reasoning.command_validator import CommandValidator

        actuator = _create_actuator()
        registry = _create_registry({"actuator_001": actuator})
        validator = CommandValidator(registry=registry, rate_limit=2)

        for i in range(2):
            command = _create_command(command_id=f"cmd_{i:03d}")
            validator.validate(command)

        validator.clear_rate_limit_history()

        command = _create_command(command_id="cmd_new")
        result = validator.validate(command)

        assert result.valid is True

    @pytest.mark.unit
    def test_clear_rate_limit_history_specific_device(self) -> None:
        from src.control_reasoning.command_validator import CommandValidator

        actuator1 = _create_actuator(device_id="actuator_001")
        actuator2 = _create_actuator(device_id="actuator_002")
        registry = _create_registry(
            {
                "actuator_001": actuator1,
                "actuator_002": actuator2,
            }
        )
        validator = CommandValidator(registry=registry, rate_limit=1)

        validator.validate(_create_command(device_id="actuator_001"))
        validator.validate(
            _create_command(command_id="cmd_002", device_id="actuator_002")
        )

        validator.clear_rate_limit_history("actuator_001")

        result1 = validator.validate(
            _create_command(command_id="cmd_003", device_id="actuator_001")
        )
        result2 = validator.validate(
            _create_command(command_id="cmd_004", device_id="actuator_002")
        )

        assert result1.valid is True
        assert result2.valid is False

    @pytest.mark.unit
    def test_get_rate_limit_status(self) -> None:
        from src.control_reasoning.command_validator import CommandValidator

        actuator = _create_actuator()
        registry = _create_registry({"actuator_001": actuator})
        validator = CommandValidator(registry=registry, rate_limit=10, rate_window=60.0)

        validator.validate(_create_command())
        validator.validate(_create_command(command_id="cmd_002"))

        status = validator.get_rate_limit_status("actuator_001")

        assert status["device_id"] == "actuator_001"
        assert status["commands_in_window"] == 2
        assert status["limit"] == 10
        assert status["remaining"] == 8


class TestCommandValidatorCriticalCommands:
    @pytest.mark.unit
    def test_validate_marks_critical_command(self) -> None:
        from src.control_reasoning.command_validator import CommandValidator

        actuator = _create_actuator(capabilities=("turn_on", "emergency_stop"))
        registry = _create_registry({"actuator_001": actuator})
        validator = CommandValidator(
            registry=registry,
            critical_commands={"emergency_stop"},
        )
        command = _create_command(command_type="emergency_stop")

        result = validator.validate(command)

        assert result.valid is True
        assert result.is_critical is True

    @pytest.mark.unit
    def test_validate_non_critical_command(self) -> None:
        from src.control_reasoning.command_validator import CommandValidator

        actuator = _create_actuator()
        registry = _create_registry({"actuator_001": actuator})
        validator = CommandValidator(
            registry=registry,
            critical_commands={"emergency_stop"},
        )
        command = _create_command(command_type="turn_on")

        result = validator.validate(command)

        assert result.valid is True
        assert result.is_critical is False


class TestCommandValidatorBatch:
    @pytest.mark.unit
    def test_validate_batch_empty(self) -> None:
        from src.control_reasoning.command_validator import CommandValidator

        validator = CommandValidator()

        results = validator.validate_batch([])

        assert results == []

    @pytest.mark.unit
    def test_validate_batch_mixed_results(self) -> None:
        from src.control_reasoning.command_validator import CommandValidator

        actuator = _create_actuator(capabilities=("turn_on",))
        registry = _create_registry({"actuator_001": actuator})
        validator = CommandValidator(registry=registry)

        commands = [
            _create_command(command_type="turn_on"),
            _create_command(command_id="cmd_002", command_type="invalid_cmd"),
        ]

        results = validator.validate_batch(commands)

        assert len(results) == 2
        assert results[0].valid is True
        assert results[1].valid is False


class TestCommandValidatorCommandStatus:
    @pytest.mark.unit
    def test_validate_marks_command_validated(self) -> None:
        from src.control_reasoning.command_generator import CommandStatus
        from src.control_reasoning.command_validator import CommandValidator

        actuator = _create_actuator()
        registry = _create_registry({"actuator_001": actuator})
        validator = CommandValidator(registry=registry)
        command = _create_command()

        validator.validate(command)

        assert command.status == CommandStatus.VALIDATED

    @pytest.mark.unit
    def test_validate_marks_command_rejected(self) -> None:
        from src.control_reasoning.command_generator import CommandStatus
        from src.control_reasoning.command_validator import CommandValidator

        registry = _create_registry({})
        validator = CommandValidator(registry=registry)
        command = _create_command()

        validator.validate(command)

        assert command.status == CommandStatus.REJECTED
        assert command.rejection_reason is not None
