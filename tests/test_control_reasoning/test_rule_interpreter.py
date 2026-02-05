from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest


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


class TestNaturalLanguageRule:
    @pytest.mark.unit
    def test_rule_with_required_fields(self) -> None:
        from src.control_reasoning.rule_interpreter import NaturalLanguageRule

        rule = NaturalLanguageRule(
            rule_id="rule_001",
            rule_text="If temperature is hot, turn on AC",
        )
        assert rule.rule_id == "rule_001"
        assert rule.rule_text == "If temperature is hot, turn on AC"
        assert rule.priority == 1
        assert rule.enabled is True
        assert rule.trigger_count == 0

    @pytest.mark.unit
    def test_rule_with_all_fields(self) -> None:
        from src.control_reasoning.rule_interpreter import NaturalLanguageRule

        rule = NaturalLanguageRule(
            rule_id="rule_002",
            rule_text="If humidity is high, turn on dehumidifier",
            priority=2,
            enabled=False,
            created_timestamp="2024-01-15T10:00:00Z",
            last_triggered="2024-01-15T14:30:00Z",
            trigger_count=5,
            metadata={"tags": ["climate", "humidity"]},
        )
        assert rule.priority == 2
        assert rule.enabled is False
        assert rule.trigger_count == 5
        assert rule.metadata["tags"] == ["climate", "humidity"]

    @pytest.mark.unit
    def test_rule_raises_on_empty_rule_id(self) -> None:
        from src.control_reasoning.rule_interpreter import NaturalLanguageRule

        with pytest.raises(ValueError) as exc_info:
            NaturalLanguageRule(rule_id="", rule_text="some rule")
        assert "rule_id" in str(exc_info.value)

    @pytest.mark.unit
    def test_rule_raises_on_empty_rule_text(self) -> None:
        from src.control_reasoning.rule_interpreter import NaturalLanguageRule

        with pytest.raises(ValueError) as exc_info:
            NaturalLanguageRule(rule_id="rule_001", rule_text="")
        assert "rule_text" in str(exc_info.value)

    @pytest.mark.unit
    def test_rule_raises_on_invalid_priority(self) -> None:
        from src.control_reasoning.rule_interpreter import NaturalLanguageRule

        with pytest.raises(ValueError) as exc_info:
            NaturalLanguageRule(rule_id="r1", rule_text="text", priority=0)
        assert "priority" in str(exc_info.value)

    @pytest.mark.unit
    def test_rule_from_dict(self) -> None:
        from src.control_reasoning.rule_interpreter import NaturalLanguageRule

        data = {
            "rule_id": "rule_003",
            "rule_text": "If cold, turn on heater",
            "priority": 3,
            "enabled": True,
            "metadata": {"tags": ["heating"]},
        }
        rule = NaturalLanguageRule.from_dict(data)
        assert rule.rule_id == "rule_003"
        assert rule.priority == 3
        assert rule.metadata["tags"] == ["heating"]

    @pytest.mark.unit
    def test_rule_to_dict(self) -> None:
        from src.control_reasoning.rule_interpreter import NaturalLanguageRule

        rule = NaturalLanguageRule(
            rule_id="rule_004",
            rule_text="If motion detected, turn on lights",
            priority=1,
            metadata={"tags": ["security"]},
        )
        result = rule.to_dict()
        assert result["rule_id"] == "rule_004"
        assert result["rule_text"] == "If motion detected, turn on lights"
        assert result["priority"] == 1

    @pytest.mark.unit
    def test_rule_record_trigger(self) -> None:
        from src.control_reasoning.rule_interpreter import NaturalLanguageRule

        rule = NaturalLanguageRule(rule_id="r1", rule_text="text")
        assert rule.trigger_count == 0
        assert rule.last_triggered is None

        rule.record_trigger()
        assert rule.trigger_count == 1
        assert rule.last_triggered is not None

        rule.record_trigger()
        assert rule.trigger_count == 2


