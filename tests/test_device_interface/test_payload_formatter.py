from __future__ import annotations

from datetime import datetime

import pytest

from src.common.exceptions import ValidationError
from src.device_interface.models import PayloadSchema
from src.device_interface.payload_formatter import PayloadFormatter


@pytest.mark.unit
def test_extract_value_with_schema_value_field() -> None:
    formatter = PayloadFormatter(schema=PayloadSchema(value_field="sensor_value"))

    value = formatter.extract_value({"sensor_value": 25.5})

    assert value == 25.5


@pytest.mark.unit
def test_extract_value_with_schema_missing_field() -> None:
    formatter = PayloadFormatter(schema=PayloadSchema(value_field="sensor_value"))

    with pytest.raises(ValidationError):
        formatter.extract_value({"value": 25.5})


@pytest.mark.unit
def test_extract_value_legacy_fallback_value() -> None:
    formatter = PayloadFormatter()

    value = formatter.extract_value({"value": 25.5})

    assert value == 25.5


@pytest.mark.unit
def test_extract_value_legacy_fallback_reading() -> None:
    formatter = PayloadFormatter()

    value = formatter.extract_value({"reading": 30.0})

    assert value == 30.0


@pytest.mark.unit
def test_extract_value_legacy_fallback_v() -> None:
    formatter = PayloadFormatter()

    value = formatter.extract_value({"v": 10})

    assert value == 10.0


@pytest.mark.unit
def test_extract_value_no_schema_no_legacy_fields() -> None:
    formatter = PayloadFormatter()

    with pytest.raises(ValidationError):
        formatter.extract_value({"sensor_value": 10})


@pytest.mark.unit
def test_extract_value_converts_to_float() -> None:
    formatter = PayloadFormatter()

    value = formatter.extract_value({"value": 5})

    assert isinstance(value, float)
    assert value == 5.0


@pytest.mark.unit
def test_extract_timestamp_with_schema_field() -> None:
    formatter = PayloadFormatter(
        schema=PayloadSchema(value_field="value", timestamp_field="ts")
    )

    timestamp = formatter.extract_timestamp({"ts": "2026-01-01T00:00:00"})

    assert timestamp == datetime.fromisoformat("2026-01-01T00:00:00")


@pytest.mark.unit
def test_extract_timestamp_no_schema() -> None:
    formatter = PayloadFormatter()

    timestamp = formatter.extract_timestamp({"ts": "2026-01-01T00:00:00"})

    assert timestamp is None


@pytest.mark.unit
def test_extract_timestamp_missing_field_returns_none() -> None:
    formatter = PayloadFormatter(
        schema=PayloadSchema(value_field="value", timestamp_field="ts")
    )

    timestamp = formatter.extract_timestamp({"value": 5})

    assert timestamp is None


@pytest.mark.unit
def test_extract_unit_with_schema_field() -> None:
    formatter = PayloadFormatter(
        schema=PayloadSchema(value_field="value", unit_field="measurement_unit")
    )

    unit = formatter.extract_unit({"measurement_unit": "celsius"})

    assert unit == "celsius"


@pytest.mark.unit
def test_extract_unit_no_schema() -> None:
    formatter = PayloadFormatter()

    unit = formatter.extract_unit({"measurement_unit": "celsius"})

    assert unit is None


@pytest.mark.unit
def test_extract_unit_missing_field_returns_none() -> None:
    formatter = PayloadFormatter(
        schema=PayloadSchema(value_field="value", unit_field="measurement_unit")
    )

    unit = formatter.extract_unit({"value": 5})

    assert unit is None


@pytest.mark.unit
def test_formatter_default_schema() -> None:
    formatter = PayloadFormatter(schema=PayloadSchema.default())

    assert formatter is not None


@pytest.mark.unit
def test_formatter_no_schema() -> None:
    formatter = PayloadFormatter()

    assert formatter is not None
