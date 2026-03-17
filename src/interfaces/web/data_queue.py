from __future__ import annotations

import threading
from typing import TYPE_CHECKING

from src.device_interface.messages import SensorReading

if TYPE_CHECKING:
    from src.interfaces.web.bridge import OrchestratorBridge


class SensorDataQueue:
    def __init__(
        self,
        bridge: OrchestratorBridge | None = None,
        max_history: int = 100,
    ) -> None:
        self._bridge = bridge
        self._max_history = max_history
        self._latest: dict[str, SensorReading] = {}
        self._history: dict[str, list[SensorReading]] = {}
        self._lock = threading.RLock()

    def get_latest_readings(self) -> dict[str, SensorReading]:
        with self._lock:
            return dict(self._latest)

    def get_reading_history(
        self,
        device_id: str,
        limit: int = 10,
    ) -> list[SensorReading]:
        with self._lock:
            history = self._history.get(device_id, [])
            return list(reversed(history[-limit:])) if limit > 0 else []

    def push_reading(self, reading: SensorReading) -> None:
        with self._lock:
            self._latest[reading.sensor_id] = reading
            history = self._history.setdefault(reading.sensor_id, [])
            history.append(reading)
            if len(history) > self._max_history:
                del history[: len(history) - self._max_history]
