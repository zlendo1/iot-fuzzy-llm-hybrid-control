from __future__ import annotations

from unittest.mock import MagicMock, patch

from src.common.exceptions import IoTFuzzyLLMError
from src.interfaces.web.bridge import OrchestratorBridge


def test_get_status_success() -> None:
    expected = {"status": "RUNNING", "uptime_seconds": 10, "version": "0.1.0"}

    with patch("src.interfaces.web.bridge._build_grpc_client") as mock_builder:
        mock_client = MagicMock()
        mock_client.get_status.return_value = expected
        mock_builder.return_value = mock_client

        bridge = OrchestratorBridge()
        result = bridge.get_status()

    assert result == expected
    mock_builder.assert_called_once_with("localhost", 50051)
    mock_client.connect.assert_called_once_with()
    mock_client.get_status.assert_called_once_with()


def test_get_status_error() -> None:
    with patch("src.interfaces.web.bridge._build_grpc_client") as mock_builder:
        mock_client = MagicMock()
        mock_client.get_status.side_effect = IoTFuzzyLLMError("gRPC server unavailable")
        mock_builder.return_value = mock_client

        bridge = OrchestratorBridge()
        result = bridge.get_status()

    assert result["status"] == "unavailable"
    assert "error" in result


def test_is_app_running_when_up() -> None:
    with patch("src.interfaces.web.bridge._build_grpc_client") as mock_builder:
        mock_client = MagicMock()
        mock_client.get_status.return_value = {"status": "RUNNING"}
        mock_builder.return_value = mock_client

        bridge = OrchestratorBridge()
        assert bridge.is_app_running() is True


def test_is_app_running_when_down() -> None:
    with patch("src.interfaces.web.bridge._build_grpc_client") as mock_builder:
        mock_client = MagicMock()
        mock_client.get_status.side_effect = IoTFuzzyLLMError("gRPC server unavailable")
        mock_builder.return_value = mock_client

        bridge = OrchestratorBridge()
        assert bridge.is_app_running() is False


def test_get_devices() -> None:
    expected = [{"id": "dev-1"}, {"id": "dev-2"}]

    with patch("src.interfaces.web.bridge._build_grpc_client") as mock_builder:
        mock_client = MagicMock()
        mock_client.list_devices.return_value = expected
        mock_builder.return_value = mock_client

        bridge = OrchestratorBridge()
        result = bridge.get_devices()

    assert result == expected
    mock_client.list_devices.assert_called_once_with()


def test_get_rules() -> None:
    expected = [{"id": "rule-1", "text": "If hot then cool", "enabled": True}]

    with patch("src.interfaces.web.bridge._build_grpc_client") as mock_builder:
        mock_client = MagicMock()
        mock_client.list_rules.return_value = {"rules": expected, "pagination": {}}
        mock_builder.return_value = mock_client

        bridge = OrchestratorBridge()
        result = bridge.get_rules()

    assert result == expected
    mock_client.list_rules.assert_called_once_with()


def test_start() -> None:
    with patch("src.interfaces.web.bridge._build_grpc_client") as mock_builder:
        mock_client = MagicMock()
        mock_client.start.return_value = {"success": True, "message": "started"}
        mock_builder.return_value = mock_client

        bridge = OrchestratorBridge()
        result = bridge.start()

    assert result is True
    mock_client.start.assert_called_once_with()


def test_shutdown() -> None:
    with patch("src.interfaces.web.bridge._build_grpc_client") as mock_builder:
        mock_client = MagicMock()
        mock_client.stop.return_value = {"success": True, "message": "stopped"}
        mock_builder.return_value = mock_client

        bridge = OrchestratorBridge()
        result = bridge.shutdown()

    assert result is True
    mock_client.stop.assert_called_once_with()


def test_is_connected() -> None:
    with patch("src.interfaces.web.bridge._build_grpc_client") as mock_builder:
        mock_client = MagicMock()
        mock_client.get_status.return_value = {"status": "RUNNING"}
        mock_builder.return_value = mock_client

        bridge = OrchestratorBridge()
        bridge.connect()

    assert bridge.is_connected() is True


def test_get_devices_returns_empty_on_connection_failure() -> None:
    with patch(
        "src.interfaces.web.bridge._build_grpc_client",
        side_effect=IoTFuzzyLLMError("gRPC server unavailable"),
    ):
        bridge = OrchestratorBridge()
        assert bridge.get_devices() == []


def test_get_rules_returns_empty_on_connection_failure() -> None:
    with patch(
        "src.interfaces.web.bridge._build_grpc_client",
        side_effect=IoTFuzzyLLMError("gRPC server unavailable"),
    ):
        bridge = OrchestratorBridge()
        assert bridge.get_rules() == []


def test_get_bridge_returns_cached_instance() -> None:
    from src.interfaces.web import bridge as bridge_module

    bridge_module.get_bridge.clear()
    with patch.object(bridge_module, "OrchestratorBridge") as mocked_bridge:
        first = bridge_module.get_bridge()
        second = bridge_module.get_bridge()

    assert first is second
    mocked_bridge.assert_called_once_with()
