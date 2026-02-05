from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from src.data_processing.fuzzy_pipeline import FuzzyProcessingPipeline
    from src.data_processing.linguistic_descriptor import LinguisticDescription
    from src.device_interface.messages import SensorReading


def _make_sensor_reading(
    sensor_id: str = "temp_1",
    value: float | int | bool | str = 28.5,
    unit: str | None = "°C",
) -> SensorReading:
    from src.device_interface.messages import SensorReading

    return SensorReading(sensor_id=sensor_id, value=value, unit=unit)


def _make_temperature_config() -> dict:
    return {
        "sensor_type": "temperature",
        "unit": "celsius",
        "universe_of_discourse": {"min": -10, "max": 50},
        "confidence_threshold": 0.1,
        "linguistic_variables": [
            {"term": "cold", "function_type": "trapezoidal", "parameters": {"a": -10, "b": -10, "c": 10, "d": 18}},
            {"term": "comfortable", "function_type": "triangular", "parameters": {"a": 16, "b": 22, "c": 28}},
            {"term": "hot", "function_type": "trapezoidal", "parameters": {"a": 26, "b": 32, "c": 50, "d": 50}},
        ],
    }


def _make_humidity_config() -> dict:
    return {
        "sensor_type": "humidity",
        "unit": "percent",
        "universe_of_discourse": {"min": 0, "max": 100},
        "confidence_threshold": 0.1,
        "linguistic_variables": [
            {"term": "dry", "function_type": "trapezoidal", "parameters": {"a": 0, "b": 0, "c": 20, "d": 35}},
            {"term": "moderate", "function_type": "triangular", "parameters": {"a": 30, "b": 50, "c": 70}},
            {"term": "humid", "function_type": "trapezoidal", "parameters": {"a": 65, "b": 80, "c": 100, "d": 100}},
        ],
    }


@pytest.mark.unit
class TestFuzzyProcessingPipelineInit:
    def test_pipeline_creation_with_defaults(self) -> None:
        from src.data_processing.fuzzy_pipeline import FuzzyProcessingPipeline

        pipeline = FuzzyProcessingPipeline()

        assert pipeline.is_initialized is False
        assert pipeline.supported_sensor_types == []

    def test_pipeline_creation_with_custom_paths(self, tmp_path: Path) -> None:
        from src.data_processing.fuzzy_pipeline import FuzzyProcessingPipeline

        config_dir = tmp_path / "configs"
        schema_path = tmp_path / "schema.json"

        pipeline = FuzzyProcessingPipeline(
            config_dir=config_dir,
            schema_path=schema_path,
            validate_configs=False,
        )

        assert pipeline._config_dir == config_dir
        assert pipeline._schema_path == schema_path

    def test_pipeline_get_engine_and_builder(self) -> None:
        from src.data_processing.fuzzy_engine import FuzzyEngine
        from src.data_processing.fuzzy_pipeline import FuzzyProcessingPipeline
        from src.data_processing.linguistic_descriptor import (
            LinguisticDescriptorBuilder,
        )

        pipeline = FuzzyProcessingPipeline()

        assert isinstance(pipeline.get_engine(), FuzzyEngine)
        assert isinstance(pipeline.get_builder(), LinguisticDescriptorBuilder)


