from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock, patch

import pytest

if TYPE_CHECKING:
    from click.testing import CliRunner


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _build_get_config_side_effect(
    *,
    devices_content: dict[str, Any] | None = None,
    mqtt_content: dict[str, Any] | None = None,
    devices_error: Exception | None = None,
    mqtt_error: Exception | None = None,
) -> Any:
    def _side_effect(name: str) -> dict[str, Any]:
        if name == "devices":
            if devices_error is not None:
                raise devices_error
            if devices_content is None:
                raise Exception("Config not found: devices")
            return {"content": copy.deepcopy(devices_content), "version": "1"}

        if name == "mqtt_config":
            if mqtt_error is not None:
                raise mqtt_error
            if mqtt_content is None:
                raise Exception("Config not found: mqtt_config")
            return {"content": copy.deepcopy(mqtt_content), "version": "1"}

        raise Exception(f"Config not found: {name}")

    return _side_effect


def _invoke_migrate_with_mocked_grpc(
    cli_runner: CliRunner,
    args: list[str],
    *,
    devices_content: dict[str, Any] | None = None,
    mqtt_content: dict[str, Any] | None = None,
    devices_error: Exception | None = None,
    mqtt_error: Exception | None = None,
) -> tuple[Any, MagicMock]:
    from src.interfaces.cli import cli

    with patch("src.interfaces.rpc.client.GrpcClient") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_client.get_config.side_effect = _build_get_config_side_effect(
            devices_content=devices_content,
            mqtt_content=mqtt_content,
            devices_error=devices_error,
            mqtt_error=mqtt_error,
        )

        result = cli_runner.invoke(cli, args)

    return result, mock_client


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
def devices_needing_migration(temp_dirs: dict[str, Path]) -> Path:
    devices = {
        "devices": [
            {
                "id": "temp-001",
                "name": "Temperature Sensor 1",
                "type": "sensor",
                "device_class": "temperature",
                "location": "living_room",
                "unit": "celsius",
                "mqtt": {
                    "topic": "home/living_room/temperature",
                    "qos": 1,
                },
            },
            {
                "id": "humid-001",
                "name": "Humidity Sensor 1",
                "type": "sensor",
                "device_class": "humidity",
                "location": "living_room",
                "unit": "%",
                "mqtt": {
                    "topic": "home/living_room/humidity",
                    "qos": 1,
                },
            },
        ]
    }
    config_file = temp_dirs["config"] / "devices.json"
    config_file.write_text(json.dumps(devices, indent=2))
    return config_file


@pytest.fixture
def devices_already_migrated(temp_dirs: dict[str, Path]) -> Path:
    devices = {
        "devices": [
            {
                "id": "temp-001",
                "name": "Temperature Sensor 1",
                "type": "sensor",
                "device_class": "temperature",
                "location": "living_room",
                "unit": "celsius",
                "mqtt": {
                    "topic": "home/living_room/temperature",
                    "qos": 1,
                    "payload_mapping": {"value_field": "value"},
                },
            },
        ]
    }
    config_file = temp_dirs["config"] / "devices.json"
    config_file.write_text(json.dumps(devices, indent=2))
    return config_file


@pytest.fixture
def devices_no_mqtt(temp_dirs: dict[str, Path]) -> Path:
    devices = {
        "devices": [
            {
                "id": "temp-001",
                "name": "Temperature Sensor (no mqtt)",
                "type": "sensor",
                "device_class": "temperature",
                "location": "living_room",
            },
        ]
    }
    config_file = temp_dirs["config"] / "devices.json"
    config_file.write_text(json.dumps(devices, indent=2))
    return config_file


@pytest.fixture
def mqtt_config_needing_migration(temp_dirs: dict[str, Path]) -> Path:
    mqtt_cfg = {
        "broker": {
            "host": "localhost",
            "port": 1883,
        },
        "client": {
            "id": "iot-test",
            "clean_session": True,
        },
    }
    config_file = temp_dirs["config"] / "mqtt_config.json"
    config_file.write_text(json.dumps(mqtt_cfg, indent=2))
    return config_file


