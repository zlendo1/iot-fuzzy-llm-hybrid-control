# ruff: noqa: ARG002
from __future__ import annotations

import json
import urllib.error
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

if TYPE_CHECKING:
    from click.testing import CliRunner


@pytest.fixture
def cli_runner() -> CliRunner:
    from click.testing import CliRunner

    return CliRunner()


@pytest.fixture
def temp_dirs(tmp_path: Path) -> dict[str, Path]:
    config_dir = tmp_path / "config"
    rules_dir = tmp_path / "rules"
    logs_dir = tmp_path / "logs"
    config_dir.mkdir()
    rules_dir.mkdir()
    logs_dir.mkdir()
    return {
        "config": config_dir,
        "rules": rules_dir,
        "logs": logs_dir,
    }


@pytest.fixture
def sample_devices_config(temp_dirs: dict[str, Path]) -> Path:
    devices = {
        "devices": [
            {
                "id": "sensor_temp_1",
                "name": "Living Room Temperature",
                "type": "sensor",
                "device_class": "temperature",
                "location": "living_room",
                "unit": "celsius",
                "mqtt": {"topic": "home/living_room/temperature"},
            },
            {
                "id": "actuator_ac_1",
                "name": "AC Unit",
                "type": "actuator",
                "device_class": "climate",
                "location": "living_room",
                "capabilities": ["turn_on", "turn_off", "set_temperature"],
                "mqtt": {
                    "topic": "home/living_room/ac/state",
                    "command_topic": "home/living_room/ac/set",
                },
            },
        ]
    }
    config_file = temp_dirs["config"] / "devices.json"
    config_file.write_text(json.dumps(devices))
    return config_file


@pytest.fixture
def sample_rules_file(temp_dirs: dict[str, Path]) -> Path:
    rules = {
        "rules": [
            {
                "rule_id": "rule_001",
                "rule_text": "When temperature is hot, turn on AC",
                "priority": 50,
                "enabled": True,
                "created_timestamp": "2024-01-01T00:00:00Z",
                "trigger_count": 5,
                "metadata": {"tags": ["climate", "comfort"]},
            },
            {
                "rule_id": "rule_002",
                "rule_text": "When humidity is high, activate dehumidifier",
                "priority": 30,
                "enabled": False,
                "created_timestamp": "2024-01-02T00:00:00Z",
                "trigger_count": 0,
                "metadata": {},
            },
        ]
    }
    rules_file = temp_dirs["rules"] / "active_rules.json"
    rules_file.write_text(json.dumps(rules))
    return rules_file


class TestOutputFormatter:
    @pytest.mark.unit
    def test_format_table_with_data(self) -> None:
        from src.interfaces.cli import OutputFormatter

        formatter = OutputFormatter()
        headers = ["ID", "Name", "Status"]
        rows = [["1", "Test", "Active"], ["2", "Demo", "Inactive"]]

        result = formatter.format_table(headers, rows)

        assert "ID" in result
        assert "Name" in result
        assert "Status" in result
        assert "Test" in result
        assert "Active" in result

    @pytest.mark.unit
    def test_format_table_empty(self) -> None:
        from src.interfaces.cli import OutputFormatter

        formatter = OutputFormatter()
        result = formatter.format_table(["A", "B"], [])

        assert result == "No data to display."

    @pytest.mark.unit
    def test_format_json(self) -> None:
        from src.interfaces.cli import OutputFormatter

        formatter = OutputFormatter()
        data = {"key": "value", "nested": {"inner": 123}}

        result = formatter.format_json(data)
        parsed = json.loads(result)

        assert parsed == data

    @pytest.mark.unit
    def test_format_dict(self) -> None:
        from src.interfaces.cli import OutputFormatter

        formatter = OutputFormatter()
        data = {"name": "test", "count": 42}

        result = formatter.format_dict(data)

        assert "name: test" in result
        assert "count: 42" in result

    @pytest.mark.unit
    def test_format_dict_nested(self) -> None:
        from src.interfaces.cli import OutputFormatter

        formatter = OutputFormatter()
        data = {"outer": {"inner": "value"}}

        result = formatter.format_dict(data)

        assert "outer:" in result
        assert "inner: value" in result

    @pytest.mark.unit
    def test_success_message(self) -> None:
        from src.interfaces.cli import OutputFormatter

        formatter = OutputFormatter()
        result = formatter.success("Operation completed")

        assert "Operation completed" in result
        assert "✓" in result

    @pytest.mark.unit
    def test_error_message(self) -> None:
        from src.interfaces.cli import OutputFormatter

        formatter = OutputFormatter()
        result = formatter.error("Something failed")

        assert "Something failed" in result
        assert "✗" in result

    @pytest.mark.unit
    def test_warning_message(self) -> None:
        from src.interfaces.cli import OutputFormatter

        formatter = OutputFormatter()
        result = formatter.warning("Caution needed")

        assert "Caution needed" in result
        assert "⚠" in result

    @pytest.mark.unit
    def test_info_message(self) -> None:
        from src.interfaces.cli import OutputFormatter

        formatter = OutputFormatter()
        result = formatter.info("Information")

        assert "Information" in result
        assert "ℹ" in result