@pytest.mark.unit
class TestFuzzyProcessingPipelineInitialization:
    def test_initialize_loads_configs(self, tmp_path: Path) -> None:
        from src.common.utils import save_json
        from src.data_processing.fuzzy_pipeline import FuzzyProcessingPipeline

        config_dir = tmp_path / "membership_functions"
        config_dir.mkdir()
        save_json(config_dir / "temperature.json", _make_temperature_config())
        save_json(config_dir / "humidity.json", _make_humidity_config())

        pipeline = FuzzyProcessingPipeline(
            config_dir=config_dir,
            validate_configs=False,
        )

        count = pipeline.initialize()

        assert count == 2
        assert pipeline.is_initialized is True
        assert "temperature" in pipeline.supported_sensor_types
        assert "humidity" in pipeline.supported_sensor_types

    def test_initialize_raises_on_missing_dir(self, tmp_path: Path) -> None:
        from src.data_processing.fuzzy_pipeline import (
            FuzzyPipelineError,
            FuzzyProcessingPipeline,
        )

        pipeline = FuzzyProcessingPipeline(
            config_dir=tmp_path / "nonexistent",
            validate_configs=False,
        )

        with pytest.raises(FuzzyPipelineError, match="not found"):
            pipeline.initialize()

    def test_initialize_with_empty_dir_logs_warning(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        from src.data_processing.fuzzy_pipeline import FuzzyProcessingPipeline

        config_dir = tmp_path / "empty"
        config_dir.mkdir()

        pipeline = FuzzyProcessingPipeline(
            config_dir=config_dir,
            validate_configs=False,
        )

        count = pipeline.initialize()

        assert count == 0
        assert "No configuration files found" in caplog.text


@pytest.mark.unit
class TestFuzzyProcessingPipelineValidation:
    def test_validate_valid_config(self, tmp_path: Path) -> None:
        from src.common.utils import load_json, save_json
        from src.data_processing.fuzzy_pipeline import FuzzyProcessingPipeline

        config_dir = tmp_path / "configs"
        config_dir.mkdir()
        schema_dir = tmp_path / "schemas"
        schema_dir.mkdir()

        save_json(config_dir / "temperature.json", _make_temperature_config())

        real_schema = load_json(Path("config/schemas/membership_functions.schema.json"))
        save_json(schema_dir / "schema.json", real_schema)

        pipeline = FuzzyProcessingPipeline(
            config_dir=config_dir,
            schema_path=schema_dir / "schema.json",
            validate_configs=True,
        )

        count = pipeline.initialize()

        assert count == 1

    def test_validate_invalid_config_raises(self, tmp_path: Path) -> None:
        from src.common.utils import load_json, save_json
        from src.data_processing.fuzzy_pipeline import (
            FuzzyPipelineError,
            FuzzyProcessingPipeline,
        )

        config_dir = tmp_path / "configs"
        config_dir.mkdir()
        schema_dir = tmp_path / "schemas"
        schema_dir.mkdir()

        invalid_config = {"sensor_type": "temperature"}
        save_json(config_dir / "bad.json", invalid_config)

        real_schema = load_json(Path("config/schemas/membership_functions.schema.json"))
        save_json(schema_dir / "schema.json", real_schema)

        pipeline = FuzzyProcessingPipeline(
            config_dir=config_dir,
            schema_path=schema_dir / "schema.json",
            validate_configs=True,
        )

        with pytest.raises(FuzzyPipelineError, match="Invalid configuration"):
            pipeline.initialize()

    def test_validate_missing_schema_raises(self, tmp_path: Path) -> None:
        from src.common.utils import save_json
        from src.data_processing.fuzzy_pipeline import (
            FuzzyPipelineError,
            FuzzyProcessingPipeline,
        )

        config_dir = tmp_path / "configs"
        config_dir.mkdir()
        save_json(config_dir / "temperature.json", _make_temperature_config())

        pipeline = FuzzyProcessingPipeline(
            config_dir=config_dir,
            schema_path=tmp_path / "nonexistent.json",
            validate_configs=True,
        )

        with pytest.raises(FuzzyPipelineError, match="Schema file not found"):
            pipeline.initialize()


@pytest.mark.unit
class TestFuzzyProcessingPipelineProcessing:
    def _create_initialized_pipeline(self, tmp_path: Path) -> FuzzyProcessingPipeline:
        from src.common.utils import save_json
        from src.data_processing.fuzzy_pipeline import FuzzyProcessingPipeline

        config_dir = tmp_path / "configs"
        config_dir.mkdir()
        save_json(config_dir / "temperature.json", _make_temperature_config())
        save_json(config_dir / "humidity.json", _make_humidity_config())

        pipeline = FuzzyProcessingPipeline(
            config_dir=config_dir,
            validate_configs=False,
        )
        pipeline.initialize()
        return pipeline

    def test_process_reading_returns_description(self, tmp_path: Path) -> None:
        from src.data_processing.linguistic_descriptor import LinguisticDescription

        pipeline = self._create_initialized_pipeline(tmp_path)
        reading = _make_sensor_reading(value=30.0)

        result = pipeline.process_reading(reading, sensor_type="temperature")

        assert isinstance(result, LinguisticDescription)
        assert result.sensor_id == "temp_1"
        assert result.sensor_type == "temperature"
        assert result.raw_value == 30.0

    def test_process_reading_hot_temperature(self, tmp_path: Path) -> None:
        pipeline = self._create_initialized_pipeline(tmp_path)
        reading = _make_sensor_reading(value=35.0)

        result = pipeline.process_reading(reading, sensor_type="temperature")

        assert result.dominant_term is not None
        assert result.dominant_term.term == "hot"

    def test_process_reading_cold_temperature(self, tmp_path: Path) -> None:
        pipeline = self._create_initialized_pipeline(tmp_path)
        reading = _make_sensor_reading(value=5.0)

        result = pipeline.process_reading(reading, sensor_type="temperature")

        assert result.dominant_term is not None
        assert result.dominant_term.term == "cold"

    def test_process_reading_preserves_unit(self, tmp_path: Path) -> None:
        pipeline = self._create_initialized_pipeline(tmp_path)
        reading = _make_sensor_reading(value=25.0, unit="°C")

        result = pipeline.process_reading(reading, sensor_type="temperature")

        assert result.unit == "°C"

    def test_process_reading_raises_if_not_initialized(self) -> None:
        from src.data_processing.fuzzy_pipeline import (
            FuzzyPipelineError,
            FuzzyProcessingPipeline,
        )

        pipeline = FuzzyProcessingPipeline()
        reading = _make_sensor_reading()

        with pytest.raises(FuzzyPipelineError, match="not initialized"):
            pipeline.process_reading(reading, sensor_type="temperature")

    def test_process_reading_raises_on_unknown_sensor_type(
        self, tmp_path: Path
    ) -> None:
        from src.data_processing.fuzzy_pipeline import FuzzyPipelineError

        pipeline = self._create_initialized_pipeline(tmp_path)
        reading = _make_sensor_reading()

        with pytest.raises(FuzzyPipelineError, match="Unknown sensor type"):
            pipeline.process_reading(reading, sensor_type="pressure")

    def test_process_reading_raises_on_non_numeric_value(
        self, tmp_path: Path
    ) -> None:
        from src.data_processing.fuzzy_pipeline import FuzzyPipelineError

        pipeline = self._create_initialized_pipeline(tmp_path)
        reading = _make_sensor_reading(value="hot")

        with pytest.raises(FuzzyPipelineError, match="non-numeric"):
            pipeline.process_reading(reading, sensor_type="temperature")

    def test_process_reading_batch(self, tmp_path: Path) -> None:
        pipeline = self._create_initialized_pipeline(tmp_path)
        readings = [
            (_make_sensor_reading(sensor_id="temp_1", value=30.0), "temperature"),
            (_make_sensor_reading(sensor_id="hum_1", value=50.0, unit="%"), "humidity"),
        ]

        results = pipeline.process_reading_batch(readings)

        assert len(results) == 2
        assert results[0].sensor_id == "temp_1"
        assert results[1].sensor_id == "hum_1"


@pytest.mark.unit
class TestFuzzyProcessingPipelineStateCache:
    def _create_initialized_pipeline(self, tmp_path: Path) -> FuzzyProcessingPipeline:
        from src.common.utils import save_json
        from src.data_processing.fuzzy_pipeline import FuzzyProcessingPipeline

        config_dir = tmp_path / "configs"
        config_dir.mkdir()
        save_json(config_dir / "temperature.json", _make_temperature_config())

        pipeline = FuzzyProcessingPipeline(
            config_dir=config_dir,
            validate_configs=False,
        )
        pipeline.initialize()
        return pipeline

    def test_state_cache_populated_after_processing(self, tmp_path: Path) -> None:
        pipeline = self._create_initialized_pipeline(tmp_path)
        reading = _make_sensor_reading(sensor_id="temp_1", value=30.0)

        pipeline.process_reading(reading, sensor_type="temperature")

        state = pipeline.get_current_state()
        assert "temp_1" in state
        assert state["temp_1"].raw_value == 30.0

    def test_get_sensor_state_returns_cached(self, tmp_path: Path) -> None:
        pipeline = self._create_initialized_pipeline(tmp_path)
        reading = _make_sensor_reading(sensor_id="temp_1", value=30.0)

        pipeline.process_reading(reading, sensor_type="temperature")

        result = pipeline.get_sensor_state("temp_1")
        assert result is not None
        assert result.sensor_id == "temp_1"

    def test_get_sensor_state_returns_none_if_not_cached(
        self, tmp_path: Path
    ) -> None:
        pipeline = self._create_initialized_pipeline(tmp_path)

        result = pipeline.get_sensor_state("nonexistent")

        assert result is None

    def test_clear_state_cache(self, tmp_path: Path) -> None:
        pipeline = self._create_initialized_pipeline(tmp_path)
        reading = _make_sensor_reading(value=30.0)
        pipeline.process_reading(reading, sensor_type="temperature")

        pipeline.clear_state_cache()

        assert pipeline.get_current_state() == {}

    def test_state_callback_called_on_state_change(self, tmp_path: Path) -> None:
        pipeline = self._create_initialized_pipeline(tmp_path)

        callback_calls: list[tuple[str, LinguisticDescription]] = []

        def on_state_change(sensor_id: str, desc: LinguisticDescription) -> None:
            callback_calls.append((sensor_id, desc))

        pipeline.add_state_callback(on_state_change)

        reading = _make_sensor_reading(sensor_id="temp_1", value=30.0)
        pipeline.process_reading(reading, sensor_type="temperature")

        assert len(callback_calls) == 1
        assert callback_calls[0][0] == "temp_1"

    def test_state_callback_not_called_when_state_unchanged(
        self, tmp_path: Path
    ) -> None:
        pipeline = self._create_initialized_pipeline(tmp_path)

        callback_calls: list[tuple[str, LinguisticDescription]] = []

        def on_state_change(sensor_id: str, desc: LinguisticDescription) -> None:
            callback_calls.append((sensor_id, desc))

        pipeline.add_state_callback(on_state_change)

        reading1 = _make_sensor_reading(sensor_id="temp_1", value=35.0)
        reading2 = _make_sensor_reading(sensor_id="temp_1", value=36.0)

        pipeline.process_reading(reading1, sensor_type="temperature")
        pipeline.process_reading(reading2, sensor_type="temperature")

        assert len(callback_calls) == 1

    def test_state_callback_called_when_dominant_term_changes(
        self, tmp_path: Path
    ) -> None:
        pipeline = self._create_initialized_pipeline(tmp_path)

        callback_calls: list[tuple[str, LinguisticDescription]] = []

        def on_state_change(sensor_id: str, desc: LinguisticDescription) -> None:
            callback_calls.append((sensor_id, desc))

        pipeline.add_state_callback(on_state_change)

        reading_hot = _make_sensor_reading(sensor_id="temp_1", value=35.0)
        reading_cold = _make_sensor_reading(sensor_id="temp_1", value=5.0)

        pipeline.process_reading(reading_hot, sensor_type="temperature")
        pipeline.process_reading(reading_cold, sensor_type="temperature")

        assert len(callback_calls) == 2

    def test_remove_state_callback(self, tmp_path: Path) -> None:
        pipeline = self._create_initialized_pipeline(tmp_path)

        callback_calls: list[str] = []

        def on_state_change(sensor_id: str, desc: LinguisticDescription) -> None:
            callback_calls.append(sensor_id)

        pipeline.add_state_callback(on_state_change)
        pipeline.remove_state_callback(on_state_change)

        reading = _make_sensor_reading(value=30.0)
        pipeline.process_reading(reading, sensor_type="temperature")

        assert len(callback_calls) == 0

    def test_callback_exception_does_not_break_processing(
        self, tmp_path: Path
    ) -> None:
        pipeline = self._create_initialized_pipeline(tmp_path)

        def bad_callback(sensor_id: str, desc: LinguisticDescription) -> None:
            raise RuntimeError("Callback error")

        pipeline.add_state_callback(bad_callback)

        reading = _make_sensor_reading(value=30.0)
        result = pipeline.process_reading(reading, sensor_type="temperature")

        assert result is not None


@pytest.mark.unit
class TestFuzzyProcessingPipelineFormatting:
    def _create_initialized_pipeline(self, tmp_path: Path) -> FuzzyProcessingPipeline:
        from src.common.utils import save_json
        from src.data_processing.fuzzy_pipeline import FuzzyProcessingPipeline

        config_dir = tmp_path / "configs"
        config_dir.mkdir()
        save_json(config_dir / "temperature.json", _make_temperature_config())
        save_json(config_dir / "humidity.json", _make_humidity_config())

        pipeline = FuzzyProcessingPipeline(
            config_dir=config_dir,
            validate_configs=False,
        )
        pipeline.initialize()
        return pipeline

    def test_format_system_state_empty(self, tmp_path: Path) -> None:
        pipeline = self._create_initialized_pipeline(tmp_path)

        result = pipeline.format_system_state()

        assert "no data available" in result

    def test_format_system_state_with_sensors(self, tmp_path: Path) -> None:
        pipeline = self._create_initialized_pipeline(tmp_path)

        pipeline.process_reading(
            _make_sensor_reading(sensor_id="temp_1", value=35.0),
            sensor_type="temperature",
        )
        pipeline.process_reading(
            _make_sensor_reading(sensor_id="hum_1", value=50.0, unit="%"),
            sensor_type="humidity",
        )

        result = pipeline.format_system_state()

        assert "temperature is" in result
        assert "humidity is" in result
        assert "hot" in result
        assert "moderate" in result

    def test_format_system_state_with_values(self, tmp_path: Path) -> None:
        pipeline = self._create_initialized_pipeline(tmp_path)

        pipeline.process_reading(
            _make_sensor_reading(sensor_id="temp_1", value=35.0, unit="°C"),
            sensor_type="temperature",
        )

        result = pipeline.format_system_state(include_values=True)

        assert "35.0°C" in result


@pytest.mark.unit
class TestFuzzyProcessingPipelineCacheStats:
    def test_get_cache_stats(self, tmp_path: Path) -> None:
        from src.common.utils import save_json
        from src.data_processing.fuzzy_pipeline import FuzzyProcessingPipeline

        config_dir = tmp_path / "configs"
        config_dir.mkdir()
        save_json(config_dir / "temperature.json", _make_temperature_config())

        pipeline = FuzzyProcessingPipeline(
            config_dir=config_dir,
            validate_configs=False,
        )
        pipeline.initialize()

        reading = _make_sensor_reading(value=30.0)
        pipeline.process_reading(reading, sensor_type="temperature")

        stats = pipeline.get_cache_stats()

        assert stats["initialized"] is True
        assert stats["sensor_types_loaded"] == 1
        assert stats["state_cache_size"] == 1
        assert stats["fuzzy_cache_size"] >= 1


@pytest.mark.unit
class TestDataProcessingLayerInterface:
    def test_interface_is_abstract(self) -> None:
        from src.data_processing.fuzzy_pipeline import DataProcessingLayerInterface

        with pytest.raises(TypeError, match="abstract"):
            DataProcessingLayerInterface()  # type: ignore[abstract]

    def test_pipeline_implements_interface(self) -> None:
        from src.data_processing.fuzzy_pipeline import (
            DataProcessingLayerInterface,
            FuzzyProcessingPipeline,
        )

        assert issubclass(FuzzyProcessingPipeline, DataProcessingLayerInterface)


@pytest.mark.unit
class TestModuleExports:
    def test_exports_from_data_processing_package(self) -> None:
        from src.data_processing import (
            DataProcessingLayerInterface,
            FuzzyPipelineError,
            FuzzyProcessingPipeline,
        )

        assert FuzzyProcessingPipeline is not None
        assert FuzzyPipelineError is not None
        assert DataProcessingLayerInterface is not None
