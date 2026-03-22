"""gRPC client wrapper with typed Python methods."""

from __future__ import annotations

import json
from typing import Any

import grpc

from src.common.exceptions import (
    ConfigurationError,
    DeviceError,
    IoTFuzzyLLMError,
    RuleError,
    ValidationError,
)
from src.interfaces.rpc.generated import (
    common_pb2,
    config_pb2,
    config_pb2_grpc,
    devices_pb2,
    devices_pb2_grpc,
    lifecycle_pb2,
    lifecycle_pb2_grpc,
    logs_pb2,
    logs_pb2_grpc,
    membership_pb2,
    membership_pb2_grpc,
    rules_pb2,
    rules_pb2_grpc,
)


class GrpcClient:
    def __init__(
        self, host: str = "localhost", port: int = 50051, timeout: float = 30.0
    ) -> None:
        self._host = host
        self._port = port
        self._timeout = timeout
        self._channel: grpc.Channel | None = None
        self._lifecycle_stub: lifecycle_pb2_grpc.LifecycleServiceStub | None = None
        self._rules_stub: rules_pb2_grpc.RulesServiceStub | None = None
        self._devices_stub: devices_pb2_grpc.DevicesServiceStub | None = None
        self._config_stub: config_pb2_grpc.ConfigServiceStub | None = None
        self._logs_stub: logs_pb2_grpc.LogsServiceStub | None = None
        self._membership_stub: membership_pb2_grpc.MembershipServiceStub | None = None

    def connect(self) -> None:
        self._channel = grpc.insecure_channel(f"{self._host}:{self._port}")
        self._lifecycle_stub = lifecycle_pb2_grpc.LifecycleServiceStub(self._channel)
        self._rules_stub = rules_pb2_grpc.RulesServiceStub(self._channel)
        self._devices_stub = devices_pb2_grpc.DevicesServiceStub(self._channel)
        self._config_stub = config_pb2_grpc.ConfigServiceStub(self._channel)
        self._logs_stub = logs_pb2_grpc.LogsServiceStub(self._channel)
        self._membership_stub = membership_pb2_grpc.MembershipServiceStub(self._channel)

    def disconnect(self) -> None:
        if self._channel:
            self._channel.close()
            self._channel = None
            self._lifecycle_stub = None
            self._rules_stub = None
            self._devices_stub = None
            self._config_stub = None
            self._logs_stub = None
            self._membership_stub = None

    def __enter__(self) -> GrpcClient:
        self.connect()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.disconnect()

    def _handle_grpc_error(self, error: grpc.RpcError, context: str) -> None:
        code = error.code()
        details = error.details()

        if code == grpc.StatusCode.NOT_FOUND:
            if "device" in context.lower():
                raise DeviceError(details) from error
            elif "rule" in context.lower():
                raise RuleError(details) from error
            else:
                raise IoTFuzzyLLMError(details) from error
        elif code == grpc.StatusCode.UNAVAILABLE:
            raise IoTFuzzyLLMError("gRPC server unavailable") from error
        elif code == grpc.StatusCode.INVALID_ARGUMENT:
            raise ValidationError(details) from error
        elif code == grpc.StatusCode.ABORTED:
            raise ConfigurationError(details) from error
        else:
            raise IoTFuzzyLLMError(f"gRPC error ({code}): {details}") from error

    def start(self) -> dict[str, Any]:
        if not self._lifecycle_stub:
            raise IoTFuzzyLLMError("Not connected - call connect() first")
        try:
            response = self._lifecycle_stub.Start(
                lifecycle_pb2.StartRequest(), timeout=self._timeout
            )
            return {"success": response.success, "message": response.message}
        except grpc.RpcError as e:
            self._handle_grpc_error(e, "start")
            raise

    def stop(self) -> dict[str, Any]:
        if not self._lifecycle_stub:
            raise IoTFuzzyLLMError("Not connected - call connect() first")
        try:
            response = self._lifecycle_stub.Stop(
                lifecycle_pb2.StopRequest(), timeout=self._timeout
            )
            return {"success": response.success, "message": response.message}
        except grpc.RpcError as e:
            self._handle_grpc_error(e, "stop")
            raise

    def get_status(self) -> dict[str, Any]:
        if not self._lifecycle_stub:
            raise IoTFuzzyLLMError("Not connected - call connect() first")
        try:
            response = self._lifecycle_stub.GetStatus(
                lifecycle_pb2.GetStatusRequest(), timeout=self._timeout
            )
            state_name = common_pb2.SystemState.Name(response.status.state)
            return {
                "state": state_name.lower(),
                "uptime_seconds": response.status.uptime_seconds,
                "version": response.status.version,
            }
        except grpc.RpcError as e:
            self._handle_grpc_error(e, "get_status")
            raise

    def get_system_info(self) -> dict[str, Any]:
        if not self._lifecycle_stub:
            raise IoTFuzzyLLMError("Not connected - call connect() first")
        try:
            response = self._lifecycle_stub.GetSystemInfo(
                lifecycle_pb2.GetSystemInfoRequest(), timeout=self._timeout
            )
            return {
                "name": response.name,
                "version": response.version,
                "uptime_seconds": response.uptime_seconds,
                "python_version": response.python_version,
                "running_components": list(response.running_components),
            }
        except grpc.RpcError as e:
            self._handle_grpc_error(e, "get_system_info")
            raise

    def add_rule(self, text: str) -> dict[str, Any]:
        if not self._rules_stub:
            raise IoTFuzzyLLMError("Not connected - call connect() first")
        try:
            response = self._rules_stub.AddRule(
                rules_pb2.AddRuleRequest(text=text, enabled=True),
                timeout=self._timeout,
            )
            return {
                "rule": {
                    "id": response.rule.id,
                    "text": response.rule.text,
                    "enabled": response.rule.enabled,
                }
            }
        except grpc.RpcError as e:
            self._handle_grpc_error(e, "add_rule")
            raise

    def remove_rule(self, rule_id: str) -> dict[str, Any]:
        if not self._rules_stub:
            raise IoTFuzzyLLMError("Not connected - call connect() first")
        try:
            response = self._rules_stub.RemoveRule(
                rules_pb2.RemoveRuleRequest(id=rule_id), timeout=self._timeout
            )
            return {"success": response.success}
        except grpc.RpcError as e:
            self._handle_grpc_error(e, "remove_rule")
            raise

    def list_rules(self, limit: int = 100, offset: int = 0) -> dict[str, Any]:
        if not self._rules_stub:
            raise IoTFuzzyLLMError("Not connected - call connect() first")
        try:
            response = self._rules_stub.ListRules(
                rules_pb2.ListRulesRequest(
                    pagination=common_pb2.PaginationRequest(limit=limit, offset=offset)
                ),
                timeout=self._timeout,
            )
            return {
                "rules": [
                    {
                        "id": rule.id,
                        "text": rule.text,
                        "enabled": rule.enabled,
                    }
                    for rule in response.rules
                ],
                "pagination": {
                    "total": response.pagination.total,
                    "has_more": response.pagination.has_more,
                },
            }
        except grpc.RpcError as e:
            self._handle_grpc_error(e, "list_rules")
            raise

    def get_rule(self, rule_id: str) -> dict[str, Any]:
        if not self._rules_stub:
            raise IoTFuzzyLLMError("Not connected - call connect() first")
        try:
            response = self._rules_stub.GetRule(
                rules_pb2.GetRuleRequest(id=rule_id), timeout=self._timeout
            )
            return {
                "id": response.rule.id,
                "text": response.rule.text,
                "enabled": response.rule.enabled,
            }
        except grpc.RpcError as e:
            self._handle_grpc_error(e, "get_rule")
            raise

    def enable_rule(self, rule_id: str) -> dict[str, Any]:
        if not self._rules_stub:
            raise IoTFuzzyLLMError("Not connected - call connect() first")
        try:
            response = self._rules_stub.EnableRule(
                rules_pb2.EnableRuleRequest(id=rule_id), timeout=self._timeout
            )
            return {"success": response.success}
        except grpc.RpcError as e:
            self._handle_grpc_error(e, "enable_rule")
            raise

    def disable_rule(self, rule_id: str) -> dict[str, Any]:
        if not self._rules_stub:
            raise IoTFuzzyLLMError("Not connected - call connect() first")
        try:
            response = self._rules_stub.DisableRule(
                rules_pb2.DisableRuleRequest(id=rule_id), timeout=self._timeout
            )
            return {"success": response.success}
        except grpc.RpcError as e:
            self._handle_grpc_error(e, "disable_rule")
            raise

    def evaluate_rules(self) -> dict[str, Any]:
        if not self._rules_stub:
            raise IoTFuzzyLLMError("Not connected - call connect() first")
        try:
            response = self._rules_stub.EvaluateRules(
                rules_pb2.EvaluateRulesRequest(), timeout=self._timeout
            )
            return {
                "commands_generated": list(response.commands_generated),
                "rules_evaluated": response.rules_evaluated,
            }
        except grpc.RpcError as e:
            self._handle_grpc_error(e, "evaluate_rules")
            raise

    def list_devices(self) -> list[dict[str, Any]]:
        if not self._devices_stub:
            raise IoTFuzzyLLMError("Not connected - call connect() first")
        try:
            response = self._devices_stub.ListDevices(
                devices_pb2.ListDevicesRequest(), timeout=self._timeout
            )
            return [
                {
                    "id": device.id,
                    "name": device.name,
                    "type": device.type,
                    "location": device.location,
                    "capabilities": list(device.capabilities),
                }
                for device in response.devices
            ]
        except grpc.RpcError as e:
            self._handle_grpc_error(e, "list_devices")
            raise

    def get_device(self, device_id: str) -> dict[str, Any]:
        if not self._devices_stub:
            raise IoTFuzzyLLMError("Not connected - call connect() first")
        try:
            response = self._devices_stub.GetDevice(
                devices_pb2.GetDeviceRequest(device_id=device_id),
                timeout=self._timeout,
            )
            return {
                "id": response.device.id,
                "name": response.device.name,
                "type": response.device.type,
                "location": response.device.location,
                "capabilities": list(response.device.capabilities),
            }
        except grpc.RpcError as e:
            self._handle_grpc_error(e, "get_device")
            raise

    def get_device_status(self, device_id: str) -> dict[str, Any]:
        if not self._devices_stub:
            raise IoTFuzzyLLMError("Not connected - call connect() first")
        try:
            response = self._devices_stub.GetDeviceStatus(
                devices_pb2.GetDeviceStatusRequest(device_id=device_id),
                timeout=self._timeout,
            )
            return {
                "device_id": response.device_id,
                "online": response.online,
                "last_seen": response.last_seen.ToDatetime()
                if response.HasField("last_seen")
                else None,
            }
        except grpc.RpcError as e:
            self._handle_grpc_error(e, "get_device_status")
            raise

    def get_latest_reading(self, device_id: str) -> dict[str, Any]:
        if not self._devices_stub:
            raise IoTFuzzyLLMError("Not connected - call connect() first")
        try:
            response = self._devices_stub.GetLatestReading(
                devices_pb2.GetLatestReadingRequest(device_id=device_id),
                timeout=self._timeout,
            )
            return {
                "device_id": response.reading.device_id,
                "value": response.reading.value,
                "unit": response.reading.unit,
                "timestamp": response.reading.timestamp.ToDatetime()
                if response.reading.HasField("timestamp")
                else None,
            }
        except grpc.RpcError as e:
            self._handle_grpc_error(e, "get_latest_reading")
            raise

    def send_command(
        self, device_id: str, action: str, parameters: dict[str, str]
    ) -> dict[str, Any]:
        if not self._devices_stub:
            raise IoTFuzzyLLMError("Not connected - call connect() first")
        try:
            response = self._devices_stub.SendCommand(
                devices_pb2.SendCommandRequest(
                    command=devices_pb2.DeviceCommand(
                        device_id=device_id, action=action, parameters=parameters
                    )
                ),
                timeout=self._timeout,
            )
            return {"success": response.success, "message": response.message}
        except grpc.RpcError as e:
            self._handle_grpc_error(e, "send_command")
            raise

    def get_config(self, name: str) -> dict[str, Any]:
        if not self._config_stub:
            raise IoTFuzzyLLMError("Not connected - call connect() first")
        try:
            response = self._config_stub.GetConfig(
                config_pb2.GetConfigRequest(name=name), timeout=self._timeout
            )
            return {
                "content": json.loads(response.config.content),
                "version": response.config.version,
            }
        except grpc.RpcError as e:
            self._handle_grpc_error(e, "get_config")
            raise

    def update_config(
        self, name: str, content: dict[str, Any], version: str
    ) -> dict[str, Any]:
        if not self._config_stub:
            raise IoTFuzzyLLMError("Not connected - call connect() first")
        try:
            response = self._config_stub.UpdateConfig(
                config_pb2.UpdateConfigRequest(
                    config=config_pb2.ConfigFile(
                        name=name, content=json.dumps(content), version=version
                    )
                ),
                timeout=self._timeout,
            )
            return {
                "success": response.success,
                "message": response.message,
                "new_version": response.new_version,
            }
        except grpc.RpcError as e:
            self._handle_grpc_error(e, "update_config")
            raise

    def validate_config(self, name: str, content: dict[str, Any]) -> dict[str, Any]:
        if not self._config_stub:
            raise IoTFuzzyLLMError("Not connected - call connect() first")
        try:
            response = self._config_stub.ValidateConfig(
                config_pb2.ValidateConfigRequest(
                    name=name, content=json.dumps(content)
                ),
                timeout=self._timeout,
            )
            return {"valid": response.valid, "errors": list(response.errors)}
        except grpc.RpcError as e:
            self._handle_grpc_error(e, "validate_config")
            raise

    def reload_config(self) -> dict[str, Any]:
        if not self._config_stub:
            raise IoTFuzzyLLMError("Not connected - call connect() first")
        try:
            response = self._config_stub.ReloadConfig(
                config_pb2.ReloadConfigRequest(), timeout=self._timeout
            )
            return {"success": response.success, "message": response.message}
        except grpc.RpcError as e:
            self._handle_grpc_error(e, "reload_config")
            raise

    def list_configs(self) -> list[str]:
        if not self._config_stub:
            raise IoTFuzzyLLMError("Not connected - call connect() first")
        try:
            response = self._config_stub.ListConfigs(
                config_pb2.ListConfigsRequest(), timeout=self._timeout
            )
            return list(response.names)
        except grpc.RpcError as e:
            self._handle_grpc_error(e, "list_configs")
            raise

    def get_log_entries(
        self,
        limit: int = 100,
        offset: int = 0,
        level_filter: str = "",
        category_filter: str = "",
        from_time: str = "",
        to_time: str = "",
    ) -> dict[str, Any]:
        if not self._logs_stub:
            raise IoTFuzzyLLMError("Not connected - call connect() first")
        try:
            response = self._logs_stub.GetLogEntries(
                logs_pb2.GetLogEntriesRequest(
                    pagination=common_pb2.PaginationRequest(limit=limit, offset=offset),
                    level_filter=level_filter,
                    category_filter=category_filter,
                ),
                timeout=self._timeout,
            )
            return {
                "entries": [
                    {
                        "timestamp": entry.timestamp.ToDatetime()
                        if entry.HasField("timestamp")
                        else None,
                        "level": entry.level,
                        "category": entry.category,
                        "message": entry.message,
                        "extra": dict(entry.extra),
                    }
                    for entry in response.entries
                ],
                "pagination": {
                    "total": response.pagination.total,
                    "has_more": response.pagination.has_more,
                },
            }
        except grpc.RpcError as e:
            self._handle_grpc_error(e, "get_log_entries")
            raise

    def get_log_categories(self) -> list[str]:
        if not self._logs_stub:
            raise IoTFuzzyLLMError("Not connected - call connect() first")
        try:
            response = self._logs_stub.GetLogCategories(
                logs_pb2.GetLogCategoriesRequest(), timeout=self._timeout
            )
            return list(response.categories)
        except grpc.RpcError as e:
            self._handle_grpc_error(e, "get_log_categories")
            raise

    def get_log_stats(self) -> dict[str, Any]:
        if not self._logs_stub:
            raise IoTFuzzyLLMError("Not connected - call connect() first")
        try:
            response = self._logs_stub.GetLogStats(
                logs_pb2.GetLogStatsRequest(), timeout=self._timeout
            )
            return {
                "total": response.stats.total_entries,
                "by_level": dict(response.stats.entries_by_level),
                "by_category": dict(response.stats.entries_by_category),
            }
        except grpc.RpcError as e:
            self._handle_grpc_error(e, "get_log_stats")
            raise

    def get_membership_functions(self, sensor_type: str) -> dict[str, Any]:
        if not self._membership_stub:
            raise IoTFuzzyLLMError("Not connected - call connect() first")
        try:
            response = self._membership_stub.GetMembershipFunctions(
                membership_pb2.GetMembershipFunctionsRequest(sensor_type=sensor_type),
                timeout=self._timeout,
            )
            return {
                "sensor_type": response.membership.sensor_type,
                "linguistic_variables": [
                    {
                        "name": lv.name,
                        "membership_functions": [
                            {
                                "name": mf.name,
                                "function_type": mf.function_type,
                                "parameters": dict(mf.parameters),
                            }
                            for mf in lv.membership_functions
                        ],
                    }
                    for lv in response.membership.linguistic_variables
                ],
            }
        except grpc.RpcError as e:
            self._handle_grpc_error(e, "get_membership_functions")
            raise

    def update_membership_function(
        self,
        sensor_type: str,
        variable_name: str,
        function_name: str,
        function_type: str,
        parameters: dict[str, float],
    ) -> dict[str, Any]:
        if not self._membership_stub:
            raise IoTFuzzyLLMError("Not connected - call connect() first")
        try:
            response = self._membership_stub.UpdateMembershipFunction(
                membership_pb2.UpdateMembershipFunctionRequest(
                    sensor_type=sensor_type,
                    variable_name=variable_name,
                    function=membership_pb2.MembershipFunction(
                        name=function_name,
                        function_type=function_type,
                        parameters=parameters,
                    ),
                ),
                timeout=self._timeout,
            )
            return {"success": response.success, "message": response.message}
        except grpc.RpcError as e:
            self._handle_grpc_error(e, "update_membership_function")
            raise

    def list_sensor_types(self) -> list[str]:
        if not self._membership_stub:
            raise IoTFuzzyLLMError("Not connected - call connect() first")
        try:
            response = self._membership_stub.ListSensorTypes(
                membership_pb2.ListSensorTypesRequest(), timeout=self._timeout
            )
            return list(response.sensor_types)
        except grpc.RpcError as e:
            self._handle_grpc_error(e, "list_sensor_types")
            raise
