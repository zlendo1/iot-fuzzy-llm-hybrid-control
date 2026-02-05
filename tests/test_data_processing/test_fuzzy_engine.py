from __future__ import annotations

import time
from pathlib import Path

import pytest


class TestUniverseOfDiscourse:
    @pytest.mark.unit
    def test_universe_contains_value_in_range(self) -> None:
        from src.data_processing.fuzzy_engine import UniverseOfDiscourse

        universe = UniverseOfDiscourse(min=0.0, max=100.0)
        assert universe.contains(50.0) is True

    @pytest.mark.unit
    def test_universe_contains_value_at_boundaries(self) -> None:
        from src.data_processing.fuzzy_engine import UniverseOfDiscourse

        universe = UniverseOfDiscourse(min=0.0, max=100.0)
        assert universe.contains(0.0) is True
        assert universe.contains(100.0) is True

    @pytest.mark.unit
    def test_universe_excludes_value_outside_range(self) -> None:
        from src.data_processing.fuzzy_engine import UniverseOfDiscourse

        universe = UniverseOfDiscourse(min=0.0, max=100.0)
        assert universe.contains(-1.0) is False
        assert universe.contains(101.0) is False

    @pytest.mark.unit
    def test_universe_from_dict(self) -> None:
        from src.data_processing.fuzzy_engine import UniverseOfDiscourse

        data = {"min": -10.0, "max": 50.0}
        universe = UniverseOfDiscourse.from_dict(data)
        assert universe.min == -10.0
        assert universe.max == 50.0


class TestLinguisticVariable:
    @pytest.mark.unit
    def test_linguistic_variable_compute_degree(self) -> None:
        from src.data_processing.fuzzy_engine import LinguisticVariable
        from src.data_processing.membership_functions import TriangularMF

        mf = TriangularMF(a=0.0, b=10.0, c=20.0)
        var = LinguisticVariable(term="medium", membership_function=mf)
        assert var.compute_degree(10.0) == 1.0
        assert var.compute_degree(5.0) == 0.5

    @pytest.mark.unit
    def test_linguistic_variable_from_dict(self) -> None:
        from src.data_processing.fuzzy_engine import LinguisticVariable

        data = {
            "term": "hot",
            "function_type": "triangular",
            "parameters": {"a": 25.0, "b": 35.0, "c": 50.0},
        }
        var = LinguisticVariable.from_dict(data)
        assert var.term == "hot"
        assert var.compute_degree(35.0) == 1.0


class TestSensorTypeConfig:
    @pytest.mark.unit
    def test_sensor_type_config_from_dict(self) -> None:
        from src.data_processing.fuzzy_engine import SensorTypeConfig

        data = {
            "sensor_type": "temperature",
            "unit": "celsius",
            "universe_of_discourse": {"min": -10.0, "max": 50.0},
            "confidence_threshold": 0.15,
            "linguistic_variables": [
                {
                    "term": "cold",
                    "function_type": "triangular",
                    "parameters": {"a": -10.0, "b": 0.0, "c": 15.0},
                },
                {
                    "term": "hot",
                    "function_type": "triangular",
                    "parameters": {"a": 25.0, "b": 35.0, "c": 50.0},
                },
            ],
        }
        config = SensorTypeConfig.from_dict(data)
        assert config.sensor_type == "temperature"
        assert config.unit == "celsius"
        assert config.confidence_threshold == 0.15
        assert len(config.linguistic_variables) == 2
        assert config.linguistic_variables[0].term == "cold"

    @pytest.mark.unit
    def test_sensor_type_config_default_threshold(self) -> None:
        from src.data_processing.fuzzy_engine import SensorTypeConfig

        data = {
            "sensor_type": "humidity",
            "unit": "percent",
            "universe_of_discourse": {"min": 0.0, "max": 100.0},
            "linguistic_variables": [
                {
                    "term": "dry",
                    "function_type": "triangular",
                    "parameters": {"a": 0.0, "b": 20.0, "c": 40.0},
                },
            ],
        }
        config = SensorTypeConfig.from_dict(data)
        assert config.confidence_threshold == 0.1

    @pytest.mark.unit
    def test_sensor_type_config_from_json_file(self, tmp_path: Path) -> None:
        from src.data_processing.fuzzy_engine import SensorTypeConfig

        config_file = tmp_path / "test_sensor.json"
        config_file.write_text(
            """{
            "sensor_type": "pressure",
            "unit": "hPa",
            "universe_of_discourse": {"min": 900.0, "max": 1100.0},
            "confidence_threshold": 0.2,
            "linguistic_variables": [
                {
                    "term": "low",
                    "function_type": "trapezoidal",
                    "parameters": {"a": 900.0, "b": 900.0, "c": 980.0, "d": 1000.0}
                }
            ]
        }"""
        )
        config = SensorTypeConfig.from_json_file(config_file)
        assert config.sensor_type == "pressure"
        assert config.unit == "hPa"


