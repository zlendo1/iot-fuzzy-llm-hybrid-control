from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from src.common.logging import get_logger

if TYPE_CHECKING:
    from collections.abc import Sequence

    from src.data_processing.linguistic_descriptor import LinguisticDescription

logger = get_logger(__name__)


@dataclass(frozen=True)
class PromptTemplate:
    template: str
    sensor_state_placeholder: str = "{sensor_state}"
    rule_text_placeholder: str = "{rule_text}"

    @classmethod
    def from_file(cls, path: Path) -> PromptTemplate:
        template = path.read_text(encoding="utf-8")
        return cls(template=template)

    @classmethod
    def from_string(cls, template: str) -> PromptTemplate:
        return cls(template=template)

    def validate(self) -> bool:
        return (
            self.sensor_state_placeholder in self.template
            and self.rule_text_placeholder in self.template
        )


@dataclass(frozen=True)
class BuiltPrompt:
    prompt_text: str
    rule_text: str
    sensor_state_summary: str
    sensor_count: int

    @property
    def character_count(self) -> int:
        return len(self.prompt_text)

    @property
    def estimated_tokens(self) -> int:
        return self.character_count // 4


class PromptBuilder:
    DEFAULT_TEMPLATE_PATH = Path("config/prompt_template.txt")

    def __init__(
        self,
        template: PromptTemplate | None = None,
        template_path: Path | None = None,
    ) -> None:
        if template is not None:
            self._template = template
        elif template_path is not None:
            self._template = PromptTemplate.from_file(template_path)
        else:
            self._template = PromptTemplate.from_file(self.DEFAULT_TEMPLATE_PATH)

        if not self._template.validate():
            raise ValueError(
                f"Template missing required placeholders: "
                f"{self._template.sensor_state_placeholder} and/or "
                f"{self._template.rule_text_placeholder}"
            )

    @property
    def template(self) -> PromptTemplate:
        return self._template

    def build(
        self,
        rule_text: str,
        sensor_descriptions: Sequence[LinguisticDescription],
    ) -> BuiltPrompt:
        if not rule_text.strip():
            raise ValueError("rule_text cannot be empty")

        sensor_state_summary = self._format_sensor_state(sensor_descriptions)

        prompt_text = self._template.template.replace(
            self._template.sensor_state_placeholder, sensor_state_summary
        ).replace(self._template.rule_text_placeholder, rule_text)

        logger.debug(
            "Built prompt",
            extra={
                "rule_text": rule_text[:50],
                "sensor_count": len(sensor_descriptions),
                "prompt_length": len(prompt_text),
            },
        )

        return BuiltPrompt(
            prompt_text=prompt_text,
            rule_text=rule_text,
            sensor_state_summary=sensor_state_summary,
            sensor_count=len(sensor_descriptions),
        )

    def _format_sensor_state(
        self,
        descriptions: Sequence[LinguisticDescription],
    ) -> str:
        if not descriptions:
            return "No sensor data available."

        lines = []
        for desc in descriptions:
            line = f"- {desc.format_description()}"
            if desc.unit:
                line += f" (raw: {desc.raw_value} {desc.unit})"
            lines.append(line)

        return "\n".join(lines)

    def build_batch(
        self,
        rules: Sequence[str],
        sensor_descriptions: Sequence[LinguisticDescription],
    ) -> list[BuiltPrompt]:
        return [self.build(rule, sensor_descriptions) for rule in rules]
