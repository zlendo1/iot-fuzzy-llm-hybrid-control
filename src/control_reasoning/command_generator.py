from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any

from src.common.logging import get_logger
from src.control_reasoning.response_parser import ActionSpec

if TYPE_CHECKING:
    from src.device_interface.models import Actuator
    from src.device_interface.registry import DeviceRegistry

logger = get_logger(__name__)


class CommandStatus(Enum):
    PENDING = "pending"
    VALIDATED = "validated"
    REJECTED = "rejected"
    EXECUTED = "executed"
    FAILED = "failed"


@dataclass
class DeviceCommand:
    command_id: str
    device_id: str
    command_type: str
    parameters: dict[str, Any] = field(default_factory=dict)
    status: CommandStatus = CommandStatus.PENDING
    created_at: float = field(default_factory=time.time)
    rule_id: str | None = None
    rejection_reason: str | None = None

    def to_mqtt_payload(self) -> dict[str, Any]:
        return {
            "command": self.command_type,
            "parameters": self.parameters,
            "command_id": self.command_id,
            "timestamp": self.created_at,
        }

    def mark_validated(self) -> None:
        self.status = CommandStatus.VALIDATED

    def mark_rejected(self, reason: str) -> None:
        self.status = CommandStatus.REJECTED
        self.rejection_reason = reason

    def mark_executed(self) -> None:
        self.status = CommandStatus.EXECUTED

    def mark_failed(self, reason: str) -> None:
        self.status = CommandStatus.FAILED
        self.rejection_reason = reason


@dataclass(frozen=True)
class GenerationResult:
    success: bool
    command: DeviceCommand | None = None
    error: str | None = None

    @classmethod
    def ok(cls, command: DeviceCommand) -> GenerationResult:
        return cls(success=True, command=command)

    @classmethod
    def fail(cls, error: str) -> GenerationResult:
        return cls(success=False, error=error)


class CommandGenerator:
    def __init__(self, registry: DeviceRegistry | None = None) -> None:
        self._registry = registry
        self._command_counter = 0

    @property
    def registry(self) -> DeviceRegistry | None:
        return self._registry

    def set_registry(self, registry: DeviceRegistry) -> None:
        self._registry = registry

    def generate(
        self,
        action: ActionSpec,
        rule_id: str | None = None,
    ) -> GenerationResult:
        if self._registry is None:
            return GenerationResult.fail("No device registry configured")

        device = self._registry.get_optional(action.device_id)
        if device is None:
            logger.warning(
                "Device not found for command generation",
                extra={"device_id": action.device_id},
            )
            return GenerationResult.fail(f"Device '{action.device_id}' not found")

        from src.device_interface.models import Actuator

        if not isinstance(device, Actuator):
            logger.warning(
                "Cannot send command to non-actuator device",
                extra={
                    "device_id": action.device_id,
                    "device_type": device.device_type.value,
                },
            )
            return GenerationResult.fail(
                f"Device '{action.device_id}' is not an actuator"
            )

        if not device.has_capability(action.command):
            logger.warning(
                "Device lacks required capability",
                extra={
                    "device_id": action.device_id,
                    "command": action.command,
                    "capabilities": device.capabilities,
                },
            )
            return GenerationResult.fail(
                f"Device '{action.device_id}' does not support command '{action.command}'"
            )

        command = self._create_command(action, device, rule_id)

        logger.debug(
            "Generated command",
            extra={
                "command_id": command.command_id,
                "device_id": command.device_id,
                "command_type": command.command_type,
            },
        )

        return GenerationResult.ok(command)

    def _create_command(
        self,
        action: ActionSpec,
        device: Actuator,  # noqa: ARG002
        rule_id: str | None,
    ) -> DeviceCommand:
        self._command_counter += 1
        command_id = f"cmd_{self._command_counter:06d}"

        return DeviceCommand(
            command_id=command_id,
            device_id=action.device_id,
            command_type=action.command,
            parameters=dict(action.parameters),
            rule_id=rule_id,
        )

    def generate_batch(
        self,
        actions: list[ActionSpec],
        rule_id: str | None = None,
    ) -> list[GenerationResult]:
        return [self.generate(action, rule_id) for action in actions]

    def generate_from_parsed_response(
        self,
        parsed: Any,
        rule_id: str | None = None,
    ) -> GenerationResult | None:
        from src.control_reasoning.response_parser import ParsedResponse, ResponseType

        if not isinstance(parsed, ParsedResponse):
            return GenerationResult.fail("Invalid parsed response type")

        if parsed.response_type != ResponseType.ACTION:
            return None

        if parsed.action is None:
            return GenerationResult.fail("Parsed response has no action")

        return self.generate(parsed.action, rule_id)
