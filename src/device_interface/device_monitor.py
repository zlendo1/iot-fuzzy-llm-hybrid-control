"""Device availability monitoring via MQTT LWT and heartbeats."""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum

from src.common.logging import get_logger
from src.common.utils import format_timestamp

logger = get_logger(__name__)


class DeviceStatus(Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    UNKNOWN = "unknown"


@dataclass
class DeviceState:
    device_id: str
    status: DeviceStatus = DeviceStatus.UNKNOWN
    last_seen: str | None = None
    last_message_topic: str | None = None
    consecutive_failures: int = 0


StatusCallback = Callable[[str, DeviceStatus, DeviceStatus], None]


class DeviceMonitor:
    """Tracks device availability via LWT messages and activity monitoring."""

    DEFAULT_STALE_THRESHOLD = 300.0  # 5 minutes
    DEFAULT_CHECK_INTERVAL = 60.0  # 1 minute

    def __init__(
        self,
        stale_threshold: float = DEFAULT_STALE_THRESHOLD,
        check_interval: float = DEFAULT_CHECK_INTERVAL,
    ) -> None:
        self._devices: dict[str, DeviceState] = {}
        self._lock = threading.RLock()
        self._stale_threshold = stale_threshold
        self._check_interval = check_interval
        self._status_callbacks: list[StatusCallback] = []
        self._checker_thread: threading.Thread | None = None
        self._shutdown = threading.Event()

    def register_device(self, device_id: str) -> None:
        with self._lock:
            if device_id not in self._devices:
                self._devices[device_id] = DeviceState(device_id=device_id)
                logger.debug("Registered device for monitoring: %s", device_id)

    def unregister_device(self, device_id: str) -> None:
        with self._lock:
            self._devices.pop(device_id, None)

    def record_activity(self, device_id: str, topic: str | None = None) -> None:
        with self._lock:
            if device_id not in self._devices:
                self._devices[device_id] = DeviceState(device_id=device_id)

            state = self._devices[device_id]
            old_status = state.status
            now = format_timestamp()

            self._devices[device_id] = DeviceState(
                device_id=device_id,
                status=DeviceStatus.ONLINE,
                last_seen=now,
                last_message_topic=topic or state.last_message_topic,
                consecutive_failures=0,
            )

            if old_status != DeviceStatus.ONLINE:
                self._notify_status_change(device_id, old_status, DeviceStatus.ONLINE)

    def record_lwt(self, device_id: str, payload: bytes) -> None:
        payload_str = payload.decode("utf-8").lower().strip()
        is_offline = payload_str in ("offline", "disconnected", "0", "false")

        with self._lock:
            if device_id not in self._devices:
                self._devices[device_id] = DeviceState(device_id=device_id)

            state = self._devices[device_id]
            old_status = state.status
            new_status = DeviceStatus.OFFLINE if is_offline else DeviceStatus.ONLINE

            self._devices[device_id] = DeviceState(
                device_id=device_id,
                status=new_status,
                last_seen=format_timestamp(),
                last_message_topic=state.last_message_topic,
                consecutive_failures=state.consecutive_failures if is_offline else 0,
            )

            if old_status != new_status:
                self._notify_status_change(device_id, old_status, new_status)

    def get_status(self, device_id: str) -> DeviceStatus:
        with self._lock:
            state = self._devices.get(device_id)
            return state.status if state else DeviceStatus.UNKNOWN

    def get_state(self, device_id: str) -> DeviceState | None:
        with self._lock:
            return self._devices.get(device_id)

    def get_all_states(self) -> dict[str, DeviceState]:
        with self._lock:
            return dict(self._devices)

    def get_online_devices(self) -> list[str]:
        with self._lock:
            return [
                d.device_id
                for d in self._devices.values()
                if d.status == DeviceStatus.ONLINE
            ]

    def get_offline_devices(self) -> list[str]:
        with self._lock:
            return [
                d.device_id
                for d in self._devices.values()
                if d.status == DeviceStatus.OFFLINE
            ]

    def add_status_callback(self, callback: StatusCallback) -> None:
        self._status_callbacks.append(callback)

    def remove_status_callback(self, callback: StatusCallback) -> None:
        if callback in self._status_callbacks:
            self._status_callbacks.remove(callback)

    def start_monitoring(self) -> None:
        if self._checker_thread is not None and self._checker_thread.is_alive():
            return

        self._shutdown.clear()
        self._checker_thread = threading.Thread(
            target=self._check_stale_devices,
            daemon=True,
            name="DeviceMonitor-Checker",
        )
        self._checker_thread.start()
        logger.info("Device monitoring started")

    def stop_monitoring(self) -> None:
        self._shutdown.set()
        if self._checker_thread is not None:
            self._checker_thread.join(timeout=5.0)
            self._checker_thread = None
        logger.info("Device monitoring stopped")

    def _check_stale_devices(self) -> None:
        while not self._shutdown.wait(self._check_interval):
            self._mark_stale_devices()

    def _mark_stale_devices(self) -> None:
        now = time.time()
        from datetime import datetime

        with self._lock:
            for device_id, state in list(self._devices.items()):
                if state.status != DeviceStatus.ONLINE or state.last_seen is None:
                    continue

                try:
                    last_seen_dt = datetime.fromisoformat(
                        state.last_seen.replace("Z", "+00:00")
                    )
                    last_seen_ts = last_seen_dt.timestamp()
                    age = now - last_seen_ts

                    if age > self._stale_threshold:
                        old_status = state.status
                        self._devices[device_id] = DeviceState(
                            device_id=device_id,
                            status=DeviceStatus.OFFLINE,
                            last_seen=state.last_seen,
                            last_message_topic=state.last_message_topic,
                            consecutive_failures=state.consecutive_failures + 1,
                        )
                        self._notify_status_change(
                            device_id, old_status, DeviceStatus.OFFLINE
                        )
                        logger.warning(
                            "Device %s marked offline (stale for %.1fs)",
                            device_id,
                            age,
                        )
                except (ValueError, TypeError):
                    logger.warning("Could not parse last_seen for device %s", device_id)

    def _notify_status_change(
        self,
        device_id: str,
        old_status: DeviceStatus,
        new_status: DeviceStatus,
    ) -> None:
        logger.info(
            "Device %s status changed: %s -> %s",
            device_id,
            old_status.value,
            new_status.value,
        )
        for callback in self._status_callbacks:
            try:
                callback(device_id, old_status, new_status)
            except Exception:
                logger.exception("Error in status callback for device %s", device_id)
