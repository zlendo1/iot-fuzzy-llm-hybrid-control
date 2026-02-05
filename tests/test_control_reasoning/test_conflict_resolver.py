from __future__ import annotations

from typing import Any

import pytest


def _create_command(
    command_id: str = "cmd_001",
    device_id: str = "actuator_001",
    command_type: str = "turn_on",
    parameters: dict[str, Any] | None = None,
    rule_id: str | None = None,
    created_at: float = 1000.0,
) -> Any:
    from src.control_reasoning.command_generator import DeviceCommand

    return DeviceCommand(
        command_id=command_id,
        device_id=device_id,
        command_type=command_type,
        parameters=parameters or {},
        rule_id=rule_id,
        created_at=created_at,
    )


class TestResolutionStrategy:
    @pytest.mark.unit
    def test_strategy_values(self) -> None:
        from src.control_reasoning.conflict_resolver import ResolutionStrategy

        assert ResolutionStrategy.PRIORITY.value == "priority"
        assert ResolutionStrategy.FIRST.value == "first"
        assert ResolutionStrategy.LAST.value == "last"
        assert ResolutionStrategy.MERGE.value == "merge"

    @pytest.mark.unit
    def test_strategy_count(self) -> None:
        from src.control_reasoning.conflict_resolver import ResolutionStrategy

        assert len(ResolutionStrategy) == 4


class TestConflictInfo:
    @pytest.mark.unit
    def test_conflict_info_creation(self) -> None:
        from src.control_reasoning.conflict_resolver import (
            ConflictInfo,
            ResolutionStrategy,
        )

        cmd1 = _create_command(command_id="cmd_001")
        cmd2 = _create_command(command_id="cmd_002")

        info = ConflictInfo(
            device_id="actuator_001",
            commands=(cmd1, cmd2),
            winning_command=cmd1,
            dropped_commands=(cmd2,),
            strategy=ResolutionStrategy.PRIORITY,
        )

        assert info.device_id == "actuator_001"
        assert len(info.commands) == 2
        assert info.winning_command is cmd1
        assert len(info.dropped_commands) == 1
        assert info.strategy == ResolutionStrategy.PRIORITY

    @pytest.mark.unit
    def test_conflict_info_to_dict(self) -> None:
        from src.control_reasoning.conflict_resolver import (
            ConflictInfo,
            ResolutionStrategy,
        )

        cmd1 = _create_command(command_id="cmd_001")
        cmd2 = _create_command(command_id="cmd_002")

        info = ConflictInfo(
            device_id="actuator_001",
            commands=(cmd1, cmd2),
            winning_command=cmd1,
            dropped_commands=(cmd2,),
            strategy=ResolutionStrategy.FIRST,
        )

        result = info.to_dict()

        assert result["device_id"] == "actuator_001"
        assert result["commands_count"] == 2
        assert result["winning_command_id"] == "cmd_001"
        assert result["dropped_command_ids"] == ["cmd_002"]
        assert result["strategy"] == "first"

    @pytest.mark.unit
    def test_conflict_info_is_frozen(self) -> None:
        from dataclasses import FrozenInstanceError

        from src.control_reasoning.conflict_resolver import (
            ConflictInfo,
            ResolutionStrategy,
        )

        cmd1 = _create_command()
        info = ConflictInfo(
            device_id="actuator_001",
            commands=(cmd1,),
            winning_command=cmd1,
            dropped_commands=(),
            strategy=ResolutionStrategy.FIRST,
        )

        with pytest.raises(FrozenInstanceError):
            info.device_id = "other"  # type: ignore[misc]


class TestResolutionResult:
    @pytest.mark.unit
    def test_resolution_result_no_conflicts(self) -> None:
        from src.control_reasoning.conflict_resolver import ResolutionResult

        cmd = _create_command()
        result = ResolutionResult(
            resolved_commands=(cmd,),
            conflicts=(),
        )

        assert len(result.resolved_commands) == 1
        assert len(result.conflicts) == 0
        assert result.had_conflicts is False

    @pytest.mark.unit
    def test_resolution_result_with_conflicts(self) -> None:
        from src.control_reasoning.conflict_resolver import (
            ConflictInfo,
            ResolutionResult,
            ResolutionStrategy,
        )

        cmd1 = _create_command(command_id="cmd_001")
        cmd2 = _create_command(command_id="cmd_002")

        conflict = ConflictInfo(
            device_id="actuator_001",
            commands=(cmd1, cmd2),
            winning_command=cmd1,
            dropped_commands=(cmd2,),
            strategy=ResolutionStrategy.FIRST,
        )

        result = ResolutionResult(
            resolved_commands=(cmd1,),
            conflicts=(conflict,),
        )

        assert len(result.resolved_commands) == 1
        assert len(result.conflicts) == 1
        assert result.had_conflicts is True


