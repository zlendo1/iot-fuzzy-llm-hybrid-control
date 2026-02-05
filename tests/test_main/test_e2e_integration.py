import json
import time
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest


@pytest.fixture
def e2e_config_dir(
    tmp_path: Path,
    sample_mqtt_config: dict[str, Any],
    sample_llm_config: dict[str, Any],
    sample_devices_config: dict[str, Any],
    sample_temperature_mf: dict[str, Any],
    sample_humidity_mf: dict[str, Any],
) -> Path:
    config_dir = tmp_path / "config"
    config_dir.mkdir()

    schemas_dir = config_dir / "schemas"
    schemas_dir.mkdir()

    mf_dir = config_dir / "membership_functions"
    mf_dir.mkdir()

    (config_dir / "mqtt_config.json").write_text(json.dumps(sample_mqtt_config))
    (config_dir / "llm_config.json").write_text(json.dumps(sample_llm_config))
    (config_dir / "devices.json").write_text(json.dumps(sample_devices_config))
    (mf_dir / "temperature.json").write_text(json.dumps(sample_temperature_mf))
    (mf_dir / "humidity.json").write_text(json.dumps(sample_humidity_mf))

    return config_dir


@pytest.fixture
def e2e_rules_dir(tmp_path: Path, sample_rules: list[dict[str, Any]]) -> Path:
    rules_dir = tmp_path / "rules"
    rules_dir.mkdir()

    rules_file = {"rules": sample_rules}
    (rules_dir / "active_rules.json").write_text(json.dumps(rules_file))

    return rules_dir


@pytest.fixture
def e2e_logs_dir(tmp_path: Path) -> Path:
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    return logs_dir


@pytest.mark.integration
class TestSystemInitializationE2E:
    def test_system_initializes_all_layers_in_order(
        self,
        e2e_config_dir: Path,
        e2e_rules_dir: Path,
        e2e_logs_dir: Path,
    ) -> None:
        from src.configuration.system_orchestrator import (
            SystemOrchestrator,
            SystemState,
        )

        orchestrator = SystemOrchestrator(
            config_dir=e2e_config_dir,
            rules_dir=e2e_rules_dir,
            logs_dir=e2e_logs_dir,
        )

        result = orchestrator.initialize(skip_mqtt=True, skip_ollama=True)

        assert result is True
        assert orchestrator.state == SystemState.READY
        assert orchestrator.config_manager is not None
        assert orchestrator.logging_manager is not None
        assert orchestrator.rule_manager is not None
        assert orchestrator.device_registry is not None
        assert orchestrator.fuzzy_pipeline is not None

        orchestrator.shutdown()

    def test_initialization_steps_recorded(
        self,
        e2e_config_dir: Path,
        e2e_rules_dir: Path,
        e2e_logs_dir: Path,
    ) -> None:
        from src.configuration.system_orchestrator import SystemOrchestrator

        orchestrator = SystemOrchestrator(
            config_dir=e2e_config_dir,
            rules_dir=e2e_rules_dir,
            logs_dir=e2e_logs_dir,
        )

        orchestrator.initialize(skip_mqtt=True, skip_ollama=True)
        steps = orchestrator.initialization_steps

        step_names = [s.name for s in steps]
        assert "load_config" in step_names
        assert "init_logging" in step_names
        assert "populate_registry" in step_names
        assert "load_membership_functions" in step_names
        assert "load_rules" in step_names

        for step in steps:
            assert step.completed is True
            assert step.error is None

        orchestrator.shutdown()

    def test_system_status_reflects_components(
        self,
        e2e_config_dir: Path,
        e2e_rules_dir: Path,
        e2e_logs_dir: Path,
    ) -> None:
        from src.configuration.system_orchestrator import SystemOrchestrator

        orchestrator = SystemOrchestrator(
            config_dir=e2e_config_dir,
            rules_dir=e2e_rules_dir,
            logs_dir=e2e_logs_dir,
        )

        orchestrator.initialize(skip_mqtt=True, skip_ollama=True)
        status = orchestrator.get_system_status()

        assert status["state"] == "ready"
        assert status["is_ready"] is True
        assert status["components"]["config_manager"] is True
        assert status["components"]["logging_manager"] is True
        assert status["components"]["rule_manager"] is True
        assert status["components"]["device_registry"] is True
        assert status["components"]["fuzzy_pipeline"] is True

        orchestrator.shutdown()


