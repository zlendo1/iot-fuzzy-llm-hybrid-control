import json
import time
import urllib.request
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


@pytest.mark.unit
class TestApplicationConfig:
    def test_default_config_values(self) -> None:
        from src.application import ApplicationConfig

        config = ApplicationConfig()

        assert config.config_dir == Path("config")
        assert config.rules_dir == Path("rules")
        assert config.logs_dir == Path("logs")
        assert config.skip_mqtt is False
        assert config.skip_ollama is False
        assert config.evaluation_interval == 1.0

    def test_custom_config_values(self, tmp_path: Path) -> None:
        from src.application import ApplicationConfig

        config = ApplicationConfig(
            config_dir=tmp_path / "custom_config",
            rules_dir=tmp_path / "custom_rules",
            logs_dir=tmp_path / "custom_logs",
            skip_mqtt=True,
            skip_ollama=True,
            evaluation_interval=0.5,
        )

        assert config.config_dir == tmp_path / "custom_config"
        assert config.rules_dir == tmp_path / "custom_rules"
        assert config.logs_dir == tmp_path / "custom_logs"
        assert config.skip_mqtt is True
        assert config.skip_ollama is True
        assert config.evaluation_interval == 0.5


@pytest.mark.unit
class TestApplicationStats:
    def test_default_stats(self) -> None:
        from src.application import ApplicationStats

        stats = ApplicationStats()

        assert stats.readings_processed == 0
        assert stats.rules_evaluated == 0
        assert stats.commands_generated == 0
        assert stats.commands_sent == 0
        assert stats.errors == 0
        assert stats.start_time is None

    def test_to_dict_without_start_time(self) -> None:
        from src.application import ApplicationStats

        stats = ApplicationStats()
        result = stats.to_dict()

        assert result["readings_processed"] == 0
        assert result["rules_evaluated"] == 0
        assert result["commands_generated"] == 0
        assert result["commands_sent"] == 0
        assert result["errors"] == 0
        assert result["uptime_seconds"] == 0

    def test_to_dict_with_start_time(self) -> None:
        from src.application import ApplicationStats

        start = time.time() - 100
        stats = ApplicationStats(
            readings_processed=10,
            rules_evaluated=5,
            commands_generated=3,
            commands_sent=2,
            errors=1,
            start_time=start,
        )
        result = stats.to_dict()

        assert result["readings_processed"] == 10
        assert result["rules_evaluated"] == 5
        assert result["commands_generated"] == 3
        assert result["commands_sent"] == 2
        assert result["errors"] == 1
        assert result["uptime_seconds"] >= 100


@pytest.mark.unit
class TestApplicationState:
    def test_state_values(self) -> None:
        from src.application import ApplicationState

        assert ApplicationState.STOPPED.value == "stopped"
        assert ApplicationState.STARTING.value == "starting"
        assert ApplicationState.RUNNING.value == "running"
        assert ApplicationState.STOPPING.value == "stopping"


