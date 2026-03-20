from __future__ import annotations

import hashlib
import importlib
import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import grpc
import pytest

from src.interfaces.rpc.generated import config_pb2


def _version_for(content: str) -> str:
    return hashlib.md5(content.encode("utf-8")).hexdigest()[:8]


@pytest.fixture
def config_root(tmp_path: Path) -> Path:
    config_dir = tmp_path / "config"
    schemas_dir = config_dir / "schemas"
    config_dir.mkdir(parents=True, exist_ok=True)
    schemas_dir.mkdir(parents=True, exist_ok=True)

    (config_dir / "mqtt_config.json").write_text(
        json.dumps({"broker": {"host": "localhost", "port": 1883}}, indent=2),
        encoding="utf-8",
    )
    (config_dir / "llm_config.json").write_text(
        json.dumps({"llm": {"provider": "ollama"}}, indent=2),
        encoding="utf-8",
    )
    (config_dir / "devices.json").write_text(
        json.dumps({"devices": []}, indent=2),
        encoding="utf-8",
    )

    (schemas_dir / "mqtt.schema.json").write_text(
        json.dumps(
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "required": ["broker"],
                "properties": {
                    "broker": {
                        "type": "object",
                        "required": ["host", "port"],
                        "properties": {
                            "host": {"type": "string"},
                            "port": {"type": "integer"},
                        },
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    return config_dir


@pytest.fixture
def servicer(config_root: Path) -> Any:
    module = importlib.import_module("src.interfaces.rpc.servicers.config_servicer")
    return module.ConfigServicer(config_dir=config_root)


class TestConfigServicer:
    def test_get_config_returns_content_and_version(
        self, servicer: Any, config_root: Path
    ) -> None:
        request = config_pb2.GetConfigRequest(name="mqtt_config")

        response = servicer.GetConfig(request, MagicMock())

        expected_content = (config_root / "mqtt_config.json").read_text(
            encoding="utf-8"
        )
        assert response.config.name == "mqtt_config"
        assert response.config.content == expected_content
        assert response.config.version == _version_for(expected_content)

    def test_get_config_missing_file_aborts_not_found(self, servicer: Any) -> None:
        request = config_pb2.GetConfigRequest(name="missing")
        context = MagicMock()

        servicer.GetConfig(request, context)

        context.abort.assert_called_once()
        code, _ = context.abort.call_args[0]
        assert code == grpc.StatusCode.NOT_FOUND

    def test_update_config_success_with_matching_version(
        self, servicer: Any, config_root: Path
    ) -> None:
        file_path = config_root / "mqtt_config.json"
        old_content = file_path.read_text(encoding="utf-8")
        old_version = _version_for(old_content)
        new_content = json.dumps({"broker": {"host": "broker", "port": 1884}}, indent=2)

        request = config_pb2.UpdateConfigRequest(
            config=config_pb2.ConfigFile(
                name="mqtt_config",
                content=new_content,
                version=old_version,
            )
        )

        response = servicer.UpdateConfig(request, MagicMock())

        assert response.success is True
        assert response.new_version == _version_for(new_content)
        assert file_path.read_text(encoding="utf-8") == new_content

    def test_update_config_aborts_on_version_conflict(self, servicer: Any) -> None:
        request = config_pb2.UpdateConfigRequest(
            config=config_pb2.ConfigFile(
                name="mqtt_config",
                content=json.dumps({"broker": {"host": "x", "port": 1}}),
                version="deadbeef",
            )
        )
        context = MagicMock()

        servicer.UpdateConfig(request, context)

        context.abort.assert_called_once()
        code, details = context.abort.call_args[0]
        assert code == grpc.StatusCode.ABORTED
        assert "Version conflict" in details

    def test_validate_config_invalid_json_returns_error(self, servicer: Any) -> None:
        request = config_pb2.ValidateConfigRequest(
            name="mqtt_config", content="{bad-json"
        )

        response = servicer.ValidateConfig(request, MagicMock())

        assert response.valid is False
        assert response.errors
        assert "JSON" in response.errors[0]

    def test_validate_config_schema_error_returns_invalid(self, servicer: Any) -> None:
        request = config_pb2.ValidateConfigRequest(
            name="mqtt_config",
            content=json.dumps({"broker": {"host": "localhost"}}),
        )

        response = servicer.ValidateConfig(request, MagicMock())

        assert response.valid is False
        assert response.errors

    def test_validate_config_valid_json_when_schema_missing(
        self, servicer: Any
    ) -> None:
        request = config_pb2.ValidateConfigRequest(
            name="custom_unknown",
            content=json.dumps({"any": "value"}),
        )

        response = servicer.ValidateConfig(request, MagicMock())

        assert response.valid is True
        assert response.errors == []

    def test_reload_config_invalidates_cache_and_succeeds(self, servicer: Any) -> None:
        request = config_pb2.ReloadConfigRequest(name="mqtt_config")

        response = servicer.ReloadConfig(request, MagicMock())

        assert response.success is True

    def test_list_configs_returns_json_basenames(self, servicer: Any) -> None:
        request = config_pb2.ListConfigsRequest()

        response = servicer.ListConfigs(request, MagicMock())

        assert response.names == ["devices", "llm_config", "mqtt_config"]