class TestCLIContext:
    @pytest.mark.unit
    def test_default_values(self) -> None:
        from src.interfaces.cli import CLIContext

        ctx = CLIContext()

        assert ctx.config_dir == Path("config")
        assert ctx.rules_dir == Path("rules")
        assert ctx.logs_dir == Path("logs")
        assert ctx.output_format == "table"
        assert ctx.verbose is False

    @pytest.mark.unit
    def test_get_initialized_orchestrator_none_when_not_created(self) -> None:
        from src.interfaces.cli import CLIContext

        ctx = CLIContext()

        assert ctx.get_initialized_orchestrator() is None


class TestCLIMainGroup:
    @pytest.mark.unit
    def test_cli_version(self, cli_runner: CliRunner) -> None:
        from src.interfaces.cli import cli

        result = cli_runner.invoke(cli, ["--version"])

        assert result.exit_code == 0
        assert "0.1.0" in result.output

    @pytest.mark.unit
    def test_cli_help(self, cli_runner: CliRunner) -> None:
        from src.interfaces.cli import cli

        result = cli_runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "Fuzzy-LLM Hybrid IoT Management System CLI" in result.output
        assert "--config-dir" in result.output
        assert "--rules-dir" in result.output
        assert "--format" in result.output


class TestRuleCommands:
    @pytest.mark.unit
    def test_rule_add_success(
        self, cli_runner: CliRunner, temp_dirs: dict[str, Path]
    ) -> None:
        from src.interfaces.cli import cli

        result = cli_runner.invoke(
            cli,
            [
                "--rules-dir",
                str(temp_dirs["rules"]),
                "rule",
                "add",
                "When temperature is high, turn on fan",
                "--priority",
                "75",
                "--tag",
                "climate",
            ],
        )

        assert result.exit_code == 0
        assert "Rule added with ID:" in result.output
        assert "Priority: 75" in result.output

    @pytest.mark.unit
    def test_rule_add_with_custom_id(
        self, cli_runner: CliRunner, temp_dirs: dict[str, Path]
    ) -> None:
        from src.interfaces.cli import cli

        result = cli_runner.invoke(
            cli,
            [
                "--rules-dir",
                str(temp_dirs["rules"]),
                "rule",
                "add",
                "Custom rule text",
                "--id",
                "my_custom_rule",
            ],
        )

        assert result.exit_code == 0
        assert "my_custom_rule" in result.output

    @pytest.mark.unit
    def test_rule_add_json_output(
        self, cli_runner: CliRunner, temp_dirs: dict[str, Path]
    ) -> None:
        from src.interfaces.cli import cli

        result = cli_runner.invoke(
            cli,
            [
                "--rules-dir",
                str(temp_dirs["rules"]),
                "--format",
                "json",
                "rule",
                "add",
                "Test rule",
            ],
        )

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "rule_id" in data
        assert data["rule_text"] == "Test rule"

    @pytest.mark.unit
    def test_rule_list_all(
        self,
        cli_runner: CliRunner,
        temp_dirs: dict[str, Path],
        sample_rules_file: Path,
    ) -> None:
        from src.interfaces.cli import cli

        result = cli_runner.invoke(
            cli,
            ["--rules-dir", str(temp_dirs["rules"]), "rule", "list"],
        )

        assert result.exit_code == 0
        assert "rule_001" in result.output
        assert "rule_002" in result.output
        assert "Total: 2 rule(s)" in result.output

    @pytest.mark.unit
    def test_rule_list_enabled_only(
        self,
        cli_runner: CliRunner,
        temp_dirs: dict[str, Path],
        sample_rules_file: Path,
    ) -> None:
        from src.interfaces.cli import cli

        result = cli_runner.invoke(
            cli,
            ["--rules-dir", str(temp_dirs["rules"]), "rule", "list", "--enabled-only"],
        )

        assert result.exit_code == 0
        assert "rule_001" in result.output
        assert "rule_002" not in result.output
        assert "Total: 1 rule(s)" in result.output

    @pytest.mark.unit
    def test_rule_list_by_tag(
        self,
        cli_runner: CliRunner,
        temp_dirs: dict[str, Path],
        sample_rules_file: Path,
    ) -> None:
        from src.interfaces.cli import cli

        result = cli_runner.invoke(
            cli,
            [
                "--rules-dir",
                str(temp_dirs["rules"]),
                "rule",
                "list",
                "--tag",
                "climate",
            ],
        )

        assert result.exit_code == 0
        assert "rule_001" in result.output
        assert "rule_002" not in result.output

    @pytest.mark.unit
    def test_rule_list_empty(
        self, cli_runner: CliRunner, temp_dirs: dict[str, Path]
    ) -> None:
        from src.interfaces.cli import cli

        result = cli_runner.invoke(
            cli,
            ["--rules-dir", str(temp_dirs["rules"]), "rule", "list"],
        )

        assert result.exit_code == 0
        assert "No rules found." in result.output

    @pytest.mark.unit
    def test_rule_list_json_output(
        self,
        cli_runner: CliRunner,
        temp_dirs: dict[str, Path],
        sample_rules_file: Path,
    ) -> None:
        from src.interfaces.cli import cli

        result = cli_runner.invoke(
            cli,
            [
                "--rules-dir",
                str(temp_dirs["rules"]),
                "--format",
                "json",
                "rule",
                "list",
            ],
        )

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data) == 2

    @pytest.mark.unit
    def test_rule_show_existing(
        self,
        cli_runner: CliRunner,
        temp_dirs: dict[str, Path],
        sample_rules_file: Path,
    ) -> None:
        from src.interfaces.cli import cli

        result = cli_runner.invoke(
            cli,
            ["--rules-dir", str(temp_dirs["rules"]), "rule", "show", "rule_001"],
        )

        assert result.exit_code == 0
        assert "Rule ID: rule_001" in result.output
        assert "When temperature is hot, turn on AC" in result.output
        assert "Priority: 50" in result.output
        assert "Trigger Count: 5" in result.output

    @pytest.mark.unit
    def test_rule_show_not_found(
        self, cli_runner: CliRunner, temp_dirs: dict[str, Path]
    ) -> None:
        from src.interfaces.cli import cli

        result = cli_runner.invoke(
            cli,
            ["--rules-dir", str(temp_dirs["rules"]), "rule", "show", "nonexistent"],
        )

        assert result.exit_code == 1
        assert "Rule not found" in result.output

    @pytest.mark.unit
    def test_rule_show_json_output(
        self,
        cli_runner: CliRunner,
        temp_dirs: dict[str, Path],
        sample_rules_file: Path,
    ) -> None:
        from src.interfaces.cli import cli

        result = cli_runner.invoke(
            cli,
            [
                "--rules-dir",
                str(temp_dirs["rules"]),
                "--format",
                "json",
                "rule",
                "show",
                "rule_001",
            ],
        )

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["rule_id"] == "rule_001"

    @pytest.mark.unit
    def test_rule_enable(
        self,
        cli_runner: CliRunner,
        temp_dirs: dict[str, Path],
        sample_rules_file: Path,
    ) -> None:
        from src.interfaces.cli import cli

        result = cli_runner.invoke(
            cli,
            ["--rules-dir", str(temp_dirs["rules"]), "rule", "enable", "rule_002"],
        )

        assert result.exit_code == 0
        assert "rule_002 enabled" in result.output

    @pytest.mark.unit
    def test_rule_enable_not_found(
        self, cli_runner: CliRunner, temp_dirs: dict[str, Path]
    ) -> None:
        from src.interfaces.cli import cli

        result = cli_runner.invoke(
            cli,
            ["--rules-dir", str(temp_dirs["rules"]), "rule", "enable", "nonexistent"],
        )

        assert result.exit_code == 1
        assert "Rule not found" in result.output

    @pytest.mark.unit
    def test_rule_disable(
        self,
        cli_runner: CliRunner,
        temp_dirs: dict[str, Path],
        sample_rules_file: Path,
    ) -> None:
        from src.interfaces.cli import cli

        result = cli_runner.invoke(
            cli,
            ["--rules-dir", str(temp_dirs["rules"]), "rule", "disable", "rule_001"],
        )

        assert result.exit_code == 0
        assert "rule_001 disabled" in result.output

    @pytest.mark.unit
    def test_rule_disable_not_found(
        self, cli_runner: CliRunner, temp_dirs: dict[str, Path]
    ) -> None:
        from src.interfaces.cli import cli

        result = cli_runner.invoke(
            cli,
            ["--rules-dir", str(temp_dirs["rules"]), "rule", "disable", "nonexistent"],
        )

        assert result.exit_code == 1
        assert "Rule not found" in result.output

    @pytest.mark.unit
    def test_rule_delete_with_confirmation(
        self,
        cli_runner: CliRunner,
        temp_dirs: dict[str, Path],
        sample_rules_file: Path,
    ) -> None:
        from src.interfaces.cli import cli

        result = cli_runner.invoke(
            cli,
            [
                "--rules-dir",
                str(temp_dirs["rules"]),
                "rule",
                "delete",
                "rule_001",
                "-y",
            ],
        )

        assert result.exit_code == 0
        assert "rule_001 deleted" in result.output

    @pytest.mark.unit
    def test_rule_delete_cancelled(
        self,
        cli_runner: CliRunner,
        temp_dirs: dict[str, Path],
        sample_rules_file: Path,
    ) -> None:
        from src.interfaces.cli import cli

        result = cli_runner.invoke(
            cli,
            ["--rules-dir", str(temp_dirs["rules"]), "rule", "delete", "rule_001"],
            input="n\n",
        )

        assert result.exit_code == 0
        assert "Cancelled" in result.output

    @pytest.mark.unit
    def test_rule_delete_not_found(
        self, cli_runner: CliRunner, temp_dirs: dict[str, Path]
    ) -> None:
        from src.interfaces.cli import cli

        result = cli_runner.invoke(
            cli,
            [
                "--rules-dir",
                str(temp_dirs["rules"]),
                "rule",
                "delete",
                "nonexistent",
                "-y",
            ],
        )

        assert result.exit_code == 1
        assert "Rule not found" in result.output


