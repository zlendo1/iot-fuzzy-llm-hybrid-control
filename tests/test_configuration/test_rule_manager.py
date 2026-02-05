import json
import threading
from pathlib import Path

import pytest


@pytest.fixture
def rules_dir(tmp_path: Path) -> Path:
    rules_path = tmp_path / "rules"
    rules_path.mkdir()
    return rules_path


@pytest.fixture
def rules_file(rules_dir: Path) -> Path:
    return rules_dir / "active_rules.json"


@pytest.fixture
def sample_rules_data() -> dict:
    return {
        "rules": [
            {
                "rule_id": "rule_001",
                "rule_text": "If temperature is hot, turn on AC",
                "priority": 1,
                "enabled": True,
                "created_timestamp": "2025-01-15T10:00:00Z",
                "trigger_count": 5,
                "metadata": {"tags": ["climate"]},
            },
            {
                "rule_id": "rule_002",
                "rule_text": "If motion is detected, turn on lights",
                "priority": 2,
                "enabled": False,
                "created_timestamp": "2025-01-16T10:00:00Z",
                "trigger_count": 0,
                "metadata": {},
            },
        ],
    }


@pytest.fixture
def populated_rules_file(rules_file: Path, sample_rules_data: dict) -> Path:
    rules_file.write_text(json.dumps(sample_rules_data))
    return rules_file


class TestRuleManagerInit:
    @pytest.mark.unit
    def test_init_with_empty_rules(self, rules_file: Path) -> None:
        from src.configuration.rule_manager import RuleManager

        manager = RuleManager(rules_file=rules_file)

        assert manager.rule_count == 0
        assert manager.rules_file == rules_file

    @pytest.mark.unit
    def test_init_loads_existing_rules(self, populated_rules_file: Path) -> None:
        from src.configuration.rule_manager import RuleManager

        manager = RuleManager(rules_file=populated_rules_file)

        assert manager.rule_count == 2

    @pytest.mark.unit
    def test_init_skips_invalid_rules(self, rules_file: Path) -> None:
        from src.configuration.rule_manager import RuleManager

        invalid_data = {
            "rules": [
                {"rule_id": "valid", "rule_text": "Valid rule"},
                {"rule_id": "", "rule_text": "Invalid - empty id"},
                {"rule_text": "Missing rule_id"},
            ],
        }
        rules_file.write_text(json.dumps(invalid_data))

        manager = RuleManager(rules_file=rules_file)

        assert manager.rule_count == 1


class TestAddRule:
    @pytest.mark.unit
    def test_add_rule_creates_rule(self, rules_file: Path) -> None:
        from src.configuration.rule_manager import RuleManager

        manager = RuleManager(rules_file=rules_file, auto_save=False)

        rule = manager.add_rule("rule_001", "If hot, turn on AC")

        assert rule.rule_id == "rule_001"
        assert rule.rule_text == "If hot, turn on AC"
        assert rule.enabled is True

    @pytest.mark.unit
    def test_add_rule_with_priority(self, rules_file: Path) -> None:
        from src.configuration.rule_manager import RuleManager

        manager = RuleManager(rules_file=rules_file, auto_save=False)

        rule = manager.add_rule("rule_001", "Rule text", priority=5)

        assert rule.priority == 5

    @pytest.mark.unit
    def test_add_rule_with_metadata(self, rules_file: Path) -> None:
        from src.configuration.rule_manager import RuleManager

        manager = RuleManager(rules_file=rules_file, auto_save=False)

        rule = manager.add_rule("rule_001", "Rule text", metadata={"tags": ["climate"]})

        assert rule.metadata == {"tags": ["climate"]}

    @pytest.mark.unit
    def test_add_rule_sets_timestamp(self, rules_file: Path) -> None:
        from src.configuration.rule_manager import RuleManager

        manager = RuleManager(rules_file=rules_file, auto_save=False)

        rule = manager.add_rule("rule_001", "Rule text")

        assert rule.created_timestamp is not None

    @pytest.mark.unit
    def test_add_rule_raises_on_duplicate(self, rules_file: Path) -> None:
        from src.common.exceptions import RuleError
        from src.configuration.rule_manager import RuleManager

        manager = RuleManager(rules_file=rules_file, auto_save=False)
        manager.add_rule("rule_001", "First rule")

        with pytest.raises(RuleError) as exc_info:
            manager.add_rule("rule_001", "Duplicate rule")

        assert "already exists" in str(exc_info.value)

    @pytest.mark.unit
    def test_add_rule_object(self, rules_file: Path) -> None:
        from src.configuration.rule_manager import RuleManager
        from src.control_reasoning.rule_interpreter import NaturalLanguageRule

        manager = RuleManager(rules_file=rules_file, auto_save=False)
        rule = NaturalLanguageRule(rule_id="rule_001", rule_text="Test rule")

        manager.add_rule_object(rule)

        assert manager.contains("rule_001")


