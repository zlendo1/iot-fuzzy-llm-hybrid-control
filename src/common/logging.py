from __future__ import annotations

import json
import logging
import logging.handlers
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_DEFAULT_LOG_LEVEL = "INFO"
_DEFAULT_LOG_DIR = "logs"
_DEFAULT_LOG_FORMAT_CONSOLE = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
_BACKUP_COUNT = 5

_configured = False


class JSONFormatter(logging.Formatter):
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


def setup_logging(
    log_level: str | None = None,
    log_dir: str | Path | None = None,
    json_output: bool = True,
    console_output: bool = True,
) -> None:
    global _configured
    if _configured:
        return

    level = getattr(logging, (log_level or _DEFAULT_LOG_LEVEL).upper(), logging.INFO)
    log_path = Path(log_dir or _DEFAULT_LOG_DIR)
    log_path.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers.clear()

    if json_output:
        json_file = log_path / "system.json"
        file_handler = logging.handlers.RotatingFileHandler(
            json_file,
            maxBytes=_MAX_BYTES,
            backupCount=_BACKUP_COUNT,
            encoding="utf-8",
        )
        file_handler.setFormatter(JSONFormatter())
        file_handler.setLevel(level)
        root_logger.addHandler(file_handler)

    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter(_DEFAULT_LOG_FORMAT_CONSOLE))
        console_handler.setLevel(level)
        root_logger.addHandler(console_handler)

    _configured = True


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