class TestSensorCommands:
    @pytest.mark.unit
    def test_sensor_list(
        self,
        cli_runner: CliRunner,
        temp_dirs: dict[str, Path],
        sample_devices_config: Path,
    ) -> None:
        from src.interfaces.cli import cli

        result = cli_runner.invoke(
            cli,
            ["--config-dir", str(temp_dirs["config"]), "sensor", "list"],
        )

        assert result.exit_code == 0
        assert "sensor_temp_1" in result.output
        assert "Living Room Temperature" in result.output
        assert "Total: 1 sensor(s)" in result.output

    @pytest.mark.unit
    def test_sensor_list_no_config(
        self, cli_runner: CliRunner, temp_dirs: dict[str, Path]
    ) -> None:
        from src.interfaces.cli import cli

        result = cli_runner.invoke(
            cli,
            ["--config-dir", str(temp_dirs["config"]), "sensor", "list"],
        )

        assert result.exit_code == 1
        assert "Configuration error" in result.output or "not found" in result.output

    @pytest.mark.unit
    def test_sensor_list_json_output(
        self,
        cli_runner: CliRunner,
        temp_dirs: dict[str, Path],
        sample_devices_config: Path,
    ) -> None:
        from src.interfaces.cli import cli

        result = cli_runner.invoke(
            cli,
            [
                "--config-dir",
                str(temp_dirs["config"]),
                "--format",
                "json",
                "sensor",
                "list",
            ],
        )

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data) == 1
        assert data[0]["id"] == "sensor_temp_1"

    @pytest.mark.unit
    def test_sensor_status_all(
        self,
        cli_runner: CliRunner,
        temp_dirs: dict[str, Path],
        sample_devices_config: Path,
    ) -> None:
        from src.interfaces.cli import cli

        result = cli_runner.invoke(
            cli,
            ["--config-dir", str(temp_dirs["config"]), "sensor", "status"],
        )

        assert result.exit_code == 0
        assert "Living Room Temperature" in result.output
        assert "temperature" in result.output

    @pytest.mark.unit
    def test_sensor_status_specific(
        self,
        cli_runner: CliRunner,
        temp_dirs: dict[str, Path],
        sample_devices_config: Path,
    ) -> None:
        from src.interfaces.cli import cli

        result = cli_runner.invoke(
            cli,
            [
                "--config-dir",
                str(temp_dirs["config"]),
                "sensor",
                "status",
                "sensor_temp_1",
            ],
        )

        assert result.exit_code == 0
        assert "sensor_temp_1" in result.output

    @pytest.mark.unit
    def test_sensor_status_not_found(
        self,
        cli_runner: CliRunner,
        temp_dirs: dict[str, Path],
        sample_devices_config: Path,
    ) -> None:
        from src.interfaces.cli import cli

        result = cli_runner.invoke(
            cli,
            [
                "--config-dir",
                str(temp_dirs["config"]),
                "sensor",
                "status",
                "nonexistent",
            ],
        )

        assert result.exit_code == 1
        assert "Sensor not found" in result.output


