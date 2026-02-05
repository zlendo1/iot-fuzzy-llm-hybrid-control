import json
import logging
import threading
import time
from pathlib import Path

import pytest


@pytest.fixture
def log_dir(tmp_path: Path) -> Path:
    logs_path = tmp_path / "logs"
    logs_path.mkdir()
    return logs_path


class TestLoggingManagerInit:
    @pytest.mark.unit
    def test_init_creates_log_directory(self, tmp_path: Path) -> None:
        from src.configuration.logging_manager import LoggingManager

        log_dir = tmp_path / "new_logs"

        manager = LoggingManager(log_dir=log_dir)

        assert log_dir.exists()
        manager.shutdown()

    @pytest.mark.unit
    def test_init_sets_default_level(self, log_dir: Path) -> None:
        from src.configuration.logging_manager import LoggingManager

        manager = LoggingManager(log_dir=log_dir)

        assert manager.log_level == "INFO"
        manager.shutdown()

    @pytest.mark.unit
    def test_init_sets_custom_level(self, log_dir: Path) -> None:
        from src.configuration.logging_manager import LoggingManager

        manager = LoggingManager(log_dir=log_dir, log_level="DEBUG")

        assert manager.log_level == "DEBUG"
        manager.shutdown()

    @pytest.mark.unit
    def test_is_initialized(self, log_dir: Path) -> None:
        from src.configuration.logging_manager import LoggingManager

        manager = LoggingManager(log_dir=log_dir)

        assert manager.is_initialized is True
        manager.shutdown()
        assert manager.is_initialized is False


class TestSingletonPattern:
    @pytest.mark.unit
    def test_get_instance_returns_same_instance(self, log_dir: Path) -> None:
        from src.configuration.logging_manager import LoggingManager

        LoggingManager.reset_instance()

        instance1 = LoggingManager.get_instance(log_dir=log_dir)
        instance2 = LoggingManager.get_instance()

        assert instance1 is instance2
        LoggingManager.reset_instance()

    @pytest.mark.unit
    def test_reset_instance_clears_singleton(self, log_dir: Path) -> None:
        from src.configuration.logging_manager import LoggingManager

        LoggingManager.reset_instance()

        instance1 = LoggingManager.get_instance(log_dir=log_dir)
        LoggingManager.reset_instance()
        instance2 = LoggingManager.get_instance(log_dir=log_dir)

        assert instance1 is not instance2
        LoggingManager.reset_instance()


class TestGetLogger:
    @pytest.mark.unit
    def test_get_logger_returns_logger(self, log_dir: Path) -> None:
        from src.configuration.logging_manager import LogCategory, LoggingManager

        manager = LoggingManager(log_dir=log_dir, console_output=False)

        logger = manager.get_logger("test", LogCategory.SYSTEM)

        assert isinstance(logger, logging.Logger)
        assert logger.name == "test"
        manager.shutdown()

    @pytest.mark.unit
    def test_get_logger_caches_logger(self, log_dir: Path) -> None:
        from src.configuration.logging_manager import LogCategory, LoggingManager

        manager = LoggingManager(log_dir=log_dir, console_output=False)

        logger1 = manager.get_logger("test", LogCategory.SYSTEM)
        logger2 = manager.get_logger("test", LogCategory.SYSTEM)

        assert logger1 is logger2
        manager.shutdown()

    @pytest.mark.unit
    def test_get_logger_different_categories_cached_separately(
        self, log_dir: Path
    ) -> None:
        from src.configuration.logging_manager import LogCategory, LoggingManager

        manager = LoggingManager(log_dir=log_dir, console_output=False)

        logger1 = manager.get_logger("test_a", LogCategory.SYSTEM)
        logger2 = manager.get_logger("test_b", LogCategory.COMMANDS)

        assert logger1.name == "test_a"
        assert logger2.name == "test_b"
        manager.shutdown()


