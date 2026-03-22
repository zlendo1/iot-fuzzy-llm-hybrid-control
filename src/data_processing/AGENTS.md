# Data Processing Layer

<!-- Generated: 2026-03-22 | Parent: src/AGENTS.md -->

> Fuzzy logic processing: transforms raw sensor values into linguistic
> descriptions that the LLM can understand.

## Purpose

The **semantic bridge** between raw numbers and natural language. Takes a sensor
reading like "temperature: 32°C" and produces "hot (0.85), warm (0.15)" — a
linguistic description the LLM can reason about.

## Key Files

| File                       | Lines | Role                                                      |
| -------------------------- | ----- | --------------------------------------------------------- |
| `fuzzy_pipeline.py`        | 366   | **Layer coordinator**. Orchestrates full processing flow  |
| `fuzzy_engine.py`          | 217   | Core fuzzy logic: membership calculation, caching         |
| `membership_functions.py`  | 233   | Mathematical MF implementations (triangular, trapezoidal) |
| `linguistic_descriptor.py` | 297   | Converts fuzzy results to natural language descriptions   |
| `__init__.py`              |       | Exports: FuzzyProcessingPipeline, FuzzyEngine, etc.       |

## Architecture

```
SensorReading (from device_interface)
        ↓
┌─ FuzzyProcessingPipeline ─────────────────┐
│  1. Load membership functions (from JSON)  │
│              ↓                             │
│  2. FuzzyEngine                            │
│     Calculate membership degrees per term  │
│     e.g. temp=32 → hot:0.85, warm:0.15    │
│              ↓                             │
│  3. LinguisticDescriptor                   │
│     Format as natural language string      │
│     e.g. "temperature is hot (0.85)"       │
└────────────────────────────────────────────┘
        ↓
LinguisticDescription (to control_reasoning)
```

### Pipeline Coordinator Methods

```python
pipeline.process_reading(reading, sensor_type)  # Full transform
pipeline.get_current_state()                     # All sensor states
pipeline.get_sensor_state(sensor_id)             # Single sensor state
```

## Core Concepts

### Membership Functions

Defined in `config/membership_functions/{sensor_type}.json`. Each sensor type
has linguistic terms with membership function parameters:

```json
{
  "sensor_type": "temperature",
  "unit": "°C",
  "terms": [
    {"name": "cold", "type": "trapezoidal", "params": [-10, -5, 10, 18]},
    {"name": "warm", "type": "triangular", "params": [15, 22, 30]},
    {"name": "hot", "type": "trapezoidal", "params": [27, 33, 45, 50]}
  ]
}
```

**Supported MF types**: `triangular` (3 params), `trapezoidal` (4 params).

### Data Models

```python
@dataclass
class TermMembership:
    term: str           # e.g. "hot"
    degree: float       # 0.0 to 1.0

@dataclass
class LinguisticDescription:
    sensor_id: str
    sensor_type: str
    value: float
    unit: str
    memberships: list[TermMembership]
    description: str    # Natural language summary
```

## Common Tasks

### Adding a New Sensor Type

1. Create `config/membership_functions/{type}.json` with linguistic terms
2. Add device with this sensor type to `config/devices.json`
3. FuzzyPipeline **auto-loads** membership functions — no code changes needed
4. Verify: check that `process_reading()` produces expected linguistic output

### Modifying Linguistic Terms

Edit the membership function JSON file directly. Changes take effect on next
pipeline initialization (or config reload via gRPC).

### Tuning Membership Function Parameters

Adjust `params` arrays in the JSON config. Use overlapping ranges for smooth
transitions between terms (e.g., warm and hot should overlap).

## DO NOT

- **Hardcode membership function parameters** — always use JSON config files
- **Skip the fuzzy pipeline** — never pass raw sensor values directly to the LLM
- **Import from control_reasoning or interfaces** — this layer only talks to
  control_reasoning (above) and device_interface (below)
- **Modify membership function JSON without overlapping ranges** — gaps cause
  undefined behavior for sensor values between terms

## Performance Targets

| Operation              | Target  |
| ---------------------- | ------- |
| Fuzzy processing       | < 50ms  |
| Sensor → description   | < 100ms |
| Membership calculation | < 10ms  |
