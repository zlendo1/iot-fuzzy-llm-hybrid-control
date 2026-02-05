"""RuleManager - Persistent storage and CRUD operations for natural language rules."""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.common.exceptions import ConfigurationError, RuleError
from src.common.logging import get_logger
from src.common.utils import ensure_directory, format_timestamp, load_json, save_json
from src.control_reasoning.rule_interpreter import NaturalLanguageRule

logger = get_logger(__name__)


@dataclass
class RuleManager:
    rules_file: Path = field(default_factory=lambda: Path("rules/active_rules.json"))
    auto_save: bool = True

    _rules: dict[str, NaturalLanguageRule] = field(default_factory=dict, repr=False)
    _lock: threading.RLock = field(default_factory=threading.RLock, repr=False)
    _dirty: bool = field(default=False, init=False, repr=False)

    def __post_init__(self) -> None:
        self.rules_file = Path(self.rules_file)
        self._load_rules()
        logger.info(
            "RuleManager initialized",
            extra={"rules_file": str(self.rules_file), "rule_count": len(self._rules)},
        )

    def _load_rules(self) -> None:
        if not self.rules_file.exists():
            logger.debug(
                "Rules file does not exist, starting with empty ruleset",
                extra={"rules_file": str(self.rules_file)},
            )
            return

        try:
            data = load_json(self.rules_file)
            rules_list = data.get("rules", [])
            for rule_data in rules_list:
                try:
                    rule = NaturalLanguageRule.from_dict(rule_data)
                    self._rules[rule.rule_id] = rule
                except (KeyError, ValueError) as e:
                    logger.warning(
                        "Skipping invalid rule",
                        extra={"error": str(e), "rule_data": rule_data},
                    )
        except Exception as e:
            raise ConfigurationError(
                f"Failed to load rules from {self.rules_file}: {e}"
            ) from e

    def _save_rules(self) -> None:
        if not self._dirty:
            return

        ensure_directory(self.rules_file.parent)
        rules_list = [rule.to_dict() for rule in self._rules.values()]
        data = {"rules": rules_list}
        save_json(self.rules_file, data)
        self._dirty = False
        logger.debug(
            "Rules saved",
            extra={"rules_file": str(self.rules_file), "rule_count": len(rules_list)},
        )

    def add_rule(
        self,
        rule_id: str,
        rule_text: str,
        priority: int = 1,
        enabled: bool = True,
        metadata: dict[str, Any] | None = None,
    ) -> NaturalLanguageRule:
        with self._lock:
            if rule_id in self._rules:
                raise RuleError(f"Rule with id '{rule_id}' already exists")

            rule = NaturalLanguageRule(
                rule_id=rule_id,
                rule_text=rule_text,
                priority=priority,
                enabled=enabled,
                created_timestamp=format_timestamp(),
                metadata=metadata or {},
            )

            self._rules[rule_id] = rule
            self._dirty = True

            if self.auto_save:
                self._save_rules()

            logger.info("Rule added", extra={"rule_id": rule_id})
            return rule

    def add_rule_object(self, rule: NaturalLanguageRule) -> None:
        with self._lock:
            if rule.rule_id in self._rules:
                raise RuleError(f"Rule with id '{rule.rule_id}' already exists")

            if rule.created_timestamp is None:
                rule.created_timestamp = format_timestamp()

            self._rules[rule.rule_id] = rule
            self._dirty = True

            if self.auto_save:
                self._save_rules()

            logger.info("Rule added", extra={"rule_id": rule.rule_id})

    def get_rule(self, rule_id: str) -> NaturalLanguageRule:
        with self._lock:
            if rule_id not in self._rules:
                raise RuleError(f"Rule with id '{rule_id}' not found")
            return self._rules[rule_id]

    def get_rule_optional(self, rule_id: str) -> NaturalLanguageRule | None:
        with self._lock:
            return self._rules.get(rule_id)

    def update_rule(
        self,
        rule_id: str,
        rule_text: str | None = None,
        priority: int | None = None,
        enabled: bool | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> NaturalLanguageRule:
        with self._lock:
            if rule_id not in self._rules:
                raise RuleError(f"Rule with id '{rule_id}' not found")

            rule = self._rules[rule_id]

            if rule_text is not None:
                rule.rule_text = rule_text
            if priority is not None:
                if priority < 1:
                    raise ValueError("priority must be >= 1")
                rule.priority = priority
            if enabled is not None:
                rule.enabled = enabled
            if metadata is not None:
                rule.metadata = metadata

            self._dirty = True

            if self.auto_save:
                self._save_rules()

            logger.info("Rule updated", extra={"rule_id": rule_id})
            return rule

    def delete_rule(self, rule_id: str) -> bool:
        with self._lock:
            if rule_id not in self._rules:
                return False

            del self._rules[rule_id]
            self._dirty = True

            if self.auto_save:
                self._save_rules()

            logger.info("Rule deleted", extra={"rule_id": rule_id})
            return True

    def enable_rule(self, rule_id: str) -> None:
        self.update_rule(rule_id, enabled=True)

    def disable_rule(self, rule_id: str) -> None:
        self.update_rule(rule_id, enabled=False)

    def record_trigger(self, rule_id: str) -> None:
        with self._lock:
            if rule_id not in self._rules:
                raise RuleError(f"Rule with id '{rule_id}' not found")

            self._rules[rule_id].record_trigger()
            self._dirty = True

            if self.auto_save:
                self._save_rules()

    def get_all_rules(self) -> list[NaturalLanguageRule]:
        with self._lock:
            return list(self._rules.values())

    def get_enabled_rules(self) -> list[NaturalLanguageRule]:
        with self._lock:
            return [r for r in self._rules.values() if r.enabled]

    def get_rules_by_priority(self, descending: bool = True) -> list[NaturalLanguageRule]:
        with self._lock:
            return sorted(
                self._rules.values(),
                key=lambda r: r.priority,
                reverse=descending,
            )

    @property
    def rule_count(self) -> int:
        return len(self._rules)

    @property
    def enabled_count(self) -> int:
        return sum(1 for r in self._rules.values() if r.enabled)

    def contains(self, rule_id: str) -> bool:
        return rule_id in self._rules

    def export_rules(self, file_path: Path | str) -> int:
        with self._lock:
            file_path = Path(file_path)
            ensure_directory(file_path.parent)
            rules_list = [rule.to_dict() for rule in self._rules.values()]
            data = {"rules": rules_list}
            save_json(file_path, data)
            logger.info(
                "Rules exported",
                extra={"file_path": str(file_path), "rule_count": len(rules_list)},
            )
            return len(rules_list)

    def import_rules(
        self,
        file_path: Path | str,
        overwrite: bool = False,
    ) -> int:
        file_path = Path(file_path)
        if not file_path.exists():
            raise ConfigurationError(f"Import file not found: {file_path}")

        try:
            data = load_json(file_path)
        except Exception as e:
            raise ConfigurationError(f"Failed to read import file: {e}") from e

        rules_list = data.get("rules", [])
        imported = 0

        with self._lock:
            for rule_data in rules_list:
                try:
                    rule = NaturalLanguageRule.from_dict(rule_data)
                    if rule.rule_id in self._rules:
                        if overwrite:
                            self._rules[rule.rule_id] = rule
                            imported += 1
                    else:
                        self._rules[rule.rule_id] = rule
                        imported += 1
                except (KeyError, ValueError) as e:
                    logger.warning(
                        "Skipping invalid rule during import",
                        extra={"error": str(e)},
                    )

            if imported > 0:
                self._dirty = True
                if self.auto_save:
                    self._save_rules()

            logger.info(
                "Rules imported",
                extra={"file_path": str(file_path), "imported_count": imported},
            )
            return imported

    def clear(self) -> int:
        with self._lock:
            count = len(self._rules)
            self._rules.clear()
            self._dirty = True

            if self.auto_save:
                self._save_rules()

            logger.info("All rules cleared", extra={"cleared_count": count})
            return count

    def save(self) -> None:
        with self._lock:
            self._dirty = True
            self._save_rules()

    def reload(self) -> None:
        with self._lock:
            self._rules.clear()
            self._dirty = False
            self._load_rules()
            logger.info(
                "Rules reloaded",
                extra={"rule_count": len(self._rules)},
            )
