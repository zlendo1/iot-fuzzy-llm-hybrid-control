from __future__ import annotations

import importlib
from concurrent import futures
from typing import TYPE_CHECKING

import grpc
from grpc_reflection.v1alpha import reflection

from src.common.logging import get_logger
from src.interfaces.rpc.generated import (
    config_pb2_grpc,
    devices_pb2_grpc,
    lifecycle_pb2_grpc,
    logs_pb2_grpc,
    membership_pb2_grpc,
    rules_pb2_grpc,
)

if TYPE_CHECKING:
    from src.configuration.system_orchestrator import SystemOrchestrator

logger = get_logger(__name__)


class GrpcServer:
    def __init__(self, orchestrator: SystemOrchestrator, port: int = 50051) -> None:
        self._orchestrator = orchestrator
        self._port = port
        self._server: grpc.Server | None = None

    def start(self) -> None:
        if self._server is not None:
            logger.warning("Server already started, stopping previous instance")
            self.stop()

        self._server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        self._register_services()
        self._server.add_insecure_port(f"[::]:{self._port}")
        self._server.start()
        logger.info("gRPC server started", extra={"port": self._port})

    def stop(self, grace: float = 5.0) -> None:
        if self._server:
            logger.info("Stopping gRPC server", extra={"grace": grace})
            self._server.stop(grace=grace)

    def wait_for_termination(self) -> None:
        if self._server:
            self._server.wait_for_termination()

    def _register_services(self) -> None:
        if not self._server:
            return

        # Register LifecycleService
        lifecycle_module = importlib.import_module(
            "src.interfaces.rpc.servicers.lifecycle_servicer"
        )
        lifecycle_servicer_cls = lifecycle_module.LifecycleServicer
        lifecycle_pb2_grpc.add_LifecycleServiceServicer_to_server(
            lifecycle_servicer_cls(orchestrator=self._orchestrator),
            self._server,
        )

        # Register RulesService
        rules_module = importlib.import_module(
            "src.interfaces.rpc.servicers.rules_servicer"
        )
        rules_servicer_cls = rules_module.RulesServicer
        rules_pb2_grpc.add_RulesServiceServicer_to_server(
            rules_servicer_cls(orchestrator=self._orchestrator),
            self._server,
        )

        # Register DevicesService
        devices_module = importlib.import_module(
            "src.interfaces.rpc.servicers.devices_servicer"
        )
        devices_servicer_cls = devices_module.DevicesServicer
        devices_pb2_grpc.add_DevicesServiceServicer_to_server(
            devices_servicer_cls(orchestrator=self._orchestrator),
            self._server,
        )

        # Register ConfigService
        config_module = importlib.import_module(
            "src.interfaces.rpc.servicers.config_servicer"
        )
        config_servicer_cls = config_module.ConfigServicer
        config_pb2_grpc.add_ConfigServiceServicer_to_server(
            config_servicer_cls(config_dir=self._orchestrator.config_dir),
            self._server,
        )

        # Register LogsService
        logs_module = importlib.import_module(
            "src.interfaces.rpc.servicers.logs_servicer"
        )
        logs_servicer_cls = logs_module.LogsServicer
        logs_pb2_grpc.add_LogsServiceServicer_to_server(
            logs_servicer_cls(log_dir=self._orchestrator.logs_dir),
            self._server,
        )

        # Register MembershipService
        membership_module = importlib.import_module(
            "src.interfaces.rpc.servicers.membership_servicer"
        )
        membership_servicer_cls = membership_module.MembershipServicer
        membership_pb2_grpc.add_MembershipServiceServicer_to_server(
            membership_servicer_cls(
                config_dir=self._orchestrator.config_dir / "membership_functions"
            ),
            self._server,
        )

        service_names = [
            "iot.v1.LifecycleService",
            "iot.v1.RulesService",
            "iot.v1.DevicesService",
            "iot.v1.ConfigService",
            "iot.v1.LogsService",
            "iot.v1.MembershipService",
            reflection.SERVICE_NAME,
        ]
        reflection.enable_server_reflection(service_names, self._server)
        logger.debug("Registered reflection service")
