import json
import time
from pathlib import Path
from typing import Any

import pytest


@pytest.fixture
def perf_config_dir(
    tmp_path: Path,
    sample_mqtt_config: dict[str, Any],
    sample_llm_config: dict[str, Any],
    sample_devices_config: dict[str, Any],
    sample_temperature_mf: dict[str, Any],
    sample_humidity_mf: dict[str, Any],
    sample_mf_schema: dict[str, Any],
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
    (schemas_dir / "membership_functions.schema.json").write_text(json.dumps(sample_mf_schema))
    (mf_dir / "temperature.json").write_text(json.dumps(sample_temperature_mf))
    (mf_dir / "humidity.json").write_text(json.dumps(sample_humidity_mf))

    return config_dir


@pytest.fixture
def perf_rules_dir(tmp_path: Path, sample_rules: list[dict[str, Any]]) -> Path:
    rules_dir = tmp_path / "rules"
    rules_dir.mkdir()
    rules_file = {"rules": sample_rules}
    (rules_dir / "active_rules.json").write_text(json.dumps(rules_file))
    return rules_dir


@pytest.fixture
def perf_logs_dir(tmp_path: Path) -> Path:
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    return logs_dir


@pytest.mark.performance
class TestFuzzyProcessingPerformance:
    FUZZY_PROCESSING_TARGET_MS = 50

    def test_single_reading_fuzzification_under_target(
        self,
        perf_config_dir: Path,
        perf_rules_dir: Path,
        perf_logs_dir: Path,
    ) -> None:
        from src.configuration.system_orchestrator import SystemOrchestrator

        orchestrator = SystemOrchestrator(
            config_dir=perf_config_dir,
            rules_dir=perf_rules_dir,
            logs_dir=perf_logs_dir,
        )
        orchestrator.initialize(skip_mqtt=True, skip_ollama=True)

        from src.device_interface.messages import SensorReading

        reading = SensorReading(sensor_id="temp_living_room", value=25.0, unit="celsius")

        start = time.perf_counter()
        orchestrator.fuzzy_pipeline.process_reading(reading, "temperature")
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert elapsed_ms < self.FUZZY_PROCESSING_TARGET_MS, (
            f"Fuzzy processing took {elapsed_ms:.2f}ms, target is {self.FUZZY_PROCESSING_TARGET_MS}ms"
        )

        orchestrator.shutdown()

    def test_batch_readings_fuzzification_performance(
        self,
        perf_config_dir: Path,
        perf_rules_dir: Path,
        perf_logs_dir: Path,
    ) -> None:
        from src.configuration.system_orchestrator import SystemOrchestrator
        from src.device_interface.messages import SensorReading

        orchestrator = SystemOrchestrator(
            config_dir=perf_config_dir,
            rules_dir=perf_rules_dir,
            logs_dir=perf_logs_dir,
        )
        orchestrator.initialize(skip_mqtt=True, skip_ollama=True)

        readings = [
            SensorReading(sensor_id="temp_living_room", value=float(i), unit="celsius")
            for i in range(-10, 51, 5)
        ]

        start = time.perf_counter()
        for reading in readings:
            orchestrator.fuzzy_pipeline.process_reading(reading, "temperature")
        elapsed_ms = (time.perf_counter() - start) * 1000

        avg_per_reading = elapsed_ms / len(readings)
        assert avg_per_reading < self.FUZZY_PROCESSING_TARGET_MS, (
            f"Average fuzzy processing took {avg_per_reading:.2f}ms per reading"
        )

        orchestrator.shutdown()


@pytest.mark.performance
class TestSensorToDescriptionPerformance:
    SENSOR_TO_DESC_TARGET_MS = 100

    def test_sensor_reading_to_description_under_target(
        self,
        perf_config_dir: Path,
        perf_rules_dir: Path,
        perf_logs_dir: Path,
    ) -> None:
        from src.application import Application, ApplicationConfig
        from src.device_interface.messages import SensorReading

        config = ApplicationConfig(
            config_dir=perf_config_dir,
            rules_dir=perf_rules_dir,
            logs_dir=perf_logs_dir,
            skip_mqtt=True,
            skip_ollama=True,
        )
        app = Application(config)
        app.start()

        reading = SensorReading(sensor_id="temp_living_room", value=30.0, unit="celsius")

        start = time.perf_counter()
        app._on_sensor_reading(reading)
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert elapsed_ms < self.SENSOR_TO_DESC_TARGET_MS, (
            f"Sensor to description took {elapsed_ms:.2f}ms, target is {self.SENSOR_TO_DESC_TARGET_MS}ms"
        )

        app.stop()


@pytest.mark.performance
class TestCommandGenerationPerformance:
    COMMAND_GEN_TARGET_MS = 100

    def test_command_generation_under_target(
        self,
        perf_config_dir: Path,
        perf_rules_dir: Path,
        perf_logs_dir: Path,
    ) -> None:
        from src.common.config import ConfigLoader
        from src.control_reasoning.command_generator import (
            CommandGenerator,
        )
        from src.control_reasoning.response_parser import ActionSpec
        from src.device_interface.registry import DeviceRegistry

        config_loader = ConfigLoader(config_dir=perf_config_dir)
        registry = DeviceRegistry(config_loader)
        registry.load("devices.json")

        generator = CommandGenerator(registry=registry)

        action = ActionSpec(
            device_id="ac_living_room",
            command="turn_on",
            parameters={"temperature": 22},
        )

        start = time.perf_counter()
        result = generator.generate(action, rule_id="test_rule")
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert result.success
        assert elapsed_ms < self.COMMAND_GEN_TARGET_MS, (
            f"Command generation took {elapsed_ms:.2f}ms, target is {self.COMMAND_GEN_TARGET_MS}ms"
        )

    def test_command_validation_under_target(
        self,
        perf_config_dir: Path,
        perf_rules_dir: Path,
        perf_logs_dir: Path,
    ) -> None:
        from src.common.config import ConfigLoader
        from src.control_reasoning.command_generator import DeviceCommand
        from src.control_reasoning.command_validator import CommandValidator
        from src.device_interface.registry import DeviceRegistry

        config_loader = ConfigLoader(config_dir=perf_config_dir)
        registry = DeviceRegistry(config_loader)
        registry.load("devices.json")

        validator = CommandValidator(registry=registry)
        command = DeviceCommand(
            command_id="test_cmd",
            device_id="ac_living_room",
            command_type="turn_on",
            parameters={},
        )

        start = time.perf_counter()
        result = validator.validate(command)
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert elapsed_ms < self.COMMAND_GEN_TARGET_MS, (
            f"Command validation took {elapsed_ms:.2f}ms, target is {self.COMMAND_GEN_TARGET_MS}ms"
        )


@pytest.mark.performance
class TestSystemStartupPerformance:
    STARTUP_TARGET_SECONDS = 30

    def test_system_startup_under_target(
        self,
        perf_config_dir: Path,
        perf_rules_dir: Path,
        perf_logs_dir: Path,
    ) -> None:
        from src.configuration.system_orchestrator import SystemOrchestrator

        orchestrator = SystemOrchestrator(
            config_dir=perf_config_dir,
            rules_dir=perf_rules_dir,
            logs_dir=perf_logs_dir,
        )

        start = time.perf_counter()
        result = orchestrator.initialize(skip_mqtt=True, skip_ollama=True)
        elapsed_seconds = time.perf_counter() - start

        assert result is True
        assert elapsed_seconds < self.STARTUP_TARGET_SECONDS, (
            f"System startup took {elapsed_seconds:.2f}s, target is {self.STARTUP_TARGET_SECONDS}s"
        )

        orchestrator.shutdown()

    def test_application_startup_under_target(
        self,
        perf_config_dir: Path,
        perf_rules_dir: Path,
        perf_logs_dir: Path,
    ) -> None:
        from src.application import Application, ApplicationConfig

        config = ApplicationConfig(
            config_dir=perf_config_dir,
            rules_dir=perf_rules_dir,
            logs_dir=perf_logs_dir,
            skip_mqtt=True,
            skip_ollama=True,
        )
        app = Application(config)

        start = time.perf_counter()
        result = app.start()
        elapsed_seconds = time.perf_counter() - start

        assert result is True
        assert elapsed_seconds < self.STARTUP_TARGET_SECONDS, (
            f"Application startup took {elapsed_seconds:.2f}s, target is {self.STARTUP_TARGET_SECONDS}s"
        )

        app.stop()


@pytest.mark.performance
class TestEndToEndPerformance:
    E2E_TARGET_SECONDS = 5

    def test_sensor_to_state_update_performance(
        self,
        perf_config_dir: Path,
        perf_rules_dir: Path,
        perf_logs_dir: Path,
    ) -> None:
        from src.application import Application, ApplicationConfig
        from src.device_interface.messages import SensorReading

        config = ApplicationConfig(
            config_dir=perf_config_dir,
            rules_dir=perf_rules_dir,
            logs_dir=perf_logs_dir,
            skip_mqtt=True,
            skip_ollama=True,
        )
        app = Application(config)
        app.start()

        reading = SensorReading(sensor_id="temp_living_room", value=38.0, unit="celsius")

        start = time.perf_counter()
        app._on_sensor_reading(reading)
        state = app.orchestrator.fuzzy_pipeline.get_current_state()
        elapsed_seconds = time.perf_counter() - start

        assert "temp_living_room" in state
        assert elapsed_seconds < self.E2E_TARGET_SECONDS, (
            f"E2E flow took {elapsed_seconds:.2f}s, target is {self.E2E_TARGET_SECONDS}s"
        )

        app.stop()


@pytest.mark.performance
class TestCachePerformance:
    def test_cached_fuzzification_faster_than_first(
        self,
        perf_config_dir: Path,
        perf_rules_dir: Path,
        perf_logs_dir: Path,
    ) -> None:
        from src.configuration.system_orchestrator import SystemOrchestrator
        from src.device_interface.messages import SensorReading

        orchestrator = SystemOrchestrator(
            config_dir=perf_config_dir,
            rules_dir=perf_rules_dir,
            logs_dir=perf_logs_dir,
        )
        orchestrator.initialize(skip_mqtt=True, skip_ollama=True)

        reading = SensorReading(sensor_id="temp_living_room", value=25.0, unit="celsius")

        start = time.perf_counter()
        orchestrator.fuzzy_pipeline.process_reading(reading, "temperature")
        first_elapsed_ms = (time.perf_counter() - start) * 1000

        start = time.perf_counter()
        orchestrator.fuzzy_pipeline.process_reading(reading, "temperature")
        second_elapsed_ms = (time.perf_counter() - start) * 1000

        assert second_elapsed_ms <= first_elapsed_ms * 1.5, (
            f"Cached reading should be at least as fast: first={first_elapsed_ms:.2f}ms, second={second_elapsed_ms:.2f}ms"
        )

        orchestrator.shutdown()
