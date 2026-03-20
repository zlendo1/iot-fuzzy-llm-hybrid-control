"""Exception to gRPC status code mapping and error handling decorator."""

from __future__ import annotations

import functools
from typing import TYPE_CHECKING, Any, Callable

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

if TYPE_CHECKING:
    from collections.abc import Awaitable


def exception_to_status(exc: Exception) -> grpc.StatusCode:
    """Map an exception to a gRPC status code.

    Maps custom IoT exceptions to appropriate gRPC status codes:
    - ConfigurationError, ValidationError, RuleError → INVALID_ARGUMENT
    - DeviceError, MQTTError, OllamaError → UNAVAILABLE
    - IoTFuzzyLLMError (base) → INTERNAL
    - Generic Exception → INTERNAL

    Args:
        exc: The exception to map.

    Returns:
        The corresponding gRPC StatusCode.
    """
    if isinstance(exc, ConfigurationError):
        return grpc.StatusCode.INVALID_ARGUMENT
    if isinstance(exc, ValidationError):
        return grpc.StatusCode.INVALID_ARGUMENT
    if isinstance(exc, RuleError):
        return grpc.StatusCode.INVALID_ARGUMENT
    if isinstance(exc, MQTTError):
        return grpc.StatusCode.UNAVAILABLE
    if isinstance(exc, DeviceError):
        return grpc.StatusCode.UNAVAILABLE
    if isinstance(exc, OllamaError):
        return grpc.StatusCode.UNAVAILABLE
    if isinstance(exc, IoTFuzzyLLMError):
        return grpc.StatusCode.INTERNAL

    return grpc.StatusCode.INTERNAL


def handle_grpc_errors(
    func: Callable[..., Any],
) -> Callable[..., Any]:
    """Decorator to catch exceptions and abort with mapped gRPC status codes.

    Wraps a gRPC servicer method to catch exceptions, map them to appropriate
    gRPC status codes, and call context.abort() with the mapped status and
    error message.

    Usage:
        @handle_grpc_errors
        def my_servicer_method(self, request, context):
            # method body
            ...

    Args:
        func: The function to decorate (typically a gRPC servicer method).

    Returns:
        The decorated function that catches and converts exceptions to gRPC errors.
    """

    @functools.wraps(func)
    def wrapper(self: Any, request: Any, context: Any) -> Any:
        try:
            return func(self, request, context)
        except Exception as e:
            status_code = exception_to_status(e)
            context.abort(status_code, str(e))

    return wrapper
