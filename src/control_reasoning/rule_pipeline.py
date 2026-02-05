from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from src.common.logging import get_logger
from src.control_reasoning.command_generator import (
    CommandGenerator,
    DeviceCommand,
    GenerationResult,
)
from src.control_reasoning.command_validator import (
    CommandValidator,
)
from src.control_reasoning.conflict_resolver import (
    ConflictResolver,
    ResolutionResult,
    ResolutionStrategy,
)
from src.control_reasoning.ollama_client import OllamaClient, OllamaConfig
from src.control_reasoning.prompt_builder import PromptBuilder
from src.control_reasoning.response_parser import (
    ParsedResponse,
    ResponseParser,
    ResponseType,
)
from src.control_reasoning.rule_interpreter import NaturalLanguageRule, RuleInterpreter

if TYPE_CHECKING:
    from src.data_processing.linguistic_descriptor import LinguisticDescription
    from src.device_interface.registry import DeviceRegistry

logger = get_logger(__name__)


class ControlReasoningLayerInterface(ABC):
    @abstractmethod
    def evaluate_rules(
        self,
        sensor_states: dict[str, LinguisticDescription],
    ) -> list[DeviceCommand]:
        ...

    @abstractmethod
    def add_rule(self, rule: NaturalLanguageRule) -> None:
        ...

    @abstractmethod
    def remove_rule(self, rule_id: str) -> bool:
        ...

    @abstractmethod
    def get_rules(self) -> list[NaturalLanguageRule]:
        ...


@dataclass(frozen=True)
class EvaluationResult:
    rule_id: str
    rule_text: str
    parsed_response: ParsedResponse
    generation_result: GenerationResult | None = None


@dataclass(frozen=True)
class PipelineResult:
    evaluations: tuple[EvaluationResult, ...]
    validated_commands: tuple[DeviceCommand, ...]
    resolution: ResolutionResult | None = None
    errors: tuple[str, ...] = ()

    @property
    def command_count(self) -> int:
        return len(self.validated_commands)

    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0


@dataclass
class PipelineConfig:
    ollama_config: OllamaConfig | None = None
    safety_whitelist: set[str] = field(default_factory=set)
    critical_commands: set[str] = field(default_factory=set)
    resolution_strategy: ResolutionStrategy = ResolutionStrategy.PRIORITY
    rate_limit: int = 60
    rate_window: float = 60.0


