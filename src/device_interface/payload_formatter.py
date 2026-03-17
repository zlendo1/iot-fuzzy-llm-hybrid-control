from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from src.common.exceptions import ValidationError
from src.common.logging import get_logger
from src.device_interface.models import LEGACY_VALUE_FIELDS, PayloadSchema

logger = get_logger(__name__)


class PayloadFormatter:
    def __init__(self, schema: Optional[PayloadSchema] = None) -> None:
        self._schema = schema

    def extract_value(self, payload: dict[str, Any]) -> float:
        if self._schema is not None:
            raw = payload.get(self._schema.value_field)
            if raw is None:
                raise ValidationError(
                    f"Value field '{self._schema.value_field}' not found in payload"
                )
            return float(raw)
        for field in LEGACY_VALUE_FIELDS:
            raw = payload.get(field)
            if raw is not None:
                return float(raw)
        raise ValidationError(f"No value field found. Tried: {LEGACY_VALUE_FIELDS}")

    def extract_timestamp(self, payload: dict[str, Any]) -> Optional[datetime]:
        if self._schema is None or self._schema.timestamp_field is None:
            return None
        raw = payload.get(self._schema.timestamp_field)
        if raw is None:
            logger.warning(
                "Timestamp field missing", extra={"field": self._schema.timestamp_field}
            )
            return None
        if isinstance(raw, str):
            try:
                return datetime.fromisoformat(raw)
            except ValueError:
                logger.warning("Could not parse timestamp", extra={"raw": raw})
                return None
        return None

    def extract_unit(self, payload: dict[str, Any]) -> Optional[str]:
        if self._schema is None or self._schema.unit_field is None:
            return None
        raw = payload.get(self._schema.unit_field)
        if raw is None:
            logger.warning(
                "Unit field missing", extra={"field": self._schema.unit_field}
            )
            return None
        return str(raw)