@pytest.fixture
def mqtt_config_already_migrated(temp_dirs: dict[str, Path]) -> Path:
    mqtt_cfg = {
        "broker": {
            "host": "localhost",
            "port": 1883,
        },
        "topic_patterns": {},
    }
    config_file = temp_dirs["config"] / "mqtt_config.json"
    config_file.write_text(json.dumps(mqtt_cfg, indent=2))
    return config_file


class TestConfigMigrateHelp:
    @pytest.mark.unit
    def test_migrate_help_shows_dry_run_option(self, cli_runner: CliRunner) -> None:
        from src.interfaces.cli import cli

        result = cli_runner.invoke(cli, ["config", "migrate", "--help"])

        assert result.exit_code == 0
        assert "--dry-run" in result.output

    @pytest.mark.unit
    def test_migrate_is_subcommand_of_config(self, cli_runner: CliRunner) -> None:
        from src.interfaces.cli import cli

        result = cli_runner.invoke(cli, ["config", "migrate", "--help"])

        assert result.exit_code == 0
        assert "migrate" in result.output.lower()


class TestConfigMigrateDryRun:
    @pytest.mark.unit
    def test_dry_run_reports_devices_needing_payload_mapping(
        self,
        cli_runner: CliRunner,
        temp_dirs: dict[str, Path],
        devices_needing_migration: Path,
    ) -> None:
        devices_data = _read_json(devices_needing_migration)
        result, mock_client = _invoke_migrate_with_mocked_grpc(
            cli_runner,
            [
                "--config-dir",
                str(temp_dirs["config"]),
                "config",
                "migrate",
                "--dry-run",
            ],
            devices_content=devices_data,
            mqtt_content={"topic_patterns": {}},
        )

        assert result.exit_code == 0
        assert "Would add payload_mapping to device: temp-001" in result.output
        assert "Would add payload_mapping to device: humid-001" in result.output
        mock_client.update_config.assert_not_called()

    @pytest.mark.unit
    def test_dry_run_reports_mqtt_config_needing_topic_patterns(
        self,
        cli_runner: CliRunner,
        temp_dirs: dict[str, Path],
        mqtt_config_needing_migration: Path,
    ) -> None:
        mqtt_data = _read_json(mqtt_config_needing_migration)
        result, mock_client = _invoke_migrate_with_mocked_grpc(
            cli_runner,
            [
                "--config-dir",
                str(temp_dirs["config"]),
                "config",
                "migrate",
                "--dry-run",
            ],
            devices_content={"devices": []},
            mqtt_content=mqtt_data,
        )

        assert result.exit_code == 0
        assert "Would add topic_patterns to mqtt_config.json" in result.output
        mock_client.update_config.assert_not_called()

    @pytest.mark.unit
    def test_dry_run_no_backup_files_created(
        self,
        cli_runner: CliRunner,
        temp_dirs: dict[str, Path],
        devices_needing_migration: Path,
        mqtt_config_needing_migration: Path,
    ) -> None:
        devices_data = _read_json(devices_needing_migration)
        mqtt_data = _read_json(mqtt_config_needing_migration)
        result, mock_client = _invoke_migrate_with_mocked_grpc(
            cli_runner,
            [
                "--config-dir",
                str(temp_dirs["config"]),
                "config",
                "migrate",
                "--dry-run",
            ],
            devices_content=devices_data,
            mqtt_content=mqtt_data,
        )

        assert result.exit_code == 0
        mock_client.update_config.assert_not_called()

    @pytest.mark.unit
    def test_dry_run_indicates_would_change_in_output(
        self,
        cli_runner: CliRunner,
        temp_dirs: dict[str, Path],
        devices_needing_migration: Path,
    ) -> None:
        devices_data = _read_json(devices_needing_migration)
        result, mock_client = _invoke_migrate_with_mocked_grpc(
            cli_runner,
            [
                "--config-dir",
                str(temp_dirs["config"]),
                "config",
                "migrate",
                "--dry-run",
            ],
            devices_content=devices_data,
            mqtt_content={"topic_patterns": {}},
        )

        assert result.exit_code == 0
        output_lower = result.output.lower()
        assert (
            "would" in output_lower
            or "dry" in output_lower
            or "dry-run" in output_lower
        )
        mock_client.update_config.assert_not_called()

    @pytest.mark.unit
    def test_dry_run_on_already_migrated_reports_nothing_to_do(
        self,
        cli_runner: CliRunner,
        temp_dirs: dict[str, Path],
        devices_already_migrated: Path,
        mqtt_config_already_migrated: Path,
    ) -> None:
        devices_data = _read_json(devices_already_migrated)
        mqtt_data = _read_json(mqtt_config_already_migrated)
        result, mock_client = _invoke_migrate_with_mocked_grpc(
            cli_runner,
            [
                "--config-dir",
                str(temp_dirs["config"]),
                "config",
                "migrate",
                "--dry-run",
            ],
            devices_content=devices_data,
            mqtt_content=mqtt_data,
        )

        assert result.exit_code == 0
        output_lower = result.output.lower()
        assert (
            "already" in output_lower
            or "up-to-date" in output_lower
            or "nothing" in output_lower
            or "no changes" in output_lower
            or "0" in result.output
        )
        mock_client.update_config.assert_not_called()