class TestConflictResolverInit:
    @pytest.mark.unit
    def test_resolver_default_strategy(self) -> None:
        from src.control_reasoning.conflict_resolver import (
            ConflictResolver,
            ResolutionStrategy,
        )

        resolver = ConflictResolver()

        assert resolver.strategy == ResolutionStrategy.PRIORITY

    @pytest.mark.unit
    def test_resolver_custom_strategy(self) -> None:
        from src.control_reasoning.conflict_resolver import (
            ConflictResolver,
            ResolutionStrategy,
        )

        resolver = ConflictResolver(strategy=ResolutionStrategy.LAST)

        assert resolver.strategy == ResolutionStrategy.LAST

    @pytest.mark.unit
    def test_resolver_set_strategy(self) -> None:
        from src.control_reasoning.conflict_resolver import (
            ConflictResolver,
            ResolutionStrategy,
        )

        resolver = ConflictResolver()
        resolver.set_strategy(ResolutionStrategy.MERGE)

        assert resolver.strategy == ResolutionStrategy.MERGE

    @pytest.mark.unit
    def test_resolver_priority_map(self) -> None:
        from src.control_reasoning.conflict_resolver import ConflictResolver

        priority_map = {"rule_high": 100, "rule_low": 10}
        resolver = ConflictResolver(priority_map=priority_map)

        assert resolver.priority_map == priority_map

    @pytest.mark.unit
    def test_resolver_set_priority_map(self) -> None:
        from src.control_reasoning.conflict_resolver import ConflictResolver

        resolver = ConflictResolver()
        resolver.set_priority_map({"rule_a": 50})

        assert resolver.priority_map == {"rule_a": 50}


class TestConflictResolverDetection:
    @pytest.mark.unit
    def test_detect_no_conflicts(self) -> None:
        from src.control_reasoning.conflict_resolver import ConflictResolver

        resolver = ConflictResolver()
        commands = [
            _create_command(device_id="device_a"),
            _create_command(command_id="cmd_002", device_id="device_b"),
        ]

        conflicts = resolver.detect_conflicts(commands)

        assert conflicts == {}

    @pytest.mark.unit
    def test_detect_conflicts(self) -> None:
        from src.control_reasoning.conflict_resolver import ConflictResolver

        resolver = ConflictResolver()
        commands = [
            _create_command(command_id="cmd_001", device_id="device_a"),
            _create_command(command_id="cmd_002", device_id="device_a"),
            _create_command(command_id="cmd_003", device_id="device_b"),
        ]

        conflicts = resolver.detect_conflicts(commands)

        assert "device_a" in conflicts
        assert len(conflicts["device_a"]) == 2
        assert "device_b" not in conflicts

    @pytest.mark.unit
    def test_has_conflicts_true(self) -> None:
        from src.control_reasoning.conflict_resolver import ConflictResolver

        resolver = ConflictResolver()
        commands = [
            _create_command(command_id="cmd_001", device_id="device_a"),
            _create_command(command_id="cmd_002", device_id="device_a"),
        ]

        assert resolver.has_conflicts(commands) is True

    @pytest.mark.unit
    def test_has_conflicts_false(self) -> None:
        from src.control_reasoning.conflict_resolver import ConflictResolver

        resolver = ConflictResolver()
        commands = [
            _create_command(device_id="device_a"),
            _create_command(command_id="cmd_002", device_id="device_b"),
        ]

        assert resolver.has_conflicts(commands) is False


