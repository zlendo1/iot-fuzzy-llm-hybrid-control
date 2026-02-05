from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any

from src.common.logging import get_logger
from src.control_reasoning.command_generator import DeviceCommand

if TYPE_CHECKING:
    pass

logger = get_logger(__name__)


class ResolutionStrategy(Enum):
    PRIORITY = "priority"
    FIRST = "first"
    LAST = "last"
    MERGE = "merge"


@dataclass(frozen=True)
class ConflictInfo:
    device_id: str
    commands: tuple[DeviceCommand, ...]
    winning_command: DeviceCommand
    dropped_commands: tuple[DeviceCommand, ...]
    strategy: ResolutionStrategy

    def to_dict(self) -> dict[str, Any]:
        return {
            "device_id": self.device_id,
            "commands_count": len(self.commands),
            "winning_command_id": self.winning_command.command_id,
            "dropped_command_ids": [cmd.command_id for cmd in self.dropped_commands],
            "strategy": self.strategy.value,
        }


@dataclass(frozen=True)
class ResolutionResult:
    resolved_commands: tuple[DeviceCommand, ...]
    conflicts: tuple[ConflictInfo, ...]
    had_conflicts: bool = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "had_conflicts", len(self.conflicts) > 0)


class ConflictResolver:
    def __init__(
        self,
        strategy: ResolutionStrategy = ResolutionStrategy.PRIORITY,
        priority_map: dict[str, int] | None = None,
    ) -> None:
        self._strategy = strategy
        self._priority_map = priority_map or {}

    @property
    def strategy(self) -> ResolutionStrategy:
        return self._strategy

    def set_strategy(self, strategy: ResolutionStrategy) -> None:
        self._strategy = strategy

    @property
    def priority_map(self) -> dict[str, int]:
        return self._priority_map

    def set_priority_map(self, priority_map: dict[str, int]) -> None:
        self._priority_map = priority_map

    def resolve(
        self,
        commands: list[DeviceCommand],
    ) -> ResolutionResult:
        if not commands:
            return ResolutionResult(
                resolved_commands=(),
                conflicts=(),
            )

        device_commands: dict[str, list[DeviceCommand]] = {}
        for cmd in commands:
            if cmd.device_id not in device_commands:
                device_commands[cmd.device_id] = []
            device_commands[cmd.device_id].append(cmd)

        resolved: list[DeviceCommand] = []
        conflicts: list[ConflictInfo] = []

        for device_id, cmds in device_commands.items():
            if len(cmds) == 1:
                resolved.append(cmds[0])
            else:
                winner, dropped = self._resolve_conflict(cmds)
                resolved.append(winner)

                conflict = ConflictInfo(
                    device_id=device_id,
                    commands=tuple(cmds),
                    winning_command=winner,
                    dropped_commands=tuple(dropped),
                    strategy=self._strategy,
                )
                conflicts.append(conflict)

                logger.info(
                    "Resolved command conflict",
                    extra={
                        "device_id": device_id,
                        "winner": winner.command_id,
                        "dropped_count": len(dropped),
                        "strategy": self._strategy.value,
                    },
                )

        return ResolutionResult(
            resolved_commands=tuple(resolved),
            conflicts=tuple(conflicts),
        )

    def _resolve_conflict(
        self,
        commands: list[DeviceCommand],
    ) -> tuple[DeviceCommand, list[DeviceCommand]]:
        if self._strategy == ResolutionStrategy.FIRST:
            return self._resolve_first(commands)
        elif self._strategy == ResolutionStrategy.LAST:
            return self._resolve_last(commands)
        elif self._strategy == ResolutionStrategy.MERGE:
            return self._resolve_merge(commands)
        else:
            return self._resolve_priority(commands)

    def _resolve_first(
        self,
        commands: list[DeviceCommand],
    ) -> tuple[DeviceCommand, list[DeviceCommand]]:
        sorted_cmds = sorted(commands, key=lambda c: c.created_at)
        return sorted_cmds[0], sorted_cmds[1:]

    def _resolve_last(
        self,
        commands: list[DeviceCommand],
    ) -> tuple[DeviceCommand, list[DeviceCommand]]:
        sorted_cmds = sorted(commands, key=lambda c: c.created_at, reverse=True)
        return sorted_cmds[0], sorted_cmds[1:]

    def _resolve_priority(
        self,
        commands: list[DeviceCommand],
    ) -> tuple[DeviceCommand, list[DeviceCommand]]:
        def get_priority(cmd: DeviceCommand) -> int:
            if cmd.rule_id and cmd.rule_id in self._priority_map:
                return self._priority_map[cmd.rule_id]
            return 0

        sorted_cmds = sorted(commands, key=get_priority, reverse=True)
        return sorted_cmds[0], sorted_cmds[1:]

    def _resolve_merge(
        self,
        commands: list[DeviceCommand],
    ) -> tuple[DeviceCommand, list[DeviceCommand]]:
        sorted_cmds = sorted(commands, key=lambda c: c.created_at)
        base = sorted_cmds[0]

        merged_params = dict(base.parameters)
        for cmd in sorted_cmds[1:]:
            merged_params.update(cmd.parameters)

        merged = DeviceCommand(
            command_id=base.command_id,
            device_id=base.device_id,
            command_type=base.command_type,
            parameters=merged_params,
            status=base.status,
            created_at=base.created_at,
            rule_id=base.rule_id,
        )

        return merged, sorted_cmds[1:]

    def detect_conflicts(
        self,
        commands: list[DeviceCommand],
    ) -> dict[str, list[DeviceCommand]]:
        device_commands: dict[str, list[DeviceCommand]] = {}
        for cmd in commands:
            if cmd.device_id not in device_commands:
                device_commands[cmd.device_id] = []
            device_commands[cmd.device_id].append(cmd)

        return {
            device_id: cmds
            for device_id, cmds in device_commands.items()
            if len(cmds) > 1
        }

    def has_conflicts(self, commands: list[DeviceCommand]) -> bool:
        return len(self.detect_conflicts(commands)) > 0
