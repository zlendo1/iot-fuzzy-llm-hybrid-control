from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest


class TestPromptTemplate:
    @pytest.mark.unit
    def test_template_from_string(self) -> None:
        from src.control_reasoning.prompt_builder import PromptTemplate

        template = PromptTemplate.from_string(
            "State: {sensor_state}\nRule: {rule_text}"
        )
        assert "{sensor_state}" in template.template
        assert "{rule_text}" in template.template

    @pytest.mark.unit
    def test_template_from_file(self, tmp_path: Path) -> None:
        from src.control_reasoning.prompt_builder import PromptTemplate

        template_file = tmp_path / "template.txt"
        template_file.write_text("Sensors: {sensor_state}\nEvaluate: {rule_text}")

        template = PromptTemplate.from_file(template_file)
        assert "Sensors: {sensor_state}" in template.template

    @pytest.mark.unit
    def test_template_validate_returns_true_when_both_placeholders_present(
        self,
    ) -> None:
        from src.control_reasoning.prompt_builder import PromptTemplate

        template = PromptTemplate(template="{sensor_state} and {rule_text}")
        assert template.validate() is True

    @pytest.mark.unit
    def test_template_validate_returns_false_when_sensor_placeholder_missing(
        self,
    ) -> None:
        from src.control_reasoning.prompt_builder import PromptTemplate

        template = PromptTemplate(template="Only {rule_text}")
        assert template.validate() is False

    @pytest.mark.unit
    def test_template_validate_returns_false_when_rule_placeholder_missing(
        self,
    ) -> None:
        from src.control_reasoning.prompt_builder import PromptTemplate

        template = PromptTemplate(template="Only {sensor_state}")
        assert template.validate() is False

    @pytest.mark.unit
    def test_template_custom_placeholders(self) -> None:
        from src.control_reasoning.prompt_builder import PromptTemplate

        template = PromptTemplate(
            template="<<STATE>> and <<RULE>>",
            sensor_state_placeholder="<<STATE>>",
            rule_text_placeholder="<<RULE>>",
        )
        assert template.validate() is True

    @pytest.mark.unit
    def test_template_is_frozen(self) -> None:
        from dataclasses import FrozenInstanceError

        from src.control_reasoning.prompt_builder import PromptTemplate

        template = PromptTemplate(template="test")
        with pytest.raises(FrozenInstanceError):
            template.template = "modified"  # type: ignore[misc]


class TestBuiltPrompt:
    @pytest.mark.unit
    def test_built_prompt_attributes(self) -> None:
        from src.control_reasoning.prompt_builder import BuiltPrompt

        prompt = BuiltPrompt(
            prompt_text="Full prompt here",
            rule_text="If hot, cool",
            sensor_state_summary="temp is hot",
            sensor_count=1,
        )
        assert prompt.prompt_text == "Full prompt here"
        assert prompt.rule_text == "If hot, cool"
        assert prompt.sensor_state_summary == "temp is hot"
        assert prompt.sensor_count == 1

    @pytest.mark.unit
    def test_built_prompt_character_count(self) -> None:
        from src.control_reasoning.prompt_builder import BuiltPrompt

        prompt = BuiltPrompt(
            prompt_text="A" * 100,
            rule_text="rule",
            sensor_state_summary="state",
            sensor_count=1,
        )
        assert prompt.character_count == 100

    @pytest.mark.unit
    def test_built_prompt_estimated_tokens(self) -> None:
        from src.control_reasoning.prompt_builder import BuiltPrompt

        prompt = BuiltPrompt(
            prompt_text="A" * 400,
            rule_text="rule",
            sensor_state_summary="state",
            sensor_count=1,
        )
        assert prompt.estimated_tokens == 100

    @pytest.mark.unit
    def test_built_prompt_is_frozen(self) -> None:
        from dataclasses import FrozenInstanceError

        from src.control_reasoning.prompt_builder import BuiltPrompt

        prompt = BuiltPrompt(
            prompt_text="test",
            rule_text="rule",
            sensor_state_summary="state",
            sensor_count=1,
        )
        with pytest.raises(FrozenInstanceError):
            prompt.prompt_text = "modified"  # type: ignore[misc]


def _create_linguistic_description(
    sensor_id: str = "temp_001",
    sensor_type: str = "temperature",
    raw_value: float = 28.5,
    terms: list[tuple[str, float]] | None = None,
    unit: str | None = "°C",
) -> Any:
    from src.data_processing.linguistic_descriptor import (
        LinguisticDescription,
        TermMembership,
    )

    if terms is None:
        terms = [("hot", 0.85), ("warm", 0.15)]

    term_memberships = tuple(TermMembership(term=t, degree=d) for t, d in terms)
    return LinguisticDescription(
        sensor_id=sensor_id,
        sensor_type=sensor_type,
        raw_value=raw_value,
        terms=term_memberships,
        unit=unit,
    )


