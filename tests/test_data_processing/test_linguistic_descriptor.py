from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from src.data_processing.fuzzy_engine import FuzzificationResult


@pytest.mark.unit
class TestTermMembership:
    def test_term_membership_creation(self) -> None:
        from src.data_processing.linguistic_descriptor import TermMembership

        tm = TermMembership(term="hot", degree=0.85)

        assert tm.term == "hot"
        assert tm.degree == 0.85

    def test_term_membership_frozen(self) -> None:
        from src.data_processing.linguistic_descriptor import TermMembership

        tm = TermMembership(term="hot", degree=0.85)

        with pytest.raises(AttributeError):
            tm.term = "cold"  # type: ignore[misc]

    def test_term_membership_degree_validation_below_zero(self) -> None:
        from src.data_processing.linguistic_descriptor import TermMembership

        with pytest.raises(ValueError, match="Degree must be in"):
            TermMembership(term="hot", degree=-0.1)

    def test_term_membership_degree_validation_above_one(self) -> None:
        from src.data_processing.linguistic_descriptor import TermMembership

        with pytest.raises(ValueError, match="Degree must be in"):
            TermMembership(term="hot", degree=1.1)

    def test_term_membership_empty_term_rejected(self) -> None:
        from src.data_processing.linguistic_descriptor import TermMembership

        with pytest.raises(ValueError, match="Term cannot be empty"):
            TermMembership(term="", degree=0.5)

    def test_term_membership_to_dict(self) -> None:
        from src.data_processing.linguistic_descriptor import TermMembership

        tm = TermMembership(term="moderate", degree=0.72)
        result = tm.to_dict()

        assert result == {"term": "moderate", "degree": 0.72}

    def test_term_membership_format_default_precision(self) -> None:
        from src.data_processing.linguistic_descriptor import TermMembership

        tm = TermMembership(term="hot", degree=0.857)

        assert tm.format() == "hot (0.86)"

    def test_term_membership_format_custom_precision(self) -> None:
        from src.data_processing.linguistic_descriptor import TermMembership

        tm = TermMembership(term="cold", degree=0.12345)

        assert tm.format(precision=3) == "cold (0.123)"

    def test_term_membership_boundary_degrees(self) -> None:
        from src.data_processing.linguistic_descriptor import TermMembership

        zero = TermMembership(term="none", degree=0.0)
        one = TermMembership(term="full", degree=1.0)

        assert zero.degree == 0.0
        assert one.degree == 1.0