class TestDeviceCommands:
    @pytest.mark.unit
    def test_device_list(
        self,
        cli_runner: CliRunner,
        temp_dirs: dict[str, Path],
        sample_devices_config: Path,
    ) -> None:
        from src.interfaces.cli import cli

        result = cli_runner.invoke(
            cli,
            ["--config-dir", str(temp_dirs["config"]), "device", "list"],
        )

        assert result.exit_code == 0
        assert "sensor_temp_1" in result.output
        assert "actuator_ac_1" in result.output
        assert "Total: 2 device(s)" in result.output

    @pytest.mark.unit
    def test_device_list_json_output(
        self,
        cli_runner: CliRunner,
        temp_dirs: dict[str, Path],
        sample_devices_config: Path,
    ) -> None:
        from src.interfaces.cli import cli

        result = cli_runner.invoke(
            cli,
            [
                "--config-dir",
                str(temp_dirs["config"]),
                "--format",
                "json",
                "device",
                "list",
            ],
        )

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data) == 2

    @pytest.mark.unit
    def test_device_status_all(
        self,
        cli_runner: CliRunner,
        temp_dirs: dict[str, Path],
        sample_devices_config: Path,
    ) -> None:
        from src.interfaces.cli import cli

        result = cli_runner.invoke(
            cli,
            ["--config-dir", str(temp_dirs["config"]), "device", "status"],
        )

        assert result.exit_code == 0
        assert "AC Unit" in result.output
        assert "Living Room Temperature" in result.output

    @pytest.mark.unit
    def test_device_status_specific(
        self,
        cli_runner: CliRunner,
        temp_dirs: dict[str, Path],
        sample_devices_config: Path,
    ) -> None:
        from src.interfaces.cli import cli

        result = cli_runner.invoke(
            cli,
            [
                "--config-dir",
                str(temp_dirs["config"]),
                "device",
                "status",
                "actuator_ac_1",
            ],
        )

        assert result.exit_code == 0
        assert "AC Unit" in result.output
        assert "Capabilities:" in result.output

    @pytest.mark.unit
    def test_device_status_not_found(
        self,
        cli_runner: CliRunner,
        temp_dirs: dict[str, Path],
        sample_devices_config: Path,
    ) -> None:
        from src.interfaces.cli import cli

        result = cli_runner.invoke(
            cli,
            [
                "--config-dir",
                str(temp_dirs["config"]),
                "device",
                "status",
                "nonexistent",
            ],
        )

        assert result.exit_code == 1
        assert "Device not found" in result.output


