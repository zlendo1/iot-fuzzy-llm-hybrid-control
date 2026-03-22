# Control & Reasoning Layer

<!-- Generated: 2026-03-22 | Parent: src/AGENTS.md -->

> Natural language rule evaluation via LLM inference. Interprets fuzzy sensor
> states, generates device commands, validates and resolves conflicts.

## Purpose

The "intelligence" layer. Takes linguistic descriptions of sensor states (from
data_processing) and natural language rules, uses an LLM to reason about what
actions to take, then generates validated device commands.

## Key Files

| File                   | Lines | Role                                                       |
| ---------------------- | ----- | ---------------------------------------------------------- |
| `rule_pipeline.py`     | 300   | **Layer coordinator**. Multi-stage rule evaluation         |
| `ollama_client.py`     | 351   | Ollama LLM client with health checks, retry, config        |
| `rule_interpreter.py`  | 213   | Matches rules to current sensor states by linguistic terms |
| `prompt_builder.py`    |       | Builds LLM prompts from sensor state + rules               |
| `response_parser.py`   |       | Extracts structured actions from LLM output                |
| `command_generator.py` |       | Parses LLM output into structured DeviceCommand objects    |
| `command_validator.py` | 291   | Validates commands against device capabilities and safety  |
| `conflict_resolver.py` | 203   | Resolves competing commands for the same device            |
| `__init__.py`          |       | Exports: RuleProcessingPipeline, OllamaClient, etc.        |

## Architecture — Rule Evaluation Pipeline

```
Linguistic Descriptions (from data_processing)
        ↓
┌─ RuleProcessingPipeline ──────────────────┐
│  1. RuleInterpreter                       │
│     Match rules against sensor states     │
│              ↓                            │
│  2. OllamaClient                          │
│     LLM inference: what actions to take   │
│              ↓                            │
│  3. CommandGenerator                      │
│     Parse LLM output → DeviceCommand      │
│              ↓                            │
│  4. CommandValidator                      │
│     Check capabilities, safety, rates     │
│              ↓                            │
│  5. ConflictResolver                      │
│     Resolve competing commands            │
└───────────────────────────────────────────┘
        ↓
DeviceCommands (sent via device_interface)
```

### Pipeline Coordinator Methods

```python
pipeline.process(sensor_states, rules)      # Full pipeline run
pipeline.add_rule(rule_text)                 # Add new rule
pipeline.remove_rule(rule_id)                # Remove rule
pipeline.evaluate_rules(sensor_states)       # Evaluate all active rules
```

## Patterns

### LLM Client Configuration

```python
# OllamaClient uses dataclass configs
@dataclass
class OllamaConfig:
    base_url: str = "http://localhost:11434"
    model: str = "qwen3:0.6b"
    timeout: float = 30.0
    max_retries: int = 3
```

Default model is `qwen3:0.6b` — small, fast, runs locally via Ollama.

### Command Validation Pipeline

CommandValidator checks in order:

1. **Device exists** in registry
2. **Capability check** — device supports the command type
3. **Safety rules** — prevents dangerous combinations
4. **Rate limiting** — prevents command flooding

### Conflict Resolution

When multiple rules generate commands for the same device:

- Priority-based resolution (higher priority rule wins)
- Most recent rule takes precedence at equal priority
- Conflicting commands logged for debugging

## Common Tasks

### Modifying the LLM Prompt

- Prompt template lives in `config/prompt_template.txt`
- Template receives: sensor states, active rules, device capabilities
- Test changes with: `make test-unit` (rule pipeline tests)

### Adding a New Pipeline Stage

1. Create new module in `src/control_reasoning/`
2. Implement with clear input/output types
3. Wire into `RuleProcessingPipeline.process()` method
4. Add corresponding tests in `tests/test_control_reasoning/`

### Changing the LLM Model

Update `config/llm_config.json` — the `model` field. Ensure Ollama has the model
pulled (`make pull-model`).

## DO NOT

- **Hardcode model names** — use config/llm_config.json
- **Skip command validation** — all generated commands must pass through
  CommandValidator before execution
- **Bypass conflict resolution** — commands for the same device must be resolved
- **Import from interfaces or configuration layer** — this layer only talks to
  configuration (above) and data_processing (below)
- **Trust LLM output directly** — always parse and validate

## Performance Targets

| Stage               | Target  |
| ------------------- | ------- |
| Rule interpretation | < 10ms  |
| LLM inference       | < 3s    |
| Command generation  | < 100ms |
| Validation          | < 50ms  |
| End-to-end pipeline | < 5s    |
