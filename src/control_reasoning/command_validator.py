from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any

from src.common.logging import get_logger
from src.control_reasoning.command_generator import DeviceCommand

if TYPE_CHECKING:
    from src.device_interface.models import Actuator
    from src.device_interface.registry import DeviceRegistry

logger = get_logger(__name__)

DEFAULT_RATE_LIMIT = 60
DEFAULT_RATE_WINDOW = 60.0


class ValidationStep(Enum):
    DEVICE_EXISTS = "device_exists"
    IS_ACTUATOR = "is_actuator"
    CAPABILITY_CHECK = "capability_check"
    CONSTRAINT_CHECK = "constraint_check"
    SAFETY_WHITELIST = "safety_whitelist"
    RATE_LIMIT = "rate_limit"
    CRITICAL_FLAG = "critical_flag"


@dataclass(frozen=True)
class ValidationError:
    step: ValidationStep
    message: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    command: DeviceCommand
    errors: tuple[ValidationError, ...] = ()
    is_critical: bool = False

    @classmethod
    def ok(
        cls,
        command: DeviceCommand,
        is_critical: bool = False,
    ) -> ValidationResult:
        return cls(valid=True, command=command, is_critical=is_critical)

    @classmethod
    def fail(
        cls,
        command: DeviceCommand,
        errors: list[ValidationError],
    ) -> ValidationResult:
        return cls(valid=False, command=command, errors=tuple(errors))


