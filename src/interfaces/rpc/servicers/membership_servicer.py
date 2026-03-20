from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

import grpc

from src.common.logging import get_logger
from src.interfaces.rpc.error_mapping import handle_grpc_errors
from src.interfaces.rpc.generated import membership_pb2, membership_pb2_grpc

logger = get_logger(__name__)


def atomic_write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        dir=path.parent,
        delete=False,
        suffix=".json",
        encoding="utf-8",
    ) as temp_file:
        json.dump(data, temp_file, indent=2)
        temp_file.write("\n")
        temp_path = temp_file.name
    os.replace(temp_path, path)


class MembershipServicer(membership_pb2_grpc.MembershipServiceServicer):
    def __init__(self, config_dir: Path | None = None) -> None:
        self._config_dir = config_dir or Path("config/membership_functions")

    @handle_grpc_errors
    def ListSensorTypes(
        self,
        request: membership_pb2.ListSensorTypesRequest,
        context: grpc.ServicerContext,
    ) -> membership_pb2.ListSensorTypesResponse:
        sensor_types = sorted(path.stem for path in self._config_dir.glob("*.json"))
        return membership_pb2.ListSensorTypesResponse(sensor_types=sensor_types)

    @handle_grpc_errors
    def GetMembershipFunctions(
        self,
        request: membership_pb2.GetMembershipFunctionsRequest,
        context: grpc.ServicerContext,
    ) -> membership_pb2.GetMembershipFunctionsResponse:
        sensor_type = request.sensor_type
        config_path = self._config_dir / f"{sensor_type}.json"
        try:
            payload = json.loads(config_path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            context.abort(
                grpc.StatusCode.NOT_FOUND,
                f"Membership definition for sensor type '{sensor_type}' not found",
            )
            return membership_pb2.GetMembershipFunctionsResponse()

        variables: list[membership_pb2.LinguisticVariable] = []
        for item in payload.get("linguistic_variables", []):
            term = str(item["term"])
            function_type = str(item["function_type"])
            parameters = {
                str(key): float(value)
                for key, value in dict(item.get("parameters", {})).items()
            }
            variables.append(
                membership_pb2.LinguisticVariable(
                    name=term,
                    membership_functions=[
                        membership_pb2.MembershipFunction(
                            name=term,
                            function_type=function_type,
                            parameters=parameters,
                        )
                    ],
                )
            )

        membership = membership_pb2.SensorTypeMembership(
            sensor_type=sensor_type,
            linguistic_variables=variables,
        )
        return membership_pb2.GetMembershipFunctionsResponse(membership=membership)

    @handle_grpc_errors
    def UpdateMembershipFunction(
        self,
        request: membership_pb2.UpdateMembershipFunctionRequest,
        context: grpc.ServicerContext,
    ) -> membership_pb2.UpdateMembershipFunctionResponse:
        sensor_type = request.sensor_type
        config_path = self._config_dir / f"{sensor_type}.json"
        try:
            payload = json.loads(config_path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            context.abort(
                grpc.StatusCode.NOT_FOUND,
                f"Membership definition for sensor type '{sensor_type}' not found",
            )
            return membership_pb2.UpdateMembershipFunctionResponse(
                success=False,
                message="Membership definition not found",
            )

        updated = False
        for item in payload.get("linguistic_variables", []):
            if item.get("term") != request.variable_name:
                continue
            item["function_type"] = request.function.function_type
            item["parameters"] = dict(request.function.parameters)
            updated = True
            break

        if not updated:
            context.abort(
                grpc.StatusCode.NOT_FOUND,
                (
                    f"Variable '{request.variable_name}' not found for sensor type "
                    f"'{sensor_type}'"
                ),
            )
            return membership_pb2.UpdateMembershipFunctionResponse(
                success=False,
                message="Membership variable not found",
            )

        atomic_write_json(config_path, payload)
        logger.info(
            "Membership function updated",
            extra={
                "sensor_type": sensor_type,
                "variable_name": request.variable_name,
                "function_type": request.function.function_type,
            },
        )
        return membership_pb2.UpdateMembershipFunctionResponse(
            success=True,
            message="Membership function updated successfully",
        )
