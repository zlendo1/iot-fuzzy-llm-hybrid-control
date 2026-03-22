"""Shared fixtures for E2E tests requiring Docker Compose services."""

from __future__ import annotations

import grpc
import pytest


def wait_for_grpc(
    host: str = "localhost", port: int = 50051, timeout: float = 30.0
) -> None:
    """Wait for gRPC server to be ready, raising RuntimeError if timeout exceeded."""
    channel = grpc.insecure_channel(f"{host}:{port}")
    try:
        grpc.channel_ready_future(channel).result(timeout=timeout)
    except grpc.FutureTimeoutError as exc:
        raise RuntimeError(
            f"gRPC server at {host}:{port} not ready after {timeout}s. "
            "Make sure Docker services are running: make up"
        ) from exc
    finally:
        channel.close()


@pytest.fixture(scope="session")
def docker_grpc_available() -> None:
    """Skip tests when Docker gRPC is unavailable (5s probe timeout)."""
    try:
        wait_for_grpc(timeout=5.0)
    except RuntimeError:
        pytest.skip("Docker gRPC not available")
