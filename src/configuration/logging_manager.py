"""LoggingManager - Centralized structured logging with rotation and retention."""

from __future__ import annotations

import json
import logging
import logging.handlers
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any


class LogCategory(Enum):
    SYSTEM = "system"
    COMMANDS = "commands"
    SENSORS = "sensors"
    ERRORS = "errors"
    RULES = "rules"


class StructuredFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_data: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        extra_data = getattr(record, "extra_data", None)
        if extra_data is not None:
            log_data["data"] = extra_data

        return json.dumps(log_data, default=str)


@dataclass
class LoggingManager:
    log_dir: Path = field(default_factory=lambda: Path("logs"))
    log_level: str = "INFO"
    max_bytes: int = 104857600
    backup_count: int = 5
    retention_days: int = 30
    json_format: bool = True
    console_output: bool = True

    _handlers: dict[str, logging.Handler] = field(default_factory=dict, repr=False)
    _loggers: dict[str, logging.Logger] = field(default_factory=dict, repr=False)
    _lock: threading.RLock = field(default_factory=threading.RLock, repr=False)
    _initialized: bool = field(default=False, init=False, repr=False)

    _instance: LoggingManager | None = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        self.log_dir = Path(self.log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._setup_handlers()
        self._initialized = True

    @classmethod
    def get_instance(
        cls,
        log_dir: Path | str | None = None,
        log_level: str = "INFO",
        **kwargs: Any,
    ) -> LoggingManager:
        if cls._instance is None:
            cls._instance = cls(
                log_dir=Path(log_dir) if log_dir else Path("logs"),
                log_level=log_level,
                **kwargs,
            )
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        if cls._instance is not None:
            cls._instance.shutdown()
        cls._instance = None

    def _get_level(self) -> int:
        return getattr(logging, self.log_level.upper(), logging.INFO)

    def _setup_handlers(self) -> None:
        level = self._get_level()

        for category in LogCategory:
            log_file = self.log_dir / f"{category.value}.json"
            handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=self.max_bytes,
                backupCount=self.backup_count,
                encoding="utf-8",
            )
            handler.setLevel(level)
            handler.setFormatter(StructuredFormatter())
            self._handlers[category.value] = handler

        if self.console_output:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(level)
            console_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
            console_handler.setFormatter(logging.Formatter(console_format))
            self._handlers["console"] = console_handler

    def get_logger(
        self, name: str, category: LogCategory = LogCategory.SYSTEM
    ) -> logging.Logger:
        with self._lock:
            cache_key = f"{name}:{category.value}"
            if cache_key in self._loggers:
                return self._loggers[cache_key]

            logger = logging.getLogger(name)
            logger.setLevel(self._get_level())
            logger.propagate = False

            for existing_handler in logger.handlers[:]:
                logger.removeHandler(existing_handler)

            category_handler = self._handlers.get(category.value)
            if category_handler:
                logger.addHandler(category_handler)

            error_handler = self._handlers.get(LogCategory.ERRORS.value)
            if error_handler and category != LogCategory.ERRORS:

                class ErrorFilter(logging.Filter):
                    def filter(self, record: logging.LogRecord) -> bool:
                        return record.levelno >= logging.ERROR

                error_handler_copy = logging.handlers.RotatingFileHandler(
                    self.log_dir / "errors.json",
                    maxBytes=self.max_bytes,
                    backupCount=self.backup_count,
                    encoding="utf-8",
                )
                error_handler_copy.setLevel(logging.ERROR)
                error_handler_copy.setFormatter(StructuredFormatter())
                error_handler_copy.addFilter(ErrorFilter())
                logger.addHandler(error_handler_copy)

            console_handler = self._handlers.get("console")
            if console_handler:
                logger.addHandler(console_handler)

            self._loggers[cache_key] = logger
            return logger

    def log_system_event(
        self,
        message: str,
        level: str = "INFO",
        **extra: Any,
    ) -> None:
        logger = self.get_logger("system", LogCategory.SYSTEM)
        log_level = getattr(logging, level.upper(), logging.INFO)
        logger.log(log_level, message, extra={"extra_data": extra} if extra else {})

    def log_command(
        self,
        command_id: str,
        device_id: str,
        action: str,
        success: bool,
        **extra: Any,
    ) -> None:
        logger = self.get_logger("commands", LogCategory.COMMANDS)
        data = {
            "command_id": command_id,
            "device_id": device_id,
            "action": action,
            "success": success,
            **extra,
        }
        level = logging.INFO if success else logging.WARNING
        logger.log(
            level,
            f"Command {command_id}: {action} on {device_id}",
            extra={"extra_data": data},
        )

    def log_sensor_reading(
        self,
        sensor_id: str,
        value: float,
        unit: str | None = None,
        **extra: Any,
    ) -> None:
        logger = self.get_logger("sensors", LogCategory.SENSORS)
        data = {
            "sensor_id": sensor_id,
            "value": value,
            "unit": unit,
            **extra,
        }
        logger.info(
            f"Sensor {sensor_id}: {value} {unit or ''}", extra={"extra_data": data}
        )

    def log_rule_evaluation(
        self,
        rule_id: str,
        matched: bool,
        triggered: bool = False,
        **extra: Any,
    ) -> None:
        logger = self.get_logger("rules", LogCategory.RULES)
        data = {
            "rule_id": rule_id,
            "matched": matched,
            "triggered": triggered,
            **extra,
        }
        logger.info(
            f"Rule {rule_id}: matched={matched}, triggered={triggered}",
            extra={"extra_data": data},
        )

    def log_error(
        self,
        message: str,
        exception: Exception | None = None,
        **extra: Any,
    ) -> None:
        logger = self.get_logger("errors", LogCategory.ERRORS)
        data = extra.copy()
        if exception:
            data["exception_type"] = type(exception).__name__
            data["exception_message"] = str(exception)
        logger.error(
            message, exc_info=exception is not None, extra={"extra_data": data}
        )

    def cleanup_old_logs(self) -> int:
        cutoff_time = time.time() - (self.retention_days * 24 * 60 * 60)
        removed_count = 0

        for log_file in self.log_dir.glob("*.json*"):
            try:
                file_mtime = log_file.stat().st_mtime
                if file_mtime < cutoff_time:
                    log_file.unlink()
                    removed_count += 1
            except OSError:
                pass

        return removed_count

    def get_log_file(self, category: LogCategory) -> Path:
        return self.log_dir / f"{category.value}.json"

    def get_log_files(self) -> dict[str, Path]:
        return {category.value: self.get_log_file(category) for category in LogCategory}

    def set_level(self, level: str) -> None:
        with self._lock:
            self.log_level = level
            log_level = self._get_level()

            for handler in self._handlers.values():
                handler.setLevel(log_level)

            for logger in self._loggers.values():
                logger.setLevel(log_level)

    def shutdown(self) -> None:
        with self._lock:
            for handler in self._handlers.values():
                handler.close()
            self._handlers.clear()

            for logger in self._loggers.values():
                logger.handlers.clear()
            self._loggers.clear()

            self._initialized = False

    @property
    def is_initialized(self) -> bool:
        return self._initialized
