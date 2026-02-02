# Membership Functions Directory

This directory contains JSON files defining fuzzy membership functions for
different sensor types. Each file configures how numerical sensor values are
mapped to linguistic descriptions.

## File Format

Each JSON file defines membership functions for one sensor type and contains:

- `sensor_type` - Name of the sensor (e.g., "temperature", "humidity")
- `unit` - Measurement unit (e.g., "celsius", "percent")
- `universe_of_discourse` - Min/max valid range for this sensor type
- `confidence_threshold` - Minimum membership degree to include in output
  (typically 0.1)
- `linguistic_variables` - Array of linguistic term definitions with
  function_type and parameters

## Supported Function Types

- `triangular` - Requires parameters: a, b, c
- `trapezoidal` - Requires parameters: a, b, c, d
- `gaussian` - Requires parameters: mean, sigma
- `sigmoid` - Requires parameters: a, b

## Example

```json
{
  "sensor_type": "temperature",
  "unit": "celsius",
  "universe_of_discourse": { "min": -10.0, "max": 50.0 },
  "confidence_threshold": 0.1,
  "linguistic_variables": [
    {
      "term": "cold",
      "function_type": "trapezoidal",
      "parameters": { "a": -10.0, "b": 0.0, "c": 10.0, "d": 15.0 }
    },
    {
      "term": "comfortable",
      "function_type": "triangular",
      "parameters": { "a": 10.0, "b": 20.0, "c": 25.0 }
    },
    {
      "term": "hot",
      "function_type": "trapezoidal",
      "parameters": { "a": 22.0, "b": 27.0, "c": 40.0, "d": 50.0 }
    }
  ]
}
```

## Usage

The Fuzzy Engine (src/data_processing/) loads these files at startup and applies
the membership functions to transform raw sensor values into linguistic
descriptions like "temperature is hot (0.85)" for LLM consumption.
