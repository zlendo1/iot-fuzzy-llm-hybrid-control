from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest


class TestActionSpec:
    @pytest.mark.unit
    def test_action_spec_with_all_fields(self) -> None:
        from src.control_reasoning.response_parser import ActionSpec

        action = ActionSpec(
            device_id="ac_living_room",
            command="turn_on",
            parameters={"temperature": 22},
        )
        assert action.device_id == "ac_living_room"
        assert action.command == "turn_on"
        assert action.parameters == {"temperature": 22}

    @pytest.mark.unit
    def test_action_spec_without_parameters(self) -> None:
        from src.control_reasoning.response_parser import ActionSpec

        action = ActionSpec(device_id="light_001", command="turn_off")
        assert action.parameters == {}

    @pytest.mark.unit
    def test_action_spec_raises_on_empty_device_id(self) -> None:
        from src.control_reasoning.response_parser import ActionSpec

        with pytest.raises(ValueError) as exc_info:
            ActionSpec(device_id="", command="turn_on")
        assert "device_id" in str(exc_info.value)

    @pytest.mark.unit
    def test_action_spec_raises_on_empty_command(self) -> None:
        from src.control_reasoning.response_parser import ActionSpec

        with pytest.raises(ValueError) as exc_info:
            ActionSpec(device_id="device_001", command="")
        assert "command" in str(exc_info.value)

    @pytest.mark.unit
    def test_action_spec_to_dict(self) -> None:
        from src.control_reasoning.response_parser import ActionSpec

        action = ActionSpec(
            device_id="fan_001",
            command="set_speed",
            parameters={"speed": 3},
        )
        result = action.to_dict()
        assert result == {
            "device_id": "fan_001",
            "command": "set_speed",
            "parameters": {"speed": 3},
        }

    @pytest.mark.unit
    def test_action_spec_is_frozen(self) -> None:
        from src.control_reasoning.response_parser import ActionSpec

        action = ActionSpec(device_id="dev", command="cmd")
        with pytest.raises(FrozenInstanceError):
            action.device_id = "other"  # type: ignore[misc]


class TestResponseType:
    @pytest.mark.unit
    def test_response_type_values(self) -> None:
        from src.control_reasoning.response_parser import ResponseType

        assert ResponseType.ACTION.value == "ACTION"
        assert ResponseType.NO_ACTION.value == "NO_ACTION"
        assert ResponseType.MALFORMED.value == "MALFORMED"


class TestParsedResponse:
    @pytest.mark.unit
    def test_parsed_response_action(self) -> None:
        from src.control_reasoning.response_parser import (
            ActionSpec,
            ParsedResponse,
            ResponseType,
        )

        action = ActionSpec(device_id="dev", command="cmd")
        response = ParsedResponse(
            response_type=ResponseType.ACTION,
            action=action,
            raw_text="ACTION: dev, cmd",
        )
        assert response.is_action is True
        assert response.is_no_action is False
        assert response.is_malformed is False
        assert response.action is action

    @pytest.mark.unit
    def test_parsed_response_no_action(self) -> None:
        from src.control_reasoning.response_parser import ParsedResponse, ResponseType

        response = ParsedResponse(
            response_type=ResponseType.NO_ACTION,
            reason="Temperature is comfortable",
            raw_text="NO_ACTION: Temperature is comfortable",
        )
        assert response.is_action is False
        assert response.is_no_action is True
        assert response.is_malformed is False
        assert response.reason == "Temperature is comfortable"

    @pytest.mark.unit
    def test_parsed_response_malformed(self) -> None:
        from src.control_reasoning.response_parser import ParsedResponse, ResponseType

        response = ParsedResponse(
            response_type=ResponseType.MALFORMED,
            reason="No ACTION or NO_ACTION found",
            raw_text="gibberish response",
        )
        assert response.is_action is False
        assert response.is_no_action is False
        assert response.is_malformed is True

    @pytest.mark.unit
    def test_parsed_response_is_frozen(self) -> None:
        from src.control_reasoning.response_parser import ParsedResponse, ResponseType

        response = ParsedResponse(
            response_type=ResponseType.NO_ACTION,
            raw_text="test",
        )
        with pytest.raises(FrozenInstanceError):
            response.raw_text = "modified"  # type: ignore[misc]


