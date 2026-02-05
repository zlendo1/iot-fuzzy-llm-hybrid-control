# Control & Reasoning Layer Tests

This directory contains tests for the Control & Reasoning Layer components.

## Test Files

```
test_control_reasoning/
├── test_command_generator.py    # Tests for CommandGenerator
├── test_command_validator.py    # Tests for CommandValidator
├── test_conflict_resolver.py    # Tests for ConflictResolver
├── test_ollama_client.py        # Tests for OllamaClient
├── test_prompt_builder.py       # Tests for PromptBuilder
├── test_response_parser.py      # Tests for ResponseParser
├── test_rule_interpreter.py     # Tests for RuleInterpreter
└── test_rule_pipeline.py        # Tests for RuleProcessingPipeline
```

## Test Focus

### OllamaClient Tests

- REST API communication with Ollama service
- Inference request submission to /api/generate endpoint
- Timeout and error handling
- Connection retry logic

### PromptBuilder Tests

- Prompt construction from sensor states and rule text
- Template variable substitution
- Edge cases (empty states, missing templates)

### ResponseParser Tests

- LLM response parsing for structured actions
- ACTION format validation
- Malformed response handling

### RuleInterpreter Tests

- Matching linguistic states to rule conditions
- Candidate rule identification
- Rule metadata updates (trigger_count, last_triggered)

### CommandGenerator Tests

- Translation of abstract LLM actions to concrete commands
- Action keyword mapping
- Command formatting

### CommandValidator Tests

- Device capability validation
- Parameter constraint checking
- Safety whitelist verification
- Rate limit enforcement

### ConflictResolver Tests

- Priority-based conflict resolution
- Multiple commands targeting same device
- Tie-breaking logic

### RuleProcessingPipeline Tests

- Integration of all Control & Reasoning components
- Rule evaluation workflow orchestration
- Validation pipeline execution

## Running Tests

```bash
# All Control & Reasoning tests
pytest tests/test_control_reasoning/

# Specific component
pytest tests/test_control_reasoning/test_ollama_client.py

# With verbose output
pytest tests/test_control_reasoning/ -v
```