class TestConfigCommands:
    @pytest.mark.unit
    def test_config_validate_success(
        self, cli_runner: CliRunner, temp_dirs: dict[str, Path]
    ) -> None:
        from src.interfaces.cli import cli

        result = cli_runner.invoke(
            cli,
            ["--config-dir", str(temp_dirs["config"]), "config", "validate"],
        )

        assert result.exit_code == 0
        assert "valid" in result.output.lower()

    @pytest.mark.unit
    def test_config_reload_not_running(
        self, cli_runner: CliRunner, temp_dirs: dict[str, Path]
    ) -> None:
        from src.interfaces.cli import cli

        result = cli_runner.invoke(
            cli,
            ["--config-dir", str(temp_dirs["config"]), "config", "reload"],
        )

        assert result.exit_code == 0
        assert "not running" in result.output.lower()


class TestLogCommands:
    @pytest.mark.unit
    def test_log_tail_no_file(
        self, cli_runner: CliRunner, temp_dirs: dict[str, Path]
    ) -> None:
        from src.interfaces.cli import cli

        result = cli_runner.invoke(
            cli,
            ["--logs-dir", str(temp_dirs["logs"]), "log", "tail"],
        )

        assert result.exit_code == 0
        assert "Log file not found" in result.output

    @pytest.mark.unit
    def test_log_tail_with_entries(
        self, cli_runner: CliRunner, temp_dirs: dict[str, Path]
    ) -> None:
        from src.interfaces.cli import cli

        log_file = temp_dirs["logs"] / "system.log"
        entries = [
            json.dumps(
                {
                    "timestamp": "2024-01-01T00:00:00Z",
                    "level": "INFO",
                    "message": "Test entry 1",
                }
            ),
            json.dumps(
                {
                    "timestamp": "2024-01-01T00:00:01Z",
                    "level": "WARNING",
                    "message": "Test entry 2",
                }
            ),
        ]
        log_file.write_text("\n".join(entries))

        result = cli_runner.invoke(
            cli,
            ["--logs-dir", str(temp_dirs["logs"]), "log", "tail", "-n", "5"],
        )

        assert result.exit_code == 0
        assert "Test entry 1" in result.output
        assert "Test entry 2" in result.output

    @pytest.mark.unit
    def test_log_tail_different_category(
        self, cli_runner: CliRunner, temp_dirs: dict[str, Path]
    ) -> None:
        from src.interfaces.cli import cli

        log_file = temp_dirs["logs"] / "errors.log"
        log_file.write_text(
            json.dumps({"level": "ERROR", "message": "An error occurred"})
        )

        result = cli_runner.invoke(
            cli,
            [
                "--logs-dir",
                str(temp_dirs["logs"]),
                "log",
                "tail",
                "--category",
                "errors",
            ],
        )

        assert result.exit_code == 0
        assert "An error occurred" in result.output


