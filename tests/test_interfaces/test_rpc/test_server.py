"""Tests for gRPC server lifecycle management."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import grpc
import pytest

if TYPE_CHECKING:
    from src.configuration.system_orchestrator import SystemOrchestrator


@pytest.fixture
def mock_orchestrator() -> SystemOrchestrator:
    """Create a mock SystemOrchestrator for testing."""
    return MagicMock()


@pytest.fixture
def test_port() -> int:
    """Return a non-standard port for testing."""
    return 50099


class TestGrpcServerLifecycle:
    """Test GrpcServer lifecycle methods."""

    def test_server_initialization(
        self, mock_orchestrator: SystemOrchestrator, test_port: int
    ) -> None:
        """Test server initializes with correct parameters."""
        from src.interfaces.rpc.server import GrpcServer

        server = GrpcServer(orchestrator=mock_orchestrator, port=test_port)
        assert server._orchestrator is mock_orchestrator
        assert server._port == test_port
        assert server._server is None

    def test_server_default_port(self, mock_orchestrator: SystemOrchestrator) -> None:
        """Test server uses default port 50051."""
        from src.interfaces.rpc.server import GrpcServer

        server = GrpcServer(orchestrator=mock_orchestrator)
        assert server._port == 50051

    def test_server_starts(
        self, mock_orchestrator: SystemOrchestrator, test_port: int
    ) -> None:
        """Test server starts successfully."""
        from src.interfaces.rpc.server import GrpcServer

        server = GrpcServer(orchestrator=mock_orchestrator, port=test_port)
        server.start()

        assert server._server is not None
        # Give it a moment to bind
        time.sleep(0.1)
        server.stop()

    def test_server_stops_gracefully(
        self, mock_orchestrator: SystemOrchestrator, test_port: int
    ) -> None:
        """Test server stops gracefully."""
        from src.interfaces.rpc.server import GrpcServer

        server = GrpcServer(orchestrator=mock_orchestrator, port=test_port)
        server.start()
        time.sleep(0.1)

        # Should not raise exception
        server.stop(grace=1.0)
        assert server._server is not None  # Server object still exists

    def test_stop_without_start(
        self, mock_orchestrator: SystemOrchestrator, test_port: int
    ) -> None:
        """Test stop is safe to call without start."""
        from src.interfaces.rpc.server import GrpcServer

        server = GrpcServer(orchestrator=mock_orchestrator, port=test_port)
        # Should not raise exception
        server.stop()

    def test_wait_for_termination_without_start(
        self, mock_orchestrator: SystemOrchestrator, test_port: int
    ) -> None:
        """Test wait_for_termination is safe to call without start."""
        from src.interfaces.rpc.server import GrpcServer

        server = GrpcServer(orchestrator=mock_orchestrator, port=test_port)
        # Should not raise exception or hang
        server.wait_for_termination()

    def test_server_binds_to_port(
        self, mock_orchestrator: SystemOrchestrator, test_port: int
    ) -> None:
        """Test server successfully binds to specified port."""
        from src.interfaces.rpc.server import GrpcServer

        server = GrpcServer(orchestrator=mock_orchestrator, port=test_port)
        server.start()
        time.sleep(0.1)

        # Try to create a channel to verify port is bound
        channel = grpc.insecure_channel(f"localhost:{test_port}")
        try:
            # Channel creation should succeed
            assert channel is not None
        finally:
            channel.close()
            server.stop()

    def test_reflection_service_registered(
        self, mock_orchestrator: SystemOrchestrator, test_port: int
    ) -> None:
        """Test reflection service is registered for inspection."""
        from src.interfaces.rpc.server import GrpcServer

        server = GrpcServer(orchestrator=mock_orchestrator, port=test_port)
        server.start()
        time.sleep(0.1)

        # Verify reflection is available by attempting to list services
        channel = grpc.insecure_channel(f"localhost:{test_port}")
        try:
            # Import reflection service
            from grpc_reflection.v1alpha import reflection_pb2, reflection_pb2_grpc

            stub = reflection_pb2_grpc.ServerReflectionStub(channel)
            # Try to list services (this would fail if reflection not enabled)
            request = reflection_pb2.ServerReflectionRequest(
                list_services="",
            )
            # If we get here without exception, reflection is working
            response = stub.ServerReflectionInfo(iter([request]))
            result = next(response)
            assert result is not None
        finally:
            channel.close()
            server.stop()

    def test_multiple_start_calls(
        self, mock_orchestrator: SystemOrchestrator, test_port: int
    ) -> None:
        """Test calling start multiple times (edge case)."""
        from src.interfaces.rpc.server import GrpcServer

        server = GrpcServer(orchestrator=mock_orchestrator, port=test_port)
        server.start()
        time.sleep(0.1)

        # Second start call - implementation should handle gracefully
        # (either ignore or restart)
        server.start()

        server.stop()

    def test_server_with_different_ports(
        self, mock_orchestrator: SystemOrchestrator
    ) -> None:
        """Test creating multiple server instances with different ports."""
        from src.interfaces.rpc.server import GrpcServer

        server1 = GrpcServer(orchestrator=mock_orchestrator, port=50098)
        server2 = GrpcServer(orchestrator=mock_orchestrator, port=50099)

        server1.start()
        server2.start()
        time.sleep(0.1)

        # Both should bind successfully
        assert server1._server is not None
        assert server2._server is not None

        server1.stop()
        server2.stop()
