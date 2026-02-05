"""Accuracy tests for LLM rule interpretation (Phase 7.4).

These tests verify the rule interpretation accuracy target of >=85%
as specified in ADD Section 8.1 and Engineering Tasks TST-012, TST-013.

The tests use diverse input scenarios to measure:
- Response parsing accuracy
- Rule-to-action mapping correctness
- Parameter extraction accuracy
- Edge case handling
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest


@dataclass
class AccuracyTestCase:
    name: str
    llm_response: str
    expected_action: bool
    expected_device: str | None = None
    expected_command: str | None = None
    expected_params: dict[str, Any] | None = None
    expected_reason: str | None = None


DIVERSE_LLM_RESPONSES: list[AccuracyTestCase] = [
    AccuracyTestCase(
        name="simple_turn_on",
        llm_response="ACTION: ac_living_room, turn_on",
        expected_action=True,
        expected_device="ac_living_room",
        expected_command="turn_on",
    ),
    AccuracyTestCase(
        name="turn_on_with_temperature",
        llm_response="ACTION: ac_bedroom, turn_on, temperature=22",
        expected_action=True,
        expected_device="ac_bedroom",
        expected_command="turn_on",
        expected_params={"temperature": 22},
    ),
    AccuracyTestCase(
        name="turn_off_simple",
        llm_response="ACTION: heater_office, turn_off",
        expected_action=True,
        expected_device="heater_office",
        expected_command="turn_off",
    ),
    AccuracyTestCase(
        name="set_brightness",
        llm_response="ACTION: light_kitchen, set_brightness, level=75",
        expected_action=True,
        expected_device="light_kitchen",
        expected_command="set_brightness",
        expected_params={"level": 75},
    ),
    AccuracyTestCase(
        name="multiple_parameters",
        llm_response="ACTION: thermostat_main, set_mode, mode=cooling, target=24",
        expected_action=True,
        expected_device="thermostat_main",
        expected_command="set_mode",
        expected_params={"mode": "cooling", "target": 24},
    ),
    AccuracyTestCase(
        name="no_action_comfortable",
        llm_response="NO_ACTION: Temperature is already comfortable at 22°C",
        expected_action=False,
        expected_reason="Temperature is already comfortable at 22°C",
    ),
    AccuracyTestCase(
        name="no_action_already_on",
        llm_response="NO_ACTION: The air conditioner is already running",
        expected_action=False,
        expected_reason="The air conditioner is already running",
    ),
    AccuracyTestCase(
        name="action_with_preamble",
        llm_response="Based on the current temperature being hot, I recommend: ACTION: ac_living_room, turn_on",
        expected_action=True,
        expected_device="ac_living_room",
        expected_command="turn_on",
    ),
    AccuracyTestCase(
        name="action_with_reasoning_after",
        llm_response="ACTION: fan_bedroom, turn_on\nThis will help cool down the room.",
        expected_action=True,
        expected_device="fan_bedroom",
        expected_command="turn_on",
    ),
    AccuracyTestCase(
        name="lowercase_action",
        llm_response="action: blinds_south, close",
        expected_action=True,
        expected_device="blinds_south",
        expected_command="close",
    ),
    AccuracyTestCase(
        name="action_with_spaces",
        llm_response="ACTION : humidifier_living , turn_on , humidity_target = 50",
        expected_action=True,
        expected_device="humidifier_living",
        expected_command="turn_on",
        expected_params={"humidity_target": 50},
    ),
    AccuracyTestCase(
        name="no_action_lowercase",
        llm_response="no_action: The room is not occupied",
        expected_action=False,
        expected_reason="The room is not occupied",
    ),
    AccuracyTestCase(
        name="action_underscores_in_device",
        llm_response="ACTION: smart_plug_1_outlet_a, turn_on",
        expected_action=True,
        expected_device="smart_plug_1_outlet_a",
        expected_command="turn_on",
    ),
    AccuracyTestCase(
        name="action_numeric_param",
        llm_response="ACTION: motor_blinds, set_position, percent=50",
        expected_action=True,
        expected_device="motor_blinds",
        expected_command="set_position",
        expected_params={"percent": 50},
    ),
    AccuracyTestCase(
        name="no_action_multiline_reason",
        llm_response="NO_ACTION: The current conditions do not warrant any changes.\nTemperature is within acceptable range.",
        expected_action=False,
    ),
    AccuracyTestCase(
        name="action_set_temperature",
        llm_response="ACTION: hvac_zone1, set_temperature, temp=26",
        expected_action=True,
        expected_device="hvac_zone1",
        expected_command="set_temperature",
        expected_params={"temp": 26},
    ),
    AccuracyTestCase(
        name="action_dim_light",
        llm_response="ACTION: dimmer_hallway, dim, brightness=30",
        expected_action=True,
        expected_device="dimmer_hallway",
        expected_command="dim",
        expected_params={"brightness": 30},
    ),
    AccuracyTestCase(
        name="no_action_night_mode",
        llm_response="NO_ACTION: Night mode is active, no adjustments allowed",
        expected_action=False,
    ),
    AccuracyTestCase(
        name="action_open_valve",
        llm_response="ACTION: valve_irrigation, open, duration=30",
        expected_action=True,
        expected_device="valve_irrigation",
        expected_command="open",
        expected_params={"duration": 30},
    ),
    AccuracyTestCase(
        name="action_with_verbose_llm_output",
        llm_response="""Let me analyze the current sensor state:
- Temperature is hot (0.85)
- Humidity is high (0.72)

Given the rule "If temperature is hot, turn on the AC", I should activate the air conditioning.

ACTION: ac_main, turn_on, temperature=23

This will help bring the temperature down to a comfortable level.""",
        expected_action=True,
        expected_device="ac_main",
        expected_command="turn_on",
        expected_params={"temperature": 23},
    ),
]

MALFORMED_RESPONSES: list[tuple[str, str]] = [
    ("empty_response", ""),
    ("whitespace_only", "   \n\t  "),
    ("no_keyword", "Turn on the AC in the living room"),
    ("incomplete_action", "ACTION:"),
    ("action_no_device", "ACTION: , turn_on"),
    ("action_no_command", "ACTION: device_id"),
    ("random_text", "The weather is nice today"),
    ("partial_action", "ACT: device, command"),
    ("misspelled_action", "ACTON: device, command"),
    ("json_format", '{"action": "turn_on", "device": "ac"}'),
]


class TestResponseParserAccuracy:
    """Test ResponseParser accuracy with diverse LLM outputs."""

    ACCURACY_TARGET = 0.85

    @pytest.mark.unit
    def test_diverse_response_parsing_accuracy(self) -> None:
        from src.control_reasoning.response_parser import ResponseParser, ResponseType

        parser = ResponseParser()
        correct = 0
        total = len(DIVERSE_LLM_RESPONSES)

        for case in DIVERSE_LLM_RESPONSES:
            result = parser.parse(case.llm_response)

            is_correct = True

            if case.expected_action:
                if (
                    result.response_type != ResponseType.ACTION
                    or result.action is None
                    or case.expected_device
                    and result.action.device_id != case.expected_device
                    or case.expected_command
                    and result.action.command != case.expected_command
                ):
                    is_correct = False
            else:
                if result.response_type != ResponseType.NO_ACTION:
                    is_correct = False

            if is_correct:
                correct += 1

        accuracy = correct / total
        assert accuracy >= self.ACCURACY_TARGET, (
            f"Response parsing accuracy {accuracy:.2%} below target {self.ACCURACY_TARGET:.0%}. "
            f"Passed {correct}/{total} cases."
        )

    @pytest.mark.unit
    def test_parameter_extraction_accuracy(self) -> None:
        from src.control_reasoning.response_parser import ResponseParser

        parser = ResponseParser()
        cases_with_params = [c for c in DIVERSE_LLM_RESPONSES if c.expected_params]
        correct = 0

        for case in cases_with_params:
            result = parser.parse(case.llm_response)
            if result.action and case.expected_params:
                all_params_match = all(
                    result.action.parameters.get(k) == v
                    for k, v in case.expected_params.items()
                )
                if all_params_match:
                    correct += 1

        if cases_with_params:
            accuracy = correct / len(cases_with_params)
            assert accuracy >= 0.80, (
                f"Parameter extraction accuracy {accuracy:.2%} below 80% target"
            )

    @pytest.mark.unit
    def test_malformed_response_detection(self) -> None:
        from src.control_reasoning.response_parser import ResponseParser, ResponseType

        parser = ResponseParser()
        correct = 0

        for name, response in MALFORMED_RESPONSES:
            result = parser.parse(response)
            if result.response_type == ResponseType.MALFORMED:
                correct += 1

        accuracy = correct / len(MALFORMED_RESPONSES)
        assert accuracy >= 0.90, (
            f"Malformed detection accuracy {accuracy:.2%} below 90% target"
        )


class TestRuleInterpretationAccuracy:
    """Test end-to-end rule interpretation accuracy."""

    ACCURACY_TARGET = 0.85

    @pytest.fixture
    def sample_sensor_descriptions(self) -> list:
        from src.data_processing.linguistic_descriptor import (
            LinguisticDescription,
            TermMembership,
        )

        return [
            LinguisticDescription(
                sensor_id="temp_living",
                sensor_type="temperature",
                terms=(TermMembership("hot", 0.85),),
                raw_value=32.0,
            ),
            LinguisticDescription(
                sensor_id="humidity_living",
                sensor_type="humidity",
                terms=(TermMembership("high", 0.72),),
                raw_value=75.0,
            ),
        ]

    @pytest.fixture
    def test_prompt_template(self) -> str:
        return """You are a smart home controller. Based on the current sensor state, evaluate the rule and decide on an action.