class TestConfigMigrateActual:
    @pytest.mark.unit
    def test_actual_migration_adds_payload_mapping_to_devices(
        self,
        cli_runner: CliRunner,
        temp_dirs: dict[str, Path],
        devices_needing_migration: Path,
    ) -> None:
        devices_data = _read_json(devices_needing_migration)
        result, mock_client = _invoke_migrate_with_mocked_grpc(
            cli_runner,
            ["--config-dir", str(temp_dirs["config"]), "config", "migrate"],
            devices_content=devices_data,
            mqtt_content={"topic_patterns": {}},
        )

        assert result.exit_code == 0
        mock_client.update_config.assert_called_once()
        call_args = mock_client.update_config.call_args
        assert call_args is not None
        assert call_args.args[0] == "devices"
        updated_devices = call_args.args[1]
        assert isinstance(updated_devices, dict)
        for dev in updated_devices.get("devices", []):
            if "mqtt" in dev:
                assert "payload_mapping" in dev["mqtt"]
                assert dev["mqtt"]["payload_mapping"] == {"value_field": "value"}
        assert call_args.args[2] == "1"

    @pytest.mark.unit
    def test_actual_migration_adds_topic_patterns_to_mqtt_config(
        self,
        cli_runner: CliRunner,
        temp_dirs: dict[str, Path],
        mqtt_config_needing_migration: Path,
    ) -> None:
        mqtt_data = _read_json(mqtt_config_needing_migration)
        result, mock_client = _invoke_migrate_with_mocked_grpc(
            cli_runner,
            ["--config-dir", str(temp_dirs["config"]), "config", "migrate"],
            devices_content={"devices": []},
            mqtt_content=mqtt_data,
        )

        assert result.exit_code == 0
        mock_client.update_config.assert_called_once()
        call_args = mock_client.update_config.call_args
        assert call_args is not None
        assert call_args.args[0] == "mqtt_config"
        updated_mqtt = call_args.args[1]
        assert isinstance(updated_mqtt, dict)
        assert "topic_patterns" in updated_mqtt
        assert isinstance(updated_mqtt["topic_patterns"], dict)
        assert call_args.args[2] == "1"

    @pytest.mark.unit
    def test_actual_migration_creates_bak_for_devices(
        self,
        cli_runner: CliRunner,
        temp_dirs: dict[str, Path],
        devices_needing_migration: Path,
    ) -> None:
        devices_data = _read_json(devices_needing_migration)
        result, mock_client = _invoke_migrate_with_mocked_grpc(
            cli_runner,
            ["--config-dir", str(temp_dirs["config"]), "config", "migrate"],
            devices_content=devices_data,
            mqtt_content={"topic_patterns": {}},
        )

        assert result.exit_code == 0
        mock_client.update_config.assert_called_once()
        updated_devices = mock_client.update_config.call_args.args[1]
        assert isinstance(updated_devices, dict)
        for dev in updated_devices.get("devices", []):
            if "mqtt" in dev:
                assert "payload_mapping" in dev["mqtt"]

    @pytest.mark.unit
    def test_actual_migration_creates_bak_for_mqtt_config(
        self,
        cli_runner: CliRunner,
        temp_dirs: dict[str, Path],
        mqtt_config_needing_migration: Path,
    ) -> None:
        mqtt_data = _read_json(mqtt_config_needing_migration)
        result, mock_client = _invoke_migrate_with_mocked_grpc(
            cli_runner,
            ["--config-dir", str(temp_dirs["config"]), "config", "migrate"],
            devices_content={"devices": []},
            mqtt_content=mqtt_data,
        )

        assert result.exit_code == 0
        mock_client.update_config.assert_called_once()
        updated_mqtt = mock_client.update_config.call_args.args[1]
        assert isinstance(updated_mqtt, dict)
        assert "topic_patterns" in updated_mqtt

    @pytest.mark.unit
    def test_actual_migration_output_reports_changes_made(
        self,
        cli_runner: CliRunner,
        temp_dirs: dict[str, Path],
        devices_needing_migration: Path,
        mqtt_config_needing_migration: Path,
    ) -> None:
        devices_data = _read_json(devices_needing_migration)
        mqtt_data = _read_json(mqtt_config_needing_migration)
        result, mock_client = _invoke_migrate_with_mocked_grpc(
            cli_runner,
            ["--config-dir", str(temp_dirs["config"]), "config", "migrate"],
            devices_content=devices_data,
            mqtt_content=mqtt_data,
        )

        assert result.exit_code == 0
        assert "Added payload_mapping to device: temp-001" in result.output
        assert "Added payload_mapping to device: humid-001" in result.output
        assert "Added topic_patterns to mqtt_config.json" in result.output
        assert mock_client.update_config.call_count == 2

    @pytest.mark.unit
    def test_already_migrated_devices_not_modified(
        self,
        cli_runner: CliRunner,
        temp_dirs: dict[str, Path],
        devices_already_migrated: Path,
        mqtt_config_already_migrated: Path,
    ) -> None:
        devices_data = _read_json(devices_already_migrated)
        mqtt_data = _read_json(mqtt_config_already_migrated)
        result, mock_client = _invoke_migrate_with_mocked_grpc(
            cli_runner,
            ["--config-dir", str(temp_dirs["config"]), "config", "migrate"],
            devices_content=devices_data,
            mqtt_content=mqtt_data,
        )

        assert result.exit_code == 0
        assert "already up-to-date" in result.output
        mock_client.update_config.assert_not_called()

    @pytest.mark.unit
    def test_devices_without_mqtt_key_not_touched(
        self,
        cli_runner: CliRunner,
        temp_dirs: dict[str, Path],
        devices_no_mqtt: Path,
    ) -> None:
        devices_data = _read_json(devices_no_mqtt)
        result, mock_client = _invoke_migrate_with_mocked_grpc(
            cli_runner,
            ["--config-dir", str(temp_dirs["config"]), "config", "migrate"],
            devices_content=devices_data,
            mqtt_content={"topic_patterns": {}},
        )

        assert result.exit_code == 0
        mock_client.update_config.assert_not_called()


