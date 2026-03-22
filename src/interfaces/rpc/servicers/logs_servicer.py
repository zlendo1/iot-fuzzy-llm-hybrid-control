from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from google.protobuf.timestamp_pb2 import Timestamp

from src.common.logging import get_logger
from src.configuration.logging_manager import LogCategory, LoggingManager
from src.interfaces.rpc.error_mapping import handle_grpc_errors
from src.interfaces.rpc.generated import logs_pb2_grpc
from src.interfaces.rpc.generated.common_pb2 import PaginationResponse
from src.interfaces.rpc.generated.logs_pb2 import (
    GetLogCategoriesResponse,
    GetLogEntriesResponse,
    GetLogStatsResponse,
    LogEntry,
    LogStats,
)

logger = get_logger(__name__)

_TIMESTAMP_KEY = "timestamp"
_LEVEL_KEY = "level"
_LOGGER_KEY = "logger"
_MESSAGE_KEY = "message"


class LogsServicer(logs_pb2_grpc.LogsServiceServicer):
    def __init__(
        self,
        log_dir: Path | None = None,
        session_start: datetime | None = None,
    ) -> None:
        log_path = log_dir or Path("logs")
        self._logging_manager = LoggingManager(log_dir=log_path)
        self._session_start = session_start or datetime.now(timezone.utc)

    @handle_grpc_errors
    def GetLogEntries(
        self,
        request: Any,
        context: Any,
    ) -> GetLogEntriesResponse:
        del context
        entries = self._load_entries()
        filtered = self._apply_filters(
            entries,
            level_filter=request.level_filter,
            category_filter=request.category_filter,
            from_time=request.from_time,
            to_time=request.to_time,
        )

        limit = request.pagination.limit if request.pagination.limit > 0 else 100
        offset = request.pagination.offset if request.pagination.offset >= 0 else 0
        paginated = filtered[offset : offset + limit]
        has_more = offset + limit < len(filtered)

        response_entries = [self._to_proto(entry) for entry in paginated]
        return GetLogEntriesResponse(
            entries=response_entries,
            pagination=PaginationResponse(total=len(filtered), has_more=has_more),
        )

    @handle_grpc_errors
    def GetLogCategories(
        self,
        request: Any,
        context: Any,
    ) -> GetLogCategoriesResponse:
        del request
        del context
        categories = sorted(cat.value for cat in LogCategory)
        return GetLogCategoriesResponse(categories=categories)

    @handle_grpc_errors
    def GetLogStats(
        self,
        request: Any,
        context: Any,
    ) -> GetLogStatsResponse:
        del context
        entries = self._load_entries()
        filtered = self._apply_filters(
            entries,
            level_filter=request.level_filter,
            category_filter=request.category_filter,
            from_time=request.from_time,
            to_time=request.to_time,
        )

        by_level = Counter(entry["level"] for entry in filtered)
        by_category = Counter(entry["category"] for entry in filtered)

        return GetLogStatsResponse(
            stats=LogStats(
                total_entries=len(filtered),
                entries_by_level=dict(by_level),
                entries_by_category=dict(by_category),
            ),
        )

    def _load_entries(self) -> list[dict[str, Any]]:
        raw_entries = self._logging_manager.get_log_entries()

        entries: list[dict[str, Any]] = []
        for entry in raw_entries:
            category = entry.get("category", "")
            normalized = self._normalize_entry(entry, category)
            if (
                normalized is not None
                and normalized["timestamp"] >= self._session_start
            ):
                entries.append(normalized)
        return entries

    def _normalize_entry(
        self,
        entry: dict[str, Any],
        category: str,
    ) -> dict[str, Any] | None:
        timestamp = self._parse_timestamp(entry.get(_TIMESTAMP_KEY))
        if timestamp is None:
            return None

        level = str(entry.get(_LEVEL_KEY, ""))
        message = str(entry.get(_MESSAGE_KEY, ""))

        extra: dict[str, str] = {}
        for key, value in entry.items():
            if key in {_TIMESTAMP_KEY, _LEVEL_KEY, _LOGGER_KEY, _MESSAGE_KEY}:
                continue
            extra[str(key)] = str(value)

        return {
            "timestamp": timestamp,
            "level": level,
            "category": category,
            "message": message,
            "extra": extra,
        }

    def _apply_filters(
        self,
        entries: list[dict[str, Any]],
        *,
        level_filter: str,
        category_filter: str,
        from_time: Timestamp,
        to_time: Timestamp,
    ) -> list[dict[str, Any]]:
        from_dt = self._timestamp_to_datetime(from_time)
        to_dt = self._timestamp_to_datetime(to_time)

        filtered: list[dict[str, Any]] = []
        for entry in entries:
            if level_filter and entry["level"] != level_filter:
                continue
            if category_filter and entry["category"] != category_filter:
                continue
            timestamp = entry["timestamp"]
            if from_dt and timestamp < from_dt:
                continue
            if to_dt and timestamp > to_dt:
                continue
            filtered.append(entry)
        return filtered

    def _to_proto(self, entry: dict[str, Any]) -> LogEntry:
        timestamp = Timestamp()
        timestamp.FromDatetime(entry["timestamp"])
        return LogEntry(
            timestamp=timestamp,
            level=entry["level"],
            category=entry["category"],
            message=entry["message"],
            extra=entry["extra"],
        )

    def _parse_timestamp(self, value: Any) -> datetime | None:
        if not value:
            return None

        text = str(value).strip()
        if not text:
            return None

        normalized = text.replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(normalized)
        except ValueError:
            return None

        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed

    def _timestamp_to_datetime(self, timestamp: Timestamp) -> datetime | None:
        if timestamp.seconds == 0 and timestamp.nanos == 0:
            return None
        value = timestamp.ToDatetime()
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value
