from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from google.protobuf.timestamp_pb2 import Timestamp

from src.common.logging import get_logger
from src.common.utils import generate_id
from src.interfaces.rpc.error_mapping import handle_grpc_errors
from src.interfaces.rpc.generated import common_pb2, rules_pb2, rules_pb2_grpc

if TYPE_CHECKING:
    from src.configuration.system_orchestrator import SystemOrchestrator
    from src.control_reasoning.rule_interpreter import NaturalLanguageRule

logger = get_logger(__name__)


def _parse_iso_timestamp(value: str | None) -> Timestamp | None:
    if not value:
        return None

    normalized = value.replace("Z", "+00:00")
    dt = datetime.fromisoformat(normalized)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    ts = Timestamp()
    ts.FromDatetime(dt.astimezone(timezone.utc))
    return ts


def _rule_to_proto(rule: NaturalLanguageRule) -> rules_pb2.Rule:
    pb_rule = rules_pb2.Rule(
        id=rule.rule_id,
        text=rule.rule_text,
        enabled=rule.enabled,
    )

    created_ts = _parse_iso_timestamp(rule.created_timestamp)
    if created_ts is not None:
        pb_rule.created_at.CopyFrom(created_ts)

    updated_ts = _parse_iso_timestamp(rule.last_triggered)
    if updated_ts is not None:
        pb_rule.updated_at.CopyFrom(updated_ts)

    return pb_rule


class RulesServicer(rules_pb2_grpc.RulesServiceServicer):
    def __init__(self, orchestrator: SystemOrchestrator) -> None:
        self._orchestrator = orchestrator

    @handle_grpc_errors
    def AddRule(
        self,
        request: rules_pb2.AddRuleRequest,
        context: object,
    ) -> rules_pb2.AddRuleResponse:
        rule_manager = self._orchestrator.rule_manager
        if rule_manager is None:
            raise RuntimeError("RuleManager is not initialized")

        rule_id = generate_id("rule")
        rule = rule_manager.add_rule(
            rule_id=rule_id,
            rule_text=request.text,
            enabled=request.enabled,
        )
        logger.info("Rule created via gRPC", extra={"rule_id": rule.rule_id})
        return rules_pb2.AddRuleResponse(rule=_rule_to_proto(rule))

    @handle_grpc_errors
    def RemoveRule(
        self,
        request: rules_pb2.RemoveRuleRequest,
        context: object,
    ) -> rules_pb2.RemoveRuleResponse:
        rule_manager = self._orchestrator.rule_manager
        if rule_manager is None:
            raise RuntimeError("RuleManager is not initialized")

        success = rule_manager.delete_rule(request.id)
        return rules_pb2.RemoveRuleResponse(success=success)

    @handle_grpc_errors
    def ListRules(
        self,
        request: rules_pb2.ListRulesRequest,
        context: object,
    ) -> rules_pb2.ListRulesResponse:
        rule_manager = self._orchestrator.rule_manager
        if rule_manager is None:
            raise RuntimeError("RuleManager is not initialized")

        rules = rule_manager.get_all_rules()
        total = len(rules)

        offset = max(0, request.pagination.offset)
        limit = request.pagination.limit if request.pagination.limit > 0 else 100
        paged_rules = rules[offset : offset + limit]

        has_more = (offset + len(paged_rules)) < total
        return rules_pb2.ListRulesResponse(
            rules=[_rule_to_proto(rule) for rule in paged_rules],
            pagination=common_pb2.PaginationResponse(total=total, has_more=has_more),
        )

    @handle_grpc_errors
    def GetRule(
        self,
        request: rules_pb2.GetRuleRequest,
        context: object,
    ) -> rules_pb2.GetRuleResponse:
        rule_manager = self._orchestrator.rule_manager
        if rule_manager is None:
            raise RuntimeError("RuleManager is not initialized")

        rule = rule_manager.get_rule(request.id)
        return rules_pb2.GetRuleResponse(rule=_rule_to_proto(rule))

    @handle_grpc_errors
    def EnableRule(
        self,
        request: rules_pb2.EnableRuleRequest,
        context: object,
    ) -> rules_pb2.EnableRuleResponse:
        rule_manager = self._orchestrator.rule_manager
        if rule_manager is None:
            raise RuntimeError("RuleManager is not initialized")

        rule_manager.enable_rule(request.id)
        return rules_pb2.EnableRuleResponse(success=True)

    @handle_grpc_errors
    def DisableRule(
        self,
        request: rules_pb2.DisableRuleRequest,
        context: object,
    ) -> rules_pb2.DisableRuleResponse:
        rule_manager = self._orchestrator.rule_manager
        if rule_manager is None:
            raise RuntimeError("RuleManager is not initialized")

        rule_manager.disable_rule(request.id)
        return rules_pb2.DisableRuleResponse(success=True)

    @handle_grpc_errors
    def EvaluateRules(
        self,
        request: rules_pb2.EvaluateRulesRequest,
        context: object,
    ) -> rules_pb2.EvaluateRulesResponse:
        fuzzy_pipeline = self._orchestrator.fuzzy_pipeline
        rule_pipeline = self._orchestrator.rule_pipeline
        if fuzzy_pipeline is None or rule_pipeline is None:
            raise RuntimeError("Pipelines are not initialized")

        current_state = fuzzy_pipeline.get_current_state()
        result = rule_pipeline.process(current_state)

        command_summaries = [
            f"{command.device_id}:{command.command_type}"
            for command in result.validated_commands
        ]
        return rules_pb2.EvaluateRulesResponse(
            commands_generated=command_summaries,
            rules_evaluated=len(result.evaluations),
        )