class TestGetRule:
    @pytest.mark.unit
    def test_get_rule_returns_rule(self, populated_rules_file: Path) -> None:
        from src.configuration.rule_manager import RuleManager

        manager = RuleManager(rules_file=populated_rules_file)

        rule = manager.get_rule("rule_001")

        assert rule.rule_id == "rule_001"
        assert rule.rule_text == "If temperature is hot, turn on AC"

    @pytest.mark.unit
    def test_get_rule_raises_on_not_found(self, rules_file: Path) -> None:
        from src.common.exceptions import RuleError
        from src.configuration.rule_manager import RuleManager

        manager = RuleManager(rules_file=rules_file)

        with pytest.raises(RuleError) as exc_info:
            manager.get_rule("nonexistent")

        assert "not found" in str(exc_info.value)

    @pytest.mark.unit
    def test_get_rule_optional_returns_none(self, rules_file: Path) -> None:
        from src.configuration.rule_manager import RuleManager

        manager = RuleManager(rules_file=rules_file)

        result = manager.get_rule_optional("nonexistent")

        assert result is None


class TestUpdateRule:
    @pytest.mark.unit
    def test_update_rule_text(self, populated_rules_file: Path) -> None:
        from src.configuration.rule_manager import RuleManager

        manager = RuleManager(rules_file=populated_rules_file, auto_save=False)

        rule = manager.update_rule("rule_001", rule_text="Updated rule text")

        assert rule.rule_text == "Updated rule text"

    @pytest.mark.unit
    def test_update_rule_priority(self, populated_rules_file: Path) -> None:
        from src.configuration.rule_manager import RuleManager

        manager = RuleManager(rules_file=populated_rules_file, auto_save=False)

        rule = manager.update_rule("rule_001", priority=10)

        assert rule.priority == 10

    @pytest.mark.unit
    def test_update_rule_enabled(self, populated_rules_file: Path) -> None:
        from src.configuration.rule_manager import RuleManager

        manager = RuleManager(rules_file=populated_rules_file, auto_save=False)

        rule = manager.update_rule("rule_001", enabled=False)

        assert rule.enabled is False

    @pytest.mark.unit
    def test_update_rule_raises_on_not_found(self, rules_file: Path) -> None:
        from src.common.exceptions import RuleError
        from src.configuration.rule_manager import RuleManager

        manager = RuleManager(rules_file=rules_file)

        with pytest.raises(RuleError):
            manager.update_rule("nonexistent", rule_text="New text")

    @pytest.mark.unit
    def test_update_rule_invalid_priority(self, populated_rules_file: Path) -> None:
        from src.configuration.rule_manager import RuleManager

        manager = RuleManager(rules_file=populated_rules_file, auto_save=False)

        with pytest.raises(ValueError):
            manager.update_rule("rule_001", priority=0)


class TestDeleteRule:
    @pytest.mark.unit
    def test_delete_rule_removes_rule(self, populated_rules_file: Path) -> None:
        from src.configuration.rule_manager import RuleManager

        manager = RuleManager(rules_file=populated_rules_file, auto_save=False)

        result = manager.delete_rule("rule_001")

        assert result is True
        assert not manager.contains("rule_001")

    @pytest.mark.unit
    def test_delete_rule_returns_false_if_not_found(self, rules_file: Path) -> None:
        from src.configuration.rule_manager import RuleManager

        manager = RuleManager(rules_file=rules_file)

        result = manager.delete_rule("nonexistent")

        assert result is False


class TestEnableDisableRule:
    @pytest.mark.unit
    def test_enable_rule(self, populated_rules_file: Path) -> None:
        from src.configuration.rule_manager import RuleManager

        manager = RuleManager(rules_file=populated_rules_file, auto_save=False)

        manager.enable_rule("rule_002")

        rule = manager.get_rule("rule_002")
        assert rule.enabled is True

    @pytest.mark.unit
    def test_disable_rule(self, populated_rules_file: Path) -> None:
        from src.configuration.rule_manager import RuleManager

        manager = RuleManager(rules_file=populated_rules_file, auto_save=False)

        manager.disable_rule("rule_001")

        rule = manager.get_rule("rule_001")
        assert rule.enabled is False


