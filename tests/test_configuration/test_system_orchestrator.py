import json
from pathlib import Path

import pytest


@pytest.fixture
def orchestrator_dirs(tmp_path: Path) -> dict[str, Path]:
    config_dir = tmp_path / "config"
    config_dir.mkdir()

    schemas_dir = config_dir / "schemas"
    schemas_dir.mkdir()

    mf_dir = config_dir / "membership_functions"
    mf_dir.mkdir()

    rules_dir = tmp_path / "rules"
    rules_dir.mkdir()

    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()

    return {
        "config": config_dir,
        "schemas": schemas_dir,
        "membership_functions": mf_dir,
        "rules": rules_dir,
        "logs": logs_dir,
    }


@pytest.fixture
def populated_config(orchestrator_dirs: dict[str, Path]) -> dict[str, Path]:
    config_dir = orchestrator_dirs["config"]

    mqtt_config = {
        "broker": {
            "host": "localhost",
            "port": 1883,
            "keepalive": 60,
        },
    }
    (config_dir / "mqtt_config.json").write_text(json.dumps(mqtt_config))

    llm_config = {
        "llm": {
            "provider": "ollama",
            "connection": {"host": "localhost", "port": 11434},
            "model": {"name": "qwen3:0.6b"},
        },
    }
    (config_dir / "llm_config.json").write_text(json.dumps(llm_config))

    devices_config = {
        "devices": [
            {
                "id": "temp_living_room",
                "name": "Living Room Temperature",
                "type": "sensor",
                "device_class": "temperature",
                "mqtt": {"topic": "home/living_room/temperature"},
            },
            {
                "id": "ac_living_room",
                "name": "Living Room AC",
                "type": "actuator",
                "device_class": "thermostat",
                "capabilities": ["turn_on", "turn_off", "set_temperature"],
                "mqtt": {
                    "topic": "home/living_room/ac/state",
                    "command_topic": "home/living_room/ac/set",
                },
            },
        ],
    }
    (config_dir / "devices.json").write_text(json.dumps(devices_config))

    temperature_mf = {
        "sensor_type": "temperature",
        "unit": "celsius",
        "universe_of_discourse": {"min": -10, "max": 50},
        "linguistic_variables": [
            {
                "term": "cold",
                "function_type": "triangular",
                "parameters": {"a": -10, "b": 0, "c": 15},
            },
            {
                "term": "comfortable",
                "function_type": "triangular",
                "parameters": {"a": 15, "b": 22, "c": 28},
            },
            {
                "term": "hot",
                "function_type": "triangular",
                "parameters": {"a": 26, "b": 35, "c": 50},
            },
        ],
    }
    (orchestrator_dirs["membership_functions"] / "temperature.json").write_text(
        json.dumps(temperature_mf)
    )

    return orchestrator_dirs


class TestSystemOrchestratorInit:
    @pytest.mark.unit
    def test_init_sets_paths(self, orchestrator_dirs: dict[str, Path]) -> None:
        from src.configuration.system_orchestrator import SystemOrchestrator

        orchestrator = SystemOrchestrator(
            config_dir=orchestrator_dirs["config"],
            rules_dir=orchestrator_dirs["rules"],
            logs_dir=orchestrator_dirs["logs"],
        )

        assert orchestrator.config_dir == orchestrator_dirs["config"]
        assert orchestrator.rules_dir == orchestrator_dirs["rules"]
        assert orchestrator.logs_dir == orchestrator_dirs["logs"]

    @pytest.mark.unit
    def test_init_state_is_uninitialized(
        self, orchestrator_dirs: dict[str, Path]
    ) -> None:
        from src.configuration.system_orchestrator import (
            SystemOrchestrator,
            SystemState,
        )

        orchestrator = SystemOrchestrator(
            config_dir=orchestrator_dirs["config"],
        )

        assert orchestrator.state == SystemState.UNINITIALIZED


class TestSystemState:
    @pytest.mark.unit
    def test_system_state_values(self) -> None:
        from src.configuration.system_orchestrator import SystemState

        assert SystemState.UNINITIALIZED.value == "uninitialized"
        assert SystemState.INITIALIZING.value == "initializing"
        assert SystemState.READY.value == "ready"
        assert SystemState.RUNNING.value == "running"
        assert SystemState.STOPPING.value == "stopping"
        assert SystemState.STOPPED.value == "stopped"
        assert SystemState.ERROR.value == "error"


