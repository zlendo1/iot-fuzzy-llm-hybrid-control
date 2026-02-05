from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from src.common.logging import get_logger

logger = get_logger(__name__)


class ResponseType(Enum):
    ACTION = "ACTION"
    NO_ACTION = "NO_ACTION"
    MALFORMED = "MALFORMED"


@dataclass(frozen=True)
class ActionSpec:
    device_id: str
    command: str
    parameters: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.device_id:
            raise ValueError("device_id cannot be empty")
        if not self.command:
            raise ValueError("command cannot be empty")

    def to_dict(self) -> dict[str, Any]:
        return {
            "device_id": self.device_id,
            "command": self.command,
            "parameters": dict(self.parameters),
        }


@dataclass(frozen=True)
class ParsedResponse:
    response_type: ResponseType
    action: ActionSpec | None = None
    reason: str | None = None
    raw_text: str = ""

    @property
    def is_action(self) -> bool:
        return self.response_type == ResponseType.ACTION

    @property
    def is_no_action(self) -> bool:
        return self.response_type == ResponseType.NO_ACTION

    @property
    def is_malformed(self) -> bool:
        return self.response_type == ResponseType.MALFORMED


class ResponseParser:
    ACTION_PATTERN = re.compile(
        r"ACTION\s*:\s*([^,\s]+)\s*,\s*([^,\s]+)(?:\s*,\s*(.+))?",
        re.IGNORECASE,
    )
    NO_ACTION_PATTERN = re.compile(
        r"NO_ACTION\s*:\s*(.+)",
        re.IGNORECASE | re.DOTALL,
    )
    PARAM_PATTERN = re.compile(r"(\w+)\s*=\s*([^,]+)")

    def parse(self, llm_response: str) -> ParsedResponse:
        if not llm_response or not llm_response.strip():
            return self._malformed("Empty response", llm_response)

        text = llm_response.strip()

        action_match = self.ACTION_PATTERN.search(text)
        if action_match:
            return self._parse_action(action_match, text)

        no_action_match = self.NO_ACTION_PATTERN.search(text)
        if no_action_match:
            reason = no_action_match.group(1).strip()
            logger.debug("Parsed NO_ACTION response", extra={"reason": reason[:50]})
            return ParsedResponse(
                response_type=ResponseType.NO_ACTION,
                reason=reason,
                raw_text=text,
            )

        return self._malformed("No ACTION or NO_ACTION found", text)

    def _parse_action(self, match: re.Match[str], raw_text: str) -> ParsedResponse:
        device_id = match.group(1).strip()
        command = match.group(2).strip()
        params_str = match.group(3)

        parameters = self._parse_parameters(params_str) if params_str else {}

        try:
            action = ActionSpec(
                device_id=device_id,
                command=command,
                parameters=parameters,
            )
        except ValueError as e:
            return self._malformed(str(e), raw_text)

        logger.debug(
            "Parsed ACTION response",
            extra={
                "device_id": device_id,
                "command": command,
                "param_count": len(parameters),
            },
        )

        return ParsedResponse(
            response_type=ResponseType.ACTION,
            action=action,
            raw_text=raw_text,
        )

    def _parse_parameters(self, params_str: str) -> dict[str, Any]:
        if not params_str:
            return {}

        params: dict[str, Any] = {}
        for match in self.PARAM_PATTERN.finditer(params_str):
            key = match.group(1).strip()
            value_str = match.group(2).strip()
            params[key] = self._parse_value(value_str)

        return params

    def _parse_value(self, value_str: str) -> Any:
        value_str = value_str.strip()

        if value_str.lower() == "true":
            return True
        if value_str.lower() == "false":
            return False

        try:
            return int(value_str)
        except ValueError:
            pass

        try:
            return float(value_str)
        except ValueError:
            pass

        return value_str

    def _malformed(self, reason: str, raw_text: str) -> ParsedResponse:
        logger.warning(
            "Malformed LLM response",
            extra={"reason": reason, "response_preview": raw_text[:100]},
        )
        return ParsedResponse(
            response_type=ResponseType.MALFORMED,
            reason=reason,
            raw_text=raw_text,
        )

    def parse_batch(self, responses: list[str]) -> list[ParsedResponse]:
        return [self.parse(resp) for resp in responses]
