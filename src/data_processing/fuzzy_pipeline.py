"""Fuzzy Processing Pipeline - the Data Processing layer coordinator.

This module provides the FuzzyProcessingPipeline class which orchestrates:
- FuzzyEngine for fuzzification of sensor values
- LinguisticDescriptorBuilder for natural language output
- State cache for current linguistic descriptions
- Configuration loading and validation

The pipeline serves as the sole interface between:
- Device Interface Layer (below) - receives SensorReading
- Control & Reasoning Layer (above) - provides LinguisticDescription
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any

import jsonschema

from src.common.logging import get_logger
from src.common.utils import load_json
from src.data_processing.fuzzy_engine import FuzzyEngine, FuzzyEngineError
from src.data_processing.linguistic_descriptor import (
    LinguisticDescription,
    LinguisticDescriptorBuilder,
)

if TYPE_CHECKING:
    from src.device_interface.messages import SensorReading

logger = get_logger(__name__)


class DataProcessingLayerInterface(ABC):
    """Abstract interface for the Data Processing Layer.

    This defines the contract between the Data Processing Layer
    and the Control & Reasoning Layer above it.
    """

    @abstractmethod
    def process_reading(
        self,
        reading: SensorReading,
        sensor_type: str,
    ) -> LinguisticDescription:
        """Process a sensor reading into a linguistic description."""
        ...

    @abstractmethod
    def get_current_state(self) -> dict[str, LinguisticDescription]:
        """Get the current linguistic state for all sensors."""
        ...

    @abstractmethod
    def get_sensor_state(self, sensor_id: str) -> LinguisticDescription | None:
        """Get the current linguistic state for a specific sensor."""
        ...

    @abstractmethod
    def format_system_state(self, include_values: bool = False) -> str:
        """Format the current system state for LLM consumption."""
        ...


class FuzzyProcessingPipeline(DataProcessingLayerInterface):
    """Layer coordinator for Data Processing.

    Orchestrates the transformation of numerical sensor values
    into linguistic descriptions suitable for LLM processing.
    """

    DEFAULT_CONFIG_DIR = Path("config/membership_functions")
    DEFAULT_SCHEMA_PATH = Path("config/schemas/membership_functions.schema.json")

    def __init__(
        self,
        config_dir: Path | None = None,
        schema_path: Path | None = None,
        validate_configs: bool = True,
        cache_ttl_seconds: float = 300.0,
        max_descriptor_terms: int = 3,
    ) -> None:
        """Initialize the pipeline.

        Args:
            config_dir: Directory containing membership function JSONs
            schema_path: Path to JSON schema for validation
            validate_configs: Whether to validate configs against schema
            cache_ttl_seconds: TTL for fuzzy engine cache
            max_descriptor_terms: Max terms in linguistic descriptions
        """
        self._config_dir = config_dir or self.DEFAULT_CONFIG_DIR
        self._schema_path = schema_path or self.DEFAULT_SCHEMA_PATH
        self._validate_configs = validate_configs

        self._engine = FuzzyEngine(cache_ttl_seconds=cache_ttl_seconds)
        self._builder = LinguisticDescriptorBuilder(max_terms=max_descriptor_terms)

        self._state_cache: dict[str, LinguisticDescription] = {}
        self._state_callbacks: list[Callable[[str, LinguisticDescription], None]] = []

        self._schema: dict[str, Any] | None = None
        self._loaded_sensor_types: list[str] = []
        self._initialized = False

    @property
    def is_initialized(self) -> bool:
        """Check if pipeline has been initialized with configs."""
        return self._initialized

    @property
    def supported_sensor_types(self) -> list[str]:
        """Get list of sensor types with loaded configurations."""
        return self._engine.get_supported_sensor_types()

    def initialize(self) -> int:
        """Load all configurations and prepare the pipeline.

        Returns:
            Number of sensor type configurations loaded

        Raises:
            FuzzyPipelineError: If initialization fails
        """
        if self._validate_configs:
            self._load_schema()

        count = self._load_configurations()
        self._initialized = True
        logger.info(
            "FuzzyProcessingPipeline initialized",
            extra={"sensor_types_loaded": count},
        )
        return count

    def _load_schema(self) -> None:
        """Load JSON schema for configuration validation."""
        if not self._schema_path.exists():
            raise FuzzyPipelineError(f"Schema file not found: {self._schema_path}")

        self._schema = load_json(self._schema_path)
        logger.debug(
            "Loaded membership function schema", extra={"path": str(self._schema_path)}
        )

    def _load_configurations(self) -> int:
        """Load all membership function configurations from directory.

        Returns:
            Number of configurations loaded

        Raises:
            FuzzyPipelineError: If config directory doesn't exist or configs invalid
        """
        if not self._config_dir.exists():
            raise FuzzyPipelineError(
                f"Configuration directory not found: {self._config_dir}"
            )

        count = 0
        for json_file in sorted(self._config_dir.glob("*.json")):
            try:
                self._load_config_file(json_file)
                count += 1
            except FuzzyPipelineError:
                raise
            except Exception as e:
                raise FuzzyPipelineError(
                    f"Failed to load config {json_file.name}: {e}"
                ) from e

        if count == 0:
            logger.warning(
                "No configuration files found",
                extra={"directory": str(self._config_dir)},
            )

        return count

    def _load_config_file(self, path: Path) -> None:
        """Load and validate a single configuration file."""
        config_data = load_json(path)

        if self._validate_configs and self._schema:
            try:
                jsonschema.validate(instance=config_data, schema=self._schema)
            except jsonschema.ValidationError as e:
                raise FuzzyPipelineError(
                    f"Invalid configuration in {path.name}: {e.message}"
                ) from e

        self._engine.load_config_from_dict(config_data)
        sensor_type = config_data["sensor_type"]
        self._loaded_sensor_types.append(sensor_type)
        logger.debug(
            "Loaded sensor type configuration",
            extra={"sensor_type": sensor_type, "file": path.name},
        )

    def process_reading(
        self,
        reading: SensorReading,
        sensor_type: str,
    ) -> LinguisticDescription:
        """Process a sensor reading into a linguistic description.

        Args:
            reading: The sensor reading from Device Interface Layer
            sensor_type: The type of sensor (e.g., "temperature", "humidity")

        Returns:
            LinguisticDescription for LLM consumption

        Raises:
            FuzzyPipelineError: If sensor type not configured or value invalid
        """
        if not self._initialized:
            raise FuzzyPipelineError(
                "Pipeline not initialized. Call initialize() first."
            )

        value = reading.value
        if not isinstance(value, (int, float)):
            raise FuzzyPipelineError(
                f"Cannot fuzzify non-numeric value: {type(value).__name__}"
            )

        try:
            fuzz_result = self._engine.fuzzify(sensor_type, float(value))
        except FuzzyEngineError as e:
            raise FuzzyPipelineError(str(e)) from e

        description = self._builder.build(
            sensor_id=reading.sensor_id,
            result=fuzz_result,
            unit=reading.unit,
        )

        self._update_state_cache(reading.sensor_id, description)

        return description

    def process_reading_batch(
        self,
        readings: list[tuple[SensorReading, str]],
    ) -> list[LinguisticDescription]:
        """Process multiple sensor readings.

        Args:
            readings: List of (SensorReading, sensor_type) tuples

        Returns:
            List of LinguisticDescriptions
        """
        return [
            self.process_reading(reading, sensor_type)
            for reading, sensor_type in readings
        ]

    def _update_state_cache(
        self,
        sensor_id: str,
        description: LinguisticDescription,
    ) -> None:
        """Update state cache and notify callbacks if state changed."""
        old_state = self._state_cache.get(sensor_id)
        self._state_cache[sensor_id] = description

        state_changed = (
            old_state is None or old_state.dominant_term != description.dominant_term
        )

        if state_changed:
            for callback in self._state_callbacks:
                try:
                    callback(sensor_id, description)
                except Exception:
                    logger.exception(
                        "State callback error",
                        extra={"sensor_id": sensor_id},
                    )

    def get_current_state(self) -> dict[str, LinguisticDescription]:
        """Get the current linguistic state for all sensors.

        Returns:
            Dictionary mapping sensor_id to LinguisticDescription
        """
        return dict(self._state_cache)

    def get_sensor_state(self, sensor_id: str) -> LinguisticDescription | None:
        """Get the current linguistic state for a specific sensor.

        Args:
            sensor_id: The sensor identifier

        Returns:
            LinguisticDescription or None if not in cache
        """
        return self._state_cache.get(sensor_id)

    def format_system_state(self, include_values: bool = False) -> str:
        """Format the current system state for LLM consumption.

        Args:
            include_values: Whether to include raw numerical values

        Returns:
            Formatted string suitable for LLM context
        """
        descriptions = list(self._state_cache.values())
        return self._builder.format_for_llm(descriptions, include_values=include_values)

    def add_state_callback(
        self,
        callback: Callable[[str, LinguisticDescription], None],
    ) -> None:
        """Register a callback for state changes.

        The callback receives (sensor_id, new_description) when
        the dominant term changes for a sensor.
        """
        self._state_callbacks.append(callback)

    def remove_state_callback(
        self,
        callback: Callable[[str, LinguisticDescription], None],
    ) -> None:
        """Remove a previously registered state callback."""
        if callback in self._state_callbacks:
            self._state_callbacks.remove(callback)

    def clear_state_cache(self) -> None:
        """Clear all cached linguistic states."""
        self._state_cache.clear()

    def get_engine(self) -> FuzzyEngine:
        """Get the underlying FuzzyEngine for advanced operations."""
        return self._engine

    def get_builder(self) -> LinguisticDescriptorBuilder:
        """Get the underlying LinguisticDescriptorBuilder."""
        return self._builder

    def get_cache_stats(self) -> dict[str, Any]:
        """Get statistics about the pipeline caches.

        Returns:
            Dictionary with cache statistics
        """
        return {
            "fuzzy_cache_size": self._engine.cache_size,
            "state_cache_size": len(self._state_cache),
            "sensor_types_loaded": len(self._loaded_sensor_types),
            "initialized": self._initialized,
        }


class FuzzyPipelineError(Exception):
    """Exception raised by FuzzyProcessingPipeline operations."""

    pass