class TestPromptBuilderInit:
    @pytest.mark.unit
    def test_builder_with_explicit_template(self) -> None:
        from src.control_reasoning.prompt_builder import PromptBuilder, PromptTemplate

        template = PromptTemplate.from_string("{sensor_state}\n{rule_text}")
        builder = PromptBuilder(template=template)
        assert builder.template is template

    @pytest.mark.unit
    def test_builder_with_template_path(self, tmp_path: Path) -> None:
        from src.control_reasoning.prompt_builder import PromptBuilder

        template_file = tmp_path / "template.txt"
        template_file.write_text("State: {sensor_state}\nRule: {rule_text}")

        builder = PromptBuilder(template_path=template_file)
        assert "State: {sensor_state}" in builder.template.template

    @pytest.mark.unit
    def test_builder_with_default_template(self) -> None:
        from src.control_reasoning.prompt_builder import PromptBuilder

        builder = PromptBuilder()
        assert builder.template.validate() is True
        assert "{sensor_state}" in builder.template.template
        assert "{rule_text}" in builder.template.template

    @pytest.mark.unit
    def test_builder_raises_on_invalid_template(self) -> None:
        from src.control_reasoning.prompt_builder import PromptBuilder, PromptTemplate

        template = PromptTemplate(template="Missing placeholders")
        with pytest.raises(ValueError) as exc_info:
            PromptBuilder(template=template)
        assert "missing required placeholders" in str(exc_info.value).lower()


class TestPromptBuilderBuild:
    @pytest.mark.unit
    def test_build_with_single_sensor(self) -> None:
        from src.control_reasoning.prompt_builder import PromptBuilder, PromptTemplate

        template = PromptTemplate.from_string(
            "Sensors:\n{sensor_state}\n\nRule: {rule_text}"
        )
        builder = PromptBuilder(template=template)
        desc = _create_linguistic_description()

        result = builder.build(
            rule_text="If temperature is hot, turn on AC",
            sensor_descriptions=[desc],
        )

        assert "temperature is hot" in result.prompt_text
        assert "If temperature is hot" in result.prompt_text
        assert result.rule_text == "If temperature is hot, turn on AC"
        assert result.sensor_count == 1

    @pytest.mark.unit
    def test_build_with_multiple_sensors(self) -> None:
        from src.control_reasoning.prompt_builder import PromptBuilder, PromptTemplate

        template = PromptTemplate.from_string("{sensor_state}\n{rule_text}")
        builder = PromptBuilder(template=template)

        temp_desc = _create_linguistic_description(
            sensor_id="temp_001",
            sensor_type="temperature",
            raw_value=28.5,
            terms=[("hot", 0.85)],
            unit="°C",
        )
        humidity_desc = _create_linguistic_description(
            sensor_id="hum_001",
            sensor_type="humidity",
            raw_value=75.0,
            terms=[("high", 0.70), ("moderate", 0.30)],
            unit="%",
        )

        result = builder.build(
            rule_text="If hot and humid, cool",
            sensor_descriptions=[temp_desc, humidity_desc],
        )

        assert "temperature is hot" in result.prompt_text
        assert "humidity is high" in result.prompt_text
        assert result.sensor_count == 2

    @pytest.mark.unit
    def test_build_with_no_sensors(self) -> None:
        from src.control_reasoning.prompt_builder import PromptBuilder, PromptTemplate

        template = PromptTemplate.from_string("{sensor_state}\n{rule_text}")
        builder = PromptBuilder(template=template)

        result = builder.build(
            rule_text="Always turn on lights at 6pm",
            sensor_descriptions=[],
        )

        assert "No sensor data available" in result.prompt_text
        assert result.sensor_count == 0

    @pytest.mark.unit
    def test_build_raises_on_empty_rule_text(self) -> None:
        from src.control_reasoning.prompt_builder import PromptBuilder, PromptTemplate

        template = PromptTemplate.from_string("{sensor_state}\n{rule_text}")
        builder = PromptBuilder(template=template)
        desc = _create_linguistic_description()

        with pytest.raises(ValueError) as exc_info:
            builder.build(rule_text="", sensor_descriptions=[desc])
        assert "empty" in str(exc_info.value).lower()

    @pytest.mark.unit
    def test_build_raises_on_whitespace_rule_text(self) -> None:
        from src.control_reasoning.prompt_builder import PromptBuilder, PromptTemplate

        template = PromptTemplate.from_string("{sensor_state}\n{rule_text}")
        builder = PromptBuilder(template=template)
        desc = _create_linguistic_description()

        with pytest.raises(ValueError):
            builder.build(rule_text="   ", sensor_descriptions=[desc])

    @pytest.mark.unit
    def test_build_includes_raw_value_with_unit(self) -> None:
        from src.control_reasoning.prompt_builder import PromptBuilder, PromptTemplate

        template = PromptTemplate.from_string("{sensor_state}\n{rule_text}")
        builder = PromptBuilder(template=template)
        desc = _create_linguistic_description(
            raw_value=28.5,
            unit="°C",
        )

        result = builder.build(
            rule_text="test rule",
            sensor_descriptions=[desc],
        )

        assert "(raw: 28.5 °C)" in result.prompt_text

    @pytest.mark.unit
    def test_build_omits_raw_value_when_no_unit(self) -> None:
        from src.control_reasoning.prompt_builder import PromptBuilder, PromptTemplate

        template = PromptTemplate.from_string("{sensor_state}\n{rule_text}")
        builder = PromptBuilder(template=template)
        desc = _create_linguistic_description(unit=None)

        result = builder.build(
            rule_text="test rule",
            sensor_descriptions=[desc],
        )

        assert "(raw:" not in result.prompt_text


