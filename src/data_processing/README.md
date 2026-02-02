# Data Processing Layer

This directory contains the layer that transforms raw numerical sensor data into
linguistic descriptions suitable for LLM consumption.

## Coordinator

- **FuzzyProcessingPipeline** - The sole interface between the Device Interface
  Layer below and the Control & Reasoning Layer above it. Orchestrates fuzzy
  logic processing.

## Components

### FuzzyEngine

- Applies membership functions to numerical sensor values
- Computes membership degrees for all configured linguistic terms
- Filters results by confidence threshold (default 0.1)
- Uses NumPy vectorization for efficient computation

### MembershipFunctionLibrary

- Implements fuzzy membership function types:
  - Triangular (parameters: a, b, c)
  - Trapezoidal (parameters: a, b, c, d)
  - Gaussian (parameters: mean, sigma)
  - Sigmoid (parameters: a, b)
- Provides factory pattern for function creation
- Supports custom function type registration

### LinguisticDescriptorBuilder

- Formats fuzzy logic output into natural language descriptions
- Structures output optimized for LLM consumption
- Example: `temperature is hot (0.85), humidity is moderate (0.72)`
- Handles multiple sensors in single response

## Communication Flow

**Downward** (from Device Interface Layer):

- Raw sensor readings and their device metadata

**Upward** (to Control & Reasoning Layer):

- Cached linguistic descriptions
- State change notifications

## Caching Strategy

Per Section 5.3 of the ADD:

- Cache fuzzy results per sensor type (up to 1000 entries)
- LRU eviction policy with 300 second TTL
- Reduces redundant membership function computation
- Improves performance for repeated sensor values

## Performance Target

As specified in Section 8.1:

- Fuzzy logic processing: < 50ms per sensor
- Sensor reading to linguistic description: < 100ms total

## Integration

This layer depends only on the Configuration Manager (via System Orchestrator)
for accessing membership function definitions. It has no knowledge of rules or
LLM operations, maintaining strict layer separation.
