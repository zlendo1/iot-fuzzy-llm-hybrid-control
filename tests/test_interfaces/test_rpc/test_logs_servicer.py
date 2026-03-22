from __future__ import annotations

import json
import importlib
from collections.abc import Sequence
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock
from typing import Any

from google.protobuf.timestamp_pb2 import Timestamp

from src.interfaces.rpc.generated.logs_pb2 import (
    GetLogCategoriesRequest,
    GetLogEntriesRequest,
    GetLogStatsRequest,
    LogEntry,
)

LogsServicer = importlib.import_module(
    "src.interfaces.rpc.servicers.logs_servicer"
).LogsServicer

# Session start far in the past so test entries (dated 2026-03-19) are not
# filtered out by the session-start gate.
_TEST_SESSION_START = datetime(2020, 1, 1, tzinfo=timezone.utc)


def _make_servicer(tmp_path: Path) -> Any:
    return LogsServicer(log_dir=tmp_path, session_start=_TEST_SESSION_START)


def _write_json_lines(log_file: Path, entries: Sequence[dict[str, Any]]) -> None:
    log_file.write_text(
        "\n".join(json.dumps(entry) for entry in entries) + "\n",
        encoding="utf-8",
    )


def _ts(value: str) -> Timestamp:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    timestamp = Timestamp()
    timestamp.FromDatetime(dt)
    return timestamp


class TestLogsServicerGetLogEntries:
    def test_returns_empty_when_log_directory_missing(self, tmp_path: Path) -> None:
        servicer = LogsServicer(
            log_dir=tmp_path / "missing", session_start=_TEST_SESSION_START
        )

        response = servicer.GetLogEntries(GetLogEntriesRequest(), MagicMock())

        assert response.entries == []
        assert response.pagination.total == 0
        assert response.pagination.has_more is False

    def test_applies_default_pagination(self, tmp_path: Path) -> None:
        entries = [
            {
                "timestamp": "2026-03-19T10:00:00+00:00",
                "level": "INFO",
                "logger": "system",
                "message": f"Entry {i}",
                "module": "mod",
            }
            for i in range(130)
        ]
        _write_json_lines(tmp_path / "system.json", entries)

        servicer = _make_servicer(tmp_path)
        response = servicer.GetLogEntries(GetLogEntriesRequest(), MagicMock())

        assert len(response.entries) == 100
        assert response.pagination.total == 130
        assert response.pagination.has_more is True
        assert response.entries[0].message == "Entry 0"
        assert response.entries[-1].message == "Entry 99"

    def test_applies_explicit_pagination_offset_and_limit(self, tmp_path: Path) -> None:
        entries = [
            {
                "timestamp": "2026-03-19T10:00:00+00:00",
                "level": "INFO",
                "logger": "system",
                "message": f"Entry {i}",
            }
            for i in range(5)
        ]
        _write_json_lines(tmp_path / "system.json", entries)

        servicer = _make_servicer(tmp_path)
        request = GetLogEntriesRequest()
        request.pagination.limit = 2
        request.pagination.offset = 1

        response = servicer.GetLogEntries(request, MagicMock())

        assert [entry.message for entry in response.entries] == ["Entry 1", "Entry 2"]
        assert response.pagination.total == 5
        assert response.pagination.has_more is True

    def test_filters_entries_by_level_and_category_and_time_range(
        self, tmp_path: Path
    ) -> None:
        _write_json_lines(
            tmp_path / "system.json",
            [
                {
                    "timestamp": "2026-03-19T10:00:00+00:00",
                    "level": "INFO",
                    "logger": "system",
                    "message": "before window",
                },
                {
                    "timestamp": "2026-03-19T11:00:00+00:00",
                    "level": "ERROR",
                    "logger": "system",
                    "message": "inside window",
                },
                {
                    "timestamp": "2026-03-19T12:00:00+00:00",
                    "level": "ERROR",
                    "logger": "commands",
                    "message": "wrong category",
                },
            ],
        )

        servicer = _make_servicer(tmp_path)
        request = GetLogEntriesRequest(
            level_filter="ERROR",
            category_filter="system",
            from_time=_ts("2026-03-19T10:30:00Z"),
            to_time=_ts("2026-03-19T11:30:00Z"),
        )

        response = servicer.GetLogEntries(request, MagicMock())

        assert len(response.entries) == 1
        assert response.entries[0].message == "inside window"
        assert response.entries[0].category == "system"
        assert response.entries[0].level == "ERROR"

    def test_maps_log_payload_to_proto_entry(self, tmp_path: Path) -> None:
        _write_json_lines(
            tmp_path / "commands.json",
            [
                {
                    "timestamp": "2026-03-19T10:00:00+00:00",
                    "level": "WARNING",
                    "logger": "commands",
                    "message": "command rejected",
                    "device_id": "ac_1",
                    "reason": "offline",
                }
            ],
        )

        servicer = _make_servicer(tmp_path)
        response = servicer.GetLogEntries(GetLogEntriesRequest(), MagicMock())

        assert len(response.entries) == 1
        entry: LogEntry = response.entries[0]
        assert entry.category == "commands"
        assert entry.level == "WARNING"
        assert entry.message == "command rejected"
        assert entry.extra["device_id"] == "ac_1"
        assert entry.extra["reason"] == "offline"