class TestRuleMatch:
    @pytest.mark.unit
    def test_rule_match_attributes(self) -> None:
        from src.control_reasoning.rule_interpreter import (
            NaturalLanguageRule,
            RuleMatch,
        )

        rule = NaturalLanguageRule(rule_id="r1", rule_text="text")
        match = RuleMatch(
            rule=rule,
            matched_terms=("hot", "temperature"),
            confidence=0.75,
        )
        assert match.rule is rule
        assert match.matched_terms == ("hot", "temperature")
        assert match.confidence == 0.75
        assert match.rule_id == "r1"


class TestRuleInterpreterInit:
    @pytest.mark.unit
    def test_interpreter_empty_init(self) -> None:
        from src.control_reasoning.rule_interpreter import RuleInterpreter

        interpreter = RuleInterpreter()
        assert len(interpreter) == 0

    @pytest.mark.unit
    def test_interpreter_init_with_rules(self) -> None:
        from src.control_reasoning.rule_interpreter import (
            NaturalLanguageRule,
            RuleInterpreter,
        )

        rules = [
            NaturalLanguageRule(rule_id="r1", rule_text="Rule 1"),
            NaturalLanguageRule(rule_id="r2", rule_text="Rule 2"),
        ]
        interpreter = RuleInterpreter(rules)
        assert len(interpreter) == 2

    @pytest.mark.unit
    def test_interpreter_from_json_file(self, tmp_path: Path) -> None:
        from src.control_reasoning.rule_interpreter import RuleInterpreter

        rules_data = {
            "rules": [
                {"rule_id": "r1", "rule_text": "Rule 1", "priority": 1},
                {"rule_id": "r2", "rule_text": "Rule 2", "priority": 2},
            ]
        }
        rules_file = tmp_path / "rules.json"
        rules_file.write_text(json.dumps(rules_data))

        interpreter = RuleInterpreter.from_json_file(rules_file)
        assert len(interpreter) == 2
        assert "r1" in interpreter
        assert "r2" in interpreter


class TestRuleInterpreterManagement:
    @pytest.mark.unit
    def test_add_rule(self) -> None:
        from src.control_reasoning.rule_interpreter import (
            NaturalLanguageRule,
            RuleInterpreter,
        )

        interpreter = RuleInterpreter()
        rule = NaturalLanguageRule(rule_id="r1", rule_text="text")
        interpreter.add_rule(rule)
        assert "r1" in interpreter
        assert len(interpreter) == 1

    @pytest.mark.unit
    def test_add_duplicate_rule_raises(self) -> None:
        from src.control_reasoning.rule_interpreter import (
            NaturalLanguageRule,
            RuleInterpreter,
        )

        interpreter = RuleInterpreter()
        rule = NaturalLanguageRule(rule_id="r1", rule_text="text")
        interpreter.add_rule(rule)

        with pytest.raises(ValueError) as exc_info:
            interpreter.add_rule(rule)
        assert "already exists" in str(exc_info.value)

    @pytest.mark.unit
    def test_remove_rule(self) -> None:
        from src.control_reasoning.rule_interpreter import (
            NaturalLanguageRule,
            RuleInterpreter,
        )

        interpreter = RuleInterpreter()
        rule = NaturalLanguageRule(rule_id="r1", rule_text="text")
        interpreter.add_rule(rule)

        result = interpreter.remove_rule("r1")
        assert result is True
        assert "r1" not in interpreter

    @pytest.mark.unit
    def test_remove_nonexistent_rule(self) -> None:
        from src.control_reasoning.rule_interpreter import RuleInterpreter

        interpreter = RuleInterpreter()
        result = interpreter.remove_rule("nonexistent")
        assert result is False

    @pytest.mark.unit
    def test_get_rule(self) -> None:
        from src.control_reasoning.rule_interpreter import (
            NaturalLanguageRule,
            RuleInterpreter,
        )

        interpreter = RuleInterpreter()
        rule = NaturalLanguageRule(rule_id="r1", rule_text="text")
        interpreter.add_rule(rule)

        retrieved = interpreter.get_rule("r1")
        assert retrieved is rule

    @pytest.mark.unit
    def test_get_nonexistent_rule(self) -> None:
        from src.control_reasoning.rule_interpreter import RuleInterpreter

        interpreter = RuleInterpreter()
        result = interpreter.get_rule("nonexistent")
        assert result is None

    @pytest.mark.unit
    def test_enable_rule(self) -> None:
        from src.control_reasoning.rule_interpreter import (
            NaturalLanguageRule,
            RuleInterpreter,
        )

        interpreter = RuleInterpreter()
        rule = NaturalLanguageRule(rule_id="r1", rule_text="text", enabled=False)
        interpreter.add_rule(rule)

        result = interpreter.enable_rule("r1")
        assert result is True
        assert interpreter.get_rule("r1").enabled is True  # type: ignore[union-attr]

    @pytest.mark.unit
    def test_disable_rule(self) -> None:
        from src.control_reasoning.rule_interpreter import (
            NaturalLanguageRule,
            RuleInterpreter,
        )

        interpreter = RuleInterpreter()
        rule = NaturalLanguageRule(rule_id="r1", rule_text="text", enabled=True)
        interpreter.add_rule(rule)

        result = interpreter.disable_rule("r1")
        assert result is True
        assert interpreter.get_rule("r1").enabled is False  # type: ignore[union-attr]

    @pytest.mark.unit
    def test_enabled_rules_property(self) -> None:
        from src.control_reasoning.rule_interpreter import (
            NaturalLanguageRule,
            RuleInterpreter,
        )

        interpreter = RuleInterpreter(
            [
                NaturalLanguageRule(rule_id="r1", rule_text="t1", enabled=True),
                NaturalLanguageRule(rule_id="r2", rule_text="t2", enabled=False),
                NaturalLanguageRule(rule_id="r3", rule_text="t3", enabled=True),
            ]
        )

        enabled = interpreter.enabled_rules
        assert len(enabled) == 2
        assert all(r.enabled for r in enabled)


