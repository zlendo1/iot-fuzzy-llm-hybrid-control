from __future__ import annotations

from importlib import import_module
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from src.control_reasoning.rule_interpreter import NaturalLanguageRule
from src.interfaces.rpc.generated import common_pb2, rules_pb2


@pytest.fixture
def mock_orchestrator() -> MagicMock:
    orchestrator = MagicMock()
    orchestrator.rule_manager = MagicMock()
    orchestrator.rule_pipeline = MagicMock()
    orchestrator.fuzzy_pipeline = MagicMock()
    return orchestrator


@pytest.fixture
def context() -> MagicMock:
    return MagicMock()


def _rule(rule_id: str, text: str, enabled: bool = True) -> NaturalLanguageRule:
    return NaturalLanguageRule(
        rule_id=rule_id,
        rule_text=text,
        enabled=enabled,
        created_timestamp="2026-03-20T10:30:00Z",
        last_triggered="2026-03-20T11:00:00Z",
    )


def _rules_servicer_cls() -> type:
    module = import_module("src.interfaces.rpc.servicers.rules_servicer")
    return module.RulesServicer


class TestRulesServicer:
    def test_add_rule_creates_rule_via_rule_manager(
        self, mock_orchestrator: MagicMock, context: MagicMock
    ) -> None:
        RulesServicer = _rules_servicer_cls()

        created = _rule("rule_001", "If hot then cool", enabled=True)
        mock_orchestrator.rule_manager.add_rule.return_value = created

        servicer = RulesServicer(mock_orchestrator)
        request = rules_pb2.AddRuleRequest(text="If hot then cool", enabled=True)

        response = servicer.AddRule(request, context)

        assert isinstance(response, rules_pb2.AddRuleResponse)
        assert response.rule.id == "rule_001"
        assert response.rule.text == "If hot then cool"
        assert response.rule.enabled is True
        mock_orchestrator.rule_manager.add_rule.assert_called_once()
        context.abort.assert_not_called()

    def test_remove_rule_deletes_rule(
        self, mock_orchestrator: MagicMock, context: MagicMock
    ) -> None:
        RulesServicer = _rules_servicer_cls()

        mock_orchestrator.rule_manager.delete_rule.return_value = True
        servicer = RulesServicer(mock_orchestrator)

        response = servicer.RemoveRule(
            rules_pb2.RemoveRuleRequest(id="rule_001"), context
        )

        assert isinstance(response, rules_pb2.RemoveRuleResponse)
        assert response.success is True
        mock_orchestrator.rule_manager.delete_rule.assert_called_once_with("rule_001")

    def test_list_rules_applies_pagination(
        self, mock_orchestrator: MagicMock, context: MagicMock
    ) -> None:
        RulesServicer = _rules_servicer_cls()

        all_rules = [
            _rule("rule_001", "r1"),
            _rule("rule_002", "r2", enabled=False),
            _rule("rule_003", "r3"),
        ]
        mock_orchestrator.rule_manager.get_all_rules.return_value = all_rules
        servicer = RulesServicer(mock_orchestrator)

        request = rules_pb2.ListRulesRequest(
            pagination=common_pb2.PaginationRequest(limit=2, offset=1)
        )
        response = servicer.ListRules(request, context)

        assert isinstance(response, rules_pb2.ListRulesResponse)
        assert [r.id for r in response.rules] == ["rule_002", "rule_003"]
        assert response.pagination.total == 3
        assert response.pagination.has_more is False

    def test_list_rules_uses_default_limit_when_not_provided(
        self, mock_orchestrator: MagicMock, context: MagicMock
    ) -> None:
        RulesServicer = _rules_servicer_cls()

        all_rules = [_rule(f"rule_{i:03d}", f"rule-{i}") for i in range(150)]
        mock_orchestrator.rule_manager.get_all_rules.return_value = all_rules
        servicer = RulesServicer(mock_orchestrator)

        response = servicer.ListRules(rules_pb2.ListRulesRequest(), context)

        assert len(response.rules) == 100
        assert response.pagination.total == 150
        assert response.pagination.has_more is True

    def test_get_rule_returns_single_rule(
        self, mock_orchestrator: MagicMock, context: MagicMock
    ) -> None:
        RulesServicer = _rules_servicer_cls()

        mock_orchestrator.rule_manager.get_rule.return_value = _rule("rule_777", "rule")
        servicer = RulesServicer(mock_orchestrator)

        response = servicer.GetRule(rules_pb2.GetRuleRequest(id="rule_777"), context)

        assert isinstance(response, rules_pb2.GetRuleResponse)
        assert response.rule.id == "rule_777"

    def test_enable_rule_enables_and_returns_success(
        self, mock_orchestrator: MagicMock, context: MagicMock
    ) -> None:
        RulesServicer = _rules_servicer_cls()

        servicer = RulesServicer(mock_orchestrator)
        response = servicer.EnableRule(
            rules_pb2.EnableRuleRequest(id="rule_001"), context
        )

        assert isinstance(response, rules_pb2.EnableRuleResponse)
        assert response.success is True
        mock_orchestrator.rule_manager.enable_rule.assert_called_once_with("rule_001")

    def test_disable_rule_disables_and_returns_success(
        self, mock_orchestrator: MagicMock, context: MagicMock
    ) -> None:
        RulesServicer = _rules_servicer_cls()

        servicer = RulesServicer(mock_orchestrator)
        response = servicer.DisableRule(
            rules_pb2.DisableRuleRequest(id="rule_001"), context
        )

        assert isinstance(response, rules_pb2.DisableRuleResponse)
        assert response.success is True
        mock_orchestrator.rule_manager.disable_rule.assert_called_once_with("rule_001")

    def test_evaluate_rules_uses_current_fuzzy_state(
        self, mock_orchestrator: MagicMock, context: MagicMock
    ) -> None:
        RulesServicer = _rules_servicer_cls()

        state = {"temp": object()}
        mock_orchestrator.fuzzy_pipeline.get_current_state.return_value = state
        mock_orchestrator.rule_pipeline.process.return_value = SimpleNamespace(
            evaluations=[object(), object(), object()],
            validated_commands=[
                SimpleNamespace(device_id="ac_1", command_type="turn_on"),
                SimpleNamespace(device_id="fan_1", command_type="set_speed"),
            ],
        )
        servicer = RulesServicer(mock_orchestrator)

        response = servicer.EvaluateRules(rules_pb2.EvaluateRulesRequest(), context)

        mock_orchestrator.fuzzy_pipeline.get_current_state.assert_called_once_with()
        mock_orchestrator.rule_pipeline.process.assert_called_once_with(state)
        assert response.rules_evaluated == 3
        assert response.commands_generated == ["ac_1:turn_on", "fan_1:set_speed"]

    def test_all_rpc_methods_are_wrapped_with_grpc_error_handler(self) -> None:
        RulesServicer = _rules_servicer_cls()

        method_names = [
            "AddRule",
            "RemoveRule",
            "ListRules",
            "GetRule",
            "EnableRule",
            "DisableRule",
            "EvaluateRules",
        ]
        for method_name in method_names:
            method = getattr(RulesServicer, method_name)
            assert hasattr(method, "__wrapped__")
