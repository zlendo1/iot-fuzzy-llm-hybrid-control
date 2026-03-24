from __future__ import annotations

import os
from typing import Any, Protocol

import streamlit as st

from src.common.exceptions import IoTFuzzyLLMError


class _GrpcClientProtocol(Protocol):
    def connect(self) -> None: ...

    def disconnect(self) -> None: ...

    def get_status(self) -> dict[str, Any]: ...

    def start(self) -> dict[str, Any]: ...

    def stop(self) -> dict[str, Any]: ...

    def list_devices(self) -> list[dict[str, Any]]: ...

    def list_rules(self, limit: int = 100, offset: int = 0) -> dict[str, Any]: ...

    def add_rule(self, text: str) -> dict[str, Any]: ...

    def remove_rule(self, rule_id: str) -> dict[str, Any]: ...

    def enable_rule(self, rule_id: str) -> dict[str, Any]: ...

    def disable_rule(self, rule_id: str) -> dict[str, Any]: ...

    def evaluate_rules(self) -> dict[str, Any]: ...

    def get_config(self, name: str) -> dict[str, Any]: ...

    def update_config(
        self, name: str, content: dict[str, Any], version: str
    ) -> dict[str, Any]: ...

    def list_configs(self) -> list[str]: ...

    def validate_config(self, name: str, content: dict[str, Any]) -> dict[str, Any]: ...

    def reload_config(self) -> dict[str, Any]: ...

    def list_sensor_types(self) -> list[str]: ...

    def get_membership_functions(self, sensor_type: str) -> dict[str, Any]: ...

    def update_membership_function(
        self,
        sensor_type: str,
        variable_name: str,
        function_name: str,
        function_type: str,
        parameters: dict[str, float],
    ) -> dict[str, Any]: ...

    def get_log_entries(
        self,
        limit: int = 100,
        offset: int = 0,
        level_filter: str = "",
        category_filter: str = "",
        from_time: str = "",
        to_time: str = "",
    ) -> dict[str, Any]: ...

    def get_log_categories(self) -> list[str]: ...

    def get_log_stats(self) -> dict[str, Any]: ...

    def get_device(self, device_id: str) -> dict[str, Any]: ...

    def get_device_status(self, device_id: str) -> dict[str, Any]: ...

    def get_latest_reading(self, device_id: str) -> dict[str, Any]: ...

    def send_command(
        self, device_id: str, action: str, parameters: dict[str, str]
    ) -> dict[str, Any]: ...


def _build_grpc_client(host: str, port: int) -> _GrpcClientProtocol:
    from src.interfaces.rpc.client import GrpcClient

    return GrpcClient(host, port)


