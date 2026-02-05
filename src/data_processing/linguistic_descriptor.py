"""Linguistic descriptor module for converting fuzzy output to natural language.

This module provides:
- LinguisticDescription: Dataclass representing a sensor's linguistic state
- LinguisticDescriptorBuilder: Converts FuzzificationResult to natural language

Example output format:
- "temperature is hot (0.85)"
- "humidity is moderate (0.72), high (0.28)"
"""

from __future__ import annotations

import time
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from src.data_processing.fuzzy_engine import FuzzificationResult


@dataclass(frozen=True)
class TermMembership:
    """A linguistic term with its membership degree.

    Attributes:
        term: The linguistic term (e.g., "hot", "cold", "moderate")
        degree: The membership degree in range [0, 1]
    """

    term: str
    degree: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.degree <= 1.0:
            raise ValueError(f"Degree must be in [0, 1], got {self.degree}")
        if not self.term:
            raise ValueError("Term cannot be empty")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {"term": self.term, "degree": self.degree}

    def format(self, precision: int = 2) -> str:
        """Format as 'term (degree)'.

        Args:
            precision: Decimal precision for degree display

        Returns:
            Formatted string like 'hot (0.85)'
        """
        return f"{self.term} ({self.degree:.{precision}f})"


@dataclass(frozen=True)
class LinguisticDescription:
    """Represents a sensor's linguistic state from fuzzy processing.

    This is the output of the Data Processing layer, ready for consumption
    by the Control & Reasoning layer (LLM).

    Attributes:
        sensor_id: Unique identifier of the sensor
        sensor_type: Type of sensor (e.g., "temperature", "humidity")
        raw_value: The original numerical sensor reading
        terms: Tuple of applicable terms with membership degrees (sorted by degree desc)
        timestamp: Unix timestamp when description was created
        unit: Optional unit of measurement (e.g., "°C", "%")
    """

    sensor_id: str
    sensor_type: str
    raw_value: float
    terms: tuple[TermMembership, ...]
    timestamp: float = field(default_factory=time.time)
    unit: str | None = None

    def __post_init__(self) -> None:
        if not self.sensor_id:
            raise ValueError("sensor_id cannot be empty")
        if not self.sensor_type:
            raise ValueError("sensor_type cannot be empty")

    @property
    def dominant_term(self) -> TermMembership | None:
        """Get the term with highest membership degree."""
        if not self.terms:
            return None
        return self.terms[0]

    @property
    def is_ambiguous(self) -> bool:
        """Check if multiple terms have significant membership.

        Returns True if there are 2+ terms with degree > 0.3
        """
        return sum(1 for t in self.terms if t.degree > 0.3) >= 2

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation for JSON serialization."""
        return {
            "sensor_id": self.sensor_id,
            "sensor_type": self.sensor_type,
            "raw_value": self.raw_value,
            "terms": [t.to_dict() for t in self.terms],
            "timestamp": self.timestamp,
            "unit": self.unit,
        }

    def format_description(self, precision: int = 2) -> str:
        """Format as natural language description.

        Args:
            precision: Decimal precision for degree display

        Returns:
            String like 'temperature is hot (0.85), warm (0.15)'
            or 'temperature is unknown' if no terms
        """
        if not self.terms:
            return f"{self.sensor_type} is unknown"

        terms_str = ", ".join(t.format(precision) for t in self.terms)
        return f"{self.sensor_type} is {terms_str}"

    def format_simple(self) -> str:
        """Format as simple description without degrees.

        Returns:
            String like 'temperature is hot'
            or 'temperature is unknown' if no terms
        """
        if not self.terms:
            return f"{self.sensor_type} is unknown"

        return f"{self.sensor_type} is {self.terms[0].term}"

    def format_with_value(self, precision: int = 2) -> str:
        """Format with raw value included.

        Args:
            precision: Decimal precision for degree display

        Returns:
            String like 'temperature (25.5°C) is hot (0.85)'
        """
        value_str = f"{self.raw_value}"
        if self.unit:
            value_str = f"{self.raw_value}{self.unit}"

        if not self.terms:
            return f"{self.sensor_type} ({value_str}) is unknown"

        terms_str = ", ".join(t.format(precision) for t in self.terms)
        return f"{self.sensor_type} ({value_str}) is {terms_str}"


class LinguisticDescriptorBuilder:
    """Converts FuzzificationResult to natural language descriptions.

    The builder takes fuzzy engine output and transforms it into
    LinguisticDescription objects suitable for LLM consumption.

    Example:
        >>> builder = LinguisticDescriptorBuilder()
        >>> result = fuzzy_engine.fuzzify("temperature", 28.5)
        >>> description = builder.build(sensor_id="temp_1", result=result)
        >>> print(description.format_description())
        'temperature is hot (0.85), warm (0.15)'
    """

    def __init__(
        self,
        max_terms: int = 3,
        min_degree: float = 0.0,
    ) -> None:
        """Initialize the descriptor builder.

        Args:
            max_terms: Maximum number of terms to include in description
            min_degree: Minimum degree to include a term (0.0 = include all)
        """
        if max_terms < 1:
            raise ValueError("max_terms must be at least 1")
        if not 0.0 <= min_degree <= 1.0:
            raise ValueError("min_degree must be in [0, 1]")

        self._max_terms = max_terms
        self._min_degree = min_degree

    @property
    def max_terms(self) -> int:
        """Maximum number of terms to include."""
        return self._max_terms

    @property
    def min_degree(self) -> float:
        """Minimum degree threshold for inclusion."""
        return self._min_degree

    def build(
        self,
        sensor_id: str,
        result: FuzzificationResult,
        unit: str | None = None,
    ) -> LinguisticDescription:
        """Build a LinguisticDescription from a FuzzificationResult.

        Args:
            sensor_id: Unique identifier of the sensor
            result: Fuzzification result from FuzzyEngine
            unit: Optional unit of measurement

        Returns:
            LinguisticDescription ready for LLM consumption
        """
        filtered_terms: list[TermMembership] = []
        for term_name, degree in result.memberships:
            if degree >= self._min_degree and len(filtered_terms) < self._max_terms:
                filtered_terms.append(TermMembership(term=term_name, degree=degree))

        return LinguisticDescription(
            sensor_id=sensor_id,
            sensor_type=result.sensor_type,
            raw_value=result.raw_value,
            terms=tuple(filtered_terms),
            timestamp=result.timestamp,
            unit=unit,
        )

    def build_batch(
        self,
        sensor_results: Sequence[tuple[str, FuzzificationResult, str | None]],
    ) -> list[LinguisticDescription]:
        """Build multiple LinguisticDescriptions from a batch of results.

        Args:
            sensor_results: List of (sensor_id, result, unit) tuples

        Returns:
            List of LinguisticDescription objects
        """
        return [
            self.build(sensor_id, result, unit)
            for sensor_id, result, unit in sensor_results
        ]

    def format_multi_sensor(
        self,
        descriptions: list[LinguisticDescription],
        separator: str = "; ",
        precision: int = 2,
    ) -> str:
        """Format multiple sensor descriptions into a single string.

        Useful for providing context to LLM about overall system state.

        Args:
            descriptions: List of LinguisticDescription objects
            separator: String to separate descriptions
            precision: Decimal precision for degree display

        Returns:
            Combined description string, e.g.:
            'temperature is hot (0.85); humidity is moderate (0.72)'
        """
        if not descriptions:
            return "no sensor data available"

        return separator.join(d.format_description(precision) for d in descriptions)

    def format_for_llm(
        self,
        descriptions: list[LinguisticDescription],
        include_values: bool = False,
    ) -> str:
        """Format descriptions in a structured way for LLM consumption.

        Args:
            descriptions: List of LinguisticDescription objects
            include_values: Whether to include raw numerical values

        Returns:
            Formatted multi-line string suitable for LLM context
        """
        if not descriptions:
            return "Current sensor state: no data available."

        lines = ["Current sensor state:"]
        for desc in descriptions:
            if include_values:
                lines.append(f"- {desc.format_with_value()}")
            else:
                lines.append(f"- {desc.format_description()}")

        return "\n".join(lines)