class TestConflictResolverResolve:
    @pytest.mark.unit
    def test_resolve_empty_commands(self) -> None:
        from src.control_reasoning.conflict_resolver import ConflictResolver

        resolver = ConflictResolver()

        result = resolver.resolve([])

        assert result.resolved_commands == ()
        assert result.conflicts == ()
        assert result.had_conflicts is False

    @pytest.mark.unit
    def test_resolve_no_conflicts(self) -> None:
        from src.control_reasoning.conflict_resolver import ConflictResolver

        resolver = ConflictResolver()
        commands = [
            _create_command(device_id="device_a"),
            _create_command(command_id="cmd_002", device_id="device_b"),
        ]

        result = resolver.resolve(commands)

        assert len(result.resolved_commands) == 2
        assert result.had_conflicts is False

    @pytest.mark.unit
    def test_resolve_first_strategy(self) -> None:
        from src.control_reasoning.conflict_resolver import (
            ConflictResolver,
            ResolutionStrategy,
        )

        resolver = ConflictResolver(strategy=ResolutionStrategy.FIRST)
        commands = [
            _create_command(command_id="cmd_001", created_at=2000.0),
            _create_command(command_id="cmd_002", created_at=1000.0),
        ]

        result = resolver.resolve(commands)

        assert len(result.resolved_commands) == 1
        assert result.resolved_commands[0].command_id == "cmd_002"
        assert result.had_conflicts is True

    @pytest.mark.unit
    def test_resolve_last_strategy(self) -> None:
        from src.control_reasoning.conflict_resolver import (
            ConflictResolver,
            ResolutionStrategy,
        )

        resolver = ConflictResolver(strategy=ResolutionStrategy.LAST)
        commands = [
            _create_command(command_id="cmd_001", created_at=1000.0),
            _create_command(command_id="cmd_002", created_at=2000.0),
        ]

        result = resolver.resolve(commands)

        assert len(result.resolved_commands) == 1
        assert result.resolved_commands[0].command_id == "cmd_002"
        assert result.had_conflicts is True

    @pytest.mark.unit
    def test_resolve_priority_strategy(self) -> None:
        from src.control_reasoning.conflict_resolver import (
            ConflictResolver,
            ResolutionStrategy,
        )

        priority_map = {"rule_high": 100, "rule_low": 10}
        resolver = ConflictResolver(
            strategy=ResolutionStrategy.PRIORITY,
            priority_map=priority_map,
        )
        commands = [
            _create_command(command_id="cmd_001", rule_id="rule_low"),
            _create_command(command_id="cmd_002", rule_id="rule_high"),
        ]

        result = resolver.resolve(commands)

        assert len(result.resolved_commands) == 1
        assert result.resolved_commands[0].command_id == "cmd_002"

    @pytest.mark.unit
    def test_resolve_priority_default_when_no_rule_id(self) -> None:
        from src.control_reasoning.conflict_resolver import (
            ConflictResolver,
            ResolutionStrategy,
        )

        priority_map = {"rule_high": 100}
        resolver = ConflictResolver(
            strategy=ResolutionStrategy.PRIORITY,
            priority_map=priority_map,
        )
        commands = [
            _create_command(command_id="cmd_001", rule_id=None),
            _create_command(command_id="cmd_002", rule_id="rule_high"),
        ]

        result = resolver.resolve(commands)

        assert result.resolved_commands[0].command_id == "cmd_002"

    @pytest.mark.unit
    def test_resolve_merge_strategy(self) -> None:
        from src.control_reasoning.conflict_resolver import (
            ConflictResolver,
            ResolutionStrategy,
        )

        resolver = ConflictResolver(strategy=ResolutionStrategy.MERGE)
        commands = [
            _create_command(
                command_id="cmd_001",
                created_at=1000.0,
                parameters={"temp": 22},
            ),
            _create_command(
                command_id="cmd_002",
                created_at=2000.0,
                parameters={"mode": "cool"},
            ),
        ]

        result = resolver.resolve(commands)

        assert len(result.resolved_commands) == 1
        assert result.resolved_commands[0].command_id == "cmd_001"
        assert result.resolved_commands[0].parameters == {"temp": 22, "mode": "cool"}

    @pytest.mark.unit
    def test_resolve_merge_later_overrides_earlier(self) -> None:
        from src.control_reasoning.conflict_resolver import (
            ConflictResolver,
            ResolutionStrategy,
        )

        resolver = ConflictResolver(strategy=ResolutionStrategy.MERGE)
        commands = [
            _create_command(
                command_id="cmd_001",
                created_at=1000.0,
                parameters={"temp": 22},
            ),
            _create_command(
                command_id="cmd_002",
                created_at=2000.0,
                parameters={"temp": 25},
            ),
        ]

        result = resolver.resolve(commands)

        assert result.resolved_commands[0].parameters["temp"] == 25

    @pytest.mark.unit
    def test_resolve_multiple_devices_with_conflicts(self) -> None:
        from src.control_reasoning.conflict_resolver import (
            ConflictResolver,
            ResolutionStrategy,
        )

        resolver = ConflictResolver(strategy=ResolutionStrategy.FIRST)
        commands = [
            _create_command(command_id="cmd_001", device_id="dev_a", created_at=2000.0),
            _create_command(command_id="cmd_002", device_id="dev_a", created_at=1000.0),
            _create_command(command_id="cmd_003", device_id="dev_b", created_at=3000.0),
            _create_command(command_id="cmd_004", device_id="dev_b", created_at=1500.0),
        ]

        result = resolver.resolve(commands)

        assert len(result.resolved_commands) == 2
        assert len(result.conflicts) == 2

        resolved_ids = {cmd.command_id for cmd in result.resolved_commands}
        assert "cmd_002" in resolved_ids
        assert "cmd_004" in resolved_ids


class TestConflictResolverConflictInfo:
    @pytest.mark.unit
    def test_resolve_records_conflict_info(self) -> None:
        from src.control_reasoning.conflict_resolver import (
            ConflictResolver,
            ResolutionStrategy,
        )

        resolver = ConflictResolver(strategy=ResolutionStrategy.FIRST)
        commands = [
            _create_command(command_id="cmd_001", created_at=2000.0),
            _create_command(command_id="cmd_002", created_at=1000.0),
            _create_command(command_id="cmd_003", created_at=3000.0),
        ]

        result = resolver.resolve(commands)

        assert len(result.conflicts) == 1
        conflict = result.conflicts[0]
        assert conflict.device_id == "actuator_001"
        assert len(conflict.commands) == 3
        assert conflict.winning_command.command_id == "cmd_002"
        assert len(conflict.dropped_commands) == 2
        assert conflict.strategy == ResolutionStrategy.FIRST
