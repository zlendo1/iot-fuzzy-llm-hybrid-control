from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import streamlit as st

from src.common.logging import get_logger
from src.interfaces.web.http_client import AppStatusClient

logger = get_logger(__name__)


class OrchestratorBridge:
    def __init__(self, base_url: str | None = None) -> None:
        if base_url is None:
            base_url = os.environ.get("IOT_APP_URL", "http://localhost:8080")
        self._http_client = AppStatusClient(base_url=base_url)
        project_root = Path(__file__).resolve().parents[3]
        self._config_dir = project_root / "config"
        self._rules_dir = project_root / "rules"

    def get_system_status(self) -> dict[str, Any] | None:
        return self._http_client.get_status()

    def is_app_running(self) -> bool:
        return self._http_client.is_app_running()

    def get_devices(self) -> list[dict[str, Any]]:
        status = self.get_system_status()
        if status:
            orchestrator = status.get("orchestrator")
            if isinstance(orchestrator, dict):
                devices = orchestrator.get("devices")
                if isinstance(devices, list):
                    return [d for d in devices if isinstance(d, dict)]

        return self._load_list_field(self._config_dir / "devices.json", "devices")

    def get_rules(self) -> list[dict[str, Any]]:
        return self._load_list_field(self._rules_dir / "active_rules.json", "rules")

    def start(self) -> bool:
        return self._http_client.start()

    def shutdown(self) -> bool:
        return self._http_client.shutdown()

    def _load_list_field(
        self, file_path: Path, field_name: str
    ) -> list[dict[str, Any]]:
        if not file_path.exists():
            return []

        try:
            with file_path.open(encoding="utf-8") as file:
                data = json.load(file)
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning(
                "Failed to load bridge data file",
                extra={"path": str(file_path), "field": field_name, "error": str(exc)},
            )
            return []

        values = data.get(field_name)
        if not isinstance(values, list):
            return []

        return [item for item in values if isinstance(item, dict)]


@st.cache_resource
def get_bridge() -> OrchestratorBridge:
    return OrchestratorBridge()