class TestLogsServicerGetLogCategories:
    def test_returns_sorted_unique_categories(self, tmp_path: Path) -> None:
        _write_json_lines(
            tmp_path / "system.json",
            [
                {
                    "timestamp": "2026-03-19T10:00:00+00:00",
                    "level": "INFO",
                    "logger": "system",
                    "message": "a",
                }
            ],
        )
        _write_json_lines(
            tmp_path / "commands.json",
            [
                {
                    "timestamp": "2026-03-19T11:00:00+00:00",
                    "level": "INFO",
                    "logger": "commands",
                    "message": "b",
                }
            ],
        )

        servicer = _make_servicer(tmp_path)
        response = servicer.GetLogCategories(GetLogCategoriesRequest(), MagicMock())

        assert response.categories == [
            "commands",
            "errors",
            "rules",
            "sensors",
            "system",
        ]


class TestLogsServicerGetLogStats:
    def test_returns_counts_by_level_and_category(self, tmp_path: Path) -> None:
        _write_json_lines(
            tmp_path / "system.json",
            [
                {
                    "timestamp": "2026-03-19T10:00:00+00:00",
                    "level": "INFO",
                    "logger": "system",
                    "message": "one",
                },
                {
                    "timestamp": "2026-03-19T10:10:00+00:00",
                    "level": "ERROR",
                    "logger": "system",
                    "message": "two",
                },
            ],
        )
        _write_json_lines(
            tmp_path / "commands.json",
            [
                {
                    "timestamp": "2026-03-19T10:20:00+00:00",
                    "level": "ERROR",
                    "logger": "commands",
                    "message": "three",
                }
            ],
        )

        servicer = _make_servicer(tmp_path)
        response = servicer.GetLogStats(GetLogStatsRequest(), MagicMock())

        assert response.stats.total_entries == 3
        assert dict(response.stats.entries_by_level) == {"INFO": 1, "ERROR": 2}
        assert dict(response.stats.entries_by_category) == {"system": 2, "commands": 1}

    def test_applies_filters_to_stats(self, tmp_path: Path) -> None:
        _write_json_lines(
            tmp_path / "system.json",
            [
                {
                    "timestamp": "2026-03-19T10:00:00+00:00",
                    "level": "INFO",
                    "logger": "system",
                    "message": "outside level",
                },
                {
                    "timestamp": "2026-03-19T11:00:00+00:00",
                    "level": "ERROR",
                    "logger": "system",
                    "message": "inside",
                },
            ],
        )

        servicer = _make_servicer(tmp_path)
        request = GetLogStatsRequest(
            level_filter="ERROR",
            category_filter="system",
            from_time=_ts("2026-03-19T10:30:00Z"),
            to_time=_ts("2026-03-19T11:30:00Z"),
        )

        response = servicer.GetLogStats(request, MagicMock())

        assert response.stats.total_entries == 1
        assert dict(response.stats.entries_by_level) == {"ERROR": 1}
        assert dict(response.stats.entries_by_category) == {"system": 1}
