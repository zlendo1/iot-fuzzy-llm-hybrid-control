from __future__ import annotations

import importlib
import sys
from typing import Any
from unittest.mock import MagicMock

import grpc

from src.common.exceptions import ConfigurationError
from src.interfaces.rpc.generated import common_pb2, lifecycle_pb2


def _create_servicer(orchestrator: MagicMock) -> Any:
    lifecycle_module = importlib.import_module(
        "src.interfaces.rpc.servicers.lifecycle_servicer"
    )
    lifecycle_servicer_cls = lifecycle_module.LifecycleServicer
    return lifecycle_servicer_cls(orchestrator=orchestrator)


def test_start_calls_orchestrator_initialize_and_returns_success() -> None:
    orchestrator = MagicMock()
    orchestrator.initialize.return_value = True
    servicer = _create_servicer(orchestrator)

    response = servicer.Start(lifecycle_pb2.StartRequest(), MagicMock())

    orchestrator.initialize.assert_called_once_with()
    assert response.success is True
    assert "started" in response.message.lower()


def test_stop_calls_orchestrator_shutdown_and_returns_success() -> None:
    orchestrator = MagicMock()
    orchestrator.shutdown.return_value = True
    servicer = _create_servicer(orchestrator)

    response = servicer.Stop(lifecycle_pb2.StopRequest(), MagicMock())

    orchestrator.shutdown.assert_called_once_with()
    assert response.success is True
    assert "stopped" in response.message.lower()


def test_get_status_maps_running_state_and_version() -> None:
    orchestrator = MagicMock()
    orchestrator.get_system_status.return_value = {
        "state": "running",
        "uptime_seconds": 42,
        "version": "0.1.0",
        "components": {
            "config_manager": True,
            "rule_manager": False,
        },
    }
    servicer = _create_servicer(orchestrator)

    response = servicer.GetStatus(lifecycle_pb2.GetStatusRequest(), MagicMock())

    orchestrator.get_system_status.assert_called_once_with()
    assert response.status.state == common_pb2.SystemState.RUNNING
    assert response.status.uptime_seconds == 42
    assert response.status.version == "0.1.0"
    assert "retrieved" in response.message.lower()


def test_get_status_maps_unknown_state_when_not_mapped() -> None:
    orchestrator = MagicMock()
    orchestrator.get_system_status.return_value = {
        "state": "idle",
        "uptime_seconds": 0,
        "version": "0.1.0",
    }
    servicer = _create_servicer(orchestrator)

    response = servicer.GetStatus(lifecycle_pb2.GetStatusRequest(), MagicMock())

    assert response.status.state == common_pb2.SystemState.UNKNOWN


def test_get_system_info_returns_expected_fields() -> None:
    orchestrator = MagicMock()
    orchestrator.get_system_status.return_value = {
        "uptime_seconds": 99,
        "components": {
            "config_manager": True,
            "logging_manager": False,
            "rule_manager": True,
        },
    }
    servicer = _create_servicer(orchestrator)

    response = servicer.GetSystemInfo(lifecycle_pb2.GetSystemInfoRequest(), MagicMock())

    assert response.name == "iot-fuzzy-llm"
    assert response.version == "0.1.0"
    assert response.uptime_seconds == 99
    assert response.python_version == sys.version.split()[0]
    assert sorted(response.running_components) == ["config_manager", "rule_manager"]


def test_start_uses_grpc_error_decorator() -> None:
    orchestrator = MagicMock()
    orchestrator.initialize.side_effect = ConfigurationError("bad configuration")
    context = MagicMock()
    servicer = _create_servicer(orchestrator)

    servicer.Start(lifecycle_pb2.StartRequest(), context)

    context.abort.assert_called_once()
    assert context.abort.call_args[0][0] == grpc.StatusCode.INVALID_ARGUMENT
    assert "bad configuration" in context.abort.call_args[0][1]


def test_stop_uses_grpc_error_decorator() -> None:
    orchestrator = MagicMock()
    orchestrator.shutdown.side_effect = ConfigurationError("shutdown blocked")
    context = MagicMock()
    servicer = _create_servicer(orchestrator)

    servicer.Stop(lifecycle_pb2.StopRequest(), context)

    context.abort.assert_called_once()
    assert context.abort.call_args[0][0] == grpc.StatusCode.INVALID_ARGUMENT