class TestInitialization:
    @pytest.mark.unit
    def test_initialize_succeeds_with_valid_config(
        self, populated_config: dict[str, Path]
    ) -> None:
        from src.configuration.system_orchestrator import (
            SystemOrchestrator,
            SystemState,
        )

        orchestrator = SystemOrchestrator(
            config_dir=populated_config["config"],
            rules_dir=populated_config["rules"],
            logs_dir=populated_config["logs"],
        )

        result = orchestrator.initialize(skip_mqtt=True, skip_ollama=True)

        assert result is True
        assert orchestrator.state == SystemState.READY
        orchestrator.shutdown()

    @pytest.mark.unit
    def test_initialize_loads_config_manager(
        self, populated_config: dict[str, Path]
    ) -> None:
        from src.configuration.system_orchestrator import SystemOrchestrator

        orchestrator = SystemOrchestrator(
            config_dir=populated_config["config"],
            rules_dir=populated_config["rules"],
            logs_dir=populated_config["logs"],
        )

        orchestrator.initialize(skip_mqtt=True, skip_ollama=True)

        assert orchestrator.config_manager is not None
        orchestrator.shutdown()

    @pytest.mark.unit
    def test_initialize_loads_logging_manager(
        self, populated_config: dict[str, Path]
    ) -> None:
        from src.configuration.system_orchestrator import SystemOrchestrator

        orchestrator = SystemOrchestrator(
            config_dir=populated_config["config"],
            rules_dir=populated_config["rules"],
            logs_dir=populated_config["logs"],
        )

        orchestrator.initialize(skip_mqtt=True, skip_ollama=True)

        assert orchestrator.logging_manager is not None
        orchestrator.shutdown()

    @pytest.mark.unit
    def test_initialize_loads_device_registry(
        self, populated_config: dict[str, Path]
    ) -> None:
        from src.configuration.system_orchestrator import SystemOrchestrator

        orchestrator = SystemOrchestrator(
            config_dir=populated_config["config"],
            rules_dir=populated_config["rules"],
            logs_dir=populated_config["logs"],
        )

        orchestrator.initialize(skip_mqtt=True, skip_ollama=True)

        assert orchestrator.device_registry is not None
        assert len(list(orchestrator.device_registry)) == 2
        orchestrator.shutdown()

    @pytest.mark.unit
    def test_initialize_loads_fuzzy_pipeline(
        self, populated_config: dict[str, Path]
    ) -> None:
        from src.configuration.system_orchestrator import SystemOrchestrator

        orchestrator = SystemOrchestrator(
            config_dir=populated_config["config"],
            rules_dir=populated_config["rules"],
            logs_dir=populated_config["logs"],
        )

        orchestrator.initialize(skip_mqtt=True, skip_ollama=True)

        assert orchestrator.fuzzy_pipeline is not None
        orchestrator.shutdown()

    @pytest.mark.unit
    def test_initialize_loads_rule_manager(
        self, populated_config: dict[str, Path]
    ) -> None:
        from src.configuration.system_orchestrator import SystemOrchestrator

        orchestrator = SystemOrchestrator(
            config_dir=populated_config["config"],
            rules_dir=populated_config["rules"],
            logs_dir=populated_config["logs"],
        )

        orchestrator.initialize(skip_mqtt=True, skip_ollama=True)

        assert orchestrator.rule_manager is not None
        orchestrator.shutdown()

    @pytest.mark.unit
    def test_initialize_records_steps(self, populated_config: dict[str, Path]) -> None:
        from src.configuration.system_orchestrator import SystemOrchestrator

        orchestrator = SystemOrchestrator(
            config_dir=populated_config["config"],
            rules_dir=populated_config["rules"],
            logs_dir=populated_config["logs"],
        )

        orchestrator.initialize(skip_mqtt=True, skip_ollama=True)

        steps = orchestrator.initialization_steps
        assert len(steps) >= 6
        assert all(step.completed for step in steps)
        orchestrator.shutdown()

    @pytest.mark.unit
    def test_initialize_returns_false_on_already_initialized(
        self, populated_config: dict[str, Path]
    ) -> None:
        from src.configuration.system_orchestrator import SystemOrchestrator

        orchestrator = SystemOrchestrator(
            config_dir=populated_config["config"],
            rules_dir=populated_config["rules"],
            logs_dir=populated_config["logs"],
        )

        orchestrator.initialize(skip_mqtt=True, skip_ollama=True)
        result = orchestrator.initialize(skip_mqtt=True, skip_ollama=True)

        assert result is False
        orchestrator.shutdown()


class TestInitializationFailures:
    @pytest.mark.unit
    def test_initialize_fails_on_missing_config(
        self, orchestrator_dirs: dict[str, Path]
    ) -> None:
        from src.configuration.system_orchestrator import (
            SystemOrchestrator,
            SystemState,
        )

        orchestrator = SystemOrchestrator(
            config_dir=orchestrator_dirs["config"],
            rules_dir=orchestrator_dirs["rules"],
            logs_dir=orchestrator_dirs["logs"],
        )

        result = orchestrator.initialize(skip_mqtt=True, skip_ollama=True)

        assert result is False
        assert orchestrator.state == SystemState.ERROR


