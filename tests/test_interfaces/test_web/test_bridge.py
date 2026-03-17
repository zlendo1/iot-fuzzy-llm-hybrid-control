from __future__ import annotations

import importlib
from unittest.mock import MagicMock, patch

import pytest


def _load_bridge_module():
    return importlib.import_module("src.interfaces.web.bridge")


def test_get_orchestrator_lazy_init_starts_once() -> None:
    with patch("src.interfaces.web.bridge.SystemOrchestrator") as mocked_cls:
        orchestrator_instance = mocked_cls.return_value
        bridge_module = _load_bridge_module()
        bridge = bridge_module.OrchestratorBridge()

        first = bridge.get_orchestrator()
        second = bridge.get_orchestrator()

        assert first is second
        mocked_cls.assert_called_once()
        orchestrator_instance.initialize.assert_called_once()


def test_get_orchestrator_raises_runtime_error_on_start_failure() -> None:
    with patch("src.interfaces.web.bridge.SystemOrchestrator") as mocked_cls:
        orchestrator_instance = mocked_cls.return_value
        orchestrator_instance.initialize.side_effect = RuntimeError("boom")

        bridge_module = _load_bridge_module()
        bridge = bridge_module.OrchestratorBridge()

        with pytest.raises(
            RuntimeError, match="Failed to initialize SystemOrchestrator"
        ):
            bridge.get_orchestrator()


def test_get_device_registry_proxies_orchestrator() -> None:
    with patch("src.interfaces.web.bridge.SystemOrchestrator") as mocked_cls:
        orchestrator_instance = mocked_cls.return_value
        orchestrator_instance.device_registry = MagicMock()

        bridge_module = _load_bridge_module()
        bridge = bridge_module.OrchestratorBridge()

        registry = bridge.get_device_registry()

        assert registry is orchestrator_instance.device_registry
        orchestrator_instance.initialize.assert_called_once()


def test_get_rule_manager_proxies_orchestrator() -> None:
    with patch("src.interfaces.web.bridge.SystemOrchestrator") as mocked_cls:
        orchestrator_instance = mocked_cls.return_value
        orchestrator_instance.rule_manager = MagicMock()

        bridge_module = _load_bridge_module()
        bridge = bridge_module.OrchestratorBridge()

        manager = bridge.get_rule_manager()

        assert manager is orchestrator_instance.rule_manager
        orchestrator_instance.initialize.assert_called_once()


def test_get_config_manager_proxies_orchestrator() -> None:
    with patch("src.interfaces.web.bridge.SystemOrchestrator") as mocked_cls:
        orchestrator_instance = mocked_cls.return_value
        orchestrator_instance.config_manager = MagicMock()

        bridge_module = _load_bridge_module()
        bridge = bridge_module.OrchestratorBridge()

        manager = bridge.get_config_manager()

        assert manager is orchestrator_instance.config_manager
        orchestrator_instance.initialize.assert_called_once()


def test_get_bridge_returns_singleton_instance() -> None:
    with patch("src.interfaces.web.bridge.OrchestratorBridge") as mocked_bridge:
        bridge_module = _load_bridge_module()
        first = bridge_module.get_bridge()
        second = bridge_module.get_bridge()

        assert first is second
        mocked_bridge.assert_called_once()
