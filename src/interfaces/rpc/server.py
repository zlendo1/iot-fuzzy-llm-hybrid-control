from __future__ import annotations

from concurrent import futures
from typing import TYPE_CHECKING

import grpc
from grpc_reflection.v1alpha import reflection

from src.common.logging import get_logger

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

        service_names = [
            reflection.SERVICE_NAME,
        ]
        reflection.enable_server_reflection(service_names, self._server)
        logger.debug("Registered reflection service")