class TestConfigMigrateMissingFiles:
    @pytest.mark.unit
    def test_migrate_when_devices_json_missing(
        self,
        cli_runner: CliRunner,
        temp_dirs: dict[str, Path],
    ) -> None:
        result, mock_client = _invoke_migrate_with_mocked_grpc(
            cli_runner,
            [
                "--config-dir",
                str(temp_dirs["config"]),
                "config",
                "migrate",
                "--dry-run",
            ],
            devices_error=Exception("Not found"),
            mqtt_content={"broker": {"host": "localhost", "port": 1883}},
        )

        assert result.exit_code == 0
        assert result.exception is None
        assert "devices.json not found" in result.output
        mock_client.update_config.assert_not_called()

    @pytest.mark.unit
    def test_migrate_when_mqtt_config_missing(
        self,
        cli_runner: CliRunner,
        temp_dirs: dict[str, Path],
        devices_needing_migration: Path,
    ) -> None:
        devices_data = _read_json(devices_needing_migration)
        result, mock_client = _invoke_migrate_with_mocked_grpc(
            cli_runner,
            [
                "--config-dir",
                str(temp_dirs["config"]),
                "config",
                "migrate",
                "--dry-run",
            ],
            devices_content=devices_data,
            mqtt_error=Exception("Not found"),
        )

        assert result.exit_code == 0
        assert result.exception is None
        assert "mqtt_config.json not found" in result.output
        mock_client.update_config.assert_not_called()