class TestRuleInterpreterFindCandidates:
    @pytest.mark.unit
    def test_find_candidates_with_matching_term(self) -> None:
        from src.control_reasoning.rule_interpreter import (
            NaturalLanguageRule,
            RuleInterpreter,
        )

        interpreter = RuleInterpreter(
            [
                NaturalLanguageRule(
                    rule_id="r1",
                    rule_text="If temperature is hot, turn on AC",
                ),
            ]
        )
        desc = _create_linguistic_description(
            sensor_type="temperature",
            terms=[("hot", 0.85)],
        )

        candidates = interpreter.find_candidate_rules([desc])
        assert len(candidates) == 1
        assert candidates[0].rule_id == "r1"
        assert "hot" in candidates[0].matched_terms or "temperature" in candidates[0].matched_terms

    @pytest.mark.unit
    def test_find_candidates_no_match(self) -> None:
        from src.control_reasoning.rule_interpreter import (
            NaturalLanguageRule,
            RuleInterpreter,
        )

        interpreter = RuleInterpreter(
            [
                NaturalLanguageRule(
                    rule_id="r1",
                    rule_text="If motion detected, turn on lights",
                ),
            ]
        )
        desc = _create_linguistic_description(
            sensor_type="temperature",
            terms=[("hot", 0.85)],
        )

        candidates = interpreter.find_candidate_rules([desc])
        assert len(candidates) == 0

    @pytest.mark.unit
    def test_find_candidates_skips_disabled_rules(self) -> None:
        from src.control_reasoning.rule_interpreter import (
            NaturalLanguageRule,
            RuleInterpreter,
        )

        interpreter = RuleInterpreter(
            [
                NaturalLanguageRule(
                    rule_id="r1",
                    rule_text="If temperature is hot, turn on AC",
                    enabled=False,
                ),
            ]
        )
        desc = _create_linguistic_description(
            sensor_type="temperature",
            terms=[("hot", 0.85)],
        )

        candidates = interpreter.find_candidate_rules([desc])
        assert len(candidates) == 0

    @pytest.mark.unit
    def test_find_candidates_sorted_by_priority(self) -> None:
        from src.control_reasoning.rule_interpreter import (
            NaturalLanguageRule,
            RuleInterpreter,
        )

        interpreter = RuleInterpreter(
            [
                NaturalLanguageRule(
                    rule_id="r1",
                    rule_text="If temperature is hot, do A",
                    priority=3,
                ),
                NaturalLanguageRule(
                    rule_id="r2",
                    rule_text="If temperature is hot, do B",
                    priority=1,
                ),
                NaturalLanguageRule(
                    rule_id="r3",
                    rule_text="If temperature is hot, do C",
                    priority=2,
                ),
            ]
        )
        desc = _create_linguistic_description(
            sensor_type="temperature",
            terms=[("hot", 0.85)],
        )

        candidates = interpreter.find_candidate_rules([desc])
        assert len(candidates) == 3
        assert candidates[0].rule_id == "r2"
        assert candidates[1].rule_id == "r3"
        assert candidates[2].rule_id == "r1"

    @pytest.mark.unit
    def test_find_candidates_empty_descriptions(self) -> None:
        from src.control_reasoning.rule_interpreter import (
            NaturalLanguageRule,
            RuleInterpreter,
        )

        interpreter = RuleInterpreter(
            [
                NaturalLanguageRule(rule_id="r1", rule_text="some rule"),
            ]
        )

        candidates = interpreter.find_candidate_rules([])
        assert candidates == []

    @pytest.mark.unit
    def test_find_candidates_multiple_sensors(self) -> None:
        from src.control_reasoning.rule_interpreter import (
            NaturalLanguageRule,
            RuleInterpreter,
        )

        interpreter = RuleInterpreter(
            [
                NaturalLanguageRule(
                    rule_id="r1",
                    rule_text="If temperature is hot and humidity is high, turn on AC",
                ),
            ]
        )
        temp_desc = _create_linguistic_description(
            sensor_type="temperature",
            terms=[("hot", 0.85)],
        )
        hum_desc = _create_linguistic_description(
            sensor_id="hum_001",
            sensor_type="humidity",
            terms=[("high", 0.70)],
        )

        candidates = interpreter.find_candidate_rules([temp_desc, hum_desc])
        assert len(candidates) == 1
        assert len(candidates[0].matched_terms) >= 2


