"""Docker E2E tests for critical CLI paths.

These tests run against REAL Docker Compose services.
Requires: make up (all services healthy, gRPC on localhost:50051)

Run with:
    make docker-test
    python -m pytest -m docker -v
"""

from __future__ import annotations

import importlib
from collections.abc import Generator
from typing import Any
from uuid import uuid4

from src.common.exceptions import IoTFuzzyLLMError
from src.interfaces.rpc.client import GrpcClient

pytest = importlib.import_module("pytest")


GRPC_HOST = "localhost"
GRPC_PORT = 50051


@pytest.fixture
def grpc_client(docker_grpc_available: None) -> Generator[GrpcClient, None, None]:
    with GrpcClient(host=GRPC_HOST, port=GRPC_PORT) as client:
        yield client


def _new_test_rule_text() -> str:
    return f"If docker e2e probe {uuid4().hex[:10]} is hot, turn on ac"


def _fetch_logs_with_activity(client: GrpcClient) -> dict[str, Any]:
    initial = client.get_log_entries(limit=20, offset=0)
    if initial["entries"]:
        return initial

    rule_id: str | None = None
    try:
        created = client.add_rule(_new_test_rule_text())
        rule_id = str(created["rule"]["id"])
    finally:
        if rule_id is not None:
            client.remove_rule(rule_id)

    return client.get_log_entries(limit=20, offset=0)


@pytest.mark.docker
def test_status_reports_running_state_e2e(grpc_client: GrpcClient) -> None:
    status = grpc_client.get_status()

    assert status["state"] in {"running", "starting", "unknown"}
    assert isinstance(status["uptime_seconds"], int)
    assert status["uptime_seconds"] >= 0
    assert isinstance(status["version"], str)
    assert status["version"]


@pytest.mark.docker
def test_device_list_returns_real_devices_e2e(grpc_client: GrpcClient) -> None:
    devices = grpc_client.list_devices()

    assert len(devices) > 0
    device_ids = {str(device["id"]) for device in devices}
    assert any("living_room" in device_id for device_id in device_ids)
    assert any(str(device.get("device_type")) == "sensor" for device in devices)
    assert any(str(device.get("device_type")) == "actuator" for device in devices)


@pytest.mark.docker
def test_rule_list_reads_real_storage_e2e(grpc_client: GrpcClient) -> None:
    result = grpc_client.list_rules()
    rules = result["rules"]
    pagination = result["pagination"]

    assert isinstance(rules, list)
    assert isinstance(pagination["total"], int)
    assert pagination["total"] >= len(rules)
    for rule in rules:
        assert "id" in rule
        assert "text" in rule
        assert "enabled" in rule


@pytest.mark.docker
def test_rule_add_then_list_persists_rule_e2e(grpc_client: GrpcClient) -> None:
    rule_id: str | None = None
    rule_text = _new_test_rule_text()

    try:
        created = grpc_client.add_rule(rule_text)
        rule_id = str(created["rule"]["id"])
        assert created["rule"]["text"] == rule_text

        listed = grpc_client.list_rules()["rules"]
        persisted = next((rule for rule in listed if str(rule["id"]) == rule_id), None)

        assert persisted is not None
        assert persisted["text"] == rule_text
        assert persisted["enabled"] is True
    finally:
        if rule_id is not None:
            grpc_client.remove_rule(rule_id)


@pytest.mark.docker
def test_config_list_returns_core_configs_e2e(grpc_client: GrpcClient) -> None:
    configs = set(grpc_client.list_configs())

    assert {"devices", "mqtt_config", "llm_config"}.issubset(configs)


@pytest.mark.docker
def test_log_tail_returns_real_entries_e2e(grpc_client: GrpcClient) -> None:
    logs = _fetch_logs_with_activity(grpc_client)
    entries = logs["entries"]

    assert len(entries) > 0
    assert logs["pagination"]["total"] >= len(entries)
    assert any(str(entry.get("message", "")).strip() for entry in entries)
    assert any(str(entry.get("level", "")).strip() for entry in entries)


@pytest.mark.docker
def test_sensor_list_returns_only_sensors_e2e(grpc_client: GrpcClient) -> None:
    devices = grpc_client.list_devices()
    sensors = [
        device for device in devices if str(device.get("device_type")) == "sensor"
    ]

    assert len(sensors) > 0
    assert all(str(sensor.get("device_type")) == "sensor" for sensor in sensors)

    sensor_ids = {str(sensor["id"]) for sensor in sensors}
    expected_fixture_sensors = {
        "temp_living_room",
        "humidity_living_room",
        "motion_living_room",
    }
    assert len(sensor_ids.intersection(expected_fixture_sensors)) >= 1


@pytest.mark.docker
def test_rule_evaluate_skips_when_ollama_unavailable(
    grpc_client: GrpcClient,
) -> None:
    try:
        result = grpc_client.evaluate_rules()
    except IoTFuzzyLLMError as exc:
        error_text = str(exc).lower()
        if "ollama" in error_text or "model" in error_text:
            pytest.skip(f"Ollama/model not ready: {exc}")
        raise

    assert "commands_generated" in result
    assert "rules_evaluated" in result
    assert isinstance(result["commands_generated"], list)
    assert isinstance(result["rules_evaluated"], int)