class TestSystemCommands:
    @pytest.mark.unit
    def test_status_command(
        self, cli_runner: CliRunner, temp_dirs: dict[str, Path]
    ) -> None:
        from src.interfaces.cli import cli

        result = cli_runner.invoke(
            cli,
            [
                "--config-dir",
                str(temp_dirs["config"]),
                "--rules-dir",
                str(temp_dirs["rules"]),
                "--logs-dir",
                str(temp_dirs["logs"]),
                "status",
            ],
        )

        assert result.exit_code == 0
        assert "System State:" in result.output

    @pytest.mark.unit
    def test_status_command_falls_back_when_endpoint_unreachable(
        self, cli_runner: CliRunner, temp_dirs: dict[str, Path]
    ) -> None:
        from src.interfaces.cli import cli

        def raise_url_error(*_args: object, **_kwargs: object) -> None:
            raise urllib.error.URLError("connection failed")

        with patch("urllib.request.urlopen", side_effect=raise_url_error):
            result = cli_runner.invoke(
                cli,
                [
                    "--config-dir",
                    str(temp_dirs["config"]),
                    "--rules-dir",
                    str(temp_dirs["rules"]),
                    "--logs-dir",
                    str(temp_dirs["logs"]),
                    "status",
                ],
            )

        assert result.exit_code == 0
        assert "standalone" in result.output.lower()

    @pytest.mark.unit
    def test_stop_not_running(
        self, cli_runner: CliRunner, temp_dirs: dict[str, Path]
    ) -> None:
        from src.interfaces.cli import cli

        result = cli_runner.invoke(
            cli,
            [
                "--config-dir",
                str(temp_dirs["config"]),
                "--rules-dir",
                str(temp_dirs["rules"]),
                "--logs-dir",
                str(temp_dirs["logs"]),
                "stop",
            ],
        )

        assert result.exit_code == 0
        assert "not running" in result.output.lower()


