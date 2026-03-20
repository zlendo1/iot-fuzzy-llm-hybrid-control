from __future__ import annotations

import sys
from typing import TYPE_CHECKING

import grpc

from src.common.logging import get_logger
from src.interfaces.rpc.error_mapping import handle_grpc_errors
from src.interfaces.rpc.generated import common_pb2, lifecycle_pb2, lifecycle_pb2_grpc

if TYPE_CHECKING:
    from src.configuration.system_orchestrator import SystemOrchestrator

logger = get_logger(__name__)


class LifecycleServicer(lifecycle_pb2_grpc.LifecycleServiceServicer):
    def __init__(self, orchestrator: SystemOrchestrator) -> None:
        self._orchestrator = orchestrator

    @handle_grpc_errors
    def Start(
        self,
        request: lifecycle_pb2.StartRequest,
        context: grpc.ServicerContext,
    ) -> lifecycle_pb2.StartResponse:
        del request, context
        started = self._orchestrator.initialize()
        if started:
            logger.info("Lifecycle Start RPC succeeded")
            return lifecycle_pb2.StartResponse(
                success=True,
                message="System started successfully",
            )

        logger.warning("Lifecycle Start RPC failed")
        return lifecycle_pb2.StartResponse(
            success=False,
            message="System failed to start",
        )

    @handle_grpc_errors
    def Stop(
        self,
        request: lifecycle_pb2.StopRequest,
        context: grpc.ServicerContext,
    ) -> lifecycle_pb2.StopResponse:
        del request, context
        stopped = self._orchestrator.shutdown()
        if stopped:
            logger.info("Lifecycle Stop RPC succeeded")
            return lifecycle_pb2.StopResponse(
                success=True,
                message="System stopped successfully",
            )

        logger.warning("Lifecycle Stop RPC failed")
        return lifecycle_pb2.StopResponse(
            success=False,
            message="System failed to stop",
        )

    @handle_grpc_errors
    def GetStatus(
        self,
        request: lifecycle_pb2.GetStatusRequest,
        context: grpc.ServicerContext,
    ) -> lifecycle_pb2.GetStatusResponse:
        del request, context
        status = self._orchestrator.get_system_status()
        state_value = str(status.get("state", "unknown")).lower()
        state_mapping = {
            "starting": common_pb2.SystemState.STARTING,
            "running": common_pb2.SystemState.RUNNING,
            "stopping": common_pb2.SystemState.STOPPING,
            "stopped": common_pb2.SystemState.STOPPED,
            "error": common_pb2.SystemState.ERROR,
        }
        mapped_state = state_mapping.get(state_value, common_pb2.SystemState.UNKNOWN)

        return lifecycle_pb2.GetStatusResponse(
            status=common_pb2.Status(
                state=mapped_state,
                uptime_seconds=int(status.get("uptime_seconds", 0)),
                version=str(status.get("version", "0.1.0")),
            ),
            message="System status retrieved",
        )

    @handle_grpc_errors
    def GetSystemInfo(
        self,
        request: lifecycle_pb2.GetSystemInfoRequest,
        context: grpc.ServicerContext,
    ) -> lifecycle_pb2.GetSystemInfoResponse:
        del request, context
        status = self._orchestrator.get_system_status()
        components = status.get("components", {})
        running_components = [
            str(name) for name, is_running in components.items() if bool(is_running)
        ]

        return lifecycle_pb2.GetSystemInfoResponse(
            name="iot-fuzzy-llm",
            version=str(status.get("version", "0.1.0")),
            uptime_seconds=int(status.get("uptime_seconds", 0)),
            python_version=sys.version.split()[0],
            running_components=sorted(running_components),
        )
