"""Application - Main event loop coordinating all system layers."""

from __future__ import annotations

import signal
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any

from src.common.logging import get_logger
from src.configuration.system_orchestrator import SystemOrchestrator

if TYPE_CHECKING:
    from src.control_reasoning.command_generator import DeviceCommand
    from src.device_interface.messages import (
        DeviceCommand as MQTTDeviceCommand,
    )
    from src.device_interface.messages import (
        SensorReading,
    )

logger = get_logger(__name__)


class ApplicationState(Enum):
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"


@dataclass
class ApplicationConfig:
    config_dir: Path = field(default_factory=lambda: Path("config"))
    rules_dir: Path = field(default_factory=lambda: Path("rules"))
    logs_dir: Path = field(default_factory=lambda: Path("logs"))
    skip_mqtt: bool = False
    skip_ollama: bool = False
    evaluation_interval: float = 1.0


@dataclass
class ApplicationStats:
    readings_processed: int = 0
    rules_evaluated: int = 0
    commands_generated: int = 0
    commands_sent: int = 0
    errors: int = 0
    start_time: float | None = None

    def to_dict(self) -> dict[str, Any]:
        uptime = time.time() - self.start_time if self.start_time else 0
        return {
            "readings_processed": self.readings_processed,
            "rules_evaluated": self.rules_evaluated,
            "commands_generated": self.commands_generated,
            "commands_sent": self.commands_sent,
            "errors": self.errors,
            "uptime_seconds": uptime,
        }


