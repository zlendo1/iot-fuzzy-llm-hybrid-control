from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, Mock

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


def _create_rule(
    rule_id: str = "rule_001",
    rule_text: str = "If temperature is hot, turn on AC",
    priority: int = 1,
    enabled: bool = True,
) -> Any:
    from src.control_reasoning.rule_interpreter import NaturalLanguageRule

    return NaturalLanguageRule(
        rule_id=rule_id,
        rule_text=rule_text,
        priority=priority,
        enabled=enabled,
    )


def _create_command(
    command_id: str = "cmd_001",
    device_id: str = "actuator_001",
    command_type: str = "turn_on",
    parameters: dict[str, Any] | None = None,
    rule_id: str | None = None,
    created_at: float = 1000.0,
) -> Any:
    from src.control_reasoning.command_generator import DeviceCommand

    return DeviceCommand(
        command_id=command_id,
        device_id=device_id,
        command_type=command_type,
        parameters=parameters or {},
        rule_id=rule_id,
        created_at=created_at,
    )


class TestControlReasoningLayerInterface:
    @pytest.mark.unit
    def test_interface_is_abstract(self) -> None:
        from src.control_reasoning.rule_pipeline import ControlReasoningLayerInterface

        with pytest.raises(TypeError):
            ControlReasoningLayerInterface()  # type: ignore[abstract]

    @pytest.mark.unit
    def test_interface_has_required_methods(self) -> None:
        from src.control_reasoning.rule_pipeline import ControlReasoningLayerInterface

        assert hasattr(ControlReasoningLayerInterface, "evaluate_rules")
        assert hasattr(ControlReasoningLayerInterface, "add_rule")
        assert hasattr(ControlReasoningLayerInterface, "remove_rule")
        assert hasattr(ControlReasoningLayerInterface, "get_rules")


class TestEvaluationResult:
    @pytest.mark.unit
    def test_evaluation_result_creation(self) -> None:
        from src.control_reasoning.response_parser import ParsedResponse, ResponseType
        from src.control_reasoning.rule_pipeline import EvaluationResult

        parsed = ParsedResponse(response_type=ResponseType.NO_ACTION, reason="test")
        result = EvaluationResult(
            rule_id="rule_001",
            rule_text="If hot, cool",
            parsed_response=parsed,
        )

        assert result.rule_id == "rule_001"
        assert result.rule_text == "If hot, cool"
        assert result.parsed_response is parsed
        assert result.generation_result is None

    @pytest.mark.unit
    def test_evaluation_result_with_generation_result(self) -> None:
        from src.control_reasoning.command_generator import GenerationResult
        from src.control_reasoning.response_parser import ParsedResponse, ResponseType
        from src.control_reasoning.rule_pipeline import EvaluationResult

        parsed = ParsedResponse(response_type=ResponseType.ACTION)
        cmd = _create_command()
        gen_result = GenerationResult(success=True, command=cmd)

        result = EvaluationResult(
            rule_id="rule_001",
            rule_text="If hot, cool",
            parsed_response=parsed,
            generation_result=gen_result,
        )

        assert result.generation_result is gen_result
        assert result.generation_result.success is True

    @pytest.mark.unit
    def test_evaluation_result_is_frozen(self) -> None:
        from dataclasses import FrozenInstanceError

        from src.control_reasoning.response_parser import ParsedResponse, ResponseType
        from src.control_reasoning.rule_pipeline import EvaluationResult

        parsed = ParsedResponse(response_type=ResponseType.NO_ACTION)
        result = EvaluationResult(
            rule_id="rule_001",
            rule_text="If hot, cool",
            parsed_response=parsed,
        )

        with pytest.raises(FrozenInstanceError):
            result.rule_id = "other"  # type: ignore[misc]


