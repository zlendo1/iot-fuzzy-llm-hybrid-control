from __future__ import annotations

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


class MembershipFunction(ABC):
    """Abstract base class for fuzzy membership functions.

    A membership function maps a crisp numerical value to a degree of membership
    in a fuzzy set, returning a value in the range [0.0, 1.0].
    """

    @abstractmethod
    def compute_degree(self, value: float) -> float:
        """Compute the degree of membership for a given value.

        Args:
            value: The crisp input value to fuzzify.

        Returns:
            Membership degree in the range [0.0, 1.0].
        """
        ...  # pragma: no cover

    @property
    @abstractmethod
    def function_type(self) -> str:
        """Return the type identifier for this membership function."""
        ...  # pragma: no cover


@dataclass(frozen=True)
class TriangularMF(MembershipFunction):
    """Triangular membership function defined by three parameters.

    The function forms a triangle with:
    - a: left foot (membership = 0)
    - b: peak (membership = 1)
    - c: right foot (membership = 0)

    Constraint: a <= b <= c
    """

    a: float
    b: float
    c: float

    def __post_init__(self) -> None:
        if not (self.a <= self.b <= self.c):
            raise ValueError(
                f"Invalid triangular parameters: a <= b <= c required, "
                f"got a={self.a}, b={self.b}, c={self.c}"
            )

    def compute_degree(self, value: float) -> float:
        if value == self.b:
            return 1.0
        if value < self.a or value > self.c:
            return 0.0
        if value < self.b:
            return (value - self.a) / (self.b - self.a)
        return (self.c - value) / (self.c - self.b)

    @property
    def function_type(self) -> str:
        return "triangular"


@dataclass(frozen=True)
class TrapezoidalMF(MembershipFunction):
    """Trapezoidal membership function defined by four parameters.

    The function forms a trapezoid with:
    - a: left foot (membership = 0)
    - b: left shoulder (membership = 1 starts)
    - c: right shoulder (membership = 1 ends)
    - d: right foot (membership = 0)

    Constraint: a <= b <= c <= d
    """

    a: float
    b: float
    c: float
    d: float

    def __post_init__(self) -> None:
        if not (self.a <= self.b <= self.c <= self.d):
            raise ValueError(
                f"Invalid trapezoidal parameters: a <= b <= c <= d required, "
                f"got a={self.a}, b={self.b}, c={self.c}, d={self.d}"
            )

    def compute_degree(self, value: float) -> float:
        if self.b <= value <= self.c:
            return 1.0
        if value < self.a or value > self.d:
            return 0.0
        if value < self.b:
            return (value - self.a) / (self.b - self.a)
        return (self.d - value) / (self.d - self.c)

    @property
    def function_type(self) -> str:
        return "trapezoidal"


@dataclass(frozen=True)
class GaussianMF(MembershipFunction):
    """Gaussian membership function defined by mean and standard deviation.

    The function follows the Gaussian (normal) distribution curve:
    - mean: center of the curve (membership = 1)
    - sigma: standard deviation controlling curve width

    Formula: exp(-0.5 * ((x - mean) / sigma)^2)
    """

    mean: float
    sigma: float

    def __post_init__(self) -> None:
        if self.sigma <= 0:
            raise ValueError(
                f"Invalid Gaussian parameters: sigma must be positive, got {self.sigma}"
            )

    def compute_degree(self, value: float) -> float:
        exponent = -0.5 * ((value - self.mean) / self.sigma) ** 2
        return math.exp(exponent)

    @property
    def function_type(self) -> str:
        return "gaussian"


@dataclass(frozen=True)
class SigmoidMF(MembershipFunction):
    """Sigmoid membership function for monotonic transitions.

    The function follows the logistic curve:
    - a: slope parameter (positive = increasing, negative = decreasing)
    - c: inflection point (where membership = 0.5)

    Formula: 1 / (1 + exp(-a * (x - c)))
    """

    a: float
    c: float

    def __post_init__(self) -> None:
        if self.a == 0:
            raise ValueError("Invalid sigmoid parameters: a cannot be zero")

    def compute_degree(self, value: float) -> float:
        exponent = -self.a * (value - self.c)
        # Clamp to avoid overflow
        if exponent > 700:
            return 0.0
        if exponent < -700:
            return 1.0
        return 1.0 / (1.0 + math.exp(exponent))

    @property
    def function_type(self) -> str:
        return "sigmoid"


class MembershipFunctionError(Exception):
    """Raised when membership function creation or configuration fails."""

    pass


def create_membership_function(config: dict[str, Any]) -> MembershipFunction:
    """Factory function to create a membership function from configuration.

    Args:
        config: Dictionary containing 'function_type' and 'parameters' keys.
            function_type: One of 'triangular', 'trapezoidal', 'gaussian', 'sigmoid'
            parameters: Dictionary of parameters specific to the function type

    Returns:
        Instantiated MembershipFunction subclass.

    Raises:
        MembershipFunctionError: If function_type is unknown or parameters are invalid.
    """
    function_type = config.get("function_type")
    parameters = config.get("parameters", {})

    if not function_type:
        raise MembershipFunctionError("Missing 'function_type' in configuration")

    if not isinstance(parameters, dict):
        raise MembershipFunctionError("'parameters' must be a dictionary")

    try:
        if function_type == "triangular":
            return TriangularMF(
                a=parameters["a"],
                b=parameters["b"],
                c=parameters["c"],
            )
        if function_type == "trapezoidal":
            return TrapezoidalMF(
                a=parameters["a"],
                b=parameters["b"],
                c=parameters["c"],
                d=parameters["d"],
            )
        if function_type == "gaussian":
            return GaussianMF(
                mean=parameters["mean"],
                sigma=parameters["sigma"],
            )
        if function_type == "sigmoid":
            return SigmoidMF(
                a=parameters["a"],
                c=parameters["c"],
            )
        raise MembershipFunctionError(f"Unknown function type: '{function_type}'")
    except KeyError as e:
        raise MembershipFunctionError(
            f"Missing required parameter {e} for {function_type}"
        ) from e
    except (TypeError, ValueError) as e:
        raise MembershipFunctionError(
            f"Invalid parameters for {function_type}: {e}"
        ) from e