class CommandValidator:
    def __init__(
        self,
        registry: DeviceRegistry | None = None,
        safety_whitelist: set[str] | None = None,
        critical_commands: set[str] | None = None,
        rate_limit: int = DEFAULT_RATE_LIMIT,
        rate_window: float = DEFAULT_RATE_WINDOW,
    ) -> None:
        self._registry = registry
        self._safety_whitelist = safety_whitelist or set()
        self._critical_commands = critical_commands or set()
        self._rate_limit = rate_limit
        self._rate_window = rate_window
        self._command_history: dict[str, list[float]] = defaultdict(list)

    @property
    def registry(self) -> DeviceRegistry | None:
        return self._registry

    def set_registry(self, registry: DeviceRegistry) -> None:
        self._registry = registry

    @property
    def safety_whitelist(self) -> set[str]:
        return self._safety_whitelist

    def set_safety_whitelist(self, whitelist: set[str]) -> None:
        self._safety_whitelist = whitelist

    @property
    def critical_commands(self) -> set[str]:
        return self._critical_commands

    def set_critical_commands(self, commands: set[str]) -> None:
        self._critical_commands = commands

    def validate(self, command: DeviceCommand) -> ValidationResult:
        errors: list[ValidationError] = []

        if self._registry is None:
            errors.append(
                ValidationError(
                    step=ValidationStep.DEVICE_EXISTS,
                    message="No device registry configured",
                )
            )
            command.mark_rejected("No device registry configured")
            return ValidationResult.fail(command, errors)

        device = self._registry.get_optional(command.device_id)
        if device is None:
            errors.append(
                ValidationError(
                    step=ValidationStep.DEVICE_EXISTS,
                    message=f"Device '{command.device_id}' not found",
                    details={"device_id": command.device_id},
                )
            )
            command.mark_rejected(f"Device '{command.device_id}' not found")
            return ValidationResult.fail(command, errors)

        from src.device_interface.models import Actuator

        if not isinstance(device, Actuator):
            errors.append(
                ValidationError(
                    step=ValidationStep.IS_ACTUATOR,
                    message=f"Device '{command.device_id}' is not an actuator",
                    details={"device_type": device.device_type.value},
                )
            )
            command.mark_rejected("Device is not an actuator")
            return ValidationResult.fail(command, errors)

        if not device.has_capability(command.command_type):
            errors.append(
                ValidationError(
                    step=ValidationStep.CAPABILITY_CHECK,
                    message=f"Device does not support command '{command.command_type}'",
                    details={
                        "command": command.command_type,
                        "capabilities": list(device.capabilities),
                    },
                )
            )
            command.mark_rejected(f"Unsupported command: {command.command_type}")
            return ValidationResult.fail(command, errors)

        constraint_error = self._validate_constraints(command, device)
        if constraint_error:
            errors.append(constraint_error)
            command.mark_rejected("Parameter constraint violation")
            return ValidationResult.fail(command, errors)

        whitelist_error = self._validate_safety_whitelist(command)
        if whitelist_error:
            errors.append(whitelist_error)
            command.mark_rejected("Command not in safety whitelist")
            return ValidationResult.fail(command, errors)

        rate_error = self._validate_rate_limit(command)
        if rate_error:
            errors.append(rate_error)
            command.mark_rejected("Rate limit exceeded")
            return ValidationResult.fail(command, errors)

        is_critical = self._is_critical_command(command)

        command.mark_validated()
        self._record_command(command)

        logger.debug(
            "Command validated",
            extra={
                "command_id": command.command_id,
                "device_id": command.device_id,
                "is_critical": is_critical,
            },
        )

        return ValidationResult.ok(command, is_critical=is_critical)

    def _validate_constraints(
        self,
        command: DeviceCommand,
        device: Actuator,
    ) -> ValidationError | None:
        if device.constraints is None:
            return None

        for param_name, param_value in command.parameters.items():
            if not device.constraints.validate(param_value):
                return ValidationError(
                    step=ValidationStep.CONSTRAINT_CHECK,
                    message=f"Parameter '{param_name}' value {param_value} violates constraints",
                    details={
                        "parameter": param_name,
                        "value": param_value,
                        "min": device.constraints.min_value,
                        "max": device.constraints.max_value,
                        "allowed_values": (
                            list(device.constraints.allowed_values)
                            if device.constraints.allowed_values
                            else None
                        ),
                    },
                )

        return None

    def _validate_safety_whitelist(
        self,
        command: DeviceCommand,
    ) -> ValidationError | None:
        if not self._safety_whitelist:
            return None

        if command.command_type not in self._safety_whitelist:
            return ValidationError(
                step=ValidationStep.SAFETY_WHITELIST,
                message=f"Command '{command.command_type}' not in safety whitelist",
                details={
                    "command": command.command_type,
                    "whitelist": list(self._safety_whitelist),
                },
            )

        return None

    def _validate_rate_limit(
        self,
        command: DeviceCommand,
    ) -> ValidationError | None:
        now = time.time()
        device_id = command.device_id

        self._command_history[device_id] = [
            ts
            for ts in self._command_history[device_id]
            if now - ts < self._rate_window
        ]

        if len(self._command_history[device_id]) >= self._rate_limit:
            return ValidationError(
                step=ValidationStep.RATE_LIMIT,
                message=f"Rate limit exceeded for device '{device_id}'",
                details={
                    "device_id": device_id,
                    "limit": self._rate_limit,
                    "window_seconds": self._rate_window,
                    "current_count": len(self._command_history[device_id]),
                },
            )

        return None

    def _is_critical_command(self, command: DeviceCommand) -> bool:
        return command.command_type in self._critical_commands

    def _record_command(self, command: DeviceCommand) -> None:
        self._command_history[command.device_id].append(time.time())

    def validate_batch(
        self,
        commands: list[DeviceCommand],
    ) -> list[ValidationResult]:
        return [self.validate(cmd) for cmd in commands]

    def clear_rate_limit_history(self, device_id: str | None = None) -> None:
        if device_id is None:
            self._command_history.clear()
        elif device_id in self._command_history:
            del self._command_history[device_id]

    def get_rate_limit_status(self, device_id: str) -> dict[str, Any]:
        now = time.time()
        history = [
            ts
            for ts in self._command_history.get(device_id, [])
            if now - ts < self._rate_window
        ]
        return {
            "device_id": device_id,
            "commands_in_window": len(history),
            "limit": self._rate_limit,
            "window_seconds": self._rate_window,
            "remaining": max(0, self._rate_limit - len(history)),
        }
