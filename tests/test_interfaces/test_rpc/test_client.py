"""Tests for gRPC client wrapper."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import grpc
import pytest

from src.common.exceptions import (
    DeviceError,
    IoTFuzzyLLMError,
    RuleError,
    ValidationError,
)


@pytest.fixture
def mock_channel() -> MagicMock:
    """Create mock gRPC channel."""
    return MagicMock(spec=grpc.Channel)


@pytest.fixture
def mock_lifecycle_stub() -> MagicMock:
    """Create mock LifecycleService stub."""
    return MagicMock()


@pytest.fixture
def mock_rules_stub() -> MagicMock:
    """Create mock RulesService stub."""
    return MagicMock()


@pytest.fixture
def mock_devices_stub() -> MagicMock:
    """Create mock DevicesService stub."""
    return MagicMock()


@pytest.fixture
def mock_config_stub() -> MagicMock:
    """Create mock ConfigService stub."""
    return MagicMock()


@pytest.fixture
def mock_logs_stub() -> MagicMock:
    """Create mock LogsService stub."""
    return MagicMock()


@pytest.fixture
def mock_membership_stub() -> MagicMock:
    """Create mock MembershipService stub."""
    return MagicMock()


class TestGrpcClientInitialization:
    """Test GrpcClient initialization and connection management."""

    def test_initialization_with_defaults(self) -> None:
        """Test client initializes with default parameters."""
        from src.interfaces.rpc.client import GrpcClient

        client = GrpcClient()
        assert client._host == "localhost"
        assert client._port == 50051
        assert client._timeout == 30.0
        assert client._channel is None

    def test_initialization_with_custom_params(self) -> None:
        """Test client initializes with custom parameters."""
        from src.interfaces.rpc.client import GrpcClient

        client = GrpcClient(host="192.168.1.100", port=8080, timeout=60.0)
        assert client._host == "192.168.1.100"
        assert client._port == 8080
        assert client._timeout == 60.0

    @patch("src.interfaces.rpc.client.grpc.insecure_channel")
    @patch("src.interfaces.rpc.client.lifecycle_pb2_grpc.LifecycleServiceStub")
    @patch("src.interfaces.rpc.client.rules_pb2_grpc.RulesServiceStub")
    @patch("src.interfaces.rpc.client.devices_pb2_grpc.DevicesServiceStub")
    @patch("src.interfaces.rpc.client.config_pb2_grpc.ConfigServiceStub")
    @patch("src.interfaces.rpc.client.logs_pb2_grpc.LogsServiceStub")
    @patch("src.interfaces.rpc.client.membership_pb2_grpc.MembershipServiceStub")
    def test_connect_creates_channel_and_stubs(
        self,
        mock_membership_stub_cls: MagicMock,
        mock_logs_stub_cls: MagicMock,
        mock_config_stub_cls: MagicMock,
        mock_devices_stub_cls: MagicMock,
        mock_rules_stub_cls: MagicMock,
        mock_lifecycle_stub_cls: MagicMock,
        mock_channel_factory: MagicMock,
        mock_channel: MagicMock,
    ) -> None:
        """Test connect() creates channel and all stubs."""
        from src.interfaces.rpc.client import GrpcClient

        mock_channel_factory.return_value = mock_channel

        client = GrpcClient()
        client.connect()

        # Verify channel created
        mock_channel_factory.assert_called_once_with("localhost:50051")
        assert client._channel is mock_channel

        # Verify all stubs created
        mock_lifecycle_stub_cls.assert_called_once_with(mock_channel)
        mock_rules_stub_cls.assert_called_once_with(mock_channel)
        mock_devices_stub_cls.assert_called_once_with(mock_channel)
        mock_config_stub_cls.assert_called_once_with(mock_channel)
        mock_logs_stub_cls.assert_called_once_with(mock_channel)
        mock_membership_stub_cls.assert_called_once_with(mock_channel)

    @patch("src.interfaces.rpc.client.grpc.insecure_channel")
    def test_disconnect_closes_channel(self, mock_channel_factory: MagicMock) -> None:
        """Test disconnect() closes the channel."""
        from src.interfaces.rpc.client import GrpcClient

        mock_channel = MagicMock()
        mock_channel_factory.return_value = mock_channel

        with patch("src.interfaces.rpc.client.lifecycle_pb2_grpc.LifecycleServiceStub"):
            with patch("src.interfaces.rpc.client.rules_pb2_grpc.RulesServiceStub"):
                with patch(
                    "src.interfaces.rpc.client.devices_pb2_grpc.DevicesServiceStub"
                ):
                    with patch(
                        "src.interfaces.rpc.client.config_pb2_grpc.ConfigServiceStub"
                    ):
                        with patch(
                            "src.interfaces.rpc.client.logs_pb2_grpc.LogsServiceStub"
                        ):
                            with patch(
                                "src.interfaces.rpc.client.membership_pb2_grpc.MembershipServiceStub"
                            ):
                                client = GrpcClient()
                                client.connect()
                                client.disconnect()

        mock_channel.close.assert_called_once()
        assert client._channel is None

    def test_disconnect_without_connect(self) -> None:
        """Test disconnect() is safe to call without connect."""
        from src.interfaces.rpc.client import GrpcClient

        client = GrpcClient()
        # Should not raise
        client.disconnect()

    @patch("src.interfaces.rpc.client.grpc.insecure_channel")
    def test_context_manager_support(self, mock_channel_factory: MagicMock) -> None:
        """Test client works as context manager."""
        from src.interfaces.rpc.client import GrpcClient

        mock_channel = MagicMock()
        mock_channel_factory.return_value = mock_channel

        with patch("src.interfaces.rpc.client.lifecycle_pb2_grpc.LifecycleServiceStub"):
            with patch("src.interfaces.rpc.client.rules_pb2_grpc.RulesServiceStub"):
                with patch(
                    "src.interfaces.rpc.client.devices_pb2_grpc.DevicesServiceStub"
                ):
                    with patch(
                        "src.interfaces.rpc.client.config_pb2_grpc.ConfigServiceStub"
                    ):
                        with patch(
                            "src.interfaces.rpc.client.logs_pb2_grpc.LogsServiceStub"
                        ):
                            with patch(
                                "src.interfaces.rpc.client.membership_pb2_grpc.MembershipServiceStub"
                            ):
                                with GrpcClient() as client:
                                    assert client._channel is not None

        # Verify channel closed after context exit
        mock_channel.close.assert_called_once()


class TestLifecycleServiceMethods:
    """Test LifecycleService methods."""

    @patch("src.interfaces.rpc.client.grpc.insecure_channel")
    def test_start(self, mock_channel_factory: MagicMock) -> None:
        """Test start() method."""
        from src.interfaces.rpc.client import GrpcClient
        from src.interfaces.rpc.generated import lifecycle_pb2

        mock_channel = MagicMock()
        mock_channel_factory.return_value = mock_channel
        mock_stub = MagicMock()

        with patch(
            "src.interfaces.rpc.client.lifecycle_pb2_grpc.LifecycleServiceStub",
            return_value=mock_stub,
        ):
            with patch("src.interfaces.rpc.client.rules_pb2_grpc.RulesServiceStub"):
                with patch(
                    "src.interfaces.rpc.client.devices_pb2_grpc.DevicesServiceStub"
                ):
                    with patch(
                        "src.interfaces.rpc.client.config_pb2_grpc.ConfigServiceStub"
                    ):
                        with patch(
                            "src.interfaces.rpc.client.logs_pb2_grpc.LogsServiceStub"
                        ):
                            with patch(
                                "src.interfaces.rpc.client.membership_pb2_grpc.MembershipServiceStub"
                            ):
                                mock_stub.Start.return_value = (
                                    lifecycle_pb2.StartResponse(
                                        success=True,
                                        message="System started successfully",
                                    )
                                )

                                client = GrpcClient()
                                client.connect()
                                result = client.start()

                                assert result["success"] is True
                                assert (
                                    result["message"] == "System started successfully"
                                )

    @patch("src.interfaces.rpc.client.grpc.insecure_channel")
    def test_stop(self, mock_channel_factory: MagicMock) -> None:
        """Test stop() method."""
        from src.interfaces.rpc.client import GrpcClient
        from src.interfaces.rpc.generated import lifecycle_pb2

        mock_channel = MagicMock()
        mock_channel_factory.return_value = mock_channel
        mock_stub = MagicMock()

        with patch(
            "src.interfaces.rpc.client.lifecycle_pb2_grpc.LifecycleServiceStub",
            return_value=mock_stub,
        ):
            with patch("src.interfaces.rpc.client.rules_pb2_grpc.RulesServiceStub"):
                with patch(
                    "src.interfaces.rpc.client.devices_pb2_grpc.DevicesServiceStub"
                ):
                    with patch(
                        "src.interfaces.rpc.client.config_pb2_grpc.ConfigServiceStub"
                    ):
                        with patch(
                            "src.interfaces.rpc.client.logs_pb2_grpc.LogsServiceStub"
                        ):
                            with patch(
                                "src.interfaces.rpc.client.membership_pb2_grpc.MembershipServiceStub"
                            ):
                                mock_stub.Stop.return_value = (
                                    lifecycle_pb2.StopResponse(
                                        success=True,
                                        message="System stopped successfully",
                                    )
                                )

                                client = GrpcClient()
                                client.connect()
                                result = client.stop()

                                assert result["success"] is True
                                assert (
                                    result["message"] == "System stopped successfully"
                                )

    @patch("src.interfaces.rpc.client.grpc.insecure_channel")
    def test_get_status(self, mock_channel_factory: MagicMock) -> None:
        """Test get_status() method."""
        from src.interfaces.rpc.client import GrpcClient
        from src.interfaces.rpc.generated import common_pb2, lifecycle_pb2

        mock_channel = MagicMock()
        mock_channel_factory.return_value = mock_channel
        mock_stub = MagicMock()

        with patch(
            "src.interfaces.rpc.client.lifecycle_pb2_grpc.LifecycleServiceStub",
            return_value=mock_stub,
        ):
            with patch("src.interfaces.rpc.client.rules_pb2_grpc.RulesServiceStub"):
                with patch(
                    "src.interfaces.rpc.client.devices_pb2_grpc.DevicesServiceStub"
                ):
                    with patch(
                        "src.interfaces.rpc.client.config_pb2_grpc.ConfigServiceStub"
                    ):
                        with patch(
                            "src.interfaces.rpc.client.logs_pb2_grpc.LogsServiceStub"
                        ):
                            with patch(
                                "src.interfaces.rpc.client.membership_pb2_grpc.MembershipServiceStub"
                            ):
                                mock_stub.GetStatus.return_value = (
                                    lifecycle_pb2.GetStatusResponse(
                                        status=common_pb2.Status(
                                            state=common_pb2.SystemState.RUNNING,
                                            uptime_seconds=120,
                                            version="0.1.0",
                                        ),
                                        message="System running",
                                    )
                                )

                                client = GrpcClient()
                                client.connect()
                                result = client.get_status()

                                assert result["state"] == "running"
                                assert result["uptime_seconds"] == 120
                                assert result["version"] == "0.1.0"

    @patch("src.interfaces.rpc.client.grpc.insecure_channel")
    def test_get_system_info(self, mock_channel_factory: MagicMock) -> None:
        """Test get_system_info() method."""
        from src.interfaces.rpc.client import GrpcClient
        from src.interfaces.rpc.generated import lifecycle_pb2

        mock_channel = MagicMock()
        mock_channel_factory.return_value = mock_channel
        mock_stub = MagicMock()

        with patch(
            "src.interfaces.rpc.client.lifecycle_pb2_grpc.LifecycleServiceStub",
            return_value=mock_stub,
        ):
            with patch("src.interfaces.rpc.client.rules_pb2_grpc.RulesServiceStub"):
                with patch(
                    "src.interfaces.rpc.client.devices_pb2_grpc.DevicesServiceStub"
                ):
                    with patch(
                        "src.interfaces.rpc.client.config_pb2_grpc.ConfigServiceStub"
                    ):
                        with patch(
                            "src.interfaces.rpc.client.logs_pb2_grpc.LogsServiceStub"
                        ):
                            with patch(
                                "src.interfaces.rpc.client.membership_pb2_grpc.MembershipServiceStub"
                            ):
                                mock_stub.GetSystemInfo.return_value = (
                                    lifecycle_pb2.GetSystemInfoResponse(
                                        name="iot-fuzzy-llm",
                                        version="0.1.0",
                                        uptime_seconds=300,
                                        python_version="3.9.0",
                                        running_components=["mqtt", "ollama"],
                                    )
                                )

                                client = GrpcClient()
                                client.connect()
                                result = client.get_system_info()

                                assert result["name"] == "iot-fuzzy-llm"
                                assert result["version"] == "0.1.0"
                                assert result["uptime_seconds"] == 300
                                assert result["python_version"] == "3.9.0"
                                assert result["running_components"] == [
                                    "mqtt",
                                    "ollama",
                                ]


class TestRulesServiceMethods:
    """Test RulesService methods."""

    @patch("src.interfaces.rpc.client.grpc.insecure_channel")
    def test_add_rule(self, mock_channel_factory: MagicMock) -> None:
        """Test add_rule() method."""
        from src.interfaces.rpc.client import GrpcClient
        from src.interfaces.rpc.generated import rules_pb2

        mock_channel = MagicMock()
        mock_channel_factory.return_value = mock_channel
        mock_stub = MagicMock()

        with patch("src.interfaces.rpc.client.lifecycle_pb2_grpc.LifecycleServiceStub"):
            with patch(
                "src.interfaces.rpc.client.rules_pb2_grpc.RulesServiceStub",
                return_value=mock_stub,
            ):
                with patch(
                    "src.interfaces.rpc.client.devices_pb2_grpc.DevicesServiceStub"
                ):
                    with patch(
                        "src.interfaces.rpc.client.config_pb2_grpc.ConfigServiceStub"
                    ):
                        with patch(
                            "src.interfaces.rpc.client.logs_pb2_grpc.LogsServiceStub"
                        ):
                            with patch(
                                "src.interfaces.rpc.client.membership_pb2_grpc.MembershipServiceStub"
                            ):
                                mock_stub.AddRule.return_value = (
                                    rules_pb2.AddRuleResponse(
                                        rule=rules_pb2.Rule(
                                            id="rule123",
                                            text="If hot, turn on AC",
                                            enabled=True,
                                        )
                                    )
                                )

                                client = GrpcClient()
                                client.connect()
                                result = client.add_rule("If hot, turn on AC")

                                assert result["rule"]["id"] == "rule123"
                                assert result["rule"]["text"] == "If hot, turn on AC"
                                assert result["rule"]["enabled"] is True

    @patch("src.interfaces.rpc.client.grpc.insecure_channel")
    def test_remove_rule(self, mock_channel_factory: MagicMock) -> None:
        """Test remove_rule() method."""
        from src.interfaces.rpc.client import GrpcClient
        from src.interfaces.rpc.generated import rules_pb2

        mock_channel = MagicMock()
        mock_channel_factory.return_value = mock_channel
        mock_stub = MagicMock()

        with patch("src.interfaces.rpc.client.lifecycle_pb2_grpc.LifecycleServiceStub"):
            with patch(
                "src.interfaces.rpc.client.rules_pb2_grpc.RulesServiceStub",
                return_value=mock_stub,
            ):
                with patch(
                    "src.interfaces.rpc.client.devices_pb2_grpc.DevicesServiceStub"
                ):
                    with patch(
                        "src.interfaces.rpc.client.config_pb2_grpc.ConfigServiceStub"
                    ):
                        with patch(
                            "src.interfaces.rpc.client.logs_pb2_grpc.LogsServiceStub"
                        ):
                            with patch(
                                "src.interfaces.rpc.client.membership_pb2_grpc.MembershipServiceStub"
                            ):
                                mock_stub.RemoveRule.return_value = (
                                    rules_pb2.RemoveRuleResponse(
                                        success=True,
                                    )
                                )

                                client = GrpcClient()
                                client.connect()
                                result = client.remove_rule("rule123")

                                assert result["success"] is True

    @patch("src.interfaces.rpc.client.grpc.insecure_channel")
    def test_list_rules(self, mock_channel_factory: MagicMock) -> None:
        """Test list_rules() method."""
        from src.interfaces.rpc.client import GrpcClient
        from src.interfaces.rpc.generated import common_pb2, rules_pb2

        mock_channel = MagicMock()
        mock_channel_factory.return_value = mock_channel
        mock_stub = MagicMock()

        with patch("src.interfaces.rpc.client.lifecycle_pb2_grpc.LifecycleServiceStub"):
            with patch(
                "src.interfaces.rpc.client.rules_pb2_grpc.RulesServiceStub",
                return_value=mock_stub,
            ):
                with patch(
                    "src.interfaces.rpc.client.devices_pb2_grpc.DevicesServiceStub"
                ):
                    with patch(
                        "src.interfaces.rpc.client.config_pb2_grpc.ConfigServiceStub"
                    ):
                        with patch(
                            "src.interfaces.rpc.client.logs_pb2_grpc.LogsServiceStub"
                        ):
                            with patch(
                                "src.interfaces.rpc.client.membership_pb2_grpc.MembershipServiceStub"
                            ):
                                mock_stub.ListRules.return_value = (
                                    rules_pb2.ListRulesResponse(
                                        rules=[
                                            rules_pb2.Rule(
                                                id="rule1",
                                                text="If hot, turn on AC",
                                                enabled=True,
                                            )
                                        ],
                                        pagination=common_pb2.PaginationResponse(
                                            total=1,
                                            has_more=False,
                                        ),
                                    )
                                )

                                client = GrpcClient()
                                client.connect()
                                result = client.list_rules(limit=100, offset=0)

                                assert len(result["rules"]) == 1
                                assert result["rules"][0]["id"] == "rule1"
                                assert result["pagination"]["total"] == 1
                                assert result["pagination"]["has_more"] is False

    @patch("src.interfaces.rpc.client.grpc.insecure_channel")
    def test_get_rule(self, mock_channel_factory: MagicMock) -> None:
        """Test get_rule() method."""
        from src.interfaces.rpc.client import GrpcClient
        from src.interfaces.rpc.generated import rules_pb2

        mock_channel = MagicMock()
        mock_channel_factory.return_value = mock_channel
        mock_stub = MagicMock()

        with patch("src.interfaces.rpc.client.lifecycle_pb2_grpc.LifecycleServiceStub"):
            with patch(
                "src.interfaces.rpc.client.rules_pb2_grpc.RulesServiceStub",
                return_value=mock_stub,
            ):
                with patch(
                    "src.interfaces.rpc.client.devices_pb2_grpc.DevicesServiceStub"
                ):
                    with patch(
                        "src.interfaces.rpc.client.config_pb2_grpc.ConfigServiceStub"
                    ):
                        with patch(
                            "src.interfaces.rpc.client.logs_pb2_grpc.LogsServiceStub"
                        ):
                            with patch(
                                "src.interfaces.rpc.client.membership_pb2_grpc.MembershipServiceStub"
                            ):
                                mock_stub.GetRule.return_value = (
                                    rules_pb2.GetRuleResponse(
                                        rule=rules_pb2.Rule(
                                            id="rule123",
                                            text="If hot, turn on AC",
                                            enabled=True,
                                        )
                                    )
                                )

                                client = GrpcClient()
                                client.connect()
                                result = client.get_rule("rule123")

                                assert result["id"] == "rule123"
                                assert result["text"] == "If hot, turn on AC"
                                assert result["enabled"] is True

    @patch("src.interfaces.rpc.client.grpc.insecure_channel")
    def test_enable_rule(self, mock_channel_factory: MagicMock) -> None:
        """Test enable_rule() method."""
        from src.interfaces.rpc.client import GrpcClient
        from src.interfaces.rpc.generated import rules_pb2

        mock_channel = MagicMock()
        mock_channel_factory.return_value = mock_channel
        mock_stub = MagicMock()

        with patch("src.interfaces.rpc.client.lifecycle_pb2_grpc.LifecycleServiceStub"):
            with patch(
                "src.interfaces.rpc.client.rules_pb2_grpc.RulesServiceStub",
                return_value=mock_stub,
            ):
                with patch(
                    "src.interfaces.rpc.client.devices_pb2_grpc.DevicesServiceStub"
                ):
                    with patch(
                        "src.interfaces.rpc.client.config_pb2_grpc.ConfigServiceStub"
                    ):
                        with patch(
                            "src.interfaces.rpc.client.logs_pb2_grpc.LogsServiceStub"
                        ):
                            with patch(
                                "src.interfaces.rpc.client.membership_pb2_grpc.MembershipServiceStub"
                            ):
                                mock_stub.EnableRule.return_value = (
                                    rules_pb2.EnableRuleResponse(
                                        success=True,
                                    )
                                )

                                client = GrpcClient()
                                client.connect()
                                result = client.enable_rule("rule123")

                                assert result["success"] is True

    @patch("src.interfaces.rpc.client.grpc.insecure_channel")
    def test_disable_rule(self, mock_channel_factory: MagicMock) -> None:
        """Test disable_rule() method."""
        from src.interfaces.rpc.client import GrpcClient
        from src.interfaces.rpc.generated import rules_pb2

        mock_channel = MagicMock()
        mock_channel_factory.return_value = mock_channel
        mock_stub = MagicMock()

        with patch("src.interfaces.rpc.client.lifecycle_pb2_grpc.LifecycleServiceStub"):
            with patch(
                "src.interfaces.rpc.client.rules_pb2_grpc.RulesServiceStub",
                return_value=mock_stub,
            ):
                with patch(
                    "src.interfaces.rpc.client.devices_pb2_grpc.DevicesServiceStub"
                ):
                    with patch(
                        "src.interfaces.rpc.client.config_pb2_grpc.ConfigServiceStub"
                    ):
                        with patch(
                            "src.interfaces.rpc.client.logs_pb2_grpc.LogsServiceStub"
                        ):
                            with patch(
                                "src.interfaces.rpc.client.membership_pb2_grpc.MembershipServiceStub"
                            ):
                                mock_stub.DisableRule.return_value = (
                                    rules_pb2.DisableRuleResponse(
                                        success=True,
                                    )
                                )

                                client = GrpcClient()
                                client.connect()
                                result = client.disable_rule("rule123")

                                assert result["success"] is True

    @patch("src.interfaces.rpc.client.grpc.insecure_channel")
    def test_evaluate_rules(self, mock_channel_factory: MagicMock) -> None:
        """Test evaluate_rules() method."""
        from src.interfaces.rpc.client import GrpcClient
        from src.interfaces.rpc.generated import rules_pb2

        mock_channel = MagicMock()
        mock_channel_factory.return_value = mock_channel
        mock_stub = MagicMock()

        with patch("src.interfaces.rpc.client.lifecycle_pb2_grpc.LifecycleServiceStub"):
            with patch(
                "src.interfaces.rpc.client.rules_pb2_grpc.RulesServiceStub",
                return_value=mock_stub,
            ):
                with patch(
                    "src.interfaces.rpc.client.devices_pb2_grpc.DevicesServiceStub"
                ):
                    with patch(
                        "src.interfaces.rpc.client.config_pb2_grpc.ConfigServiceStub"
                    ):
                        with patch(
                            "src.interfaces.rpc.client.logs_pb2_grpc.LogsServiceStub"
                        ):
                            with patch(
                                "src.interfaces.rpc.client.membership_pb2_grpc.MembershipServiceStub"
                            ):
                                mock_stub.EvaluateRules.return_value = (
                                    rules_pb2.EvaluateRulesResponse(
                                        commands_generated=[
                                            "turn_on(ac)",
                                            "set_temp(22)",
                                        ],
                                        rules_evaluated=2,
                                    )
                                )

                                client = GrpcClient()
                                client.connect()
                                result = client.evaluate_rules()

                                assert result["commands_generated"] == [
                                    "turn_on(ac)",
                                    "set_temp(22)",
                                ]
                                assert result["rules_evaluated"] == 2


class TestDevicesServiceMethods:
    """Test DevicesService methods."""

    @patch("src.interfaces.rpc.client.grpc.insecure_channel")
    def test_list_devices(self, mock_channel_factory: MagicMock) -> None:
        """Test list_devices() method."""
        from src.interfaces.rpc.client import GrpcClient
        from src.interfaces.rpc.generated import devices_pb2

        mock_channel = MagicMock()
        mock_channel_factory.return_value = mock_channel
        mock_stub = MagicMock()

        with patch("src.interfaces.rpc.client.lifecycle_pb2_grpc.LifecycleServiceStub"):
            with patch("src.interfaces.rpc.client.rules_pb2_grpc.RulesServiceStub"):
                with patch(
                    "src.interfaces.rpc.client.devices_pb2_grpc.DevicesServiceStub",
                    return_value=mock_stub,
                ):
                    with patch(
                        "src.interfaces.rpc.client.config_pb2_grpc.ConfigServiceStub"
                    ):
                        with patch(
                            "src.interfaces.rpc.client.logs_pb2_grpc.LogsServiceStub"
                        ):
                            with patch(
                                "src.interfaces.rpc.client.membership_pb2_grpc.MembershipServiceStub"
                            ):
                                mock_stub.ListDevices.return_value = (
                                    devices_pb2.ListDevicesResponse(
                                        devices=[
                                            devices_pb2.Device(
                                                id="sensor1",
                                                name="Living Room Sensor",
                                                type="temperature",
                                                location="living_room",
                                                capabilities=["temperature"],
                                            )
                                        ]
                                    )
                                )

                                client = GrpcClient()
                                client.connect()
                                result = client.list_devices()

                                assert len(result) == 1
                                assert result[0]["id"] == "sensor1"
                                assert result[0]["name"] == "Living Room Sensor"

    @patch("src.interfaces.rpc.client.grpc.insecure_channel")
    def test_get_device(self, mock_channel_factory: MagicMock) -> None:
        """Test get_device() method."""
        from src.interfaces.rpc.client import GrpcClient
        from src.interfaces.rpc.generated import devices_pb2

        mock_channel = MagicMock()
        mock_channel_factory.return_value = mock_channel
        mock_stub = MagicMock()

        with patch("src.interfaces.rpc.client.lifecycle_pb2_grpc.LifecycleServiceStub"):
            with patch("src.interfaces.rpc.client.rules_pb2_grpc.RulesServiceStub"):
                with patch(
                    "src.interfaces.rpc.client.devices_pb2_grpc.DevicesServiceStub",
                    return_value=mock_stub,
                ):
                    with patch(
                        "src.interfaces.rpc.client.config_pb2_grpc.ConfigServiceStub"
                    ):
                        with patch(
                            "src.interfaces.rpc.client.logs_pb2_grpc.LogsServiceStub"
                        ):
                            with patch(
                                "src.interfaces.rpc.client.membership_pb2_grpc.MembershipServiceStub"
                            ):
                                mock_stub.GetDevice.return_value = (
                                    devices_pb2.GetDeviceResponse(
                                        device=devices_pb2.Device(
                                            id="sensor1",
                                            name="Living Room Sensor",
                                            type="temperature",
                                            location="living_room",
                                            capabilities=["temperature"],
                                        )
                                    )
                                )

                                client = GrpcClient()
                                client.connect()
                                result = client.get_device("sensor1")

                                assert result["id"] == "sensor1"
                                assert result["name"] == "Living Room Sensor"

    @patch("src.interfaces.rpc.client.grpc.insecure_channel")
    def test_send_command(self, mock_channel_factory: MagicMock) -> None:
        """Test send_command() method."""
        from src.interfaces.rpc.client import GrpcClient
        from src.interfaces.rpc.generated import devices_pb2

        mock_channel = MagicMock()
        mock_channel_factory.return_value = mock_channel
        mock_stub = MagicMock()

        with patch("src.interfaces.rpc.client.lifecycle_pb2_grpc.LifecycleServiceStub"):
            with patch("src.interfaces.rpc.client.rules_pb2_grpc.RulesServiceStub"):
                with patch(
                    "src.interfaces.rpc.client.devices_pb2_grpc.DevicesServiceStub",
                    return_value=mock_stub,
                ):
                    with patch(
                        "src.interfaces.rpc.client.config_pb2_grpc.ConfigServiceStub"
                    ):
                        with patch(
                            "src.interfaces.rpc.client.logs_pb2_grpc.LogsServiceStub"
                        ):
                            with patch(
                                "src.interfaces.rpc.client.membership_pb2_grpc.MembershipServiceStub"
                            ):
                                mock_stub.SendCommand.return_value = (
                                    devices_pb2.SendCommandResponse(
                                        success=True,
                                        message="Command sent",
                                    )
                                )

                                client = GrpcClient()
                                client.connect()
                                result = client.send_command(
                                    "ac1", "turn_on", {"temp": "22"}
                                )

                                assert result["success"] is True
                                assert result["message"] == "Command sent"


class TestConfigServiceMethods:
    """Test ConfigService methods."""

    @patch("src.interfaces.rpc.client.grpc.insecure_channel")
    def test_get_config(self, mock_channel_factory: MagicMock) -> None:
        """Test get_config() method."""
        from src.interfaces.rpc.client import GrpcClient
        from src.interfaces.rpc.generated import config_pb2

        mock_channel = MagicMock()
        mock_channel_factory.return_value = mock_channel
        mock_stub = MagicMock()

        with patch("src.interfaces.rpc.client.lifecycle_pb2_grpc.LifecycleServiceStub"):
            with patch("src.interfaces.rpc.client.rules_pb2_grpc.RulesServiceStub"):
                with patch(
                    "src.interfaces.rpc.client.devices_pb2_grpc.DevicesServiceStub"
                ):
                    with patch(
                        "src.interfaces.rpc.client.config_pb2_grpc.ConfigServiceStub",
                        return_value=mock_stub,
                    ):
                        with patch(
                            "src.interfaces.rpc.client.logs_pb2_grpc.LogsServiceStub"
                        ):
                            with patch(
                                "src.interfaces.rpc.client.membership_pb2_grpc.MembershipServiceStub"
                            ):
                                mock_stub.GetConfig.return_value = (
                                    config_pb2.GetConfigResponse(
                                        config=config_pb2.ConfigFile(
                                            name="mqtt_config",
                                            content='{"broker": "localhost"}',
                                            version="v1",
                                        )
                                    )
                                )

                                client = GrpcClient()
                                client.connect()
                                result = client.get_config("mqtt_config")

                                assert result["content"] == {"broker": "localhost"}
                                assert result["version"] == "v1"

    @patch("src.interfaces.rpc.client.grpc.insecure_channel")
    def test_list_configs(self, mock_channel_factory: MagicMock) -> None:
        """Test list_configs() method."""
        from src.interfaces.rpc.client import GrpcClient
        from src.interfaces.rpc.generated import config_pb2

        mock_channel = MagicMock()
        mock_channel_factory.return_value = mock_channel
        mock_stub = MagicMock()

        with patch("src.interfaces.rpc.client.lifecycle_pb2_grpc.LifecycleServiceStub"):
            with patch("src.interfaces.rpc.client.rules_pb2_grpc.RulesServiceStub"):
                with patch(
                    "src.interfaces.rpc.client.devices_pb2_grpc.DevicesServiceStub"
                ):
                    with patch(
                        "src.interfaces.rpc.client.config_pb2_grpc.ConfigServiceStub",
                        return_value=mock_stub,
                    ):
                        with patch(
                            "src.interfaces.rpc.client.logs_pb2_grpc.LogsServiceStub"
                        ):
                            with patch(
                                "src.interfaces.rpc.client.membership_pb2_grpc.MembershipServiceStub"
                            ):
                                mock_stub.ListConfigs.return_value = (
                                    config_pb2.ListConfigsResponse(
                                        names=["mqtt_config", "llm_config", "devices"]
                                    )
                                )

                                client = GrpcClient()
                                client.connect()
                                result = client.list_configs()

                                assert result == [
                                    "mqtt_config",
                                    "llm_config",
                                    "devices",
                                ]


class TestMembershipServiceMethods:
    """Test MembershipService methods."""

    @patch("src.interfaces.rpc.client.grpc.insecure_channel")
    def test_update_membership_function(self, mock_channel_factory: MagicMock) -> None:
        """Test update_membership_function() method."""
        from src.interfaces.rpc.client import GrpcClient
        from src.interfaces.rpc.generated import membership_pb2

        mock_channel = MagicMock()
        mock_channel_factory.return_value = mock_channel
        mock_stub = MagicMock()

        with patch("src.interfaces.rpc.client.lifecycle_pb2_grpc.LifecycleServiceStub"):
            with patch("src.interfaces.rpc.client.rules_pb2_grpc.RulesServiceStub"):
                with patch(
                    "src.interfaces.rpc.client.devices_pb2_grpc.DevicesServiceStub"
                ):
                    with patch(
                        "src.interfaces.rpc.client.config_pb2_grpc.ConfigServiceStub"
                    ):
                        with patch(
                            "src.interfaces.rpc.client.logs_pb2_grpc.LogsServiceStub"
                        ):
                            with patch(
                                "src.interfaces.rpc.client.membership_pb2_grpc.MembershipServiceStub",
                                return_value=mock_stub,
                            ):
                                mock_stub.UpdateMembershipFunction.return_value = (
                                    membership_pb2.UpdateMembershipFunctionResponse(
                                        success=True,
                                        message="Membership function updated",
                                    )
                                )

                                client = GrpcClient()
                                client.connect()
                                result = client.update_membership_function(
                                    sensor_type="temperature",
                                    variable_name="temperature",
                                    function_name="cold",
                                    function_type="trapezoidal",
                                    parameters={
                                        "a": 0.0,
                                        "b": 10.0,
                                        "c": 15.0,
                                        "d": 20.0,
                                    },
                                )

                                assert result["success"] is True
                                assert (
                                    result["message"] == "Membership function updated"
                                )


class TestErrorHandling:
    """Test gRPC error handling and conversion to Python exceptions."""

    @patch("src.interfaces.rpc.client.grpc.insecure_channel")
    def test_not_found_error_on_get_device(
        self, mock_channel_factory: MagicMock
    ) -> None:
        """Test NOT_FOUND error raises DeviceError."""
        from src.interfaces.rpc.client import GrpcClient

        mock_channel = MagicMock()
        mock_channel_factory.return_value = mock_channel
        mock_stub = MagicMock()

        with patch("src.interfaces.rpc.client.lifecycle_pb2_grpc.LifecycleServiceStub"):
            with patch("src.interfaces.rpc.client.rules_pb2_grpc.RulesServiceStub"):
                with patch(
                    "src.interfaces.rpc.client.devices_pb2_grpc.DevicesServiceStub",
                    return_value=mock_stub,
                ):
                    with patch(
                        "src.interfaces.rpc.client.config_pb2_grpc.ConfigServiceStub"
                    ):
                        with patch(
                            "src.interfaces.rpc.client.logs_pb2_grpc.LogsServiceStub"
                        ):
                            with patch(
                                "src.interfaces.rpc.client.membership_pb2_grpc.MembershipServiceStub"
                            ):
                                # Mock gRPC NOT_FOUND error
                                mock_stub.GetDevice.side_effect = grpc.RpcError()
                                mock_stub.GetDevice.side_effect.code = lambda: (
                                    grpc.StatusCode.NOT_FOUND
                                )
                                mock_stub.GetDevice.side_effect.details = lambda: (
                                    "Device not found"
                                )

                                client = GrpcClient()
                                client.connect()

                                with pytest.raises(
                                    DeviceError, match="Device not found"
                                ):
                                    client.get_device("nonexistent")

    @patch("src.interfaces.rpc.client.grpc.insecure_channel")
    def test_not_found_error_on_get_rule(self, mock_channel_factory: MagicMock) -> None:
        """Test NOT_FOUND error raises RuleError."""
        from src.interfaces.rpc.client import GrpcClient

        mock_channel = MagicMock()
        mock_channel_factory.return_value = mock_channel
        mock_stub = MagicMock()

        with patch("src.interfaces.rpc.client.lifecycle_pb2_grpc.LifecycleServiceStub"):
            with patch(
                "src.interfaces.rpc.client.rules_pb2_grpc.RulesServiceStub",
                return_value=mock_stub,
            ):
                with patch(
                    "src.interfaces.rpc.client.devices_pb2_grpc.DevicesServiceStub"
                ):
                    with patch(
                        "src.interfaces.rpc.client.config_pb2_grpc.ConfigServiceStub"
                    ):
                        with patch(
                            "src.interfaces.rpc.client.logs_pb2_grpc.LogsServiceStub"
                        ):
                            with patch(
                                "src.interfaces.rpc.client.membership_pb2_grpc.MembershipServiceStub"
                            ):
                                # Mock gRPC NOT_FOUND error
                                mock_stub.GetRule.side_effect = grpc.RpcError()
                                mock_stub.GetRule.side_effect.code = lambda: (
                                    grpc.StatusCode.NOT_FOUND
                                )
                                mock_stub.GetRule.side_effect.details = lambda: (
                                    "Rule not found"
                                )

                                client = GrpcClient()
                                client.connect()

                                with pytest.raises(RuleError, match="Rule not found"):
                                    client.get_rule("nonexistent")

    @patch("src.interfaces.rpc.client.grpc.insecure_channel")
    def test_unavailable_error(self, mock_channel_factory: MagicMock) -> None:
        """Test UNAVAILABLE error raises IoTFuzzyLLMError."""
        from src.interfaces.rpc.client import GrpcClient

        mock_channel = MagicMock()
        mock_channel_factory.return_value = mock_channel
        mock_stub = MagicMock()

        with patch(
            "src.interfaces.rpc.client.lifecycle_pb2_grpc.LifecycleServiceStub",
            return_value=mock_stub,
        ):
            with patch("src.interfaces.rpc.client.rules_pb2_grpc.RulesServiceStub"):
                with patch(
                    "src.interfaces.rpc.client.devices_pb2_grpc.DevicesServiceStub"
                ):
                    with patch(
                        "src.interfaces.rpc.client.config_pb2_grpc.ConfigServiceStub"
                    ):
                        with patch(
                            "src.interfaces.rpc.client.logs_pb2_grpc.LogsServiceStub"
                        ):
                            with patch(
                                "src.interfaces.rpc.client.membership_pb2_grpc.MembershipServiceStub"
                            ):
                                # Mock gRPC UNAVAILABLE error
                                mock_stub.Start.side_effect = grpc.RpcError()
                                mock_stub.Start.side_effect.code = lambda: (
                                    grpc.StatusCode.UNAVAILABLE
                                )
                                mock_stub.Start.side_effect.details = lambda: (
                                    "Server unavailable"
                                )

                                client = GrpcClient()
                                client.connect()

                                with pytest.raises(
                                    IoTFuzzyLLMError, match="gRPC server unavailable"
                                ):
                                    client.start()

    @patch("src.interfaces.rpc.client.grpc.insecure_channel")
    def test_invalid_argument_error(self, mock_channel_factory: MagicMock) -> None:
        """Test INVALID_ARGUMENT error raises ValidationError."""
        from src.interfaces.rpc.client import GrpcClient

        mock_channel = MagicMock()
        mock_channel_factory.return_value = mock_channel
        mock_stub = MagicMock()

        with patch("src.interfaces.rpc.client.lifecycle_pb2_grpc.LifecycleServiceStub"):
            with patch(
                "src.interfaces.rpc.client.rules_pb2_grpc.RulesServiceStub",
                return_value=mock_stub,
            ):
                with patch(
                    "src.interfaces.rpc.client.devices_pb2_grpc.DevicesServiceStub"
                ):
                    with patch(
                        "src.interfaces.rpc.client.config_pb2_grpc.ConfigServiceStub"
                    ):
                        with patch(
                            "src.interfaces.rpc.client.logs_pb2_grpc.LogsServiceStub"
                        ):
                            with patch(
                                "src.interfaces.rpc.client.membership_pb2_grpc.MembershipServiceStub"
                            ):
                                # Mock gRPC INVALID_ARGUMENT error
                                mock_stub.AddRule.side_effect = grpc.RpcError()
                                mock_stub.AddRule.side_effect.code = lambda: (
                                    grpc.StatusCode.INVALID_ARGUMENT
                                )
                                mock_stub.AddRule.side_effect.details = lambda: (
                                    "Invalid rule text"
                                )

                                client = GrpcClient()
                                client.connect()

                                with pytest.raises(
                                    ValidationError, match="Invalid rule text"
                                ):
                                    client.add_rule("")