class TestErrorHandling:
    @pytest.mark.unit
    def test_handle_errors_decorator_catches_rule_error(
        self, cli_runner: CliRunner, temp_dirs: dict[str, Path], sample_rules_file: Path
    ) -> None:
        from src.interfaces.cli import cli

        cli_runner.invoke(
            cli,
            [
                "--rules-dir",
                str(temp_dirs["rules"]),
                "rule",
                "add",
                "Test rule",
                "--id",
                "rule_001",
            ],
        )
        result = cli_runner.invoke(
            cli,
            [
                "--rules-dir",
                str(temp_dirs["rules"]),
                "rule",
                "add",
                "Duplicate rule",
                "--id",
                "rule_001",
            ],
        )

        assert result.exit_code == 1
        assert "Rule error" in result.output

    @pytest.mark.unit
    def test_verbose_flag(
        self, cli_runner: CliRunner, temp_dirs: dict[str, Path]
    ) -> None:
        from src.interfaces.cli import cli

        result = cli_runner.invoke(
            cli,
            [
                "--verbose",
                "--config-dir",
                str(temp_dirs["config"]),
                "--rules-dir",
                str(temp_dirs["rules"]),
                "status",
            ],
        )

        assert result.exit_code == 0


class TestMain:
    @pytest.mark.unit
    def test_main_entry_point(self) -> None:
        from src.interfaces.cli import main

        assert callable(main)