class TestIsReady:
    @pytest.mark.unit
    def test_is_ready_false_before_init(
        self, orchestrator_dirs: dict[str, Path]
    ) -> None:
        from src.configuration.system_orchestrator import SystemOrchestrator

        orchestrator = SystemOrchestrator(
            config_dir=orchestrator_dirs["config"],
        )

        assert orchestrator.is_ready is False

    @pytest.mark.unit
    def test_is_ready_true_after_init(self, populated_config: dict[str, Path]) -> None:
        from src.configuration.system_orchestrator import SystemOrchestrator

        orchestrator = SystemOrchestrator(
            config_dir=populated_config["config"],
            rules_dir=populated_config["rules"],
            logs_dir=populated_config["logs"],
        )

        orchestrator.initialize(skip_mqtt=True, skip_ollama=True)

        assert orchestrator.is_ready is True
        orchestrator.shutdown()


class TestShutdown:
    @pytest.mark.unit
    def test_shutdown_changes_state(self, populated_config: dict[str, Path]) -> None:
        from src.configuration.system_orchestrator import (
            SystemOrchestrator,
            SystemState,
        )

        orchestrator = SystemOrchestrator(
            config_dir=populated_config["config"],
            rules_dir=populated_config["rules"],
            logs_dir=populated_config["logs"],
        )

        orchestrator.initialize(skip_mqtt=True, skip_ollama=True)
        orchestrator.shutdown()

        assert orchestrator.state == SystemState.STOPPED

    @pytest.mark.unit
    def test_shutdown_idempotent(self, populated_config: dict[str, Path]) -> None:
        from src.configuration.system_orchestrator import SystemOrchestrator

        orchestrator = SystemOrchestrator(
            config_dir=populated_config["config"],
            rules_dir=populated_config["rules"],
            logs_dir=populated_config["logs"],
        )

        orchestrator.initialize(skip_mqtt=True, skip_ollama=True)

        result1 = orchestrator.shutdown()
        result2 = orchestrator.shutdown()

        assert result1 is True
        assert result2 is True


class TestGetSystemStatus:
    @pytest.mark.unit
    def test_get_system_status_returns_dict(
        self, populated_config: dict[str, Path]
    ) -> None:
        from src.configuration.system_orchestrator import SystemOrchestrator

        orchestrator = SystemOrchestrator(
            config_dir=populated_config["config"],
            rules_dir=populated_config["rules"],
            logs_dir=populated_config["logs"],
        )

        orchestrator.initialize(skip_mqtt=True, skip_ollama=True)

        status = orchestrator.get_system_status()

        assert "state" in status
        assert "is_ready" in status
        assert "initialization_steps" in status
        assert "components" in status
        orchestrator.shutdown()

    @pytest.mark.unit
    def test_get_system_status_shows_components(
        self, populated_config: dict[str, Path]
    ) -> None:
        from src.configuration.system_orchestrator import SystemOrchestrator

        orchestrator = SystemOrchestrator(
            config_dir=populated_config["config"],
            rules_dir=populated_config["rules"],
            logs_dir=populated_config["logs"],
        )

        orchestrator.initialize(skip_mqtt=True, skip_ollama=True)

        status = orchestrator.get_system_status()
        components = status["components"]

        assert components["config_manager"] is True
        assert components["logging_manager"] is True
        assert components["rule_manager"] is True
        assert components["device_registry"] is True
        assert components["fuzzy_pipeline"] is True
        orchestrator.shutdown()


class TestInitializationStep:
    @pytest.mark.unit
    def test_initialization_step_creation(self) -> None:
        from src.configuration.system_orchestrator import InitializationStep

        step = InitializationStep(
            name="test_step",
            description="Test step description",
        )

        assert step.name == "test_step"
        assert step.description == "Test step description"
        assert step.completed is False
        assert step.error is None

    @pytest.mark.unit
    def test_initialization_step_with_error(self) -> None:
        from src.configuration.system_orchestrator import InitializationStep

        step = InitializationStep(
            name="failed_step",
            description="Failed step",
            completed=False,
            error="Something went wrong",
        )

        assert step.completed is False
        assert step.error == "Something went wrong"


class TestReinitializeAfterStop:
    @pytest.mark.unit
    def test_can_reinitialize_after_shutdown(
        self, populated_config: dict[str, Path]
    ) -> None:
        from src.configuration.system_orchestrator import (
            SystemOrchestrator,
            SystemState,
        )

        orchestrator = SystemOrchestrator(
            config_dir=populated_config["config"],
            rules_dir=populated_config["rules"],
            logs_dir=populated_config["logs"],
        )

        orchestrator.initialize(skip_mqtt=True, skip_ollama=True)
        orchestrator.shutdown()

        result = orchestrator.initialize(skip_mqtt=True, skip_ollama=True)

        assert result is True
        assert orchestrator.state == SystemState.READY
        orchestrator.shutdown()