class TestPromptBuilderFormatSensorState:
    @pytest.mark.unit
    def test_format_uses_format_description_method(self) -> None:
        from src.control_reasoning.prompt_builder import PromptBuilder, PromptTemplate

        template = PromptTemplate.from_string("{sensor_state}\n{rule_text}")
        builder = PromptBuilder(template=template)
        desc = _create_linguistic_description(
            sensor_type="temperature",
            terms=[("hot", 0.85), ("warm", 0.15)],
        )

        result = builder.build(
            rule_text="test",
            sensor_descriptions=[desc],
        )

        assert "temperature is hot (0.85), warm (0.15)" in result.sensor_state_summary

    @pytest.mark.unit
    def test_format_multiple_sensors_uses_bullet_points(self) -> None:
        from src.control_reasoning.prompt_builder import PromptBuilder, PromptTemplate

        template = PromptTemplate.from_string("{sensor_state}\n{rule_text}")
        builder = PromptBuilder(template=template)

        temp_desc = _create_linguistic_description(
            sensor_type="temperature",
            terms=[("hot", 0.85)],
        )
        hum_desc = _create_linguistic_description(
            sensor_id="hum_001",
            sensor_type="humidity",
            terms=[("high", 0.70)],
        )

        result = builder.build(
            rule_text="test",
            sensor_descriptions=[temp_desc, hum_desc],
        )

        assert "- temperature is hot" in result.sensor_state_summary
        assert "- humidity is high" in result.sensor_state_summary


class TestPromptBuilderBuildBatch:
    @pytest.mark.unit
    def test_build_batch_returns_list_of_prompts(self) -> None:
        from src.control_reasoning.prompt_builder import PromptBuilder, PromptTemplate

        template = PromptTemplate.from_string("{sensor_state}\n{rule_text}")
        builder = PromptBuilder(template=template)
        desc = _create_linguistic_description()

        rules = [
            "If hot, cool",
            "If cold, heat",
            "If moderate, do nothing",
        ]
        results = builder.build_batch(rules, [desc])

        assert len(results) == 3
        assert results[0].rule_text == "If hot, cool"
        assert results[1].rule_text == "If cold, heat"
        assert results[2].rule_text == "If moderate, do nothing"

    @pytest.mark.unit
    def test_build_batch_with_empty_rules(self) -> None:
        from src.control_reasoning.prompt_builder import PromptBuilder, PromptTemplate

        template = PromptTemplate.from_string("{sensor_state}\n{rule_text}")
        builder = PromptBuilder(template=template)
        desc = _create_linguistic_description()

        results = builder.build_batch([], [desc])
        assert results == []

    @pytest.mark.unit
    def test_build_batch_shares_sensor_state(self) -> None:
        from src.control_reasoning.prompt_builder import PromptBuilder, PromptTemplate

        template = PromptTemplate.from_string("{sensor_state}\n{rule_text}")
        builder = PromptBuilder(template=template)
        desc = _create_linguistic_description(
            sensor_type="temperature",
            terms=[("hot", 0.85)],
        )

        rules = ["Rule A", "Rule B"]
        results = builder.build_batch(rules, [desc])

        assert results[0].sensor_state_summary == results[1].sensor_state_summary
        assert "temperature is hot" in results[0].sensor_state_summary


class TestPromptBuilderIntegration:
    @pytest.mark.unit
    def test_build_with_default_template_file(self) -> None:
        from src.control_reasoning.prompt_builder import PromptBuilder

        builder = PromptBuilder()
        desc = _create_linguistic_description(
            sensor_type="temperature",
            raw_value=30.0,
            terms=[("hot", 0.90)],
            unit="°C",
        )

        result = builder.build(
            rule_text="If temperature is hot, turn on AC",
            sensor_descriptions=[desc],
        )

        assert "temperature is hot" in result.prompt_text.lower()
        assert "turn on ac" in result.prompt_text.lower()
        assert result.sensor_count == 1
        assert result.character_count > 0
        assert result.estimated_tokens > 0
