# Control & Reasoning Layer Tests

This directory contains tests for the Control & Reasoning Layer components.

## Components Tested

- `test_rule_interpreter.py` - Tests for RuleInterpreter component
- `test_ollama_client.py` - Tests for OllamaClient component
- `test_command_generator.py` - Tests for CommandGenerator component
- `test_rule_processing_pipeline.py` - Tests for the layer coordinator

## Test Focus

### RuleInterpreter Tests

- Matching linguistic states to rule conditions
- Candidate rule identification
- Priority-based conflict resolution
- Multiple commands targeting same device
- Rule metadata updates (trigger_count, last_triggered)
- Edge cases (no matches, multiple matches, disabled rules)

### OllamaClient Tests

- REST API communication with Ollama service
- Prompt construction from sensor states and rule text
- Inference request submission to /api/generate endpoint
- LLM response parsing for structured actions
- Model fallback mechanism (mistral → llama3.2 → phi3)
- Inference parameter application (temperature, max_tokens, etc.)
- Timeout and error handling

### CommandGenerator Tests

- Translation of abstract LLM actions to concrete commands
- Device capability validation
- Parameter constraint checking (temperature ranges, allowed modes)
- Safety whitelist verification
- Rate limit enforcement (60 commands/minute)
- Critical command flagging
- Malformed action rejection

### RuleProcessingPipeline Tests

- Integration of all Control & Reasoning components
- Rule evaluation workflow orchestration
- Validation pipeline execution
- State change request processing
- Coordinator interface compliance
- Upward communication to Configuration Layer

## Command Validation Tests

Verify 7-step validation pipeline from ADD Section 7.2:

1. Response parsing (verify ACTION format)
2. Device existence check
3. Capability match verification
4. Parameter constraint validation
5. Safety whitelist check
6. Rate limit enforcement
7. Critical command flagging

## Performance Tests

Verify latency targets from ADD Section 8.1:

- LLM inference: < 3 seconds per rule (may use fast mock for CI)
- Command generation and validation: < 100ms

## Mocking Strategy

- **Ollama Service**: Mock HTTP responses for fast, deterministic testing
- **Device Registry**: Mock device capabilities and constraints
- **Linguistic States**: Use pre-defined state fixtures
- **Time**: Mock time for rate limit testing

## Test Configuration

Fixtures provide:

- Sample rules with various conditions and priorities
- Sample linguistic sensor states
- Mock Ollama responses (valid and invalid)
- Sample LLM actions and expected commands
- Device capability configurations

## Running Tests

```bash
# All Control & Reasoning tests
pytest tests/test_control_reasoning/

# Specific component
pytest tests/test_control_reasoning/test_rule_interpreter.py

# With verbose output
pytest tests/test_control_reasoning/ -v

# Performance tests only
pytest tests/test_control_reasoning/ -m performance
```