class TestFuzzificationResult:
    @pytest.mark.unit
    def test_fuzzification_result_get_dominant_term(self) -> None:
        from src.data_processing.fuzzy_engine import FuzzificationResult

        result = FuzzificationResult(
            sensor_type="temperature",
            raw_value=28.0,
            memberships=(("warm", 0.8), ("hot", 0.3)),
        )
        dominant = result.get_dominant_term()
        assert dominant == ("warm", 0.8)

    @pytest.mark.unit
    def test_fuzzification_result_empty_memberships(self) -> None:
        from src.data_processing.fuzzy_engine import FuzzificationResult

        result = FuzzificationResult(
            sensor_type="temperature",
            raw_value=-50.0,
            memberships=(),
        )
        assert result.get_dominant_term() is None

    @pytest.mark.unit
    def test_fuzzification_result_to_dict(self) -> None:
        from src.data_processing.fuzzy_engine import FuzzificationResult

        result = FuzzificationResult(
            sensor_type="humidity",
            raw_value=65.0,
            memberships=(("humid", 0.7), ("comfortable", 0.3)),
            timestamp=1234567890.0,
        )
        d = result.to_dict()
        assert d["sensor_type"] == "humidity"
        assert d["raw_value"] == 65.0
        assert d["memberships"] == {"humid": 0.7, "comfortable": 0.3}
        assert d["timestamp"] == 1234567890.0


