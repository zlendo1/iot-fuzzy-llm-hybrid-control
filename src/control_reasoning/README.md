# Control & Reasoning Layer

This directory contains the layer that evaluates natural language rules against
linguistic sensor states and generates device commands.

## Structure

```
control_reasoning/
├── __init__.py
├── rule_pipeline.py        # Coordinator - orchestrates rule evaluation
├── ollama_client.py        # LLM communication via Ollama REST API
├── prompt_builder.py       # Constructs prompts for LLM
├── response_parser.py      # Parses LLM responses into structured actions
├── rule_interpreter.py     # Matches sensor states to rule conditions
├── command_generator.py    # Translates LLM actions to device commands
├── command_validator.py    # Validates commands against device capabilities
└── conflict_resolver.py    # Resolves conflicts when multiple rules fire
```

## Coordinator

- **RuleProcessingPipeline** (`rule_pipeline.py`) - The sole interface between
  the Data Processing Layer below and the Configuration & Management Layer above
  it. Orchestrates the full rule evaluation workflow.

## Components

### OllamaClient

- Communicates with Ollama LLM service via REST API
- Submits inference requests to `/api/generate` endpoint
- Handles timeouts, retries, and connection errors
- Configures inference parameters (temperature, max_tokens, top_p, etc.)

### PromptBuilder

- Constructs prompts from sensor states and rule text
- Uses configurable prompt templates
- Formats linguistic descriptions for LLM consumption

### ResponseParser

- Parses LLM responses to extract structured actions
- Validates response format (ACTION: command syntax)
- Handles malformed or unexpected responses

### RuleInterpreter

- Matches current linguistic sensor states to rule conditions
- Identifies candidate rules for evaluation
- Updates rule metadata (trigger_count, last_triggered)

### CommandGenerator

- Translates abstract LLM actions into concrete device commands
- Maps action keywords to device capabilities
- Formats commands for MQTT publication

### CommandValidator

- Validates commands against device capabilities
- Checks device-specific constraints (temperature ranges, allowed modes)
- Applies safety whitelists
- Enforces rate limits (60 commands/minute per device)
- Flags critical commands for user confirmation

### ConflictResolver

- Resolves conflicts when multiple rules target the same device
- Implements priority-based resolution (higher priority wins)
- Handles tie-breaking when priorities are equal

## Communication Flow

**Downward** (from Data Processing Layer):

- Linguistic descriptions of current sensor state
- State change notifications

**Upward** (to Configuration & Management Layer):

- Validation requests for commands
- Rule history updates

**Downward** (via Configuration & Management to Device Interface):

- Validated device commands for execution

## Evaluation Flow

As specified in Section 4.2 of the ADD:

1. Request current system state from Fuzzy Processing Pipeline
2. Identify candidate rules matching current state
3. Submit each rule to LLM for evaluation (per-rule prompting per DD-06)
4. Parse LLM response for action specification
5. Validate action against capabilities and safety constraints
6. Resolve conflicts if multiple commands target same device
7. Pass validated commands to Device Interface layer

## Command Validation Pipeline

Per Section 7.2, all commands pass through validation steps:

1. Response parsing (verify ACTION format)
2. Device existence check
3. Capability match verification
4. Parameter constraint validation
5. Safety whitelist check
6. Rate limit enforcement
7. Critical command flagging

## Performance Target

- LLM inference: < 3 seconds per rule
- Command generation and validation: < 100ms

## Design Decisions

- **Per-rule prompting** (DD-06): Each rule evaluated separately for better
  accuracy and clear attribution
- **Command validation** (DD-07): All LLM outputs validated before execution to
  prevent hallucinations

## Integration

This layer is the intelligence core of the system, bridging fuzzy logic data to
actionable device control. It maintains strict separation: it receives
linguistic data from below and sends validated commands through the layers
above.