@pytest.mark.integration
class TestApplicationLifecycleE2E:
    def test_application_starts_and_stops_cleanly(
        self,
        e2e_config_dir: Path,
        e2e_rules_dir: Path,
        e2e_logs_dir: Path,
    ) -> None:
        from src.application import Application, ApplicationConfig, ApplicationState

        config = ApplicationConfig(
            config_dir=e2e_config_dir,
            rules_dir=e2e_rules_dir,
            logs_dir=e2e_logs_dir,
            skip_mqtt=True,
            skip_ollama=True,
            evaluation_interval=0.1,
        )
        app = Application(config)

        assert app.state == ApplicationState.STOPPED

        result = app.start()
        assert result is True
        assert app.state == ApplicationState.RUNNING
        assert app.stats.start_time is not None

        result = app.stop()
        assert result is True
        assert app.state == ApplicationState.STOPPED

    def test_application_status_shows_all_info(
        self,
        e2e_config_dir: Path,
        e2e_rules_dir: Path,
        e2e_logs_dir: Path,
    ) -> None:
        from src.application import Application, ApplicationConfig

        config = ApplicationConfig(
            config_dir=e2e_config_dir,
            rules_dir=e2e_rules_dir,
            logs_dir=e2e_logs_dir,
            skip_mqtt=True,
            skip_ollama=True,
        )
        app = Application(config)
        app.start()

        status = app.get_status()

        assert "state" in status
        assert "is_running" in status
        assert "stats" in status
        assert "orchestrator" in status

        assert status["state"] == "running"
        assert status["is_running"] is True
        assert "uptime_seconds" in status["stats"]

        app.stop()


@pytest.mark.integration
class TestSensorToDescriptionFlowE2E:
    def test_sensor_reading_processed_to_linguistic_description(
        self,
        e2e_config_dir: Path,
        e2e_rules_dir: Path,
        e2e_logs_dir: Path,
    ) -> None:
        from src.application import Application, ApplicationConfig
        from src.device_interface.messages import SensorReading

        config = ApplicationConfig(
            config_dir=e2e_config_dir,
            rules_dir=e2e_rules_dir,
            logs_dir=e2e_logs_dir,
            skip_mqtt=True,
            skip_ollama=True,
        )
        app = Application(config)
        app.start()

        reading = SensorReading(
            sensor_id="temp_living_room",
            value=35.0,
            unit="celsius",
        )

        app._on_sensor_reading(reading)

        assert app.stats.readings_processed == 1

        fuzzy_pipeline = app.orchestrator.fuzzy_pipeline
        assert fuzzy_pipeline is not None

        state = fuzzy_pipeline.get_current_state()
        assert state is not None
        assert "temp_living_room" in state

        description = state["temp_living_room"]
        assert description.sensor_id == "temp_living_room"
        assert description.raw_value == 35.0
        assert len(description.terms) > 0

        app.stop()

    def test_multiple_sensor_readings_accumulated(
        self,
        e2e_config_dir: Path,
        e2e_rules_dir: Path,
        e2e_logs_dir: Path,
    ) -> None:
        from src.application import Application, ApplicationConfig
        from src.device_interface.messages import SensorReading

        config = ApplicationConfig(
            config_dir=e2e_config_dir,
            rules_dir=e2e_rules_dir,
            logs_dir=e2e_logs_dir,
            skip_mqtt=True,
            skip_ollama=True,
        )
        app = Application(config)
        app.start()

        temp_reading = SensorReading(
            sensor_id="temp_living_room",
            value=30.0,
            unit="celsius",
        )
        humidity_reading = SensorReading(
            sensor_id="humidity_living_room",
            value=75.0,
            unit="percent",
        )

        app._on_sensor_reading(temp_reading)
        app._on_sensor_reading(humidity_reading)

        assert app.stats.readings_processed == 2

        state = app.orchestrator.fuzzy_pipeline.get_current_state()
        assert "temp_living_room" in state
        assert "humidity_living_room" in state

        app.stop()


@pytest.mark.integration
class TestRuleEvaluationFlowE2E:
    def test_rules_loaded_into_pipeline(
        self,
        e2e_config_dir: Path,
        e2e_rules_dir: Path,
        e2e_logs_dir: Path,
    ) -> None:
        from src.application import Application, ApplicationConfig

        config = ApplicationConfig(
            config_dir=e2e_config_dir,
            rules_dir=e2e_rules_dir,
            logs_dir=e2e_logs_dir,
            skip_mqtt=True,
            skip_ollama=True,
        )
        app = Application(config)
        app.start()

        rule_manager = app.orchestrator.rule_manager
        assert rule_manager is not None

        enabled_rules = rule_manager.get_enabled_rules()
        assert len(enabled_rules) >= 1

        app.stop()

    def test_evaluation_loop_runs_periodically(
        self,
        e2e_config_dir: Path,
        e2e_rules_dir: Path,
        e2e_logs_dir: Path,
    ) -> None:
        from src.application import Application, ApplicationConfig

        config = ApplicationConfig(
            config_dir=e2e_config_dir,
            rules_dir=e2e_rules_dir,
            logs_dir=e2e_logs_dir,
            skip_mqtt=True,
            skip_ollama=True,
            evaluation_interval=0.05,
        )
        app = Application(config)

        with patch.object(app, "_evaluate_and_execute") as mock_eval:
            app.start()
            time.sleep(0.2)
            app.stop()

            assert mock_eval.call_count >= 2


