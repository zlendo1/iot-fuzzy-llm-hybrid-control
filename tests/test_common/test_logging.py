import logging
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest


@pytest.fixture
def reset_logging() -> Generator[None, Any, None]:
    yield
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(logging.WARNING)

    import src.common.logging as log_module

    log_module._configured = False


@pytest.mark.unit
def test_get_logger_returns_logger() -> None:
    from src.common.logging import get_logger

    logger = get_logger("test.module")

    assert isinstance(logger, logging.Logger)
    assert logger.name == "test.module"


@pytest.mark.unit
def test_setup_logging_creates_log_directory(
    tmp_path: Path, reset_logging: None
) -> None:
    from src.common.logging import setup_logging

    log_dir = tmp_path / "logs"
    setup_logging(log_dir=log_dir)

    assert log_dir.exists()


@pytest.mark.unit
def test_setup_logging_creates_json_file(tmp_path: Path, reset_logging: None) -> None:
    from src.common.logging import get_logger, setup_logging

    log_dir = tmp_path / "logs"
    setup_logging(log_dir=log_dir, console_output=False)

    logger = get_logger("test")
    logger.info("test message")

    json_file = log_dir / "system.json"
    assert json_file.exists()

    content = json_file.read_text()
    assert "test message" in content


@pytest.mark.unit
def test_setup_logging_only_runs_once(tmp_path: Path, reset_logging: None) -> None:
    from src.common.logging import setup_logging

    log_dir1 = tmp_path / "logs1"
    log_dir2 = tmp_path / "logs2"

    setup_logging(log_dir=log_dir1, console_output=False)
    setup_logging(log_dir=log_dir2, console_output=False)

    assert log_dir1.exists()
    assert not log_dir2.exists()
