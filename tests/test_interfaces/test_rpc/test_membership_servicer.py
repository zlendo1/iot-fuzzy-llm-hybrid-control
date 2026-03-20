from __future__ import annotations

import json
from importlib import import_module
from pathlib import Path
from unittest.mock import MagicMock, patch

import grpc

from src.interfaces.rpc.generated import membership_pb2

MembershipServicer = import_module(
    "src.interfaces.rpc.servicers.membership_servicer"
).MembershipServicer


def _write_membership_file(config_dir: Path, sensor_type: str = "temperature") -> Path:
    payload = {
        "sensor_type": sensor_type,
        "unit": "celsius",
        "universe_of_discourse": {"min": -10.0, "max": 45.0},
        "confidence_threshold": 0.1,
        "linguistic_variables": [
            {
                "term": "cold",
                "function_type": "triangular",
                "parameters": {"a": -10.0, "b": 0.0, "c": 15.0},
            },
            {
                "term": "warm",
                "function_type": "triangular",
                "parameters": {"a": 10.0, "b": 20.0, "c": 30.0},
            },
        ],
    }
    file_path = config_dir / f"{sensor_type}.json"
    file_path.write_text(json.dumps(payload), encoding="utf-8")
    return file_path


class TestMembershipServicer:
    def test_list_sensor_types_returns_json_file_stems(self, tmp_path: Path) -> None:
        _write_membership_file(tmp_path, sensor_type="temperature")
        _write_membership_file(tmp_path, sensor_type="humidity")
        (tmp_path / "README.md").write_text("ignore", encoding="utf-8")

        servicer = MembershipServicer(config_dir=tmp_path)
        response = servicer.ListSensorTypes(
            membership_pb2.ListSensorTypesRequest(),
            MagicMock(),
        )

        assert sorted(response.sensor_types) == ["humidity", "temperature"]

    def test_get_membership_functions_maps_json_to_proto(self, tmp_path: Path) -> None:
        _write_membership_file(tmp_path, sensor_type="temperature")
        servicer = MembershipServicer(config_dir=tmp_path)
        context = MagicMock()

        response = servicer.GetMembershipFunctions(
            membership_pb2.GetMembershipFunctionsRequest(sensor_type="temperature"),
            context,
        )

        assert response.membership.sensor_type == "temperature"
        assert len(response.membership.linguistic_variables) == 2

        cold_variable = response.membership.linguistic_variables[0]
        assert cold_variable.name == "cold"
        assert len(cold_variable.membership_functions) == 1
        cold_function = cold_variable.membership_functions[0]
        assert cold_function.name == "cold"
        assert cold_function.function_type == "triangular"
        assert cold_function.parameters["a"] == -10.0
        assert cold_function.parameters["b"] == 0.0
        assert cold_function.parameters["c"] == 15.0
        context.abort.assert_not_called()

    def test_get_membership_functions_missing_file_aborts_not_found(
        self,
        tmp_path: Path,
    ) -> None:
        servicer = MembershipServicer(config_dir=tmp_path)
        context = MagicMock()

        servicer.GetMembershipFunctions(
            membership_pb2.GetMembershipFunctionsRequest(sensor_type="not_real"),
            context,
        )

        context.abort.assert_called_once()
        args = context.abort.call_args[0]
        assert args[0] == grpc.StatusCode.NOT_FOUND
        assert "not_real" in args[1]

    def test_update_membership_function_updates_target_variable(
        self,
        tmp_path: Path,
    ) -> None:
        file_path = _write_membership_file(tmp_path, sensor_type="temperature")
        servicer = MembershipServicer(config_dir=tmp_path)

        request = membership_pb2.UpdateMembershipFunctionRequest(
            sensor_type="temperature",
            variable_name="cold",
            function=membership_pb2.MembershipFunction(
                name="cold",
                function_type="trapezoidal",
                parameters={"a": -10.0, "b": -5.0, "c": 8.0, "d": 15.0},
            ),
        )

        response = servicer.UpdateMembershipFunction(request, MagicMock())

        assert response.success is True
        updated = json.loads(file_path.read_text(encoding="utf-8"))
        updated_cold = next(
            item for item in updated["linguistic_variables"] if item["term"] == "cold"
        )
        assert updated_cold["function_type"] == "trapezoidal"
        assert updated_cold["parameters"] == {
            "a": -10.0,
            "b": -5.0,
            "c": 8.0,
            "d": 15.0,
        }

    def test_update_membership_function_uses_atomic_replace(
        self, tmp_path: Path
    ) -> None:
        _write_membership_file(tmp_path, sensor_type="temperature")
        servicer = MembershipServicer(config_dir=tmp_path)
        request = membership_pb2.UpdateMembershipFunctionRequest(
            sensor_type="temperature",
            variable_name="cold",
            function=membership_pb2.MembershipFunction(
                name="cold",
                function_type="triangular",
                parameters={"a": -8.0, "b": 0.0, "c": 10.0},
            ),
        )

        with patch(
            "src.interfaces.rpc.servicers.membership_servicer.os.replace"
        ) as replace:
            response = servicer.UpdateMembershipFunction(request, MagicMock())

        assert response.success is True
        replace.assert_called_once()
        source_path, target_path = replace.call_args[0]
        assert source_path != str(target_path)
        assert target_path == tmp_path / "temperature.json"
