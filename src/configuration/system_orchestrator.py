"""SystemOrchestrator - Layer coordinator managing full system lifecycle."""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any

from src.common.exceptions import ConfigurationError
from src.common.logging import get_logger
from src.configuration.config_manager import ConfigurationManager
from src.configuration.logging_manager import LoggingManager
from src.configuration.rule_manager import RuleManager

if TYPE_CHECKING:
    from src.control_reasoning.rule_pipeline import RuleProcessingPipeline
    from src.data_processing.fuzzy_pipeline import FuzzyProcessingPipeline
    from src.device_interface.communication_manager import MQTTCommunicationManager
    from src.device_interface.device_monitor import DeviceMonitor
    from src.device_interface.registry import DeviceRegistry

logger = get_logger(__name__)


class SystemState(Enum):
    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class InitializationStep:
    name: str
    description: str
    completed: bool = False
    error: str | None = None


@dataclass
class SystemOrchestrator:
    config_dir: Path = field(default_factory=lambda: Path("config"))
    rules_dir: Path = field(default_factory=lambda: Path("rules"))
    logs_dir: Path = field(default_factory=lambda: Path("logs"))

    _state: SystemState = field(default=SystemState.UNINITIALIZED, init=False)
    _lock: threading.RLock = field(default_factory=threading.RLock, repr=False)

    _config_manager: ConfigurationManager | None = field(
        default=None, init=False, repr=False
    )
    _logging_manager: LoggingManager | None = field(
        default=None, init=False, repr=False
    )
    _rule_manager: RuleManager | None = field(default=None, init=False, repr=False)

    _device_registry: DeviceRegistry | None = field(
        default=None, init=False, repr=False
    )
    _mqtt_manager: MQTTCommunicationManager | None = field(
        default=None, init=False, repr=False
    )
    _device_monitor: DeviceMonitor | None = field(default=None, init=False, repr=False)
    _fuzzy_pipeline: FuzzyProcessingPipeline | None = field(
        default=None, init=False, repr=False
    )
    _rule_pipeline: RuleProcessingPipeline | None = field(
        default=None, init=False, repr=False
    )

    _init_steps: list[InitializationStep] = field(
        default_factory=list, init=False, repr=False
    )

    def __post_init__(self) -> None:
        self.config_dir = Path(self.config_dir)
        self.rules_dir = Path(self.rules_dir)
        self.logs_dir = Path(self.logs_dir)

    @property
    def state(self) -> SystemState:
        return self._state

    @property
    def is_ready(self) -> bool:
        return self._state in (SystemState.READY, SystemState.RUNNING)

    @property
    def initialization_steps(self) -> list[InitializationStep]:
        return list(self._init_steps)

    @property
    def config_manager(self) -> ConfigurationManager | None:
        return self._config_manager

    @property
    def logging_manager(self) -> LoggingManager | None:
        return self._logging_manager

    @property
    def rule_manager(self) -> RuleManager | None:
        return self._rule_manager

    @property
    def device_registry(self) -> DeviceRegistry | None:
        return self._device_registry

    @property
    def fuzzy_pipeline(self) -> FuzzyProcessingPipeline | None:
        return self._fuzzy_pipeline

    @property
    def rule_pipeline(self) -> RuleProcessingPipeline | None:
        return self._rule_pipeline

    def _add_step(self, name: str, description: str) -> InitializationStep:
        step = InitializationStep(name=name, description=description)
        self._init_steps.append(step)
        return step

    def _complete_step(
        self, step: InitializationStep, error: str | None = None
    ) -> None:
        step.completed = error is None
        step.error = error
        if error:
            logger.error(
                f"Initialization step failed: {step.name}",
                extra={"step": step.name, "error": error},
            )
        else:
            logger.info(
                f"Initialization step completed: {step.name}",
                extra={"step": step.name},
            )

    def initialize(self, skip_mqtt: bool = False, skip_ollama: bool = False) -> bool:
        with self._lock:
            if self._state not in (
                SystemState.UNINITIALIZED,
                SystemState.STOPPED,
                SystemState.ERROR,
            ):
                logger.warning("System already initialized or initializing")
                return False

            self._state = SystemState.INITIALIZING
            self._init_steps.clear()

            try:
                if not self._step_01_load_config():
                    self._state = SystemState.ERROR
                    return False

                if not self._step_02_init_logging():
                    self._state = SystemState.ERROR
                    return False

                if not self._step_03_populate_registry():
                    self._state = SystemState.ERROR
                    return False

                if not skip_mqtt and not self._step_04_connect_mqtt():
                    self._state = SystemState.ERROR
                    return False

                if not skip_ollama and not self._step_05_verify_ollama():
                    pass

                if not self._step_06_load_membership_functions():
                    self._state = SystemState.ERROR
                    return False

                if not self._step_07_load_rules():
                    self._state = SystemState.ERROR
                    return False

                if not skip_ollama and not self._step_07b_init_rule_pipeline():
                    pass

                if not skip_mqtt and not self._step_08_start_device_monitor():
                    self._state = SystemState.ERROR
                    return False

                self._step_09_init_interfaces()

                self._step_10_enter_ready_state()

                self._state = SystemState.READY
                logger.info("System initialization completed successfully")
                return True

            except Exception as e:
                self._state = SystemState.ERROR
                logger.error(
                    "System initialization failed",
                    extra={"error": str(e)},
                )
                return False

    def _step_01_load_config(self) -> bool:
        step = self._add_step(
            "load_config", "Load and validate all configuration files"
        )
        try:
            self._config_manager = ConfigurationManager(
                config_dir=self.config_dir,
            )
            self._config_manager.get_all_configs()
            self._complete_step(step)
            return True
        except Exception as e:
            self._complete_step(step, str(e))
            return False

    def _step_02_init_logging(self) -> bool:
        step = self._add_step("init_logging", "Initialize LoggingManager")
        try:
            log_level = "INFO"
            if self._config_manager:
                log_level = self._config_manager.get_config(
                    "system_config", "logging", "level", default="INFO"
                )

            self._logging_manager = LoggingManager(
                log_dir=self.logs_dir,
                log_level=log_level,
            )
            self._complete_step(step)
            return True
        except Exception as e:
            self._complete_step(step, str(e))
            return False

    def _step_03_populate_registry(self) -> bool:
        step = self._add_step(
            "populate_registry", "Populate DeviceRegistry from device configuration"
        )
        try:
            from src.common.config import ConfigLoader
            from src.device_interface.registry import DeviceRegistry

            if not self._config_manager:
                raise ConfigurationError("ConfigurationManager not initialized")

            config_loader = ConfigLoader(config_dir=self.config_dir)
            self._device_registry = DeviceRegistry(config_loader=config_loader)
            self._device_registry.load("devices.json")

            self._complete_step(step)
            return True
        except Exception as e:
            self._complete_step(step, str(e))
            return False

    def _step_04_connect_mqtt(self) -> bool:
        step = self._add_step(
            "connect_mqtt", "Connect MQTT client and subscribe to sensor topics"
        )
        try:
            from src.common.config import ConfigLoader
            from src.device_interface.communication_manager import (
                MQTTCommunicationManager,
            )

            if not self._config_manager:
                raise ConfigurationError("Required components not initialized")

            config_loader = ConfigLoader(config_dir=self.config_dir)
            self._mqtt_manager = MQTTCommunicationManager(
                config_loader=config_loader,
                mqtt_config_file="mqtt_config.json",
                devices_config_file="devices.json",
            )
            self._mqtt_manager.start()

            self._complete_step(step)
            return True
        except Exception as e:
            self._complete_step(step, str(e))
            return False

    def _step_05_verify_ollama(self) -> bool:
        step = self._add_step(
            "verify_ollama", "Verify Ollama connectivity and model availability"
        )
        try:
            from src.control_reasoning.ollama_client import OllamaClient, OllamaConfig

            if not self._config_manager:
                raise ConfigurationError("ConfigurationManager not initialized")

            llm_config = self._config_manager.llm_config
            ollama_config = OllamaConfig.from_dict(llm_config)
            client = OllamaClient(ollama_config)

            if client.is_healthy():
                self._complete_step(step)
                return True
            else:
                self._complete_step(step, "Ollama health check failed")
                return False
        except Exception as e:
            self._complete_step(step, str(e))
            return False

    def _step_06_load_membership_functions(self) -> bool:
        step = self._add_step(
            "load_membership_functions", "Load and validate membership functions"
        )
        try:
            from src.data_processing.fuzzy_pipeline import FuzzyProcessingPipeline

            if not self._config_manager:
                raise ConfigurationError("ConfigurationManager not initialized")

            mf_dir = self.config_dir / "membership_functions"
            schema_path = (
                self.config_dir / "schemas" / "membership_functions.schema.json"
            )

            self._fuzzy_pipeline = FuzzyProcessingPipeline(
                config_dir=mf_dir,
                schema_path=schema_path if schema_path.exists() else None,
            )
            self._fuzzy_pipeline.initialize()

            self._complete_step(step)
            return True
        except Exception as e:
            self._complete_step(step, str(e))
            return False

    def _step_07_load_rules(self) -> bool:
        step = self._add_step("load_rules", "Load all persisted rules and index them")
        try:
            rules_file = self.rules_dir / "active_rules.json"
            self._rule_manager = RuleManager(
                rules_file=rules_file,
                auto_save=True,
            )

            self._complete_step(step)
            return True
        except Exception as e:
            self._complete_step(step, str(e))
            return False

    def _step_07b_init_rule_pipeline(self) -> bool:
        step = self._add_step("init_rule_pipeline", "Initialize RuleProcessingPipeline")
        try:
            from src.control_reasoning.ollama_client import OllamaConfig
            from src.control_reasoning.rule_pipeline import (
                PipelineConfig,
                RuleProcessingPipeline,
            )

            if not self._config_manager:
                raise ConfigurationError("ConfigurationManager not initialized")

            llm_config = self._config_manager.llm_config
            ollama_config = OllamaConfig.from_dict(llm_config)

            pipeline_config = PipelineConfig(ollama_config=ollama_config)
            self._rule_pipeline = RuleProcessingPipeline(
                config=pipeline_config,
                registry=self._device_registry,
            )
            self._rule_pipeline.initialize()

            self._complete_step(step)
            return True
        except Exception as e:
            self._complete_step(step, str(e))
            return False

    def _step_08_start_device_monitor(self) -> bool:
        step = self._add_step(
            "start_device_monitor",
            "Start DeviceMonitor for tracking device availability",
        )
        try:
            from src.device_interface.device_monitor import DeviceMonitor

            if not self._device_registry:
                raise ConfigurationError("DeviceRegistry not initialized")

            self._device_monitor = DeviceMonitor()
            for device in self._device_registry:
                self._device_monitor.register_device(device.id)
            self._device_monitor.start_monitoring()

            self._complete_step(step)
            return True
        except Exception as e:
            self._complete_step(step, str(e))
            return False

    def _step_09_init_interfaces(self) -> bool:
        step = self._add_step("init_interfaces", "Initialize user interfaces")
        self._complete_step(step)
        return True

    def _step_10_enter_ready_state(self) -> bool:
        step = self._add_step(
            "enter_ready", "Enter ready state and begin normal operation"
        )
        if self._logging_manager:
            self._logging_manager.log_system_event(
                "System entered ready state",
                level="INFO",
            )
        self._complete_step(step)
        return True

    def shutdown(self) -> bool:
        with self._lock:
            if self._state == SystemState.STOPPED:
                return True

            self._state = SystemState.STOPPING
            logger.info("System shutdown initiated")

            if self._device_monitor:
                try:
                    self._device_monitor.stop_monitoring()
                except Exception as e:
                    logger.warning(f"Error stopping device monitor: {e}")

            if self._mqtt_manager:
                try:
                    self._mqtt_manager.stop()
                except Exception as e:
                    logger.warning(f"Error stopping MQTT manager: {e}")

            if self._rule_pipeline:
                try:
                    self._rule_pipeline.close()
                except Exception as e:
                    logger.warning(f"Error closing rule pipeline: {e}")

            if self._logging_manager:
                self._logging_manager.log_system_event(
                    "System shutdown completed",
                    level="INFO",
                )
                self._logging_manager.shutdown()

            self._state = SystemState.STOPPED
            logger.info("System shutdown completed")
            return True

    def get_system_status(self) -> dict[str, Any]:
        return {
            "state": self._state.value,
            "is_ready": self.is_ready,
            "initialization_steps": [
                {
                    "name": step.name,
                    "description": step.description,
                    "completed": step.completed,
                    "error": step.error,
                }
                for step in self._init_steps
            ],
            "components": {
                "config_manager": self._config_manager is not None,
                "logging_manager": self._logging_manager is not None,
                "rule_manager": self._rule_manager is not None,
                "device_registry": self._device_registry is not None,
                "fuzzy_pipeline": self._fuzzy_pipeline is not None,
                "mqtt_manager": self._mqtt_manager is not None,
                "device_monitor": self._device_monitor is not None,
            },
        }