class TestFuzzyEngine:
    @pytest.fixture
    def sample_config_data(self) -> dict:
        return {
            "sensor_type": "temperature",
            "unit": "celsius",
            "universe_of_discourse": {"min": -10.0, "max": 50.0},
            "confidence_threshold": 0.1,
            "linguistic_variables": [
                {
                    "term": "cold",
                    "function_type": "trapezoidal",
                    "parameters": {"a": -10.0, "b": -10.0, "c": 10.0, "d": 18.0},
                },
                {
                    "term": "comfortable",
                    "function_type": "triangular",
                    "parameters": {"a": 16.0, "b": 22.0, "c": 26.0},
                },
                {
                    "term": "hot",
                    "function_type": "trapezoidal",
                    "parameters": {"a": 24.0, "b": 30.0, "c": 50.0, "d": 50.0},
                },
            ],
        }

    @pytest.mark.unit
    def test_engine_load_config_from_dict(self, sample_config_data: dict) -> None:
        from src.data_processing.fuzzy_engine import FuzzyEngine

        engine = FuzzyEngine()
        engine.load_config_from_dict(sample_config_data)
        assert "temperature" in engine.get_supported_sensor_types()

    @pytest.mark.unit
    def test_engine_get_config(self, sample_config_data: dict) -> None:
        from src.data_processing.fuzzy_engine import FuzzyEngine

        engine = FuzzyEngine()
        engine.load_config_from_dict(sample_config_data)
        config = engine.get_config("temperature")
        assert config is not None
        assert config.sensor_type == "temperature"

    @pytest.mark.unit
    def test_engine_get_config_unknown(self) -> None:
        from src.data_processing.fuzzy_engine import FuzzyEngine

        engine = FuzzyEngine()
        assert engine.get_config("unknown") is None

    @pytest.mark.unit
    def test_engine_fuzzify_single_term(self, sample_config_data: dict) -> None:
        from src.data_processing.fuzzy_engine import FuzzyEngine

        engine = FuzzyEngine()
        engine.load_config_from_dict(sample_config_data)
        result = engine.fuzzify("temperature", 5.0)
        assert result.sensor_type == "temperature"
        assert result.raw_value == 5.0
        terms = dict(result.memberships)
        assert "cold" in terms
        assert terms["cold"] == 1.0

    @pytest.mark.unit
    def test_engine_fuzzify_overlapping_terms(self, sample_config_data: dict) -> None:
        from src.data_processing.fuzzy_engine import FuzzyEngine

        engine = FuzzyEngine()
        engine.load_config_from_dict(sample_config_data)
        result = engine.fuzzify("temperature", 25.0)
        terms = dict(result.memberships)
        assert "comfortable" in terms
        assert "hot" in terms

    @pytest.mark.unit
    def test_engine_fuzzify_filters_below_threshold(
        self, sample_config_data: dict
    ) -> None:
        from src.data_processing.fuzzy_engine import FuzzyEngine

        engine = FuzzyEngine()
        engine.load_config_from_dict(sample_config_data)
        result = engine.fuzzify("temperature", 22.0)
        for _term, degree in result.memberships:
            assert degree >= 0.1

    @pytest.mark.unit
    def test_engine_fuzzify_unknown_sensor_raises(self) -> None:
        from src.data_processing.fuzzy_engine import FuzzyEngine, FuzzyEngineError

        engine = FuzzyEngine()
        with pytest.raises(FuzzyEngineError, match="Unknown sensor type"):
            engine.fuzzify("unknown_sensor", 25.0)

    @pytest.mark.unit
    def test_engine_fuzzify_sorted_by_degree(self, sample_config_data: dict) -> None:
        from src.data_processing.fuzzy_engine import FuzzyEngine

        engine = FuzzyEngine()
        engine.load_config_from_dict(sample_config_data)
        result = engine.fuzzify("temperature", 25.0)
        degrees = [d for _, d in result.memberships]
        assert degrees == sorted(degrees, reverse=True)

    @pytest.mark.unit
    def test_engine_cache_hit(self, sample_config_data: dict) -> None:
        from src.data_processing.fuzzy_engine import FuzzyEngine

        engine = FuzzyEngine()
        engine.load_config_from_dict(sample_config_data)
        result1 = engine.fuzzify("temperature", 25.0)
        result2 = engine.fuzzify("temperature", 25.0)
        assert result1.timestamp == result2.timestamp
        assert engine.cache_size == 1

    @pytest.mark.unit
    def test_engine_cache_disabled(self, sample_config_data: dict) -> None:
        from src.data_processing.fuzzy_engine import FuzzyEngine

        engine = FuzzyEngine()
        engine.load_config_from_dict(sample_config_data)
        engine.fuzzify("temperature", 25.0, use_cache=True)
        engine.fuzzify("temperature", 25.0, use_cache=False)
        assert engine.cache_size == 1

    @pytest.mark.unit
    def test_engine_cache_clear(self, sample_config_data: dict) -> None:
        from src.data_processing.fuzzy_engine import FuzzyEngine

        engine = FuzzyEngine()
        engine.load_config_from_dict(sample_config_data)
        engine.fuzzify("temperature", 25.0)
        engine.fuzzify("temperature", 30.0)
        assert engine.cache_size == 2
        engine.clear_cache()
        assert engine.cache_size == 0

    @pytest.mark.unit
    def test_engine_cache_invalidated_on_config_reload(
        self, sample_config_data: dict
    ) -> None:
        from src.data_processing.fuzzy_engine import FuzzyEngine

        engine = FuzzyEngine()
        engine.load_config_from_dict(sample_config_data)
        engine.fuzzify("temperature", 25.0)
        assert engine.cache_size == 1
        engine.load_config_from_dict(sample_config_data)
        assert engine.cache_size == 0

    @pytest.mark.unit
    def test_engine_fuzzify_batch(self, sample_config_data: dict) -> None:
        from src.data_processing.fuzzy_engine import FuzzyEngine

        engine = FuzzyEngine()
        engine.load_config_from_dict(sample_config_data)
        readings = [("temperature", 5.0), ("temperature", 22.0), ("temperature", 35.0)]
        results = engine.fuzzify_batch(readings)
        assert len(results) == 3
        assert results[0].raw_value == 5.0
        assert results[1].raw_value == 22.0
        assert results[2].raw_value == 35.0

    @pytest.mark.unit
    def test_engine_load_config_from_file(self, tmp_path: Path) -> None:
        from src.data_processing.fuzzy_engine import FuzzyEngine

        config_file = tmp_path / "humidity.json"
        config_file.write_text(
            """{
            "sensor_type": "humidity",
            "unit": "percent",
            "universe_of_discourse": {"min": 0.0, "max": 100.0},
            "linguistic_variables": [
                {
                    "term": "dry",
                    "function_type": "triangular",
                    "parameters": {"a": 0.0, "b": 20.0, "c": 40.0}
                }
            ]
        }"""
        )
        engine = FuzzyEngine()
        engine.load_config_from_file(config_file)
        assert "humidity" in engine.get_supported_sensor_types()

    @pytest.mark.unit
    def test_engine_load_configs_from_directory(self, tmp_path: Path) -> None:
        from src.data_processing.fuzzy_engine import FuzzyEngine

        (tmp_path / "temp.json").write_text(
            """{
            "sensor_type": "temperature",
            "unit": "celsius",
            "universe_of_discourse": {"min": 0.0, "max": 50.0},
            "linguistic_variables": [
                {"term": "warm", "function_type": "triangular", "parameters": {"a": 20.0, "b": 25.0, "c": 30.0}}
            ]
        }"""
        )
        (tmp_path / "humidity.json").write_text(
            """{
            "sensor_type": "humidity",
            "unit": "percent",
            "universe_of_discourse": {"min": 0.0, "max": 100.0},
            "linguistic_variables": [
                {"term": "dry", "function_type": "triangular", "parameters": {"a": 0.0, "b": 20.0, "c": 40.0}}
            ]
        }"""
        )
        engine = FuzzyEngine()
        count = engine.load_configs_from_directory(tmp_path)
        assert count == 2
        assert len(engine.get_supported_sensor_types()) == 2

    @pytest.mark.unit
    def test_engine_multi_sensor_types(self) -> None:
        from src.data_processing.fuzzy_engine import FuzzyEngine

        engine = FuzzyEngine()
        engine.load_config_from_dict(
            {
                "sensor_type": "temperature",
                "unit": "celsius",
                "universe_of_discourse": {"min": 0.0, "max": 50.0},
                "linguistic_variables": [
                    {
                        "term": "hot",
                        "function_type": "triangular",
                        "parameters": {"a": 30.0, "b": 40.0, "c": 50.0},
                    }
                ],
            }
        )
        engine.load_config_from_dict(
            {
                "sensor_type": "humidity",
                "unit": "percent",
                "universe_of_discourse": {"min": 0.0, "max": 100.0},
                "linguistic_variables": [
                    {
                        "term": "humid",
                        "function_type": "triangular",
                        "parameters": {"a": 60.0, "b": 80.0, "c": 100.0},
                    }
                ],
            }
        )
        temp_result = engine.fuzzify("temperature", 40.0)
        humidity_result = engine.fuzzify("humidity", 80.0)
        assert temp_result.sensor_type == "temperature"
        assert humidity_result.sensor_type == "humidity"
        assert dict(temp_result.memberships).get("hot") == 1.0
        assert dict(humidity_result.memberships).get("humid") == 1.0