class TestPipelineResult:
    @pytest.mark.unit
    def test_pipeline_result_empty(self) -> None:
        from src.control_reasoning.rule_pipeline import PipelineResult

        result = PipelineResult(
            evaluations=(),
            validated_commands=(),
        )

        assert len(result.evaluations) == 0
        assert len(result.validated_commands) == 0
        assert result.resolution is None
        assert len(result.errors) == 0
        assert result.command_count == 0
        assert result.has_errors is False

    @pytest.mark.unit
    def test_pipeline_result_with_commands(self) -> None:
        from src.control_reasoning.rule_pipeline import PipelineResult

        cmd = _create_command()
        result = PipelineResult(
            evaluations=(),
            validated_commands=(cmd,),
        )

        assert result.command_count == 1
        assert result.validated_commands[0] is cmd

    @pytest.mark.unit
    def test_pipeline_result_with_errors(self) -> None:
        from src.control_reasoning.rule_pipeline import PipelineResult

        result = PipelineResult(
            evaluations=(),
            validated_commands=(),
            errors=("Error 1", "Error 2"),
        )

        assert result.has_errors is True
        assert len(result.errors) == 2

    @pytest.mark.unit
    def test_pipeline_result_with_resolution(self) -> None:
        from src.control_reasoning.conflict_resolver import ResolutionResult
        from src.control_reasoning.rule_pipeline import PipelineResult

        resolution = ResolutionResult(resolved_commands=(), conflicts=())
        result = PipelineResult(
            evaluations=(),
            validated_commands=(),
            resolution=resolution,
        )

        assert result.resolution is resolution

    @pytest.mark.unit
    def test_pipeline_result_is_frozen(self) -> None:
        from dataclasses import FrozenInstanceError

        from src.control_reasoning.rule_pipeline import PipelineResult

        result = PipelineResult(evaluations=(), validated_commands=())

        with pytest.raises(FrozenInstanceError):
            result.errors = ("new error",)  # type: ignore[misc]


class TestPipelineConfig:
    @pytest.mark.unit
    def test_config_defaults(self) -> None:
        from src.control_reasoning.conflict_resolver import ResolutionStrategy
        from src.control_reasoning.rule_pipeline import PipelineConfig

        config = PipelineConfig()

        assert config.ollama_config is None
        assert config.safety_whitelist == set()
        assert config.critical_commands == set()
        assert config.resolution_strategy == ResolutionStrategy.PRIORITY
        assert config.rate_limit == 60
        assert config.rate_window == 60.0

    @pytest.mark.unit
    def test_config_with_custom_values(self) -> None:
        from src.control_reasoning.conflict_resolver import ResolutionStrategy
        from src.control_reasoning.ollama_client import (
            OllamaConfig,
            OllamaConnectionConfig,
            OllamaModelConfig,
        )
        from src.control_reasoning.rule_pipeline import PipelineConfig

        ollama_config = OllamaConfig(
            connection=OllamaConnectionConfig(),
            model=OllamaModelConfig(name="test-model"),
        )
        config = PipelineConfig(
            ollama_config=ollama_config,
            safety_whitelist={"turn_on", "turn_off"},
            critical_commands={"emergency_stop"},
            resolution_strategy=ResolutionStrategy.LAST,
            rate_limit=100,
            rate_window=120.0,
        )

        assert config.ollama_config is ollama_config
        assert "turn_on" in config.safety_whitelist
        assert "emergency_stop" in config.critical_commands
        assert config.resolution_strategy == ResolutionStrategy.LAST
        assert config.rate_limit == 100
        assert config.rate_window == 120.0


class TestRuleProcessingPipelineInit:
    @pytest.mark.unit
    def test_pipeline_default_init(self) -> None:
        from src.control_reasoning.rule_pipeline import RuleProcessingPipeline

        pipeline = RuleProcessingPipeline()

        assert pipeline.is_initialized is False
        assert pipeline.ollama_client is None
        assert len(pipeline.get_rules()) == 0

    @pytest.mark.unit
    def test_pipeline_with_config(self) -> None:
        from src.control_reasoning.conflict_resolver import ResolutionStrategy
        from src.control_reasoning.rule_pipeline import (
            PipelineConfig,
            RuleProcessingPipeline,
        )

        config = PipelineConfig(
            safety_whitelist={"turn_on"},
            resolution_strategy=ResolutionStrategy.MERGE,
        )
        pipeline = RuleProcessingPipeline(config=config)

        assert pipeline.is_initialized is False

    @pytest.mark.unit
    def test_pipeline_with_registry(self) -> None:
        from src.control_reasoning.rule_pipeline import RuleProcessingPipeline

        mock_registry = Mock()
        pipeline = RuleProcessingPipeline(registry=mock_registry)

        assert pipeline._registry is mock_registry

    @pytest.mark.unit
    def test_pipeline_rule_interpreter_property(self) -> None:
        from src.control_reasoning.rule_interpreter import RuleInterpreter
        from src.control_reasoning.rule_pipeline import RuleProcessingPipeline

        pipeline = RuleProcessingPipeline()

        assert isinstance(pipeline.rule_interpreter, RuleInterpreter)


