# Data Processing Layer Tests

This directory contains tests for the Data Processing Layer components.

## Test Files

```
test_data_processing/
├── test_fuzzy_engine.py           # Tests for FuzzyEngine
├── test_fuzzy_pipeline.py         # Tests for FuzzyProcessingPipeline
├── test_linguistic_descriptor.py  # Tests for LinguisticDescriptor
└── test_membership_functions.py   # Tests for membership function library
```

## Test Focus

### FuzzyEngine Tests

- Application of membership functions to numerical values
- Computation of membership degrees for all linguistic terms
- Filtering by confidence threshold
- Handling of edge cases (values outside universe of discourse)
- Vectorization performance with NumPy

### MembershipFunctions Tests

- Triangular function computation (a, b, c parameters)
- Trapezoidal function computation (a, b, c, d parameters)
- Gaussian function computation (mean, sigma parameters)
- Sigmoid function computation (a, b parameters)
- Factory pattern for function creation

### LinguisticDescriptor Tests

- Formatting fuzzy output to natural language
- Single sensor descriptions
- Multiple sensor descriptions
- Membership degree formatting
- Structure optimization for LLM consumption
- Edge cases (empty input, zero degrees)

### FuzzyProcessingPipeline Tests

- Integration of all Data Processing components
- Caching strategy (LRU with 300s TTL)
- Cache hits and misses
- State change notifications to Control Layer

## Performance Tests

Verify latency targets from ADD Section 8.1:

- Fuzzy logic processing: < 50ms per sensor
- Sensor reading to linguistic description: < 100ms total

## Running Tests

```bash
# All Data Processing tests
pytest tests/test_data_processing/

# Specific component
pytest tests/test_data_processing/test_fuzzy_engine.py

# With coverage
pytest tests/test_data_processing/ --cov=src/data_processing
```
