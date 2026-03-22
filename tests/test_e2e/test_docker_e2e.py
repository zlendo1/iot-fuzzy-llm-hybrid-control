"""Docker E2E tests for critical CLI paths.

These tests run against REAL Docker Compose services.
Requires: make up (all services healthy, gRPC on localhost:50051)

Run with:
    make docker-test
    python -m pytest -m docker -v
"""

from __future__ import annotations

import pytest


@pytest.mark.docker
class TestDockerE2ESmoke:
    def test_grpc_server_reachable(self, docker_grpc_available: None) -> None:
        pass