class TestRuleProcessingPipelineInitialize:
    @pytest.mark.unit
    def test_initialize_without_ollama(self) -> None:
        from src.control_reasoning.rule_pipeline import RuleProcessingPipeline

        pipeline = RuleProcessingPipeline()
        pipeline.initialize()

        assert pipeline.is_initialized is True

    @pytest.mark.unit
    def test_initialize_with_ollama_success(self) -> None:
        from src.control_reasoning.rule_pipeline import RuleProcessingPipeline

        pipeline = RuleProcessingPipeline()
        mock_client = Mock()
        mock_client.verify_model = Mock()
        mock_client.active_model = "test-model"
        pipeline.set_ollama_client(mock_client)

        pipeline.initialize()

        mock_client.verify_model.assert_called_once()
        assert pipeline.is_initialized is True

    @pytest.mark.unit
    def test_initialize_with_ollama_failure(self) -> None:
        from src.control_reasoning.rule_pipeline import RuleProcessingPipeline

        pipeline = RuleProcessingPipeline()
        mock_client = Mock()
        mock_client.verify_model = Mock(side_effect=Exception("Connection failed"))
        pipeline.set_ollama_client(mock_client)

        pipeline.initialize()

        assert pipeline.is_initialized is True


class TestRuleProcessingPipelineRuleManagement:
    @pytest.mark.unit
    def test_add_rule(self) -> None:
        from src.control_reasoning.rule_pipeline import RuleProcessingPipeline

        pipeline = RuleProcessingPipeline()
        rule = _create_rule()

        pipeline.add_rule(rule)

        assert len(pipeline.get_rules()) == 1
        assert pipeline.get_rules()[0].rule_id == "rule_001"

    @pytest.mark.unit
    def test_add_multiple_rules(self) -> None:
        from src.control_reasoning.rule_pipeline import RuleProcessingPipeline

        pipeline = RuleProcessingPipeline()
        rule1 = _create_rule(rule_id="rule_001")
        rule2 = _create_rule(rule_id="rule_002", rule_text="If cold, heat")

        pipeline.add_rule(rule1)
        pipeline.add_rule(rule2)

        assert len(pipeline.get_rules()) == 2

    @pytest.mark.unit
    def test_remove_rule(self) -> None:
        from src.control_reasoning.rule_pipeline import RuleProcessingPipeline

        pipeline = RuleProcessingPipeline()
        rule = _create_rule()
        pipeline.add_rule(rule)

        result = pipeline.remove_rule("rule_001")

        assert result is True
        assert len(pipeline.get_rules()) == 0

    @pytest.mark.unit
    def test_remove_nonexistent_rule(self) -> None:
        from src.control_reasoning.rule_pipeline import RuleProcessingPipeline

        pipeline = RuleProcessingPipeline()

        result = pipeline.remove_rule("nonexistent")

        assert result is False


class TestRuleProcessingPipelineSetters:
    @pytest.mark.unit
    def test_set_registry(self) -> None:
        from src.control_reasoning.rule_pipeline import RuleProcessingPipeline

        pipeline = RuleProcessingPipeline()
        mock_registry = Mock()

        pipeline.set_registry(mock_registry)

        assert pipeline._registry is mock_registry

    @pytest.mark.unit
    def test_set_ollama_client(self) -> None:
        from src.control_reasoning.rule_pipeline import RuleProcessingPipeline

        pipeline = RuleProcessingPipeline()
        mock_client = Mock()

        pipeline.set_ollama_client(mock_client)

        assert pipeline.ollama_client is mock_client

    @pytest.mark.unit
    def test_set_rule_priorities(self) -> None:
        from src.control_reasoning.rule_pipeline import RuleProcessingPipeline

        pipeline = RuleProcessingPipeline()
        priorities = {"rule_001": 100, "rule_002": 50}

        pipeline.set_rule_priorities(priorities)

        assert pipeline._conflict_resolver.priority_map == priorities


