from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

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
        from src.interfaces.cli import cli

        original_content = devices_needing_migration.read_text()

        result = cli_runner.invoke(
            cli,
            [
                "--config-dir",
                str(temp_dirs["config"]),
                "config",
                "migrate",
                "--dry-run",
            ],
        )

        assert result.exit_code == 0
        assert "temp-001" in result.output
        assert "humid-001" in result.output
        assert devices_needing_migration.read_text() == original_content

    @pytest.mark.unit
    def test_dry_run_reports_mqtt_config_needing_topic_patterns(
        self,
        cli_runner: CliRunner,
        temp_dirs: dict[str, Path],
        mqtt_config_needing_migration: Path,
    ) -> None:
        from src.interfaces.cli import cli

        original_content = mqtt_config_needing_migration.read_text()

        result = cli_runner.invoke(
            cli,
            [
                "--config-dir",
                str(temp_dirs["config"]),
                "config",
                "migrate",
                "--dry-run",
            ],
        )

        assert result.exit_code == 0
        assert "topic_patterns" in result.output
        assert mqtt_config_needing_migration.read_text() == original_content

    @pytest.mark.unit
    def test_dry_run_no_backup_files_created(
        self,
        cli_runner: CliRunner,
        temp_dirs: dict[str, Path],
        devices_needing_migration: Path,  # noqa: ARG002
        mqtt_config_needing_migration: Path,  # noqa: ARG002
    ) -> None:
        from src.interfaces.cli import cli

        cli_runner.invoke(
            cli,
            [
                "--config-dir",
                str(temp_dirs["config"]),
                "config",
                "migrate",
                "--dry-run",
            ],
        )

        bak_files = list(temp_dirs["config"].glob("*.bak"))
        assert len(bak_files) == 0

    @pytest.mark.unit
    def test_dry_run_indicates_would_change_in_output(
        self,
        cli_runner: CliRunner,
        temp_dirs: dict[str, Path],
        devices_needing_migration: Path,  # noqa: ARG002
    ) -> None:
        from src.interfaces.cli import cli

        result = cli_runner.invoke(
            cli,
            [
                "--config-dir",
                str(temp_dirs["config"]),
                "config",
                "migrate",
                "--dry-run",
            ],
        )

        assert result.exit_code == 0
        output_lower = result.output.lower()
        assert (
            "would" in output_lower
            or "dry" in output_lower
            or "dry-run" in output_lower
        )

    @pytest.mark.unit
    def test_dry_run_on_already_migrated_reports_nothing_to_do(
        self,
        cli_runner: CliRunner,
        temp_dirs: dict[str, Path],
        devices_already_migrated: Path,  # noqa: ARG002
        mqtt_config_already_migrated: Path,  # noqa: ARG002
    ) -> None:
        from src.interfaces.cli import cli

        result = cli_runner.invoke(
            cli,
            [
                "--config-dir",
                str(temp_dirs["config"]),
                "config",
                "migrate",
                "--dry-run",
            ],
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


class TestConfigMigrateActual:
    @pytest.mark.unit
    def test_actual_migration_adds_payload_mapping_to_devices(
        self,
        cli_runner: CliRunner,
        temp_dirs: dict[str, Path],
        devices_needing_migration: Path,
    ) -> None:
        from src.interfaces.cli import cli

        result = cli_runner.invoke(
            cli,
            [
                "--config-dir",
                str(temp_dirs["config"]),
                "config",
                "migrate",
            ],
        )

        assert result.exit_code == 0

        data = json.loads(devices_needing_migration.read_text())
        devices = data["devices"]
        for dev in devices:
            if "mqtt" in dev:
                assert "payload_mapping" in dev["mqtt"], (
                    f"Device {dev['id']} missing payload_mapping after migration"
                )
                assert dev["mqtt"]["payload_mapping"] == {"value_field": "value"}

    @pytest.mark.unit
    def test_actual_migration_adds_topic_patterns_to_mqtt_config(
        self,
        cli_runner: CliRunner,
        temp_dirs: dict[str, Path],
        mqtt_config_needing_migration: Path,
    ) -> None:
        from src.interfaces.cli import cli

        result = cli_runner.invoke(
            cli,
            [
                "--config-dir",
                str(temp_dirs["config"]),
                "config",
                "migrate",
            ],
        )

        assert result.exit_code == 0

        data = json.loads(mqtt_config_needing_migration.read_text())
        assert "topic_patterns" in data
        assert isinstance(data["topic_patterns"], dict)

    @pytest.mark.unit
    def test_actual_migration_creates_bak_for_devices(
        self,
        cli_runner: CliRunner,
        temp_dirs: dict[str, Path],
        devices_needing_migration: Path,
    ) -> None:
        from src.interfaces.cli import cli

        original_content = devices_needing_migration.read_text()

        cli_runner.invoke(
            cli,
            [
                "--config-dir",
                str(temp_dirs["config"]),
                "config",
                "migrate",
            ],
        )

        bak_file = temp_dirs["config"] / "devices.json.bak"
        assert bak_file.exists()
        assert bak_file.read_text() == original_content

    @pytest.mark.unit
    def test_actual_migration_creates_bak_for_mqtt_config(
        self,
        cli_runner: CliRunner,
        temp_dirs: dict[str, Path],
        mqtt_config_needing_migration: Path,
    ) -> None:
        from src.interfaces.cli import cli

        original_content = mqtt_config_needing_migration.read_text()

        cli_runner.invoke(
            cli,
            [
                "--config-dir",
                str(temp_dirs["config"]),
                "config",
                "migrate",
            ],
        )

        bak_file = temp_dirs["config"] / "mqtt_config.json.bak"
        assert bak_file.exists()
        assert bak_file.read_text() == original_content

    @pytest.mark.unit
    def test_actual_migration_output_reports_changes_made(
        self,
        cli_runner: CliRunner,
        temp_dirs: dict[str, Path],
        devices_needing_migration: Path,  # noqa: ARG002
        mqtt_config_needing_migration: Path,  # noqa: ARG002
    ) -> None:
        from src.interfaces.cli import cli

        result = cli_runner.invoke(
            cli,
            [
                "--config-dir",
                str(temp_dirs["config"]),
                "config",
                "migrate",
            ],
        )

        assert result.exit_code == 0
        assert "temp-001" in result.output
        assert "humid-001" in result.output

    @pytest.mark.unit
    def test_already_migrated_devices_not_modified(
        self,
        cli_runner: CliRunner,
        temp_dirs: dict[str, Path],
        devices_already_migrated: Path,
        mqtt_config_already_migrated: Path,
    ) -> None:
        from src.interfaces.cli import cli

        original_devices = json.loads(devices_already_migrated.read_text())
        original_mqtt = json.loads(mqtt_config_already_migrated.read_text())

        result = cli_runner.invoke(
            cli,
            [
                "--config-dir",
                str(temp_dirs["config"]),
                "config",
                "migrate",
            ],
        )

        assert result.exit_code == 0
        assert json.loads(devices_already_migrated.read_text()) == original_devices
        assert json.loads(mqtt_config_already_migrated.read_text()) == original_mqtt

    @pytest.mark.unit
    def test_devices_without_mqtt_key_not_touched(
        self,
        cli_runner: CliRunner,
        temp_dirs: dict[str, Path],
        devices_no_mqtt: Path,
    ) -> None:
        from src.interfaces.cli import cli

        original_data = json.loads(devices_no_mqtt.read_text())

        result = cli_runner.invoke(
            cli,
            [
                "--config-dir",
                str(temp_dirs["config"]),
                "config",
                "migrate",
            ],
        )

        assert result.exit_code == 0
        assert json.loads(devices_no_mqtt.read_text()) == original_data


class TestConfigMigrateMissingFiles:
    @pytest.mark.unit
    def test_migrate_when_devices_json_missing(
        self,
        cli_runner: CliRunner,
        temp_dirs: dict[str, Path],
    ) -> None:
        from src.interfaces.cli import cli

        mqtt_cfg = {"broker": {"host": "localhost", "port": 1883}}
        (temp_dirs["config"] / "mqtt_config.json").write_text(json.dumps(mqtt_cfg))

        result = cli_runner.invoke(
            cli,
            [
                "--config-dir",
                str(temp_dirs["config"]),
                "config",
                "migrate",
                "--dry-run",
            ],
        )

        assert result.exit_code in (0, 1)
        assert result.exception is None

    @pytest.mark.unit
    def test_migrate_when_mqtt_config_missing(
        self,
        cli_runner: CliRunner,
        temp_dirs: dict[str, Path],
        devices_needing_migration: Path,  # noqa: ARG002
    ) -> None:
        from src.interfaces.cli import cli

        result = cli_runner.invoke(
            cli,
            [
                "--config-dir",
                str(temp_dirs["config"]),
                "config",
                "migrate",
                "--dry-run",
            ],
        )

        assert result.exit_code in (0, 1)
        assert result.exception is None
