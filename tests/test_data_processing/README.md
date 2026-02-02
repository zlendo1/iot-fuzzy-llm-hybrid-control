# Data Processing Layer Tests

This directory contains tests for the Data Processing Layer components.

## Components Tested

- `test_fuzzy_engine.py` - Tests for FuzzyEngine component
- `test_membership_functions.py` - Tests for MembershipFunctionLibrary
- `test_linguistic_descriptor_builder.py` - Tests for
  LinguisticDescriptorBuilder
- `test_fuzzy_processing_pipeline.py` - Tests for the layer coordinator

## Test Focus

### FuzzyEngine Tests

- Application of membership functions to numerical values
- Computation of membership degrees for all linguistic terms
- Filtering by confidence threshold
- Handling of edge cases (values outside universe of discourse)
- Vectorization performance with NumPy

### MembershipFunctionLibrary Tests

- Triangular function computation (a, b, c parameters)
- Trapezoidal function computation (a, b, c, d parameters)
- Gaussian function computation (mean, sigma parameters)
- Sigmoid function computation (a, b parameters)
- Custom function registration
- Factory pattern for function creation

### LinguisticDescriptorBuilder Tests

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
- Cache eviction logic
- State change notifications to Control Layer
- Coordinator interface compliance

## Performance Tests

Verify latency targets from ADD Section 8.1:

- Fuzzy logic processing: < 50ms per sensor
- Sensor reading to linguistic description: < 100ms total

## Mocking Strategy

- **Configuration**: Mock Membership Function Library configurations
- **Cache**: In-memory cache for testing caching logic
- **Time**: Mock time for testing TTL expiration

## Test Configuration

Fixtures provide:

- Sample membership function configurations
- Sample sensor values and types
- Expected fuzzy computation results
- Expected linguistic descriptions

## Running Tests

```bash
# All Data Processing tests
pytest tests/test_data_processing/

# Specific component
pytest tests/test_data_processing/test_fuzzy_engine.py

# With coverage
pytest tests/test_data_processing/ --cov=src/data_processing
```