class TestRuleProcessingPipelineProcess:
    @pytest.mark.unit
    def test_process_no_rules(self) -> None:
        from src.control_reasoning.rule_pipeline import RuleProcessingPipeline

        pipeline = RuleProcessingPipeline()
        pipeline.initialize()

        sensor_states = {"temp_001": _create_linguistic_description()}
        result = pipeline.process(sensor_states)

        assert len(result.evaluations) == 0
        assert len(result.validated_commands) == 0
        assert result.has_errors is False

    @pytest.mark.unit
    def test_process_no_matching_rules(self) -> None:
        from src.control_reasoning.rule_pipeline import RuleProcessingPipeline

        pipeline = RuleProcessingPipeline()
        pipeline.initialize()
        rule = _create_rule(rule_text="If humidity is high, turn on dehumidifier")
        pipeline.add_rule(rule)

        sensor_states = {"temp_001": _create_linguistic_description()}
        result = pipeline.process(sensor_states)

        assert len(result.evaluations) == 0

    @pytest.mark.unit
    def test_process_matching_rule_no_llm(self) -> None:
        from src.control_reasoning.rule_pipeline import RuleProcessingPipeline

        pipeline = RuleProcessingPipeline()
        pipeline.initialize()
        rule = _create_rule(rule_text="If temperature is hot, turn on AC")
        pipeline.add_rule(rule)

        sensor_states = {
            "temp_001": _create_linguistic_description(
                terms=[("hot", 0.9), ("warm", 0.1)]
            )
        }
        result = pipeline.process(sensor_states)

        assert len(result.evaluations) == 1
        assert result.evaluations[0].rule_id == "rule_001"
        assert result.evaluations[0].parsed_response.is_no_action

    @pytest.mark.unit
    def test_process_with_mocked_llm_action(self) -> None:
        from src.control_reasoning.ollama_client import OllamaResponse
        from src.control_reasoning.rule_pipeline import RuleProcessingPipeline

        pipeline = RuleProcessingPipeline()
        pipeline.initialize()

        mock_registry = MagicMock()
        mock_device = MagicMock()
        mock_device.device_id = "ac_001"
        mock_device.capabilities = ["turn_on", "turn_off", "set_temperature"]
        mock_device.get_capability.return_value = None
        mock_registry.get_device.return_value = mock_device
        pipeline.set_registry(mock_registry)

        mock_client = MagicMock()
        mock_response = OllamaResponse(
            text="ACTION: ac_001, turn_on",
            model="test",
            total_duration_ns=1000000000,
            prompt_eval_count=10,
            eval_count=5,
        )
        mock_client.generate.return_value = mock_response
        pipeline.set_ollama_client(mock_client)

        rule = _create_rule(rule_text="If temperature is hot, turn on AC")
        pipeline.add_rule(rule)

        sensor_states = {
            "temp_001": _create_linguistic_description(terms=[("hot", 0.9)])
        }
        result = pipeline.process(sensor_states)

        assert len(result.evaluations) == 1
        assert result.evaluations[0].parsed_response.is_action

    @pytest.mark.unit
    def test_process_with_mocked_llm_no_action(self) -> None:
        from src.control_reasoning.ollama_client import OllamaResponse
        from src.control_reasoning.rule_pipeline import RuleProcessingPipeline

        pipeline = RuleProcessingPipeline()
        pipeline.initialize()

        mock_client = MagicMock()
        mock_response = OllamaResponse(
            text="NO_ACTION: Temperature is not hot enough",
            model="test",
            total_duration_ns=1000000000,
            prompt_eval_count=10,
            eval_count=5,
        )
        mock_client.generate.return_value = mock_response
        pipeline.set_ollama_client(mock_client)

        rule = _create_rule(rule_text="If temperature is hot, turn on AC")
        pipeline.add_rule(rule)

        sensor_states = {
            "temp_001": _create_linguistic_description(terms=[("hot", 0.5)])
        }
        result = pipeline.process(sensor_states)

        assert len(result.evaluations) == 1
        assert result.evaluations[0].parsed_response.is_no_action
        assert len(result.validated_commands) == 0