@pytest.mark.unit
class TestApplication:
    def test_init_default_config(self) -> None:
        from src.application import Application, ApplicationState

        app = Application()

        assert app.state == ApplicationState.STOPPED
        assert app.is_running is False
        assert app.stats.readings_processed == 0
        assert app.orchestrator is not None

    def test_init_with_custom_config(self, tmp_path: Path) -> None:
        from src.application import Application, ApplicationConfig

        config = ApplicationConfig(
            config_dir=tmp_path / "config",
            rules_dir=tmp_path / "rules",
            logs_dir=tmp_path / "logs",
            skip_mqtt=True,
            skip_ollama=True,
        )
        app = Application(config)

        assert app.orchestrator.config_dir == tmp_path / "config"
        assert app.orchestrator.rules_dir == tmp_path / "rules"
        assert app.orchestrator.logs_dir == tmp_path / "logs"

    def test_start_fails_if_orchestrator_fails(self, tmp_path: Path) -> None:
        from src.application import Application, ApplicationConfig, ApplicationState

        config = ApplicationConfig(
            config_dir=tmp_path / "nonexistent",
            skip_mqtt=True,
            skip_ollama=True,
        )
        app = Application(config)

        result = app.start()

        assert result is False
        assert app.state == ApplicationState.STOPPED

    def test_start_success_with_mocked_orchestrator(self, tmp_path: Path) -> None:
        from src.application import Application, ApplicationConfig, ApplicationState

        config = ApplicationConfig(
            config_dir=tmp_path / "config",
            rules_dir=tmp_path / "rules",
            logs_dir=tmp_path / "logs",
            skip_mqtt=True,
            skip_ollama=True,
        )
        app = Application(config)

        with patch.object(app._orchestrator, "initialize", return_value=True):
            result = app.start()

            assert result is True
            assert app.state == ApplicationState.RUNNING
            assert app.stats.start_time is not None

            app.stop()

    def test_start_twice_returns_false(self, tmp_path: Path) -> None:
        from src.application import Application, ApplicationConfig

        config = ApplicationConfig(
            config_dir=tmp_path / "config",
            skip_mqtt=True,
            skip_ollama=True,
        )
        app = Application(config)

        with patch.object(app._orchestrator, "initialize", return_value=True):
            app.start()
            result = app.start()

            assert result is False

            app.stop()

    def test_stop_when_already_stopped(self) -> None:
        from src.application import Application, ApplicationState

        app = Application()

        result = app.stop()

        assert result is True
        assert app.state == ApplicationState.STOPPED

    def test_stop_after_start(self, tmp_path: Path) -> None:
        from src.application import Application, ApplicationConfig, ApplicationState

        config = ApplicationConfig(
            config_dir=tmp_path / "config",
            skip_mqtt=True,
            skip_ollama=True,
        )
        app = Application(config)

        with (
            patch.object(app._orchestrator, "initialize", return_value=True),
            patch.object(app._orchestrator, "shutdown", return_value=True),
        ):
            app.start()
            result = app.stop()

            assert result is True
            assert app.state == ApplicationState.STOPPED

    def test_get_status(self) -> None:
        from src.application import Application

        app = Application()

        status = app.get_status()

        assert "state" in status
        assert "is_running" in status
        assert "stats" in status
        assert "orchestrator" in status
        assert status["state"] == "stopped"
        assert status["is_running"] is False

    def test_is_running_property(self, tmp_path: Path) -> None:
        from src.application import Application, ApplicationConfig

        config = ApplicationConfig(
            config_dir=tmp_path / "config",
            skip_mqtt=True,
            skip_ollama=True,
        )
        app = Application(config)

        assert app.is_running is False

        with patch.object(app._orchestrator, "initialize", return_value=True):
            app.start()
            assert app.is_running is True

            app.stop()
            assert app.is_running is False

    def test_status_endpoint_returns_payload(self, tmp_path: Path) -> None:
        from src.application import Application, ApplicationConfig

        config = ApplicationConfig(
            config_dir=tmp_path / "config",
            rules_dir=tmp_path / "rules",
            logs_dir=tmp_path / "logs",
            skip_mqtt=True,
            skip_ollama=True,
            evaluation_interval=0.1,
        )
        app = Application(config)

        with patch.object(app._orchestrator, "initialize", return_value=True):
            assert app.start() is True
            try:
                with urllib.request.urlopen(
                    "http://localhost:8080/status", timeout=2
                ) as response:
                    assert response.status == 200
                    payload = json.loads(response.read().decode("utf-8"))

                assert payload["state"] == "running"
                assert payload["is_running"] is True
                assert "stats" in payload
                assert "orchestrator" in payload
            finally:
                app.stop()


@pytest.mark.unit
class TestApplicationEvaluationLoop:
    def test_evaluation_loop_starts_on_application_start(self, tmp_path: Path) -> None:
        from src.application import Application, ApplicationConfig

        config = ApplicationConfig(
            config_dir=tmp_path / "config",
            skip_mqtt=True,
            skip_ollama=True,
            evaluation_interval=0.1,
        )
        app = Application(config)

        with patch.object(app._orchestrator, "initialize", return_value=True):
            app.start()

            assert app._eval_thread is not None
            assert app._eval_thread.is_alive()

            app.stop()

            time.sleep(0.2)
            assert not app._eval_thread.is_alive()

    def test_evaluation_loop_calls_evaluate_and_execute(self, tmp_path: Path) -> None:
        from src.application import Application, ApplicationConfig

        config = ApplicationConfig(
            config_dir=tmp_path / "config",
            skip_mqtt=True,
            skip_ollama=True,
            evaluation_interval=0.05,
        )
        app = Application(config)

        with (
            patch.object(app._orchestrator, "initialize", return_value=True),
            patch.object(app, "_evaluate_and_execute") as mock_eval,
        ):
            app.start()
            time.sleep(0.2)
            app.stop()

            assert mock_eval.call_count >= 1


