"""Tests for gRPC error mapping and exception handling."""

from __future__ import annotations

from unittest.mock import MagicMock

import grpc

from src.common.exceptions import (
    ConfigurationError,
    DeviceError,
    IoTFuzzyLLMError,
    MQTTError,
    OllamaError,
    RuleError,
    ValidationError,
)
from src.interfaces.rpc.error_mapping import (
    exception_to_status,
    handle_grpc_errors,
)


class TestExceptionToStatus:
    """Test exception_to_status() mapping function."""

    def test_iot_fuzzy_llm_error_maps_to_internal(self) -> None:
        """IoTFuzzyLLMError should map to INTERNAL status code."""
        exc = IoTFuzzyLLMError("base error")
        assert exception_to_status(exc) == grpc.StatusCode.INTERNAL

    def test_configuration_error_maps_to_invalid_argument(self) -> None:
        """ConfigurationError should map to INVALID_ARGUMENT status code."""
        exc = ConfigurationError("bad config")
        assert exception_to_status(exc) == grpc.StatusCode.INVALID_ARGUMENT

    def test_validation_error_maps_to_invalid_argument(self) -> None:
        """ValidationError should map to INVALID_ARGUMENT status code."""
        exc = ValidationError("invalid data")
        assert exception_to_status(exc) == grpc.StatusCode.INVALID_ARGUMENT

    def test_device_error_maps_to_unavailable(self) -> None:
        """DeviceError should map to UNAVAILABLE status code."""
        exc = DeviceError("device not found")
        assert exception_to_status(exc) == grpc.StatusCode.UNAVAILABLE

    def test_mqtt_error_maps_to_unavailable(self) -> None:
        """MQTTError should map to UNAVAILABLE status code."""
        exc = MQTTError("connection failed")
        assert exception_to_status(exc) == grpc.StatusCode.UNAVAILABLE

    def test_ollama_error_maps_to_unavailable(self) -> None:
        """OllamaError should map to UNAVAILABLE status code."""
        exc = OllamaError("llm service down")
        assert exception_to_status(exc) == grpc.StatusCode.UNAVAILABLE

    def test_rule_error_maps_to_invalid_argument(self) -> None:
        """RuleError should map to INVALID_ARGUMENT status code."""
        exc = RuleError("invalid rule syntax")
        assert exception_to_status(exc) == grpc.StatusCode.INVALID_ARGUMENT

    def test_generic_exception_maps_to_internal(self) -> None:
        """Generic Exception should map to INTERNAL status code."""
        exc = Exception("unknown error")
        assert exception_to_status(exc) == grpc.StatusCode.INTERNAL