class TestLogSystemEvent:
    @pytest.mark.unit
    def test_log_system_event_writes_to_file(self, log_dir: Path) -> None:
        from src.configuration.logging_manager import LoggingManager

        manager = LoggingManager(log_dir=log_dir, console_output=False)

        manager.log_system_event("System started", level="INFO")

        log_file = log_dir / "system.json"
        for handler in manager._handlers.values():
            handler.flush()

        assert log_file.exists()
        content = log_file.read_text()
        assert "System started" in content
        manager.shutdown()

    @pytest.mark.unit
    def test_log_system_event_with_extra(self, log_dir: Path) -> None:
        from src.configuration.logging_manager import LoggingManager

        manager = LoggingManager(log_dir=log_dir, console_output=False)

        manager.log_system_event("Config loaded", version="1.0.0")

        log_file = log_dir / "system.json"
        for handler in manager._handlers.values():
            handler.flush()

        content = log_file.read_text()
        assert "Config loaded" in content
        manager.shutdown()


class TestLogCommand:
    @pytest.mark.unit
    def test_log_command_writes_to_file(self, log_dir: Path) -> None:
        from src.configuration.logging_manager import LoggingManager

        manager = LoggingManager(log_dir=log_dir, console_output=False)

        manager.log_command(
            command_id="cmd_001",
            device_id="ac_living_room",
            action="turn_on",
            success=True,
        )

        log_file = log_dir / "commands.json"
        for handler in manager._handlers.values():
            handler.flush()

        assert log_file.exists()
        content = log_file.read_text()
        assert "cmd_001" in content
        assert "ac_living_room" in content
        manager.shutdown()

    @pytest.mark.unit
    def test_log_command_with_failure(self, log_dir: Path) -> None:
        from src.configuration.logging_manager import LoggingManager

        manager = LoggingManager(log_dir=log_dir, console_output=False)

        manager.log_command(
            command_id="cmd_002",
            device_id="light_bedroom",
            action="set_brightness",
            success=False,
            reason="Device offline",
        )

        log_file = log_dir / "commands.json"
        for handler in manager._handlers.values():
            handler.flush()

        content = log_file.read_text()
        assert "cmd_002" in content
        manager.shutdown()


class TestLogSensorReading:
    @pytest.mark.unit
    def test_log_sensor_reading_writes_to_file(self, log_dir: Path) -> None:
        from src.configuration.logging_manager import LoggingManager

        manager = LoggingManager(log_dir=log_dir, console_output=False)

        manager.log_sensor_reading(
            sensor_id="temp_living_room",
            value=23.5,
            unit="°C",
        )

        log_file = log_dir / "sensors.json"
        for handler in manager._handlers.values():
            handler.flush()

        assert log_file.exists()
        content = log_file.read_text()
        assert "temp_living_room" in content
        manager.shutdown()


class TestLogRuleEvaluation:
    @pytest.mark.unit
    def test_log_rule_evaluation_writes_to_file(self, log_dir: Path) -> None:
        from src.configuration.logging_manager import LoggingManager

        manager = LoggingManager(log_dir=log_dir, console_output=False)

        manager.log_rule_evaluation(
            rule_id="rule_001",
            matched=True,
            triggered=True,
        )

        log_file = log_dir / "rules.json"
        for handler in manager._handlers.values():
            handler.flush()

        assert log_file.exists()
        content = log_file.read_text()
        assert "rule_001" in content
        manager.shutdown()


class TestLogError:
    @pytest.mark.unit
    def test_log_error_writes_to_file(self, log_dir: Path) -> None:
        from src.configuration.logging_manager import LoggingManager

        manager = LoggingManager(log_dir=log_dir, console_output=False)

        manager.log_error("Something went wrong", component="mqtt")

        log_file = log_dir / "errors.json"
        for handler in manager._handlers.values():
            handler.flush()

        assert log_file.exists()
        content = log_file.read_text()
        assert "Something went wrong" in content
        manager.shutdown()

    @pytest.mark.unit
    def test_log_error_with_exception(self, log_dir: Path) -> None:
        from src.configuration.logging_manager import LoggingManager

        manager = LoggingManager(log_dir=log_dir, console_output=False)

        try:
            raise ValueError("Test error")
        except ValueError as e:
            manager.log_error("Caught exception", exception=e)

        log_file = log_dir / "errors.json"
        for handler in manager._handlers.values():
            handler.flush()

        content = log_file.read_text()
        assert "Caught exception" in content
        manager.shutdown()