class Application:
    def __init__(self, config: ApplicationConfig | None = None) -> None:
        self._config = config or ApplicationConfig()
        self._orchestrator = SystemOrchestrator(
            config_dir=self._config.config_dir,
            rules_dir=self._config.rules_dir,
            logs_dir=self._config.logs_dir,
        )
        self._state = ApplicationState.STOPPED
        self._stats = ApplicationStats()
        self._stop_event = threading.Event()
        self._eval_thread: threading.Thread | None = None
        self._lock = threading.RLock()

    @property
    def state(self) -> ApplicationState:
        return self._state

    @property
    def stats(self) -> ApplicationStats:
        return self._stats

    @property
    def orchestrator(self) -> SystemOrchestrator:
        return self._orchestrator

    @property
    def is_running(self) -> bool:
        return self._state == ApplicationState.RUNNING

    def start(self) -> bool:
        with self._lock:
            if self._state != ApplicationState.STOPPED:
                logger.warning("Application already running or starting")
                return False

            self._state = ApplicationState.STARTING
            logger.info("Application starting...")

            if not self._orchestrator.initialize(
                skip_mqtt=self._config.skip_mqtt,
                skip_ollama=self._config.skip_ollama,
            ):
                self._state = ApplicationState.STOPPED
                logger.error("Failed to initialize system orchestrator")
                return False

            self._wire_components()

            self._stats = ApplicationStats(start_time=time.time())

            self._stop_event.clear()
            self._eval_thread = threading.Thread(
                target=self._evaluation_loop,
                name="EvaluationLoop",
                daemon=True,
            )
            self._eval_thread.start()

            self._state = ApplicationState.RUNNING
            logger.info("Application started successfully")
            return True

    def _wire_components(self) -> None:
        if self._orchestrator.rule_manager and self._orchestrator._rule_pipeline:
            for rule in self._orchestrator.rule_manager.get_enabled_rules():
                self._orchestrator._rule_pipeline.add_rule(rule)
            logger.info(
                "Loaded rules into pipeline",
                extra={
                    "count": len(self._orchestrator.rule_manager.get_enabled_rules())
                },
            )

        if self._orchestrator._mqtt_manager and self._orchestrator.fuzzy_pipeline:
            self._orchestrator._mqtt_manager.add_reading_callback(
                self._on_sensor_reading
            )
            logger.debug("Wired MQTT callback to fuzzy pipeline")

    def _on_sensor_reading(self, reading: SensorReading) -> None:
        try:
            if not self._orchestrator.fuzzy_pipeline:
                return

            sensor_type = self._get_sensor_type(reading.sensor_id)
            if not sensor_type:
                logger.warning(
                    "Unknown sensor type",
                    extra={"sensor_id": reading.sensor_id},
                )
                return

            _description = self._orchestrator.fuzzy_pipeline.process_reading(
                reading=reading,
                sensor_type=sensor_type,
            )
            self._stats.readings_processed += 1

        except Exception as e:
            self._stats.errors += 1
            logger.exception(
                "Error processing sensor reading",
                extra={"sensor_id": reading.sensor_id, "error": str(e)},
            )

    def _get_sensor_type(self, sensor_id: str) -> str | None:
        if not self._orchestrator.device_registry:
            return None

        for sensor in self._orchestrator.device_registry.sensors():
            if sensor.id == sensor_id:
                return sensor.device_class
        return None

    def _evaluation_loop(self) -> None:
        logger.info("Evaluation loop started")
        while not self._stop_event.is_set():
            try:
                self._evaluate_and_execute()
            except Exception as e:
                self._stats.errors += 1
                logger.exception("Error in evaluation loop", extra={"error": str(e)})

            self._stop_event.wait(timeout=self._config.evaluation_interval)

        logger.info("Evaluation loop stopped")

    def _evaluate_and_execute(self) -> None:
        if not self._orchestrator.is_ready:
            return

        fuzzy_pipeline = self._orchestrator.fuzzy_pipeline
        rule_pipeline = self._orchestrator._rule_pipeline

        if not fuzzy_pipeline or not rule_pipeline:
            return

        current_state = fuzzy_pipeline.get_current_state()
        if not current_state:
            return

        result = rule_pipeline.process(current_state)
        self._stats.rules_evaluated += len(result.evaluations)
        self._stats.commands_generated += len(result.validated_commands)

        for command in result.validated_commands:
            self._send_command(command)

        if result.has_errors:
            for error in result.errors:
                logger.warning("Pipeline error", extra={"error": error})

    def _send_command(self, command: DeviceCommand) -> None:
        if not self._orchestrator._mqtt_manager:
            logger.warning(
                "Cannot send command: MQTT manager not available",
                extra={"command_id": command.command_id},
            )
            return

        try:
            mqtt_command = self._convert_to_mqtt_command(command)
            success = self._orchestrator._mqtt_manager.send_command(mqtt_command)
            if success:
                self._stats.commands_sent += 1
                logger.info(
                    "Command sent",
                    extra={
                        "command_id": command.command_id,
                        "device_id": command.device_id,
                        "command_type": command.command_type,
                    },
                )
            else:
                self._stats.errors += 1
                logger.warning(
                    "Failed to send command",
                    extra={"command_id": command.command_id},
                )
        except Exception as e:
            self._stats.errors += 1
            logger.exception(
                "Error sending command",
                extra={"command_id": command.command_id, "error": str(e)},
            )

    def _convert_to_mqtt_command(self, command: DeviceCommand) -> MQTTDeviceCommand:
        from src.device_interface.messages import CommandType
        from src.device_interface.messages import DeviceCommand as MQTTDeviceCommand

        command_type_str = command.command_type.lower()
        try:
            command_type = CommandType(command_type_str)
        except ValueError:
            command_type = CommandType.SET

        return MQTTDeviceCommand(
            device_id=command.device_id,
            command_type=command_type,
            parameters=command.parameters,
            command_id=command.command_id,
            source="rule_engine",
        )

    def stop(self) -> bool:
        with self._lock:
            if self._state == ApplicationState.STOPPED:
                return True

            self._state = ApplicationState.STOPPING
            logger.info("Application stopping...")

            self._stop_event.set()

            if self._eval_thread and self._eval_thread.is_alive():
                self._eval_thread.join(timeout=5.0)

            self._orchestrator.shutdown()

            self._state = ApplicationState.STOPPED
            logger.info("Application stopped")
            return True

    def get_status(self) -> dict[str, Any]:
        return {
            "state": self._state.value,
            "is_running": self.is_running,
            "stats": self._stats.to_dict(),
            "orchestrator": self._orchestrator.get_system_status(),
        }

    def run_forever(self) -> None:
        if not self.start():
            raise RuntimeError("Failed to start application")

        def signal_handler(signum: int, _frame: object) -> None:
            logger.info(f"Received signal {signum}, initiating shutdown...")
            self.stop()

        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)

        try:
            while self.is_running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
            self.stop()


def create_application(
    config_dir: Path | str = Path("config"),
    rules_dir: Path | str = Path("rules"),
    logs_dir: Path | str = Path("logs"),
    skip_mqtt: bool = False,
    skip_ollama: bool = False,
) -> Application:
    config = ApplicationConfig(
        config_dir=Path(config_dir),
        rules_dir=Path(rules_dir),
        logs_dir=Path(logs_dir),
        skip_mqtt=skip_mqtt,
        skip_ollama=skip_ollama,
    )
    return Application(config)