class TestRuleInterpreterQueries:
    @pytest.mark.unit
    def test_get_rules_by_priority(self) -> None:
        from src.control_reasoning.rule_interpreter import (
            NaturalLanguageRule,
            RuleInterpreter,
        )

        interpreter = RuleInterpreter(
            [
                NaturalLanguageRule(rule_id="r1", rule_text="t1", priority=3),
                NaturalLanguageRule(rule_id="r2", rule_text="t2", priority=1),
                NaturalLanguageRule(rule_id="r3", rule_text="t3", priority=2),
            ]
        )

        sorted_rules = interpreter.get_rules_by_priority()
        assert sorted_rules[0].priority == 1
        assert sorted_rules[1].priority == 2
        assert sorted_rules[2].priority == 3

    @pytest.mark.unit
    def test_get_rules_by_tag(self) -> None:
        from src.control_reasoning.rule_interpreter import (
            NaturalLanguageRule,
            RuleInterpreter,
        )

        interpreter = RuleInterpreter(
            [
                NaturalLanguageRule(
                    rule_id="r1",
                    rule_text="t1",
                    metadata={"tags": ["climate", "cooling"]},
                ),
                NaturalLanguageRule(
                    rule_id="r2",
                    rule_text="t2",
                    metadata={"tags": ["security"]},
                ),
                NaturalLanguageRule(
                    rule_id="r3",
                    rule_text="t3",
                    metadata={"tags": ["climate", "heating"]},
                ),
            ]
        )

        climate_rules = interpreter.get_rules_by_tag("climate")
        assert len(climate_rules) == 2

        security_rules = interpreter.get_rules_by_tag("security")
        assert len(security_rules) == 1

    @pytest.mark.unit
    def test_record_rule_trigger(self) -> None:
        from src.control_reasoning.rule_interpreter import (
            NaturalLanguageRule,
            RuleInterpreter,
        )

        interpreter = RuleInterpreter(
            [
                NaturalLanguageRule(rule_id="r1", rule_text="t1"),
            ]
        )

        result = interpreter.record_rule_trigger("r1")
        assert result is True
        assert interpreter.get_rule("r1").trigger_count == 1  # type: ignore[union-attr]

    @pytest.mark.unit
    def test_record_trigger_nonexistent_rule(self) -> None:
        from src.control_reasoning.rule_interpreter import RuleInterpreter

        interpreter = RuleInterpreter()
        result = interpreter.record_rule_trigger("nonexistent")
        assert result is False