class TestLogCategories:
    @pytest.mark.unit
    def test_all_categories_have_files(self, log_dir: Path) -> None:
        from src.configuration.logging_manager import LogCategory, LoggingManager

        manager = LoggingManager(log_dir=log_dir, console_output=False)

        log_files = manager.get_log_files()

        assert len(log_files) == len(LogCategory)
        for category in LogCategory:
            assert category.value in log_files
        manager.shutdown()

    @pytest.mark.unit
    def test_get_log_file(self, log_dir: Path) -> None:
        from src.configuration.logging_manager import LogCategory, LoggingManager

        manager = LoggingManager(log_dir=log_dir)

        log_file = manager.get_log_file(LogCategory.SYSTEM)

        assert log_file == log_dir / "system.json"
        manager.shutdown()


class TestSetLevel:
    @pytest.mark.unit
    def test_set_level_changes_level(self, log_dir: Path) -> None:
        from src.configuration.logging_manager import LoggingManager

        manager = LoggingManager(log_dir=log_dir, log_level="INFO")

        manager.set_level("DEBUG")

        assert manager.log_level == "DEBUG"
        manager.shutdown()


class TestCleanupOldLogs:
    @pytest.mark.unit
    def test_cleanup_removes_old_files(self, log_dir: Path) -> None:
        from src.configuration.logging_manager import LoggingManager

        old_file = log_dir / "old.json"
        old_file.write_text('{"test": true}')
        old_time = time.time() - (40 * 24 * 60 * 60)
        import os

        os.utime(old_file, (old_time, old_time))

        manager = LoggingManager(log_dir=log_dir, retention_days=30)

        removed = manager.cleanup_old_logs()

        assert removed >= 1
        assert not old_file.exists()
        manager.shutdown()

    @pytest.mark.unit
    def test_cleanup_keeps_recent_files(self, log_dir: Path) -> None:
        from src.configuration.logging_manager import LoggingManager

        recent_file = log_dir / "recent.json"
        recent_file.write_text('{"test": true}')

        manager = LoggingManager(log_dir=log_dir, retention_days=30)

        manager.cleanup_old_logs()

        assert recent_file.exists()
        manager.shutdown()


class TestShutdown:
    @pytest.mark.unit
    def test_shutdown_clears_handlers(self, log_dir: Path) -> None:
        from src.configuration.logging_manager import LoggingManager

        manager = LoggingManager(log_dir=log_dir)

        manager.shutdown()

        assert len(manager._handlers) == 0
        assert len(manager._loggers) == 0

    @pytest.mark.unit
    def test_shutdown_marks_not_initialized(self, log_dir: Path) -> None:
        from src.configuration.logging_manager import LoggingManager

        manager = LoggingManager(log_dir=log_dir)

        manager.shutdown()

        assert manager.is_initialized is False


class TestStructuredFormatter:
    @pytest.mark.unit
    def test_formatter_produces_json(self) -> None:
        from src.configuration.logging_manager import StructuredFormatter

        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        output = formatter.format(record)

        parsed = json.loads(output)
        assert parsed["message"] == "Test message"
        assert parsed["level"] == "INFO"
        assert "timestamp" in parsed


class TestThreadSafety:
    @pytest.mark.unit
    def test_concurrent_logging(self, log_dir: Path) -> None:
        from src.configuration.logging_manager import LoggingManager

        manager = LoggingManager(log_dir=log_dir, console_output=False)
        errors: list[Exception] = []

        def log_message(i: int) -> None:
            try:
                manager.log_system_event(f"Message {i}", index=i)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=log_message, args=(i,)) for i in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        manager.shutdown()

    @pytest.mark.unit
    def test_concurrent_get_logger(self, log_dir: Path) -> None:
        from src.configuration.logging_manager import LogCategory, LoggingManager

        manager = LoggingManager(log_dir=log_dir, console_output=False)
        errors: list[Exception] = []
        loggers: list[logging.Logger] = []

        def get_logger() -> None:
            try:
                logger = manager.get_logger("test", LogCategory.SYSTEM)
                loggers.append(logger)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=get_logger) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert all(logger is loggers[0] for logger in loggers)
        manager.shutdown()


class TestLogCategory:
    @pytest.mark.unit
    def test_log_category_values(self) -> None:
        from src.configuration.logging_manager import LogCategory

        assert LogCategory.SYSTEM.value == "system"
        assert LogCategory.COMMANDS.value == "commands"
        assert LogCategory.SENSORS.value == "sensors"
        assert LogCategory.ERRORS.value == "errors"
        assert LogCategory.RULES.value == "rules"