class TestResponseParserActionParsing:
    @pytest.mark.unit
    def test_parse_action_without_parameters(self) -> None:
        from src.control_reasoning.response_parser import ResponseParser, ResponseType

        parser = ResponseParser()
        result = parser.parse("ACTION: ac_living_room, turn_on")

        assert result.response_type == ResponseType.ACTION
        assert result.action is not None
        assert result.action.device_id == "ac_living_room"
        assert result.action.command == "turn_on"
        assert result.action.parameters == {}

    @pytest.mark.unit
    def test_parse_action_with_single_parameter(self) -> None:
        from src.control_reasoning.response_parser import ResponseParser, ResponseType

        parser = ResponseParser()
        result = parser.parse("ACTION: thermostat_001, set_temperature, temperature=22")

        assert result.response_type == ResponseType.ACTION
        assert result.action is not None
        assert result.action.device_id == "thermostat_001"
        assert result.action.command == "set_temperature"
        assert result.action.parameters == {"temperature": 22}

    @pytest.mark.unit
    def test_parse_action_with_multiple_parameters(self) -> None:
        from src.control_reasoning.response_parser import ResponseParser, ResponseType

        parser = ResponseParser()
        result = parser.parse(
            "ACTION: light_001, set_color, hue=180, saturation=100, brightness=80"
        )

        assert result.response_type == ResponseType.ACTION
        assert result.action is not None
        assert result.action.parameters == {
            "hue": 180,
            "saturation": 100,
            "brightness": 80,
        }

    @pytest.mark.unit
    def test_parse_action_with_float_parameter(self) -> None:
        from src.control_reasoning.response_parser import ResponseParser

        parser = ResponseParser()
        result = parser.parse("ACTION: thermostat, set_temp, temperature=22.5")

        assert result.action is not None
        assert result.action.parameters["temperature"] == 22.5

    @pytest.mark.unit
    def test_parse_action_with_boolean_parameters(self) -> None:
        from src.control_reasoning.response_parser import ResponseParser

        parser = ResponseParser()
        result = parser.parse("ACTION: device, configure, enabled=true, silent=false")

        assert result.action is not None
        assert result.action.parameters["enabled"] is True
        assert result.action.parameters["silent"] is False

    @pytest.mark.unit
    def test_parse_action_with_string_parameter(self) -> None:
        from src.control_reasoning.response_parser import ResponseParser

        parser = ResponseParser()
        result = parser.parse("ACTION: speaker, play_sound, sound=alarm")

        assert result.action is not None
        assert result.action.parameters["sound"] == "alarm"

    @pytest.mark.unit
    def test_parse_action_case_insensitive(self) -> None:
        from src.control_reasoning.response_parser import ResponseParser, ResponseType

        parser = ResponseParser()

        result1 = parser.parse("action: dev, cmd")
        assert result1.response_type == ResponseType.ACTION

        result2 = parser.parse("Action: dev, cmd")
        assert result2.response_type == ResponseType.ACTION

        result3 = parser.parse("ACTION: dev, cmd")
        assert result3.response_type == ResponseType.ACTION

    @pytest.mark.unit
    def test_parse_action_with_whitespace_variations(self) -> None:
        from src.control_reasoning.response_parser import ResponseParser, ResponseType

        parser = ResponseParser()

        result1 = parser.parse("ACTION:dev,cmd")
        assert result1.response_type == ResponseType.ACTION

        result2 = parser.parse("ACTION :  dev  ,  cmd")
        assert result2.response_type == ResponseType.ACTION

    @pytest.mark.unit
    def test_parse_action_in_longer_response(self) -> None:
        from src.control_reasoning.response_parser import ResponseParser, ResponseType

        parser = ResponseParser()
        response = """
Based on the sensor readings, the temperature is hot.
Therefore, I recommend the following action:

ACTION: ac_living_room, turn_on, temperature=22

This will help cool down the room.
"""
        result = parser.parse(response)

        assert result.response_type == ResponseType.ACTION
        assert result.action is not None
        assert result.action.device_id == "ac_living_room"
        assert result.action.command == "turn_on"


class TestResponseParserNoAction:
    @pytest.mark.unit
    def test_parse_no_action(self) -> None:
        from src.control_reasoning.response_parser import ResponseParser, ResponseType

        parser = ResponseParser()
        result = parser.parse("NO_ACTION: Temperature is already comfortable")

        assert result.response_type == ResponseType.NO_ACTION
        assert result.reason == "Temperature is already comfortable"
        assert result.action is None

    @pytest.mark.unit
    def test_parse_no_action_case_insensitive(self) -> None:
        from src.control_reasoning.response_parser import ResponseParser, ResponseType

        parser = ResponseParser()

        result1 = parser.parse("no_action: reason")
        assert result1.response_type == ResponseType.NO_ACTION

        result2 = parser.parse("No_Action: reason")
        assert result2.response_type == ResponseType.NO_ACTION

    @pytest.mark.unit
    def test_parse_no_action_multiline_reason(self) -> None:
        from src.control_reasoning.response_parser import ResponseParser, ResponseType

        parser = ResponseParser()
        result = parser.parse(
            "NO_ACTION: Temperature is comfortable.\nNo cooling needed."
        )

        assert result.response_type == ResponseType.NO_ACTION
        assert "Temperature is comfortable" in result.reason  # type: ignore[operator]

    @pytest.mark.unit
    def test_parse_no_action_in_longer_response(self) -> None:
        from src.control_reasoning.response_parser import ResponseParser, ResponseType

        parser = ResponseParser()
        response = """
After analyzing the sensor readings:
- Temperature: 22°C (comfortable)
- Humidity: 50% (normal)

NO_ACTION: All conditions are within acceptable ranges.
"""
        result = parser.parse(response)

        assert result.response_type == ResponseType.NO_ACTION
        assert "acceptable ranges" in result.reason  # type: ignore[operator]