@pytest.mark.unit
class TestLinguisticDescription:
    def test_linguistic_description_creation(self) -> None:
        from src.data_processing.linguistic_descriptor import (
            LinguisticDescription,
            TermMembership,
        )

        terms = (TermMembership("hot", 0.85), TermMembership("warm", 0.15))
        desc = LinguisticDescription(
            sensor_id="temp_1",
            sensor_type="temperature",
            raw_value=28.5,
            terms=terms,
            timestamp=1234567890.0,
            unit="°C",
        )

        assert desc.sensor_id == "temp_1"
        assert desc.sensor_type == "temperature"
        assert desc.raw_value == 28.5
        assert len(desc.terms) == 2
        assert desc.timestamp == 1234567890.0
        assert desc.unit == "°C"

    def test_linguistic_description_frozen(self) -> None:
        from src.data_processing.linguistic_descriptor import LinguisticDescription

        desc = LinguisticDescription(
            sensor_id="temp_1",
            sensor_type="temperature",
            raw_value=25.0,
            terms=(),
        )

        with pytest.raises(AttributeError):
            desc.sensor_id = "temp_2"  # type: ignore[misc]

    def test_linguistic_description_empty_sensor_id_rejected(self) -> None:
        from src.data_processing.linguistic_descriptor import LinguisticDescription

        with pytest.raises(ValueError, match="sensor_id cannot be empty"):
            LinguisticDescription(
                sensor_id="",
                sensor_type="temperature",
                raw_value=25.0,
                terms=(),
            )

    def test_linguistic_description_empty_sensor_type_rejected(self) -> None:
        from src.data_processing.linguistic_descriptor import LinguisticDescription

        with pytest.raises(ValueError, match="sensor_type cannot be empty"):
            LinguisticDescription(
                sensor_id="temp_1",
                sensor_type="",
                raw_value=25.0,
                terms=(),
            )

    def test_dominant_term_returns_first(self) -> None:
        from src.data_processing.linguistic_descriptor import (
            LinguisticDescription,
            TermMembership,
        )

        terms = (
            TermMembership("hot", 0.85),
            TermMembership("warm", 0.15),
        )
        desc = LinguisticDescription(
            sensor_id="temp_1",
            sensor_type="temperature",
            raw_value=28.5,
            terms=terms,
        )

        assert desc.dominant_term is not None
        assert desc.dominant_term.term == "hot"
        assert desc.dominant_term.degree == 0.85

    def test_dominant_term_none_when_no_terms(self) -> None:
        from src.data_processing.linguistic_descriptor import LinguisticDescription

        desc = LinguisticDescription(
            sensor_id="temp_1",
            sensor_type="temperature",
            raw_value=28.5,
            terms=(),
        )

        assert desc.dominant_term is None

    def test_is_ambiguous_with_multiple_high_terms(self) -> None:
        from src.data_processing.linguistic_descriptor import (
            LinguisticDescription,
            TermMembership,
        )

        terms = (
            TermMembership("warm", 0.55),
            TermMembership("hot", 0.45),
        )
        desc = LinguisticDescription(
            sensor_id="temp_1",
            sensor_type="temperature",
            raw_value=26.0,
            terms=terms,
        )

        assert desc.is_ambiguous is True

    def test_is_not_ambiguous_with_single_dominant_term(self) -> None:
        from src.data_processing.linguistic_descriptor import (
            LinguisticDescription,
            TermMembership,
        )

        terms = (
            TermMembership("hot", 0.95),
            TermMembership("warm", 0.05),
        )
        desc = LinguisticDescription(
            sensor_id="temp_1",
            sensor_type="temperature",
            raw_value=30.0,
            terms=terms,
        )

        assert desc.is_ambiguous is False

    def test_is_not_ambiguous_with_no_terms(self) -> None:
        from src.data_processing.linguistic_descriptor import LinguisticDescription

        desc = LinguisticDescription(
            sensor_id="temp_1",
            sensor_type="temperature",
            raw_value=28.5,
            terms=(),
        )

        assert desc.is_ambiguous is False

    def test_to_dict(self) -> None:
        from src.data_processing.linguistic_descriptor import (
            LinguisticDescription,
            TermMembership,
        )

        terms = (TermMembership("hot", 0.85),)
        desc = LinguisticDescription(
            sensor_id="temp_1",
            sensor_type="temperature",
            raw_value=28.5,
            terms=terms,
            timestamp=1234567890.0,
            unit="°C",
        )

        result = desc.to_dict()

        assert result == {
            "sensor_id": "temp_1",
            "sensor_type": "temperature",
            "raw_value": 28.5,
            "terms": [{"term": "hot", "degree": 0.85}],
            "timestamp": 1234567890.0,
            "unit": "°C",
        }

    def test_format_description_with_terms(self) -> None:
        from src.data_processing.linguistic_descriptor import (
            LinguisticDescription,
            TermMembership,
        )

        terms = (
            TermMembership("hot", 0.85),
            TermMembership("warm", 0.15),
        )
        desc = LinguisticDescription(
            sensor_id="temp_1",
            sensor_type="temperature",
            raw_value=28.5,
            terms=terms,
        )

        assert desc.format_description() == "temperature is hot (0.85), warm (0.15)"

    def test_format_description_no_terms(self) -> None:
        from src.data_processing.linguistic_descriptor import LinguisticDescription

        desc = LinguisticDescription(
            sensor_id="temp_1",
            sensor_type="temperature",
            raw_value=28.5,
            terms=(),
        )

        assert desc.format_description() == "temperature is unknown"

    def test_format_description_custom_precision(self) -> None:
        from src.data_processing.linguistic_descriptor import (
            LinguisticDescription,
            TermMembership,
        )

        terms = (TermMembership("hot", 0.857),)
        desc = LinguisticDescription(
            sensor_id="temp_1",
            sensor_type="temperature",
            raw_value=28.5,
            terms=terms,
        )

        assert desc.format_description(precision=3) == "temperature is hot (0.857)"

    def test_format_simple_with_terms(self) -> None:
        from src.data_processing.linguistic_descriptor import (
            LinguisticDescription,
            TermMembership,
        )

        terms = (
            TermMembership("hot", 0.85),
            TermMembership("warm", 0.15),
        )
        desc = LinguisticDescription(
            sensor_id="temp_1",
            sensor_type="temperature",
            raw_value=28.5,
            terms=terms,
        )

        assert desc.format_simple() == "temperature is hot"

    def test_format_simple_no_terms(self) -> None:
        from src.data_processing.linguistic_descriptor import LinguisticDescription

        desc = LinguisticDescription(
            sensor_id="temp_1",
            sensor_type="temperature",
            raw_value=28.5,
            terms=(),
        )

        assert desc.format_simple() == "temperature is unknown"

    def test_format_with_value_and_unit(self) -> None:
        from src.data_processing.linguistic_descriptor import (
            LinguisticDescription,
            TermMembership,
        )

        terms = (TermMembership("hot", 0.85),)
        desc = LinguisticDescription(
            sensor_id="temp_1",
            sensor_type="temperature",
            raw_value=28.5,
            terms=terms,
            unit="°C",
        )

        assert desc.format_with_value() == "temperature (28.5°C) is hot (0.85)"

    def test_format_with_value_no_unit(self) -> None:
        from src.data_processing.linguistic_descriptor import (
            LinguisticDescription,
            TermMembership,
        )

        terms = (TermMembership("hot", 0.85),)
        desc = LinguisticDescription(
            sensor_id="temp_1",
            sensor_type="temperature",
            raw_value=28.5,
            terms=terms,
        )

        assert desc.format_with_value() == "temperature (28.5) is hot (0.85)"

    def test_format_with_value_no_terms(self) -> None:
        from src.data_processing.linguistic_descriptor import LinguisticDescription

        desc = LinguisticDescription(
            sensor_id="temp_1",
            sensor_type="temperature",
            raw_value=28.5,
            terms=(),
            unit="°C",
        )

        assert desc.format_with_value() == "temperature (28.5°C) is unknown"


