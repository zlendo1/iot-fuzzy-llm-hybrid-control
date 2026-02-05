from __future__ import annotations

import time
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

from src.common.logging import get_logger
from src.common.utils import load_json

if TYPE_CHECKING:
    from src.data_processing.linguistic_descriptor import LinguisticDescription

logger = get_logger(__name__)


@dataclass
class NaturalLanguageRule:
    rule_id: str
    rule_text: str
    priority: int = 1
    enabled: bool = True
    created_timestamp: str | None = None
    last_triggered: str | None = None
    trigger_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.rule_id:
            raise ValueError("rule_id cannot be empty")
        if not self.rule_text:
            raise ValueError("rule_text cannot be empty")
        if self.priority < 1:
            raise ValueError("priority must be >= 1")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> NaturalLanguageRule:
        return cls(
            rule_id=data["rule_id"],
            rule_text=data["rule_text"],
            priority=data.get("priority", 1),
            enabled=data.get("enabled", True),
            created_timestamp=data.get("created_timestamp"),
            last_triggered=data.get("last_triggered"),
            trigger_count=data.get("trigger_count", 0),
            metadata=data.get("metadata", {}),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "rule_text": self.rule_text,
            "priority": self.priority,
            "enabled": self.enabled,
            "created_timestamp": self.created_timestamp,
            "last_triggered": self.last_triggered,
            "trigger_count": self.trigger_count,
            "metadata": self.metadata,
        }

    def record_trigger(self) -> None:
        self.trigger_count += 1
        self.last_triggered = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


@dataclass(frozen=True)
class RuleMatch:
    rule: NaturalLanguageRule
    matched_terms: tuple[str, ...]
    confidence: float

    @property
    def rule_id(self) -> str:
        return self.rule.rule_id


class RuleInterpreter:
    def __init__(self, rules: Sequence[NaturalLanguageRule] | None = None) -> None:
        self._rules: dict[str, NaturalLanguageRule] = {}
        if rules:
            for rule in rules:
                self.add_rule(rule)

    @classmethod
    def from_json_file(cls, path: Path) -> RuleInterpreter:
        data = load_json(path)
        rules_data = data.get("rules", [])
        rules = [NaturalLanguageRule.from_dict(r) for r in rules_data]
        return cls(rules)

    @property
    def rules(self) -> list[NaturalLanguageRule]:
        return list(self._rules.values())

    @property
    def enabled_rules(self) -> list[NaturalLanguageRule]:
        return [r for r in self._rules.values() if r.enabled]

    def get_rule(self, rule_id: str) -> NaturalLanguageRule | None:
        return self._rules.get(rule_id)

    def add_rule(self, rule: NaturalLanguageRule) -> None:
        if rule.rule_id in self._rules:
            raise ValueError(f"Rule with id '{rule.rule_id}' already exists")
        self._rules[rule.rule_id] = rule
        logger.debug("Added rule", extra={"rule_id": rule.rule_id})

    def remove_rule(self, rule_id: str) -> bool:
        if rule_id in self._rules:
            del self._rules[rule_id]
            logger.debug("Removed rule", extra={"rule_id": rule_id})
            return True
        return False

    def enable_rule(self, rule_id: str) -> bool:
        rule = self._rules.get(rule_id)
        if rule:
            rule.enabled = True
            return True
        return False

    def disable_rule(self, rule_id: str) -> bool:
        rule = self._rules.get(rule_id)
        if rule:
            rule.enabled = False
            return True
        return False

    def find_candidate_rules(
        self,
        sensor_descriptions: Sequence[LinguisticDescription],
    ) -> list[RuleMatch]:
        if not sensor_descriptions:
            return []

        sensor_terms = self._extract_sensor_terms(sensor_descriptions)
        candidates: list[RuleMatch] = []

        for rule in self.enabled_rules:
            matched_terms = self._match_rule_terms(rule.rule_text, sensor_terms)
            if matched_terms:
                confidence = len(matched_terms) / max(len(sensor_terms), 1)
                candidates.append(
                    RuleMatch(
                        rule=rule,
                        matched_terms=tuple(matched_terms),
                        confidence=min(confidence, 1.0),
                    )
                )

        candidates.sort(key=lambda m: (m.rule.priority, -m.confidence))

        logger.debug(
            "Found candidate rules",
            extra={
                "total_rules": len(self.enabled_rules),
                "candidates": len(candidates),
            },
        )

        return candidates

    def _extract_sensor_terms(
        self,
        descriptions: Sequence[LinguisticDescription],
    ) -> set[str]:
        terms: set[str] = set()
        for desc in descriptions:
            terms.add(desc.sensor_type.lower())
            for tm in desc.terms:
                terms.add(tm.term.lower())
                combined = f"{desc.sensor_type} is {tm.term}".lower()
                terms.add(combined)
        return terms

    def _match_rule_terms(
        self,
        rule_text: str,
        sensor_terms: set[str],
    ) -> list[str]:
        rule_lower = rule_text.lower()
        matched = []
        for term in sensor_terms:
            if term in rule_lower:
                matched.append(term)
        return matched

    def get_rules_by_priority(self) -> list[NaturalLanguageRule]:
        return sorted(self.enabled_rules, key=lambda r: r.priority)

    def get_rules_by_tag(self, tag: str) -> list[NaturalLanguageRule]:
        return [
            r
            for r in self._rules.values()
            if tag in r.metadata.get("tags", [])
        ]

    def record_rule_trigger(self, rule_id: str) -> bool:
        rule = self._rules.get(rule_id)
        if rule:
            rule.record_trigger()
            logger.debug(
                "Recorded rule trigger",
                extra={
                    "rule_id": rule_id,
                    "trigger_count": rule.trigger_count,
                },
            )
            return True
        return False

    def __len__(self) -> int:
        return len(self._rules)

    def __contains__(self, rule_id: str) -> bool:
        return rule_id in self._rules