class TestRecordTrigger:
    @pytest.mark.unit
    def test_record_trigger_increments_count(self, populated_rules_file: Path) -> None:
        from src.configuration.rule_manager import RuleManager

        manager = RuleManager(rules_file=populated_rules_file, auto_save=False)
        initial_count = manager.get_rule("rule_001").trigger_count

        manager.record_trigger("rule_001")

        assert manager.get_rule("rule_001").trigger_count == initial_count + 1

    @pytest.mark.unit
    def test_record_trigger_updates_last_triggered(
        self, populated_rules_file: Path
    ) -> None:
        from src.configuration.rule_manager import RuleManager

        manager = RuleManager(rules_file=populated_rules_file, auto_save=False)

        manager.record_trigger("rule_001")

        assert manager.get_rule("rule_001").last_triggered is not None


class TestListRules:
    @pytest.mark.unit
    def test_get_all_rules(self, populated_rules_file: Path) -> None:
        from src.configuration.rule_manager import RuleManager

        manager = RuleManager(rules_file=populated_rules_file)

        rules = manager.get_all_rules()

        assert len(rules) == 2

    @pytest.mark.unit
    def test_get_enabled_rules(self, populated_rules_file: Path) -> None:
        from src.configuration.rule_manager import RuleManager

        manager = RuleManager(rules_file=populated_rules_file)

        rules = manager.get_enabled_rules()

        assert len(rules) == 1
        assert all(r.enabled for r in rules)

    @pytest.mark.unit
    def test_get_rules_by_priority(self, populated_rules_file: Path) -> None:
        from src.configuration.rule_manager import RuleManager

        manager = RuleManager(rules_file=populated_rules_file)

        rules = manager.get_rules_by_priority(descending=True)

        assert rules[0].priority >= rules[1].priority

    @pytest.mark.unit
    def test_enabled_count(self, populated_rules_file: Path) -> None:
        from src.configuration.rule_manager import RuleManager

        manager = RuleManager(rules_file=populated_rules_file)

        assert manager.enabled_count == 1


class TestPersistence:
    @pytest.mark.unit
    def test_auto_save_on_add(self, rules_file: Path) -> None:
        from src.configuration.rule_manager import RuleManager

        manager = RuleManager(rules_file=rules_file, auto_save=True)

        manager.add_rule("rule_001", "Test rule")

        assert rules_file.exists()
        data = json.loads(rules_file.read_text())
        assert len(data["rules"]) == 1

    @pytest.mark.unit
    def test_auto_save_on_update(self, populated_rules_file: Path) -> None:
        from src.configuration.rule_manager import RuleManager

        manager = RuleManager(rules_file=populated_rules_file, auto_save=True)

        manager.update_rule("rule_001", rule_text="Updated text")

        data = json.loads(populated_rules_file.read_text())
        rule_data = next(r for r in data["rules"] if r["rule_id"] == "rule_001")
        assert rule_data["rule_text"] == "Updated text"

    @pytest.mark.unit
    def test_auto_save_on_delete(self, populated_rules_file: Path) -> None:
        from src.configuration.rule_manager import RuleManager

        manager = RuleManager(rules_file=populated_rules_file, auto_save=True)

        manager.delete_rule("rule_001")

        data = json.loads(populated_rules_file.read_text())
        assert len(data["rules"]) == 1

    @pytest.mark.unit
    def test_manual_save(self, rules_file: Path) -> None:
        from src.configuration.rule_manager import RuleManager

        manager = RuleManager(rules_file=rules_file, auto_save=False)
        manager.add_rule("rule_001", "Test rule")

        assert not rules_file.exists()

        manager.save()

        assert rules_file.exists()

    @pytest.mark.unit
    def test_reload(self, populated_rules_file: Path, sample_rules_data: dict) -> None:
        from src.configuration.rule_manager import RuleManager

        manager = RuleManager(rules_file=populated_rules_file, auto_save=False)
        manager.add_rule("rule_003", "New rule")
        assert manager.rule_count == 3

        populated_rules_file.write_text(json.dumps(sample_rules_data))

        manager.reload()

        assert manager.rule_count == 2