class OrchestratorBridge:
    def __init__(self, grpc_host: str = "localhost", grpc_port: int = 50051) -> None:
        self._grpc_host = grpc_host
        self._grpc_port = grpc_port
        self._client: _GrpcClientProtocol | None = None

    def connect(self) -> None:
        if not self._client:
            try:
                client = _build_grpc_client(self._grpc_host, self._grpc_port)
                client.connect()
            except Exception as exc:
                raise IoTFuzzyLLMError(f"gRPC connection failed: {exc}") from exc
            self._client = client

    def disconnect(self) -> None:
        if self._client:
            self._client.disconnect()
            self._client = None

    def is_connected(self) -> bool:
        if not self._client:
            return False
        try:
            self._client.get_status()
            return True
        except IoTFuzzyLLMError:
            return False

    def get_status(self) -> dict[str, Any]:
        if not self._client:
            try:
                self.connect()
            except IoTFuzzyLLMError as exc:
                return {"error": str(exc), "status": "unavailable"}

        if not self._client:
            return {"error": "gRPC client unavailable", "status": "unavailable"}

        try:
            return self._client.get_status()
        except IoTFuzzyLLMError as exc:
            return {"error": str(exc), "status": "unavailable"}

    def get_system_status(self) -> dict[str, Any] | None:
        status = self.get_status()
        if "error" in status:
            return None
        return status

    def is_app_running(self) -> bool:
        status = self.get_status()
        return "error" not in status

    def get_devices(self) -> list[dict[str, Any]]:
        if not self._client:
            try:
                self.connect()
            except IoTFuzzyLLMError:
                return []

        if not self._client:
            return []

        try:
            return self._client.list_devices()
        except IoTFuzzyLLMError:
            return []

    def get_rules(self) -> list[dict[str, Any]]:
        if not self._client:
            try:
                self.connect()
            except IoTFuzzyLLMError:
                return []

        if not self._client:
            return []

        try:
            result = self._client.list_rules()
        except IoTFuzzyLLMError:
            return []

        rules = result.get("rules")
        if not isinstance(rules, list):
            return []
        return [rule for rule in rules if isinstance(rule, dict)]

    def start(self) -> bool:
        if not self._client:
            try:
                self.connect()
            except IoTFuzzyLLMError:
                return False

        if not self._client:
            return False

        try:
            return bool(self._client.start().get("success", False))
        except IoTFuzzyLLMError:
            return False

    def shutdown(self) -> bool:
        if not self._client:
            try:
                self.connect()
            except IoTFuzzyLLMError:
                return False

        if not self._client:
            return False

        try:
            return bool(self._client.stop().get("success", False))
        except IoTFuzzyLLMError:
            return False

    def add_rule(self, text: str) -> dict[str, Any] | None:
        if not self._client:
            try:
                self.connect()
            except IoTFuzzyLLMError:
                return None

        if not self._client:
            return None

        try:
            result = self._client.add_rule(text)
            rule = result.get("rule")
            if isinstance(rule, dict):
                return rule
            return None
        except IoTFuzzyLLMError:
            return None

    def remove_rule(self, rule_id: str) -> bool:
        if not self._client:
            try:
                self.connect()
            except IoTFuzzyLLMError:
                return False

        if not self._client:
            return False

        try:
            return bool(self._client.remove_rule(rule_id).get("success", False))
        except IoTFuzzyLLMError:
            return False

    def enable_rule(self, rule_id: str) -> bool:
        if not self._client:
            try:
                self.connect()
            except IoTFuzzyLLMError:
                return False

        if not self._client:
            return False

        try:
            return bool(self._client.enable_rule(rule_id).get("success", False))
        except IoTFuzzyLLMError:
            return False

    def disable_rule(self, rule_id: str) -> bool:
        if not self._client:
            try:
                self.connect()
            except IoTFuzzyLLMError:
                return False

        if not self._client:
            return False

        try:
            return bool(self._client.disable_rule(rule_id).get("success", False))
        except IoTFuzzyLLMError:
            return False

    def evaluate_rules(self) -> dict[str, Any] | None:
        if not self._client:
            try:
                self.connect()
            except IoTFuzzyLLMError:
                return None

        if not self._client:
            return None

        try:
            return self._client.evaluate_rules()
        except IoTFuzzyLLMError:
            return None

    def get_config(self, name: str) -> dict[str, Any] | None:
        if not self._client:
            try:
                self.connect()
            except IoTFuzzyLLMError:
                return None

        if not self._client:
            return None

        try:
            return self._client.get_config(name)
        except IoTFuzzyLLMError:
            return None

    def update_config(
        self, name: str, content: dict[str, Any], version: str
    ) -> dict[str, Any] | None:
        if not self._client:
            try:
                self.connect()
            except IoTFuzzyLLMError:
                return None

        if not self._client:
            return None

        try:
            return self._client.update_config(name, content, version)
        except IoTFuzzyLLMError:
            return None

    def list_configs(self) -> list[str]:
        if not self._client:
            try:
                self.connect()
            except IoTFuzzyLLMError:
                return []

        if not self._client:
            return []

        try:
            return self._client.list_configs()
        except IoTFuzzyLLMError:
            return []

    def validate_config(
        self, name: str, content: dict[str, Any]
    ) -> dict[str, Any] | None:
        if not self._client:
            try:
                self.connect()
            except IoTFuzzyLLMError:
                return None

        if not self._client:
            return None

        try:
            return self._client.validate_config(name, content)
        except IoTFuzzyLLMError:
            return None

    def reload_config(self) -> bool:
        if not self._client:
            try:
                self.connect()
            except IoTFuzzyLLMError:
                return False

        if not self._client:
            return False

        try:
            return bool(self._client.reload_config().get("success", False))
        except IoTFuzzyLLMError:
            return False

    def list_sensor_types(self) -> list[str]:
        if not self._client:
            try:
                self.connect()
            except IoTFuzzyLLMError:
                return []

        if not self._client:
            return []

        try:
            return self._client.list_sensor_types()
        except IoTFuzzyLLMError:
            return []

    def get_membership_functions(self, sensor_type: str) -> dict[str, Any] | None:
        if not self._client:
            try:
                self.connect()
            except IoTFuzzyLLMError:
                return None

        if not self._client:
            return None

        try:
            return self._client.get_membership_functions(sensor_type)
        except IoTFuzzyLLMError:
            return None

    def update_membership_function(
        self,
        sensor_type: str,
        variable_name: str,
        function_name: str,
        function_type: str,
        parameters: dict[str, float],
    ) -> dict[str, Any] | None:
        if not self._client:
            try:
                self.connect()
            except IoTFuzzyLLMError:
                return None

        if not self._client:
            return None

        try:
            return self._client.update_membership_function(
                sensor_type,
                variable_name,
                function_name,
                function_type,
                parameters,
            )
        except IoTFuzzyLLMError:
            return None

    def get_log_entries(
        self,
        limit: int = 100,
        offset: int = 0,
        level_filter: str = "",
        category_filter: str = "",
        from_time: str = "",
        to_time: str = "",
    ) -> dict[str, Any] | None:
        if not self._client:
            try:
                self.connect()
            except IoTFuzzyLLMError:
                return None

        if not self._client:
            return None

        try:
            return self._client.get_log_entries(
                limit=limit,
                offset=offset,
                level_filter=level_filter,
                category_filter=category_filter,
                from_time=from_time,
                to_time=to_time,
            )
        except IoTFuzzyLLMError:
            return None

    def get_log_categories(self) -> list[str]:
        if not self._client:
            try:
                self.connect()
            except IoTFuzzyLLMError:
                return []

        if not self._client:
            return []

        try:
            return self._client.get_log_categories()
        except IoTFuzzyLLMError:
            return []

    def get_log_stats(self) -> dict[str, Any] | None:
        if not self._client:
            try:
                self.connect()
            except IoTFuzzyLLMError:
                return None

        if not self._client:
            return None

        try:
            return self._client.get_log_stats()
        except IoTFuzzyLLMError:
            return None

    def get_device(self, device_id: str) -> dict[str, Any] | None:
        if not self._client:
            try:
                self.connect()
            except IoTFuzzyLLMError:
                return None

        if not self._client:
            return None

        try:
            return self._client.get_device(device_id)
        except IoTFuzzyLLMError:
            return None

    def get_device_status(self, device_id: str) -> dict[str, Any] | None:
        if not self._client:
            try:
                self.connect()
            except IoTFuzzyLLMError:
                return None

        if not self._client:
            return None

        try:
            return self._client.get_device_status(device_id)
        except IoTFuzzyLLMError:
            return None

    def get_latest_reading(self, device_id: str) -> dict[str, Any] | None:
        if not self._client:
            try:
                self.connect()
            except IoTFuzzyLLMError:
                return None

        if not self._client:
            return None

        try:
            return self._client.get_latest_reading(device_id)
        except IoTFuzzyLLMError:
            return None

    def send_command(
        self,
        device_id: str,
        action: str,
        parameters: dict[str, str] | None = None,
    ) -> dict[str, Any] | None:
        if not self._client:
            try:
                self.connect()
            except IoTFuzzyLLMError:
                return None

        if not self._client:
            return None

        try:
            return self._client.send_command(device_id, action, parameters or {})
        except IoTFuzzyLLMError:
            return None


@st.cache_resource
def get_bridge() -> OrchestratorBridge:
    grpc_host = os.environ.get("IOT_GRPC_HOST", "localhost")
    grpc_port = int(os.environ.get("IOT_GRPC_PORT", "50051"))
    return OrchestratorBridge(grpc_host=grpc_host, grpc_port=grpc_port)