class TestHandleGrpcErrorsDecorator:
    """Test @handle_grpc_errors decorator."""

    def test_decorator_returns_result_on_success(self) -> None:
        """Decorator should return function result on success."""

        @handle_grpc_errors
        def successful_method(self: object, request: object, context: object) -> str:
            return "success"

        context = MagicMock()
        result = successful_method(None, None, context)
        assert result == "success"
        context.abort.assert_not_called()

    def test_decorator_catches_configuration_error(self) -> None:
        """Decorator should catch ConfigurationError and abort."""

        @handle_grpc_errors
        def failing_method(self: object, request: object, context: object) -> str:
            raise ConfigurationError("bad config")

        context = MagicMock()
        failing_method(None, None, context)
        context.abort.assert_called_once()
        call_args = context.abort.call_args
        assert call_args[0][0] == grpc.StatusCode.INVALID_ARGUMENT
        assert "bad config" in call_args[0][1]

    def test_decorator_catches_validation_error(self) -> None:
        """Decorator should catch ValidationError and abort."""

        @handle_grpc_errors
        def failing_method(self: object, request: object, context: object) -> str:
            raise ValidationError("invalid data")

        context = MagicMock()
        failing_method(None, None, context)
        context.abort.assert_called_once()
        call_args = context.abort.call_args
        assert call_args[0][0] == grpc.StatusCode.INVALID_ARGUMENT
        assert "invalid data" in call_args[0][1]

    def test_decorator_catches_device_error(self) -> None:
        """Decorator should catch DeviceError and abort."""

        @handle_grpc_errors
        def failing_method(self: object, request: object, context: object) -> str:
            raise DeviceError("device unavailable")

        context = MagicMock()
        failing_method(None, None, context)
        context.abort.assert_called_once()
        call_args = context.abort.call_args
        assert call_args[0][0] == grpc.StatusCode.UNAVAILABLE
        assert "device unavailable" in call_args[0][1]

    def test_decorator_catches_mqtt_error(self) -> None:
        """Decorator should catch MQTTError and abort."""

        @handle_grpc_errors
        def failing_method(self: object, request: object, context: object) -> str:
            raise MQTTError("mqtt connection failed")

        context = MagicMock()
        failing_method(None, None, context)
        context.abort.assert_called_once()
        call_args = context.abort.call_args
        assert call_args[0][0] == grpc.StatusCode.UNAVAILABLE
        assert "mqtt connection failed" in call_args[0][1]

    def test_decorator_catches_ollama_error(self) -> None:
        """Decorator should catch OllamaError and abort."""

        @handle_grpc_errors
        def failing_method(self: object, request: object, context: object) -> str:
            raise OllamaError("ollama service error")

        context = MagicMock()
        failing_method(None, None, context)
        context.abort.assert_called_once()
        call_args = context.abort.call_args
        assert call_args[0][0] == grpc.StatusCode.UNAVAILABLE
        assert "ollama service error" in call_args[0][1]

    def test_decorator_catches_rule_error(self) -> None:
        """Decorator should catch RuleError and abort."""

        @handle_grpc_errors
        def failing_method(self: object, request: object, context: object) -> str:
            raise RuleError("rule evaluation failed")

        context = MagicMock()
        failing_method(None, None, context)
        context.abort.assert_called_once()
        call_args = context.abort.call_args
        assert call_args[0][0] == grpc.StatusCode.INVALID_ARGUMENT
        assert "rule evaluation failed" in call_args[0][1]

    def test_decorator_catches_generic_exception(self) -> None:
        """Decorator should catch generic Exception and abort with INTERNAL."""

        @handle_grpc_errors
        def failing_method(self: object, request: object, context: object) -> str:
            raise Exception("unknown error")

        context = MagicMock()
        failing_method(None, None, context)
        context.abort.assert_called_once()
        call_args = context.abort.call_args
        assert call_args[0][0] == grpc.StatusCode.INTERNAL
        assert "unknown error" in call_args[0][1]

    def test_decorator_preserves_function_metadata(self) -> None:
        """Decorator should preserve original function name and docstring."""

        @handle_grpc_errors
        def my_service_method(self: object, request: object, context: object) -> str:
            """This is my service method."""
            return "result"

        assert my_service_method.__name__ == "my_service_method"
        assert my_service_method.__doc__ is not None
        assert "my service method" in my_service_method.__doc__

    def test_decorator_with_self_parameter(self) -> None:
        """Decorator should work with instance methods."""

        class MyServicer:
            @handle_grpc_errors
            def my_method(self, request: object, context: object) -> str:
                return "success"

        servicer = MyServicer()
        context = MagicMock()
        result = servicer.my_method(None, context)
        assert result == "success"
        context.abort.assert_not_called()

    def test_decorator_with_exception_in_instance_method(self) -> None:
        """Decorator should catch exceptions in instance methods."""

        class MyServicer:
            @handle_grpc_errors
            def my_method(self, request: object, context: object) -> str:
                raise ConfigurationError("config issue")

        servicer = MyServicer()
        context = MagicMock()
        servicer.my_method(None, context)
        context.abort.assert_called_once()
        call_args = context.abort.call_args
        assert call_args[0][0] == grpc.StatusCode.INVALID_ARGUMENT

    def test_decorator_passes_correct_exception_message(self) -> None:
        """Decorator should pass the exception message to context.abort()."""
        exception_msg = "Specific error message for debugging"

        @handle_grpc_errors
        def failing_method(self: object, request: object, context: object) -> str:
            raise ValidationError(exception_msg)

        context = MagicMock()
        failing_method(None, None, context)
        context.abort.assert_called_once()
        call_args = context.abort.call_args
        assert exception_msg in call_args[0][1]

    def test_decorator_with_nested_exceptions(self) -> None:
        """Decorator should handle nested exception hierarchies correctly."""

        @handle_grpc_errors
        def failing_method(self: object, request: object, context: object) -> str:
            # MQTTError is a subclass of DeviceError, which is subclass of IoTFuzzyLLMError
            raise MQTTError("mqtt nested error")

        context = MagicMock()
        failing_method(None, None, context)
        context.abort.assert_called_once()
        call_args = context.abort.call_args
        # Should map to UNAVAILABLE (DeviceError/MQTTError), not INTERNAL
        assert call_args[0][0] == grpc.StatusCode.UNAVAILABLE