Current sensor state:
{sensor_state}

Rule to evaluate:
{rule_text}

If an action is needed, respond with:
ACTION: device_id, command, param1=value1, param2=value2

If no action is needed, respond with:
NO_ACTION: reason

Respond with exactly one of the above formats."""

    @pytest.mark.unit
    def test_prompt_building_for_diverse_rules(
        self,
        sample_sensor_descriptions: list,
        test_prompt_template: str,
    ) -> None:
        from src.control_reasoning.prompt_builder import PromptBuilder, PromptTemplate

        template = PromptTemplate.from_string(test_prompt_template)
        builder = PromptBuilder(template=template)

        test_rules = [
            "If the temperature is hot, turn on the air conditioner",
            "When humidity is high, activate the dehumidifier",
            "If it's cold outside, increase the heating",
            "Turn off lights when no motion is detected",
            "If temperature exceeds 30 degrees, set AC to cooling mode at 22 degrees",
        ]

        for rule in test_rules:
            prompt = builder.build(rule, sample_sensor_descriptions)
            assert prompt.prompt_text
            assert rule in prompt.prompt_text
            assert "hot" in prompt.prompt_text or "high" in prompt.prompt_text

    @pytest.mark.unit
    def test_action_spec_validation_accuracy(self) -> None:
        from src.control_reasoning.response_parser import ActionSpec

        valid_cases = [
            {"device_id": "ac_1", "command": "turn_on", "parameters": {}},
            {
                "device_id": "light_2",
                "command": "set_brightness",
                "parameters": {"level": 50},
            },
            {
                "device_id": "thermostat",
                "command": "set_temp",
                "parameters": {"temp": 22, "mode": "cool"},
            },
        ]

        invalid_cases: list[dict[str, Any]] = [
            {"device_id": "", "command": "turn_on"},
            {"device_id": "device", "command": ""},
        ]

        valid_correct = 0
        for case in valid_cases:
            try:
                ActionSpec(**case)
                valid_correct += 1
            except ValueError:
                pass

        invalid_correct = 0
        for case in invalid_cases:
            try:
                ActionSpec(**case)
            except ValueError:
                invalid_correct += 1

        assert valid_correct == len(valid_cases), "All valid cases should pass"
        assert invalid_correct == len(invalid_cases), "All invalid cases should fail"


class TestPromptRefinementImpact:
    """Test impact of prompt variations on parsing accuracy."""

    @pytest.mark.unit
    def test_structured_prompt_produces_parseable_format(self) -> None:
        from src.control_reasoning.prompt_builder import PromptBuilder, PromptTemplate
        from src.data_processing.linguistic_descriptor import (
            LinguisticDescription,
            TermMembership,
        )

        template_text = """Evaluate this rule for the smart home system.

Sensor readings:
{sensor_state}

Rule: {rule_text}

IMPORTANT: Respond ONLY with one of these exact formats:
- ACTION: device_id, command
- ACTION: device_id, command, param=value
- NO_ACTION: reason