class TestRuleProcessingPipelineEvaluateRules:
    @pytest.mark.unit
    def test_evaluate_rules_returns_commands(self) -> None:
        from src.control_reasoning.rule_pipeline import RuleProcessingPipeline

        pipeline = RuleProcessingPipeline()
        pipeline.initialize()

        sensor_states = {"temp_001": _create_linguistic_description()}
        commands = pipeline.evaluate_rules(sensor_states)

        assert isinstance(commands, list)

    @pytest.mark.unit
    def test_evaluate_rules_interface_compliance(self) -> None:
        from src.control_reasoning.rule_pipeline import (
            ControlReasoningLayerInterface,
            RuleProcessingPipeline,
        )

        pipeline = RuleProcessingPipeline()

        assert isinstance(pipeline, ControlReasoningLayerInterface)


class TestRuleProcessingPipelineValidationStats:
    @pytest.mark.unit
    def test_get_validation_stats_empty(self) -> None:
        from src.control_reasoning.rule_pipeline import RuleProcessingPipeline

        pipeline = RuleProcessingPipeline()

        stats = pipeline.get_validation_stats()

        assert stats["rules_count"] == 0
        assert stats["enabled_rules_count"] == 0
        assert stats["llm_connected"] is False
        assert stats["initialized"] is False

    @pytest.mark.unit
    def test_get_validation_stats_with_rules(self) -> None:
        from src.control_reasoning.rule_pipeline import RuleProcessingPipeline

        pipeline = RuleProcessingPipeline()
        pipeline.initialize()
        pipeline.add_rule(_create_rule(rule_id="rule_001"))
        pipeline.add_rule(_create_rule(rule_id="rule_002", enabled=False))
        mock_client = Mock()
        pipeline.set_ollama_client(mock_client)

        stats = pipeline.get_validation_stats()

        assert stats["rules_count"] == 2
        assert stats["enabled_rules_count"] == 1
        assert stats["llm_connected"] is True
        assert stats["initialized"] is True


class TestRuleProcessingPipelineClose:
    @pytest.mark.unit
    def test_close_without_client(self) -> None:
        from src.control_reasoning.rule_pipeline import RuleProcessingPipeline

        pipeline = RuleProcessingPipeline()

        pipeline.close()

    @pytest.mark.unit
    def test_close_with_client(self) -> None:
        from src.control_reasoning.rule_pipeline import RuleProcessingPipeline

        pipeline = RuleProcessingPipeline()
        mock_client = Mock()
        pipeline.set_ollama_client(mock_client)

        pipeline.close()

        mock_client.close.assert_called_once()


class TestRuleProcessingPipelineConflictResolution:
    @pytest.mark.unit
    def test_process_with_conflicts(self) -> None:
        from src.control_reasoning.ollama_client import OllamaResponse
        from src.control_reasoning.rule_pipeline import RuleProcessingPipeline

        pipeline = RuleProcessingPipeline()
        pipeline.initialize()

        mock_registry = MagicMock()
        mock_device = MagicMock()
        mock_device.device_id = "ac_001"
        mock_device.capabilities = ["turn_on", "turn_off"]
        mock_device.get_capability.return_value = None
        mock_registry.get_device.return_value = mock_device
        pipeline.set_registry(mock_registry)

        call_count = 0

        def mock_generate(prompt: str) -> OllamaResponse:
            nonlocal call_count
            call_count += 1
            return OllamaResponse(
                text="ACTION: ac_001, turn_on",
                model="test",
                total_duration_ns=1000000000,
                prompt_eval_count=10,
                eval_count=5,
            )

        mock_client = MagicMock()
        mock_client.generate.side_effect = mock_generate
        pipeline.set_ollama_client(mock_client)

        rule1 = _create_rule(
            rule_id="rule_001",
            rule_text="If temperature is hot, turn on AC",
            priority=1,
        )
        rule2 = _create_rule(
            rule_id="rule_002",
            rule_text="If hot conditions, turn on AC",
            priority=2,
        )
        pipeline.add_rule(rule1)
        pipeline.add_rule(rule2)

        sensor_states = {
            "temp_001": _create_linguistic_description(terms=[("hot", 0.9)])
        }
        result = pipeline.process(sensor_states)

        assert len(result.evaluations) == 2


