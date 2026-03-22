from __future__ import annotations

import hashlib
import json
from pathlib import Path

import grpc
import jsonschema

from src.common.exceptions import ConfigurationError
from src.common.logging import get_logger
from src.configuration.config_manager import ConfigurationManager
from src.interfaces.rpc.generated import config_pb2, config_pb2_grpc

logger = get_logger(__name__)


class ConfigServicer(config_pb2_grpc.ConfigServiceServicer):
    def __init__(self, config_dir: Path | str = Path("config")) -> None:
        self._config_dir = Path(config_dir)
        self._config_manager = ConfigurationManager(config_dir=self._config_dir)

    @staticmethod
    def _compute_version(content: str) -> str:
        return hashlib.md5(content.encode("utf-8")).hexdigest()[:8]

    def GetConfig(
        self, request: config_pb2.GetConfigRequest, context: grpc.ServicerContext
    ) -> config_pb2.GetConfigResponse:
        try:
            data = self._config_manager.load_config(request.name, validate=False)
            content = json.dumps(data, indent=2)
        except (FileNotFoundError, ConfigurationError) as exc:
            context.abort(grpc.StatusCode.NOT_FOUND, str(exc))
            return config_pb2.GetConfigResponse()
        except Exception as exc:
            context.abort(grpc.StatusCode.INTERNAL, f"Failed to load config: {exc}")
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

        try:
            current_data = self._config_manager.load_config(name, validate=False)
            current_content = json.dumps(current_data, indent=2)
        except (FileNotFoundError, ConfigurationError):
            context.abort(
                grpc.StatusCode.NOT_FOUND, f"Configuration file not found: {name}"
            )
            return config_pb2.UpdateConfigResponse(
                success=False,
                message=f"Configuration file not found: {name}",
                new_version="",
            )
        except Exception as exc:
            context.abort(grpc.StatusCode.INTERNAL, f"Failed to load config: {exc}")
            return config_pb2.UpdateConfigResponse(
                success=False,
                message=f"Failed to load config: {exc}",
                new_version="",
            )

        current_version = self._compute_version(current_content)
        if request.config.version != current_version:
            context.abort(grpc.StatusCode.ABORTED, "Version conflict")
            return config_pb2.UpdateConfigResponse(
                success=False,
                message="Version conflict",
                new_version=current_version,
            )

        try:
            new_data = json.loads(request.config.content)
            self._config_manager.save_config(name, new_data, validate=True, backup=True)
        except json.JSONDecodeError as exc:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, f"Invalid JSON: {exc}")
            return config_pb2.UpdateConfigResponse(
                success=False,
                message=f"Invalid JSON: {exc}",
                new_version="",
            )
        except Exception as exc:
            context.abort(grpc.StatusCode.INTERNAL, f"Failed to save config: {exc}")
            return config_pb2.UpdateConfigResponse(
                success=False,
                message=f"Failed to save config: {exc}",
                new_version="",
            )

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

        schema = self._config_manager._get_schema_for_config(request.name)
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
        if request.name not in self._config_manager.list_configs():
            return config_pb2.ReloadConfigResponse(
                success=False,
                message=f"Configuration file not found: {request.name}",
            )

        try:
            self._config_manager.reload(request.name)
        except Exception as exc:
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
        names = self._config_manager.list_configs()
        return config_pb2.ListConfigsResponse(names=names)