class TestExportImport:
    @pytest.mark.unit
    def test_export_rules(self, populated_rules_file: Path, tmp_path: Path) -> None:
        from src.configuration.rule_manager import RuleManager

        manager = RuleManager(rules_file=populated_rules_file)
        export_file = tmp_path / "export" / "rules.json"

        count = manager.export_rules(export_file)

        assert count == 2
        assert export_file.exists()
        data = json.loads(export_file.read_text())
        assert len(data["rules"]) == 2

    @pytest.mark.unit
    def test_import_rules(self, rules_file: Path, tmp_path: Path) -> None:
        from src.configuration.rule_manager import RuleManager

        import_data = {
            "rules": [
                {"rule_id": "imported_1", "rule_text": "Imported rule 1"},
                {"rule_id": "imported_2", "rule_text": "Imported rule 2"},
            ],
        }
        import_file = tmp_path / "import.json"
        import_file.write_text(json.dumps(import_data))

        manager = RuleManager(rules_file=rules_file, auto_save=False)

        count = manager.import_rules(import_file)

        assert count == 2
        assert manager.rule_count == 2

    @pytest.mark.unit
    def test_import_rules_with_overwrite(
        self, populated_rules_file: Path, tmp_path: Path
    ) -> None:
        from src.configuration.rule_manager import RuleManager

        import_data = {
            "rules": [
                {"rule_id": "rule_001", "rule_text": "Overwritten rule"},
            ],
        }
        import_file = tmp_path / "import.json"
        import_file.write_text(json.dumps(import_data))

        manager = RuleManager(rules_file=populated_rules_file, auto_save=False)

        count = manager.import_rules(import_file, overwrite=True)

        assert count == 1
        assert manager.get_rule("rule_001").rule_text == "Overwritten rule"

    @pytest.mark.unit
    def test_import_rules_without_overwrite(
        self, populated_rules_file: Path, tmp_path: Path
    ) -> None:
        from src.configuration.rule_manager import RuleManager

        import_data = {
            "rules": [
                {"rule_id": "rule_001", "rule_text": "Should not overwrite"},
            ],
        }
        import_file = tmp_path / "import.json"
        import_file.write_text(json.dumps(import_data))

        manager = RuleManager(rules_file=populated_rules_file, auto_save=False)
        original_text = manager.get_rule("rule_001").rule_text

        count = manager.import_rules(import_file, overwrite=False)

        assert count == 0
        assert manager.get_rule("rule_001").rule_text == original_text

    @pytest.mark.unit
    def test_import_rules_file_not_found(self, rules_file: Path) -> None:
        from src.common.exceptions import ConfigurationError
        from src.configuration.rule_manager import RuleManager

        manager = RuleManager(rules_file=rules_file)

        with pytest.raises(ConfigurationError):
            manager.import_rules("nonexistent.json")


class TestClear:
    @pytest.mark.unit
    def test_clear_removes_all_rules(self, populated_rules_file: Path) -> None:
        from src.configuration.rule_manager import RuleManager

        manager = RuleManager(rules_file=populated_rules_file, auto_save=False)

        count = manager.clear()

        assert count == 2
        assert manager.rule_count == 0


class TestContains:
    @pytest.mark.unit
    def test_contains_returns_true(self, populated_rules_file: Path) -> None:
        from src.configuration.rule_manager import RuleManager

        manager = RuleManager(rules_file=populated_rules_file)

        assert manager.contains("rule_001") is True

    @pytest.mark.unit
    def test_contains_returns_false(self, populated_rules_file: Path) -> None:
        from src.configuration.rule_manager import RuleManager

        manager = RuleManager(rules_file=populated_rules_file)

        assert manager.contains("nonexistent") is False


class TestThreadSafety:
    @pytest.mark.unit
    def test_concurrent_add_rules(self, rules_file: Path) -> None:
        from src.configuration.rule_manager import RuleManager

        manager = RuleManager(rules_file=rules_file, auto_save=False)
        errors: list[Exception] = []

        def add_rule(i: int) -> None:
            try:
                manager.add_rule(f"rule_{i:03d}", f"Rule text {i}")
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=add_rule, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert manager.rule_count == 10

    @pytest.mark.unit
    def test_concurrent_read_write(self, populated_rules_file: Path) -> None:
        from src.configuration.rule_manager import RuleManager

        manager = RuleManager(rules_file=populated_rules_file, auto_save=False)
        errors: list[Exception] = []
        results: list[int] = []

        def read_rules() -> None:
            try:
                rules = manager.get_all_rules()
                results.append(len(rules))
            except Exception as e:
                errors.append(e)

        def add_rule(i: int) -> None:
            try:
                manager.add_rule(f"new_rule_{i}", f"New rule {i}")
            except Exception as e:
                errors.append(e)

        threads = []
        for i in range(5):
            threads.append(threading.Thread(target=read_rules))
            threads.append(threading.Thread(target=add_rule, args=(i,)))

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert manager.rule_count == 7