class RuleProcessingPipeline(ControlReasoningLayerInterface):
    def __init__(
        self,
        config: PipelineConfig | None = None,
        registry: DeviceRegistry | None = None,
    ) -> None:
        self._config = config or PipelineConfig()

        self._rule_interpreter = RuleInterpreter()
        self._prompt_builder = PromptBuilder()
        self._response_parser = ResponseParser()
        self._command_generator = CommandGenerator(registry=registry)
        self._command_validator = CommandValidator(
            registry=registry,
            safety_whitelist=self._config.safety_whitelist,
            critical_commands=self._config.critical_commands,
            rate_limit=self._config.rate_limit,
            rate_window=self._config.rate_window,
        )
        self._conflict_resolver = ConflictResolver(
            strategy=self._config.resolution_strategy,
        )

        self._ollama_client: OllamaClient | None = None
        if self._config.ollama_config:
            self._ollama_client = OllamaClient(self._config.ollama_config)

        self._registry = registry
        self._initialized = False

    @property
    def is_initialized(self) -> bool:
        return self._initialized

    @property
    def rule_interpreter(self) -> RuleInterpreter:
        return self._rule_interpreter

    @property
    def ollama_client(self) -> OllamaClient | None:
        return self._ollama_client

    def set_registry(self, registry: DeviceRegistry) -> None:
        self._registry = registry
        self._command_generator.set_registry(registry)
        self._command_validator.set_registry(registry)

    def set_ollama_client(self, client: OllamaClient) -> None:
        self._ollama_client = client

    def initialize(self) -> None:
        if self._ollama_client:
            try:
                self._ollama_client.verify_model()
                logger.info(
                    "Ollama model verified",
                    extra={"model": self._ollama_client.active_model},
                )
            except Exception as e:
                logger.warning(
                    "Failed to verify Ollama model",
                    extra={"error": str(e)},
                )

        self._initialized = True
        logger.info("RuleProcessingPipeline initialized")

    def add_rule(self, rule: NaturalLanguageRule) -> None:
        self._rule_interpreter.add_rule(rule)
        logger.debug("Rule added", extra={"rule_id": rule.rule_id})

    def remove_rule(self, rule_id: str) -> bool:
        return self._rule_interpreter.remove_rule(rule_id)

    def get_rules(self) -> list[NaturalLanguageRule]:
        return self._rule_interpreter.rules

    def evaluate_rules(
        self,
        sensor_states: dict[str, LinguisticDescription],
    ) -> list[DeviceCommand]:
        result = self.process(sensor_states)
        return list(result.validated_commands)

    def process(
        self,
        sensor_states: dict[str, LinguisticDescription],
    ) -> PipelineResult:
        if not self._initialized:
            logger.warning("Pipeline not initialized, call initialize() first")

        candidate_rules = self._rule_interpreter.find_candidate_rules(
            list(sensor_states.values())
        )

        if not candidate_rules:
            logger.debug("No candidate rules found for current state")
            return PipelineResult(
                evaluations=(),
                validated_commands=(),
            )

        evaluations: list[EvaluationResult] = []
        pending_commands: list[DeviceCommand] = []
        errors: list[str] = []

        for match in candidate_rules:
            rule = match.rule

            try:
                eval_result = self._evaluate_single_rule(rule, sensor_states)
                evaluations.append(eval_result)

                if eval_result.generation_result and eval_result.generation_result.success:
                    cmd = eval_result.generation_result.command
                    if cmd:
                        pending_commands.append(cmd)

                self._rule_interpreter.record_rule_trigger(rule.rule_id)

            except Exception as e:
                error_msg = f"Error evaluating rule '{rule.rule_id}': {e}"
                errors.append(error_msg)
                logger.exception(error_msg)

        resolution: ResolutionResult | None = None
        if self._conflict_resolver.has_conflicts(pending_commands):
            resolution = self._conflict_resolver.resolve(pending_commands)
            pending_commands = list(resolution.resolved_commands)

        validated_commands: list[DeviceCommand] = []
        for cmd in pending_commands:
            validation_result = self._command_validator.validate(cmd)
            if validation_result.valid:
                validated_commands.append(cmd)
            else:
                for error in validation_result.errors:
                    errors.append(f"Validation failed for {cmd.command_id}: {error.message}")

        return PipelineResult(
            evaluations=tuple(evaluations),
            validated_commands=tuple(validated_commands),
            resolution=resolution,
            errors=tuple(errors),
        )

    def _evaluate_single_rule(
        self,
        rule: NaturalLanguageRule,
        sensor_states: dict[str, LinguisticDescription],
    ) -> EvaluationResult:
        prompt = self._prompt_builder.build(
            sensor_descriptions=list(sensor_states.values()),
            rule_text=rule.rule_text,
        )

        if self._ollama_client is None:
            parsed = ParsedResponse(
                response_type=ResponseType.NO_ACTION,
                reason="LLM client not configured",
            )
            return EvaluationResult(
                rule_id=rule.rule_id,
                rule_text=rule.rule_text,
                parsed_response=parsed,
            )

        response = self._ollama_client.generate(prompt.prompt_text)
        parsed = self._response_parser.parse(response.text)

        generation_result: GenerationResult | None = None
        if parsed.is_action:
            generation_result = self._command_generator.generate_from_parsed_response(
                parsed,
                rule_id=rule.rule_id,
            )

        logger.debug(
            "Rule evaluated",
            extra={
                "rule_id": rule.rule_id,
                "response_type": parsed.response_type.value,
                "action": parsed.action.to_dict() if parsed.action else None,
            },
        )

        return EvaluationResult(
            rule_id=rule.rule_id,
            rule_text=rule.rule_text,
            parsed_response=parsed,
            generation_result=generation_result,
        )

    def set_rule_priorities(self, priority_map: dict[str, int]) -> None:
        self._conflict_resolver.set_priority_map(priority_map)

    def get_validation_stats(self) -> dict[str, Any]:
        return {
            "rules_count": len(self._rule_interpreter.rules),
            "enabled_rules_count": len(self._rule_interpreter.enabled_rules),
            "llm_connected": self._ollama_client is not None,
            "initialized": self._initialized,
        }

    def close(self) -> None:
        if self._ollama_client:
            self._ollama_client.close()
        logger.info("RuleProcessingPipeline closed")