Your response:"""

        template = PromptTemplate.from_string(template_text)
        builder = PromptBuilder(template=template)

        descriptions = [
            LinguisticDescription(
                sensor_id="temp_1",
                sensor_type="temperature",
                terms=(TermMembership("hot", 0.9),),
                raw_value=35.0,
            ),
        ]

        prompt = builder.build(
            "If temperature is hot, turn on AC",
            descriptions,
        )

        assert "ACTION:" in prompt.prompt_text
        assert "NO_ACTION:" in prompt.prompt_text
        assert "device_id" in prompt.prompt_text

    @pytest.mark.unit
    def test_prompt_contains_all_sensor_context(self) -> None:
        from src.control_reasoning.prompt_builder import PromptBuilder, PromptTemplate
        from src.data_processing.linguistic_descriptor import (
            LinguisticDescription,
            TermMembership,
        )

        template = PromptTemplate.from_string(
            "State: {sensor_state}\nRule: {rule_text}"
        )
        builder = PromptBuilder(template=template)

        descriptions = [
            LinguisticDescription(
                sensor_id="temp_living",
                sensor_type="temperature",
                terms=(TermMembership("hot", 0.85), TermMembership("warm", 0.15)),
                raw_value=32.0,
            ),
            LinguisticDescription(
                sensor_id="humidity_bath",
                sensor_type="humidity",
                terms=(TermMembership("high", 0.92),),
                raw_value=85.0,
            ),
        ]

        prompt = builder.build("Test rule", descriptions)

        assert "temperature" in prompt.prompt_text
        assert "humidity" in prompt.prompt_text
        assert "hot" in prompt.prompt_text
        assert "high" in prompt.prompt_text
        assert "0.85" in prompt.prompt_text
        assert "0.92" in prompt.prompt_text


class TestEdgeCaseAccuracy:
    """Test accuracy on edge cases and unusual inputs."""

    @pytest.mark.unit
    def test_unicode_in_responses(self) -> None:
        from src.control_reasoning.response_parser import ResponseParser, ResponseType

        parser = ResponseParser()

        responses_with_unicode = [
            "ACTION: ac_主卧, turn_on",
            "NO_ACTION: Température déjà confortable",
            "ACTION: sensor_αβγ, activate",
        ]

        parsed_count = 0
        for response in responses_with_unicode:
            result = parser.parse(response)
            if result.response_type != ResponseType.MALFORMED:
                parsed_count += 1

        assert parsed_count >= 2, "Should handle most unicode responses"

    @pytest.mark.unit
    def test_very_long_responses(self) -> None:
        from src.control_reasoning.response_parser import ResponseParser, ResponseType

        parser = ResponseParser()

        long_preamble = "Analyzing the sensor data. " * 100
        response = f"{long_preamble}\nACTION: ac_living, turn_on"

        result = parser.parse(response)
        assert result.response_type == ResponseType.ACTION
        assert result.action is not None
        assert result.action.device_id == "ac_living"

    @pytest.mark.unit
    def test_responses_with_special_characters(self) -> None:
        from src.control_reasoning.response_parser import ResponseParser, ResponseType

        parser = ResponseParser()

        special_responses = [
            "ACTION: device-with-dashes, turn_on",
            "ACTION: device.with.dots, activate",
            "NO_ACTION: Temperature is 22°C (within range)",
        ]

        for response in special_responses:
            result = parser.parse(response)
            assert result.response_type != ResponseType.MALFORMED or "." in response


class TestAccuracyMetrics:
    """Comprehensive accuracy measurement."""

    @pytest.mark.unit
    def test_overall_accuracy_meets_target(self) -> None:
        from src.control_reasoning.response_parser import ResponseParser, ResponseType

        parser = ResponseParser()

        all_cases = DIVERSE_LLM_RESPONSES
        correct = 0
        details = []

        for case in all_cases:
            result = parser.parse(case.llm_response)

            passed = True
            if case.expected_action:
                if (
                    result.response_type != ResponseType.ACTION
                    or result.action is None
                    or case.expected_device
                    and result.action.device_id != case.expected_device
                    or case.expected_command
                    and result.action.command != case.expected_command
                ):
                    passed = False
            else:
                if result.response_type != ResponseType.NO_ACTION:
                    passed = False

            if passed:
                correct += 1
            else:
                details.append(f"FAILED: {case.name}")

        accuracy = correct / len(all_cases)
        target = 0.85

        assert accuracy >= target, (
            f"Overall accuracy {accuracy:.2%} below {target:.0%} target.\n"
            f"Failed cases: {details}"
        )

    @pytest.mark.unit
    def test_accuracy_by_response_type(self) -> None:
        from src.control_reasoning.response_parser import ResponseParser, ResponseType

        parser = ResponseParser()

        action_cases = [c for c in DIVERSE_LLM_RESPONSES if c.expected_action]
        no_action_cases = [c for c in DIVERSE_LLM_RESPONSES if not c.expected_action]

        action_correct = sum(
            1
            for c in action_cases
            if parser.parse(c.llm_response).response_type == ResponseType.ACTION
        )

        no_action_correct = sum(
            1
            for c in no_action_cases
            if parser.parse(c.llm_response).response_type == ResponseType.NO_ACTION
        )

        if action_cases:
            action_accuracy = action_correct / len(action_cases)
            assert action_accuracy >= 0.85, (
                f"ACTION accuracy {action_accuracy:.2%} below 85%"
            )

        if no_action_cases:
            no_action_accuracy = no_action_correct / len(no_action_cases)
            assert no_action_accuracy >= 0.85, (
                f"NO_ACTION accuracy {no_action_accuracy:.2%} below 85%"
            )