class TestResponseParserMalformed:
    @pytest.mark.unit
    def test_parse_empty_string(self) -> None:
        from src.control_reasoning.response_parser import ResponseParser, ResponseType

        parser = ResponseParser()
        result = parser.parse("")

        assert result.response_type == ResponseType.MALFORMED
        assert "Empty response" in result.reason  # type: ignore[operator]

    @pytest.mark.unit
    def test_parse_whitespace_only(self) -> None:
        from src.control_reasoning.response_parser import ResponseParser, ResponseType

        parser = ResponseParser()
        result = parser.parse("   \n\t  ")

        assert result.response_type == ResponseType.MALFORMED

    @pytest.mark.unit
    def test_parse_no_action_or_no_action_keyword(self) -> None:
        from src.control_reasoning.response_parser import ResponseParser, ResponseType

        parser = ResponseParser()
        result = parser.parse("I think you should turn on the AC.")

        assert result.response_type == ResponseType.MALFORMED
        assert "No ACTION or NO_ACTION found" in result.reason  # type: ignore[operator]

    @pytest.mark.unit
    def test_parse_incomplete_action(self) -> None:
        from src.control_reasoning.response_parser import ResponseParser, ResponseType

        parser = ResponseParser()
        result = parser.parse("ACTION: device_only")

        assert result.response_type == ResponseType.MALFORMED

    @pytest.mark.unit
    def test_parse_preserves_raw_text(self) -> None:
        from src.control_reasoning.response_parser import ResponseParser

        parser = ResponseParser()
        raw_text = "Some malformed response text"
        result = parser.parse(raw_text)

        assert result.raw_text == raw_text


class TestResponseParserBatch:
    @pytest.mark.unit
    def test_parse_batch_multiple_responses(self) -> None:
        from src.control_reasoning.response_parser import ResponseParser, ResponseType

        parser = ResponseParser()
        responses = [
            "ACTION: dev1, cmd1",
            "NO_ACTION: reason",
            "malformed",
        ]
        results = parser.parse_batch(responses)

        assert len(results) == 3
        assert results[0].response_type == ResponseType.ACTION
        assert results[1].response_type == ResponseType.NO_ACTION
        assert results[2].response_type == ResponseType.MALFORMED

    @pytest.mark.unit
    def test_parse_batch_empty_list(self) -> None:
        from src.control_reasoning.response_parser import ResponseParser

        parser = ResponseParser()
        results = parser.parse_batch([])

        assert results == []


class TestResponseParserEdgeCases:
    @pytest.mark.unit
    def test_parse_action_with_underscore_device_id(self) -> None:
        from src.control_reasoning.response_parser import ResponseParser

        parser = ResponseParser()
        result = parser.parse("ACTION: living_room_ac_01, turn_on")

        assert result.action is not None
        assert result.action.device_id == "living_room_ac_01"

    @pytest.mark.unit
    def test_parse_action_with_hyphen_in_command(self) -> None:
        from src.control_reasoning.response_parser import ResponseParser

        parser = ResponseParser()
        result = parser.parse("ACTION: device, set-mode, mode=eco")

        assert result.action is not None
        assert result.action.command == "set-mode"

    @pytest.mark.unit
    def test_parse_action_parameter_with_special_characters(self) -> None:
        from src.control_reasoning.response_parser import ResponseParser

        parser = ResponseParser()
        result = parser.parse("ACTION: speaker, play, url=http://example.com")

        assert result.action is not None
        assert result.action.parameters["url"] == "http://example.com"

    @pytest.mark.unit
    def test_action_takes_precedence_over_no_action(self) -> None:
        from src.control_reasoning.response_parser import ResponseParser, ResponseType

        parser = ResponseParser()
        response = """
NO_ACTION: ignore this
ACTION: device, command
"""
        result = parser.parse(response)
        assert result.response_type == ResponseType.ACTION