@pytest.mark.unit
class TestLinguisticDescriptorBuilder:
    def _make_fuzzification_result(
        self,
        sensor_type: str = "temperature",
        raw_value: float = 28.5,
        memberships: tuple[tuple[str, float], ...] = (("hot", 0.85), ("warm", 0.15)),
        timestamp: float = 1234567890.0,
    ) -> FuzzificationResult:
        from src.data_processing.fuzzy_engine import FuzzificationResult

        return FuzzificationResult(
            sensor_type=sensor_type,
            raw_value=raw_value,
            memberships=memberships,
            timestamp=timestamp,
        )

    def test_builder_creation_default(self) -> None:
        from src.data_processing.linguistic_descriptor import (
            LinguisticDescriptorBuilder,
        )

        builder = LinguisticDescriptorBuilder()

        assert builder.max_terms == 3
        assert builder.min_degree == 0.0

    def test_builder_creation_custom(self) -> None:
        from src.data_processing.linguistic_descriptor import (
            LinguisticDescriptorBuilder,
        )

        builder = LinguisticDescriptorBuilder(max_terms=5, min_degree=0.1)

        assert builder.max_terms == 5
        assert builder.min_degree == 0.1

    def test_builder_max_terms_validation(self) -> None:
        from src.data_processing.linguistic_descriptor import (
            LinguisticDescriptorBuilder,
        )

        with pytest.raises(ValueError, match="max_terms must be at least 1"):
            LinguisticDescriptorBuilder(max_terms=0)

    def test_builder_min_degree_validation_below_zero(self) -> None:
        from src.data_processing.linguistic_descriptor import (
            LinguisticDescriptorBuilder,
        )

        with pytest.raises(ValueError, match="min_degree must be in"):
            LinguisticDescriptorBuilder(min_degree=-0.1)

    def test_builder_min_degree_validation_above_one(self) -> None:
        from src.data_processing.linguistic_descriptor import (
            LinguisticDescriptorBuilder,
        )

        with pytest.raises(ValueError, match="min_degree must be in"):
            LinguisticDescriptorBuilder(min_degree=1.1)

    def test_build_creates_description(self) -> None:
        from src.data_processing.linguistic_descriptor import (
            LinguisticDescriptorBuilder,
        )

        builder = LinguisticDescriptorBuilder()
        result = self._make_fuzzification_result()

        desc = builder.build(sensor_id="temp_1", result=result)

        assert desc.sensor_id == "temp_1"
        assert desc.sensor_type == "temperature"
        assert desc.raw_value == 28.5
        assert len(desc.terms) == 2
        assert desc.terms[0].term == "hot"
        assert desc.terms[0].degree == 0.85

    def test_build_with_unit(self) -> None:
        from src.data_processing.linguistic_descriptor import (
            LinguisticDescriptorBuilder,
        )

        builder = LinguisticDescriptorBuilder()
        result = self._make_fuzzification_result()

        desc = builder.build(sensor_id="temp_1", result=result, unit="°C")

        assert desc.unit == "°C"

    def test_build_respects_max_terms(self) -> None:
        from src.data_processing.linguistic_descriptor import (
            LinguisticDescriptorBuilder,
        )

        builder = LinguisticDescriptorBuilder(max_terms=1)
        result = self._make_fuzzification_result(
            memberships=(("hot", 0.85), ("warm", 0.15), ("cold", 0.05))
        )

        desc = builder.build(sensor_id="temp_1", result=result)

        assert len(desc.terms) == 1
        assert desc.terms[0].term == "hot"

    def test_build_respects_min_degree(self) -> None:
        from src.data_processing.linguistic_descriptor import (
            LinguisticDescriptorBuilder,
        )

        builder = LinguisticDescriptorBuilder(min_degree=0.2)
        result = self._make_fuzzification_result(
            memberships=(("hot", 0.85), ("warm", 0.15))
        )

        desc = builder.build(sensor_id="temp_1", result=result)

        assert len(desc.terms) == 1
        assert desc.terms[0].term == "hot"

    def test_build_preserves_timestamp(self) -> None:
        from src.data_processing.linguistic_descriptor import (
            LinguisticDescriptorBuilder,
        )

        builder = LinguisticDescriptorBuilder()
        result = self._make_fuzzification_result(timestamp=9999999.0)

        desc = builder.build(sensor_id="temp_1", result=result)

        assert desc.timestamp == 9999999.0

    def test_build_empty_memberships(self) -> None:
        from src.data_processing.linguistic_descriptor import (
            LinguisticDescriptorBuilder,
        )

        builder = LinguisticDescriptorBuilder()
        result = self._make_fuzzification_result(memberships=())

        desc = builder.build(sensor_id="temp_1", result=result)

        assert len(desc.terms) == 0
        assert desc.format_description() == "temperature is unknown"

    def test_build_batch(self) -> None:
        from src.data_processing.linguistic_descriptor import (
            LinguisticDescriptorBuilder,
        )

        builder = LinguisticDescriptorBuilder()
        results = [
            ("temp_1", self._make_fuzzification_result(), "°C"),
            (
                "hum_1",
                self._make_fuzzification_result(
                    sensor_type="humidity",
                    raw_value=65.0,
                    memberships=(("moderate", 0.72),),
                ),
                "%",
            ),
        ]

        descriptions = builder.build_batch(results)

        assert len(descriptions) == 2
        assert descriptions[0].sensor_id == "temp_1"
        assert descriptions[0].unit == "°C"
        assert descriptions[1].sensor_id == "hum_1"
        assert descriptions[1].sensor_type == "humidity"
        assert descriptions[1].unit == "%"

    def test_format_multi_sensor(self) -> None:
        from src.data_processing.linguistic_descriptor import (
            LinguisticDescription,
            LinguisticDescriptorBuilder,
            TermMembership,
        )

        builder = LinguisticDescriptorBuilder()
        descriptions = [
            LinguisticDescription(
                sensor_id="temp_1",
                sensor_type="temperature",
                raw_value=28.5,
                terms=(TermMembership("hot", 0.85),),
            ),
            LinguisticDescription(
                sensor_id="hum_1",
                sensor_type="humidity",
                raw_value=65.0,
                terms=(TermMembership("moderate", 0.72),),
            ),
        ]

        result = builder.format_multi_sensor(descriptions)

        assert result == "temperature is hot (0.85); humidity is moderate (0.72)"

    def test_format_multi_sensor_custom_separator(self) -> None:
        from src.data_processing.linguistic_descriptor import (
            LinguisticDescription,
            LinguisticDescriptorBuilder,
            TermMembership,
        )

        builder = LinguisticDescriptorBuilder()
        descriptions = [
            LinguisticDescription(
                sensor_id="temp_1",
                sensor_type="temperature",
                raw_value=28.5,
                terms=(TermMembership("hot", 0.85),),
            ),
            LinguisticDescription(
                sensor_id="hum_1",
                sensor_type="humidity",
                raw_value=65.0,
                terms=(TermMembership("moderate", 0.72),),
            ),
        ]

        result = builder.format_multi_sensor(descriptions, separator=" | ")

        assert result == "temperature is hot (0.85) | humidity is moderate (0.72)"

    def test_format_multi_sensor_empty(self) -> None:
        from src.data_processing.linguistic_descriptor import (
            LinguisticDescriptorBuilder,
        )

        builder = LinguisticDescriptorBuilder()

        result = builder.format_multi_sensor([])

        assert result == "no sensor data available"

    def test_format_for_llm(self) -> None:
        from src.data_processing.linguistic_descriptor import (
            LinguisticDescription,
            LinguisticDescriptorBuilder,
            TermMembership,
        )

        builder = LinguisticDescriptorBuilder()
        descriptions = [
            LinguisticDescription(
                sensor_id="temp_1",
                sensor_type="temperature",
                raw_value=28.5,
                terms=(TermMembership("hot", 0.85),),
            ),
            LinguisticDescription(
                sensor_id="hum_1",
                sensor_type="humidity",
                raw_value=65.0,
                terms=(TermMembership("moderate", 0.72),),
            ),
        ]

        result = builder.format_for_llm(descriptions)

        expected = (
            "Current sensor state:\n"
            "- temperature is hot (0.85)\n"
            "- humidity is moderate (0.72)"
        )
        assert result == expected

    def test_format_for_llm_with_values(self) -> None:
        from src.data_processing.linguistic_descriptor import (
            LinguisticDescription,
            LinguisticDescriptorBuilder,
            TermMembership,
        )

        builder = LinguisticDescriptorBuilder()
        descriptions = [
            LinguisticDescription(
                sensor_id="temp_1",
                sensor_type="temperature",
                raw_value=28.5,
                terms=(TermMembership("hot", 0.85),),
                unit="°C",
            ),
        ]

        result = builder.format_for_llm(descriptions, include_values=True)

        expected = "Current sensor state:\n- temperature (28.5°C) is hot (0.85)"
        assert result == expected

    def test_format_for_llm_empty(self) -> None:
        from src.data_processing.linguistic_descriptor import (
            LinguisticDescriptorBuilder,
        )

        builder = LinguisticDescriptorBuilder()

        result = builder.format_for_llm([])

        assert result == "Current sensor state: no data available."


@pytest.mark.unit
class TestModuleExports:
    def test_exports_from_data_processing_package(self) -> None:
        from src.data_processing import (
            LinguisticDescription,
            LinguisticDescriptorBuilder,
            TermMembership,
        )

        assert TermMembership is not None
        assert LinguisticDescription is not None
        assert LinguisticDescriptorBuilder is not None