@pytest.mark.integration
class TestCommandGenerationFlowE2E:
    def test_command_conversion_preserves_data(
        self,
        e2e_config_dir: Path,
        e2e_rules_dir: Path,
        e2e_logs_dir: Path,
    ) -> None:
        from src.application import Application, ApplicationConfig
        from src.control_reasoning.command_generator import DeviceCommand
        from src.device_interface.messages import CommandType

        config = ApplicationConfig(
            config_dir=e2e_config_dir,
            rules_dir=e2e_rules_dir,
            logs_dir=e2e_logs_dir,
            skip_mqtt=True,
            skip_ollama=True,
        )
        app = Application(config)

        command = DeviceCommand(
            command_id="test_cmd_001",
            device_id="ac_living_room",
            command_type="set",
            parameters={"temperature": 22},
            rule_id="rule_001",
        )

        mqtt_command = app._convert_to_mqtt_command(command)

        assert mqtt_command.device_id == "ac_living_room"
        assert mqtt_command.command_type == CommandType.SET
        assert mqtt_command.parameters == {"temperature": 22}
        assert mqtt_command.command_id == "test_cmd_001"


@pytest.mark.integration
class TestShutdownFlowE2E:
    def test_graceful_shutdown_stops_all_components(
        self,
        e2e_config_dir: Path,
        e2e_rules_dir: Path,
        e2e_logs_dir: Path,
    ) -> None:
        from src.configuration.system_orchestrator import (
            SystemOrchestrator,
            SystemState,
        )

        orchestrator = SystemOrchestrator(
            config_dir=e2e_config_dir,
            rules_dir=e2e_rules_dir,
            logs_dir=e2e_logs_dir,
        )

        orchestrator.initialize(skip_mqtt=True, skip_ollama=True)
        assert orchestrator.state == SystemState.READY

        result = orchestrator.shutdown()

        assert result is True
        assert orchestrator.state == SystemState.STOPPED

    def test_application_shutdown_cleans_up_threads(
        self,
        e2e_config_dir: Path,
        e2e_rules_dir: Path,
        e2e_logs_dir: Path,
    ) -> None:
        from src.application import Application, ApplicationConfig, ApplicationState

        config = ApplicationConfig(
            config_dir=e2e_config_dir,
            rules_dir=e2e_rules_dir,
            logs_dir=e2e_logs_dir,
            skip_mqtt=True,
            skip_ollama=True,
            evaluation_interval=0.1,
        )
        app = Application(config)

        app.start()
        assert app._eval_thread is not None
        assert app._eval_thread.is_alive()

        app.stop()

        time.sleep(0.2)
        assert app.state == ApplicationState.STOPPED
        assert not app._eval_thread.is_alive()


@pytest.mark.integration
class TestErrorHandlingE2E:
    def test_unknown_sensor_reading_handled_gracefully(
        self,
        e2e_config_dir: Path,
        e2e_rules_dir: Path,
        e2e_logs_dir: Path,
    ) -> None:
        from src.application import Application, ApplicationConfig
        from src.device_interface.messages import SensorReading

        config = ApplicationConfig(
            config_dir=e2e_config_dir,
            rules_dir=e2e_rules_dir,
            logs_dir=e2e_logs_dir,
            skip_mqtt=True,
            skip_ollama=True,
        )
        app = Application(config)
        app.start()

        reading = SensorReading(
            sensor_id="unknown_sensor_xyz",
            value=25.0,
        )

        app._on_sensor_reading(reading)

        assert app.stats.readings_processed == 0
        assert app.stats.errors == 0

        app.stop()

    def test_invalid_config_prevents_startup(self, tmp_path: Path) -> None:
        from src.application import Application, ApplicationConfig, ApplicationState

        config = ApplicationConfig(
            config_dir=tmp_path / "nonexistent",
            rules_dir=tmp_path / "rules",
            logs_dir=tmp_path / "logs",
            skip_mqtt=True,
            skip_ollama=True,
        )
        app = Application(config)

        result = app.start()

        assert result is False
        assert app.state == ApplicationState.STOPPED


@pytest.mark.integration
class TestFuzzyProcessingE2E:
    def test_temperature_fuzzification(
        self,
        e2e_config_dir: Path,
        e2e_rules_dir: Path,
        e2e_logs_dir: Path,
    ) -> None:
        from src.application import Application, ApplicationConfig
        from src.device_interface.messages import SensorReading

        config = ApplicationConfig(
            config_dir=e2e_config_dir,
            rules_dir=e2e_rules_dir,
            logs_dir=e2e_logs_dir,
            skip_mqtt=True,
            skip_ollama=True,
        )
        app = Application(config)
        app.start()

        cold_reading = SensorReading(sensor_id="temp_living_room", value=5.0, unit="celsius")
        app._on_sensor_reading(cold_reading)

        state = app.orchestrator.fuzzy_pipeline.get_current_state()
        description = state["temp_living_room"]

        term_names = [t.term for t in description.terms if t.degree > 0]
        assert "cold" in term_names

        hot_reading = SensorReading(sensor_id="temp_living_room", value=40.0, unit="celsius")
        app._on_sensor_reading(hot_reading)

        state = app.orchestrator.fuzzy_pipeline.get_current_state()
        description = state["temp_living_room"]

        term_names = [t.term for t in description.terms if t.degree > 0]
        assert "hot" in term_names

        app.stop()