class TestRuleProcessingPipelineErrorHandling:
    @pytest.mark.unit
    def test_process_handles_evaluation_error(self) -> None:
        from src.control_reasoning.rule_pipeline import RuleProcessingPipeline

        pipeline = RuleProcessingPipeline()
        pipeline.initialize()

        mock_client = MagicMock()
        mock_client.generate.side_effect = Exception("LLM error")
        pipeline.set_ollama_client(mock_client)

        rule = _create_rule(rule_text="If temperature is hot, turn on AC")
        pipeline.add_rule(rule)

        sensor_states = {
            "temp_001": _create_linguistic_description(terms=[("hot", 0.9)])
        }
        result = pipeline.process(sensor_states)

        assert result.has_errors is True
        assert len(result.errors) > 0

    @pytest.mark.unit
    def test_process_with_validation_failure(self) -> None:
        from src.control_reasoning.command_generator import GenerationResult
        from src.control_reasoning.command_validator import (
            ValidationError,
            ValidationResult,
            ValidationStep,
        )
        from src.control_reasoning.ollama_client import OllamaResponse
        from src.control_reasoning.rule_pipeline import RuleProcessingPipeline

        pipeline = RuleProcessingPipeline()
        pipeline.initialize()

        mock_registry = MagicMock()
        mock_device = MagicMock()
        mock_device.device_id = "ac_001"
        mock_device.device_type = "actuator"
        mock_device.capabilities = ["turn_on", "turn_off"]
        mock_device.get_capability.return_value = None
        mock_registry.get_device.return_value = mock_device
        pipeline.set_registry(mock_registry)

        mock_client = MagicMock()
        mock_response = OllamaResponse(
            text="ACTION: ac_001, turn_on",
            model="test",
            total_duration_ns=1000000000,
            prompt_eval_count=10,
            eval_count=5,
        )
        mock_client.generate.return_value = mock_response
        pipeline.set_ollama_client(mock_client)

        cmd = _create_command()
        gen_result = GenerationResult(success=True, command=cmd)
        pipeline._command_generator.generate_from_parsed_response = Mock(
            return_value=gen_result
        )

        validation_error = ValidationError(
            step=ValidationStep.SAFETY_WHITELIST,
            message="Command not in whitelist",
        )
        invalid_result = ValidationResult(
            valid=False,
            command=cmd,
            errors=(validation_error,),
        )
        pipeline._command_validator.validate = Mock(return_value=invalid_result)

        rule = _create_rule(rule_text="If temperature is hot, turn on AC")
        pipeline.add_rule(rule)

        sensor_states = {
            "temp_001": _create_linguistic_description(terms=[("hot", 0.9)])
        }
        result = pipeline.process(sensor_states)

        assert len(result.validated_commands) == 0
        assert result.has_errors is True
        assert "Validation failed" in result.errors[0]

    @pytest.mark.unit
    def test_process_not_initialized_warning(self) -> None:
        from src.control_reasoning.rule_pipeline import RuleProcessingPipeline

        pipeline = RuleProcessingPipeline()

        sensor_states = {"temp_001": _create_linguistic_description()}
        result = pipeline.process(sensor_states)

        assert len(result.evaluations) == 0


class TestRuleProcessingPipelineWithOllamaConfig:
    @pytest.mark.unit
    def test_pipeline_init_with_ollama_config(self) -> None:
        from unittest.mock import patch

        from src.control_reasoning.ollama_client import (
            OllamaConfig,
            OllamaConnectionConfig,
            OllamaModelConfig,
        )
        from src.control_reasoning.rule_pipeline import (
            PipelineConfig,
            RuleProcessingPipeline,
        )

        ollama_config = OllamaConfig(
            connection=OllamaConnectionConfig(),
            model=OllamaModelConfig(name="test-model"),
        )
        config = PipelineConfig(ollama_config=ollama_config)

        with patch("src.control_reasoning.rule_pipeline.OllamaClient") as MockClient:
            pipeline = RuleProcessingPipeline(config=config)
            MockClient.assert_called_once_with(ollama_config)
            assert pipeline.ollama_client is not None


class TestRuleProcessingPipelineExports:
    @pytest.mark.unit
    def test_exports_from_module(self) -> None:
        from src.control_reasoning import (
            ControlReasoningLayerInterface,
            EvaluationResult,
            PipelineConfig,
            PipelineResult,
            RuleProcessingPipeline,
        )

        assert ControlReasoningLayerInterface is not None
        assert EvaluationResult is not None
        assert PipelineConfig is not None
        assert PipelineResult is not None
        assert RuleProcessingPipeline is not None