class TestLRUCache:
    @pytest.mark.unit
    def test_cache_eviction_on_max_size(self) -> None:
        from src.data_processing.fuzzy_engine import FuzzyEngine

        engine = FuzzyEngine(cache_max_size=2)
        engine.load_config_from_dict(
            {
                "sensor_type": "temp",
                "unit": "c",
                "universe_of_discourse": {"min": 0.0, "max": 100.0},
                "linguistic_variables": [
                    {
                        "term": "mid",
                        "function_type": "triangular",
                        "parameters": {"a": 0.0, "b": 50.0, "c": 100.0},
                    }
                ],
            }
        )
        engine.fuzzify("temp", 10.0)
        engine.fuzzify("temp", 20.0)
        engine.fuzzify("temp", 30.0)
        assert engine.cache_size == 2

    @pytest.mark.unit
    def test_cache_ttl_expiration(self) -> None:
        from src.data_processing.fuzzy_engine import FuzzyEngine

        engine = FuzzyEngine(cache_ttl_seconds=0.05)
        engine.load_config_from_dict(
            {
                "sensor_type": "temp",
                "unit": "c",
                "universe_of_discourse": {"min": 0.0, "max": 100.0},
                "linguistic_variables": [
                    {
                        "term": "mid",
                        "function_type": "triangular",
                        "parameters": {"a": 0.0, "b": 50.0, "c": 100.0},
                    }
                ],
            }
        )
        result1 = engine.fuzzify("temp", 50.0)
        time.sleep(0.1)
        result2 = engine.fuzzify("temp", 50.0)
        assert result1.timestamp != result2.timestamp