@pytest.mark.unit
class TestApplicationSensorProcessing:
    def test_on_sensor_reading_increments_stats(self) -> None:
        from src.application import Application
        from src.device_interface.messages import SensorReading

        app = Application()
        mock_pipeline = MagicMock()
        mock_pipeline.process_reading.return_value = MagicMock()
        app._orchestrator._fuzzy_pipeline = mock_pipeline

        mock_registry = MagicMock()
        mock_sensor = MagicMock()
        mock_sensor.id = "temp_sensor_1"
        mock_sensor.device_class = "temperature"
        mock_registry.sensors.return_value = [mock_sensor]
        app._orchestrator._device_registry = mock_registry

        reading = SensorReading(
            sensor_id="temp_sensor_1",
            value=25.5,
        )

        app._on_sensor_reading(reading)

        assert app.stats.readings_processed == 1

    def test_on_sensor_reading_handles_unknown_sensor(self) -> None:
        from src.application import Application
        from src.device_interface.messages import SensorReading

        app = Application()
        mock_pipeline = MagicMock()
        app._orchestrator._fuzzy_pipeline = mock_pipeline

        mock_registry = MagicMock()
        mock_registry.sensors.return_value = []
        app._orchestrator._device_registry = mock_registry

        reading = SensorReading(
            sensor_id="unknown_sensor",
            value=25.5,
        )

        app._on_sensor_reading(reading)

        assert app.stats.readings_processed == 0
        mock_pipeline.process_reading.assert_not_called()


@pytest.mark.unit
class TestApplicationCommandConversion:
    def test_convert_to_mqtt_command_set(self) -> None:
        from src.application import Application
        from src.control_reasoning.command_generator import DeviceCommand
        from src.device_interface.messages import CommandType

        app = Application()
        command = DeviceCommand(
            command_id="cmd_001",
            device_id="thermostat_1",
            command_type="set",
            parameters={"value": 22},
        )

        mqtt_command = app._convert_to_mqtt_command(command)

        assert mqtt_command.device_id == "thermostat_1"
        assert mqtt_command.command_type == CommandType.SET
        assert mqtt_command.parameters == {"value": 22}
        assert mqtt_command.command_id == "cmd_001"
        assert mqtt_command.source == "rule_engine"

    def test_convert_to_mqtt_command_toggle(self) -> None:
        from src.application import Application
        from src.control_reasoning.command_generator import DeviceCommand
        from src.device_interface.messages import CommandType

        app = Application()
        command = DeviceCommand(
            command_id="cmd_002",
            device_id="light_1",
            command_type="toggle",
            parameters={},
        )

        mqtt_command = app._convert_to_mqtt_command(command)

        assert mqtt_command.command_type == CommandType.TOGGLE

    def test_convert_to_mqtt_command_unknown_type_defaults_to_set(self) -> None:
        from src.application import Application
        from src.control_reasoning.command_generator import DeviceCommand
        from src.device_interface.messages import CommandType

        app = Application()
        command = DeviceCommand(
            command_id="cmd_003",
            device_id="device_1",
            command_type="unknown_type",
            parameters={},
        )

        mqtt_command = app._convert_to_mqtt_command(command)

        assert mqtt_command.command_type == CommandType.SET


@pytest.mark.unit
class TestCreateApplicationFactory:
    def test_create_application_defaults(self) -> None:
        from src.application import create_application

        app = create_application()

        assert app is not None
        assert app.orchestrator.config_dir == Path("config")
        assert app.orchestrator.rules_dir == Path("rules")
        assert app.orchestrator.logs_dir == Path("logs")

    def test_create_application_with_paths(self, tmp_path: Path) -> None:
        from src.application import create_application

        app = create_application(
            config_dir=tmp_path / "cfg",
            rules_dir=tmp_path / "rls",
            logs_dir=tmp_path / "lgs",
            skip_mqtt=True,
            skip_ollama=True,
        )

        assert app.orchestrator.config_dir == tmp_path / "cfg"
        assert app.orchestrator.rules_dir == tmp_path / "rls"
        assert app.orchestrator.logs_dir == tmp_path / "lgs"

    def test_create_application_with_string_paths(self, tmp_path: Path) -> None:
        from src.application import create_application

        app = create_application(
            config_dir=str(tmp_path / "config"),
            rules_dir=str(tmp_path / "rules"),
            logs_dir=str(tmp_path / "logs"),
        )

        assert app.orchestrator.config_dir == tmp_path / "config"
