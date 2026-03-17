from __future__ import annotations

import threading
from typing import TYPE_CHECKING

import streamlit as st

from src.common.logging import get_logger
from src.configuration.system_orchestrator import SystemOrchestrator

if TYPE_CHECKING:
    from src.configuration.config_manager import ConfigurationManager
    from src.configuration.rule_manager import RuleManager
    from src.device_interface.registry import DeviceRegistry

logger = get_logger(__name__)


class OrchestratorBridge:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._orchestrator: SystemOrchestrator | None = None

    def get_orchestrator(self) -> SystemOrchestrator:
        with self._lock:
            if self._orchestrator is None:
                self._orchestrator = SystemOrchestrator()
                try:
                    self._orchestrator.initialize()
                except Exception as exc:
                    logger.error(
                        "Failed to initialize SystemOrchestrator",
                        extra={"error": str(exc)},
                    )
                    self._orchestrator = None
                    raise RuntimeError(
                        "Failed to initialize SystemOrchestrator"
                    ) from exc
            return self._orchestrator

    def get_device_registry(self) -> DeviceRegistry | None:
        return self.get_orchestrator().device_registry

    def get_rule_manager(self) -> RuleManager | None:
        return self.get_orchestrator().rule_manager

    def get_config_manager(self) -> ConfigurationManager | None:
        return self.get_orchestrator().config_manager


@st.cache_resource
def get_bridge() -> OrchestratorBridge:
    return OrchestratorBridge()
