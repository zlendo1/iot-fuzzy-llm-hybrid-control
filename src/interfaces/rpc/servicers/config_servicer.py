from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

import jsonschema
import grpc

from src.common.logging import get_logger
from src.common.utils import load_json
from src.interfaces.rpc.generated import config_pb2, config_pb2_grpc

logger = get_logger(__name__)


class ConfigServicer(config_pb2_grpc.ConfigServiceServicer):
    def __init__(self, config_dir: Path | str = Path("config")) -> None:
        self._config_dir = Path(config_dir)
        self._schema_dir = self._config_dir / "schemas"

    @staticmethod
    def _compute_version(content: str) -> str:
        return hashlib.md5(content.encode("utf-8")).hexdigest()[:8]

    def _config_path(self, name: str) -> Path:
        return self._config_dir / f"{name}.json"

    def _read_config_content(self, name: str) -> str:
        path = self._config_path(name)
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {name}")
        return path.read_text(encoding="utf-8")

    def _atomic_write(self, path: Path, content: str) -> None:
        directory = str(path.parent)
        with tempfile.NamedTemporaryFile(
            mode="w", dir=directory, delete=False, encoding="utf-8"
        ) as tmp_file:
            tmp_file.write(content)
            tmp_path = tmp_file.name
        os.replace(tmp_path, path)

    @staticmethod
    def _schema_name_for(config_name: str) -> str | None:
        mapping = {
            "mqtt_config": "mqtt",
            "llm_config": "llm",
            "devices": "devices",
        }
        return mapping.get(config_name)

    def _load_schema(self, name: str) -> dict[str, Any] | None:
        schema_name = self._schema_name_for(name)
        if not schema_name:
            return None
        schema_path = self._schema_dir / f"{schema_name}.schema.json"
        if not schema_path.exists():
            return None
        loaded = load_json(schema_path)
        if not isinstance(loaded, dict):
            return None
        return loaded

    def GetConfig(
        self, request: config_pb2.GetConfigRequest, context: grpc.ServicerContext
    ) -> config_pb2.GetConfigResponse:
        try:
            content = self._read_config_content(request.name)
        except FileNotFoundError as exc:
            context.abort(grpc.StatusCode.NOT_FOUND, str(exc))
            return config_pb2.GetConfigResponse()

        version = self._compute_version(content)
        return config_pb2.GetConfigResponse(
            config=config_pb2.ConfigFile(
                name=request.name,
                content=content,
                version=version,
            )
        )

    def UpdateConfig(
        self, request: config_pb2.UpdateConfigRequest, context: grpc.ServicerContext
    ) -> config_pb2.UpdateConfigResponse:
        name = request.config.name
        path = self._config_path(name)
        if not path.exists():
            context.abort(
                grpc.StatusCode.NOT_FOUND, f"Configuration file not found: {name}"
            )
            return config_pb2.UpdateConfigResponse(
                success=False,
                message=f"Configuration file not found: {name}",
                new_version="",
            )

        current_content = path.read_text(encoding="utf-8")
        current_version = self._compute_version(current_content)
        if request.config.version != current_version:
            context.abort(grpc.StatusCode.ABORTED, "Version conflict")
            return config_pb2.UpdateConfigResponse(
                success=False,
                message="Version conflict",
                new_version=current_version,
            )

        self._atomic_write(path, request.config.content)
        new_version = self._compute_version(request.config.content)
        logger.info(
            "Configuration updated via RPC",
            extra={"name": name, "new_version": new_version},
        )
        return config_pb2.UpdateConfigResponse(
            success=True,
            message="Configuration updated",
            new_version=new_version,
        )

    def ValidateConfig(
        self, request: config_pb2.ValidateConfigRequest, context: grpc.ServicerContext
    ) -> config_pb2.ValidateConfigResponse:
        errors: list[str] = []
        try:
            parsed = json.loads(request.content)
        except json.JSONDecodeError as exc:
            return config_pb2.ValidateConfigResponse(
                valid=False, errors=[f"Invalid JSON: {exc}"]
            )

        schema = self._load_schema(request.name)
        if schema is not None:
            try:
                jsonschema.validate(parsed, schema)
            except jsonschema.ValidationError as exc:
                errors.append(exc.message)
            except jsonschema.SchemaError as exc:
                errors.append(f"Schema error: {exc.message}")

        return config_pb2.ValidateConfigResponse(valid=len(errors) == 0, errors=errors)

    def ReloadConfig(
        self, request: config_pb2.ReloadConfigRequest, context: grpc.ServicerContext
    ) -> config_pb2.ReloadConfigResponse:
        path = self._config_path(request.name)
        if not path.exists():
            return config_pb2.ReloadConfigResponse(
                success=False,
                message=f"Configuration file not found: {request.name}",
            )

        try:
            _ = path.read_text(encoding="utf-8")
        except OSError as exc:
            return config_pb2.ReloadConfigResponse(
                success=False,
                message=f"Failed to reload config: {exc}",
            )

        return config_pb2.ReloadConfigResponse(
            success=True, message="Configuration reloaded"
        )

    def ListConfigs(
        self, request: config_pb2.ListConfigsRequest, context: grpc.ServicerContext
    ) -> config_pb2.ListConfigsResponse:
        names = sorted([path.stem for path in self._config_dir.glob("*.json")])
        return config_pb2.ListConfigsResponse(names=names)
