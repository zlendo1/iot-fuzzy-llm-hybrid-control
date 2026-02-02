# Source Directory

This directory contains all Python source code for the Fuzzy-LLM Hybrid IoT
Management System.

## Architecture

The source code follows the strict layered architecture defined in the ADD:

```
User Interface Layer        →  interfaces/
Configuration & Management  →  configuration/
Control & Reasoning         →  control_reasoning/
Data Processing            →  data_processing/
Device Interface           →  device_interface/
```

## Entry Point

- `main.py` - Application entry point that initializes the System Orchestrator
  and starts the system

## Layer Organization

Each layer contains:

- A **coordinator** component (the main interface to adjacent layers)
- Internal components that perform specialized work
- Communication flows exclusively through coordinators (per DD-01)

## Design Principles

- **Privacy by Design**: All data processing remains on-device
- **Fail-Safe Operation**: Default to safe states on component failure
- **Transparency**: All processing steps are logged and inspectable
- **Resource Efficiency**: Optimized for edge constraints with caching and lazy
  loading
- **Configurability**: Behavior driven by JSON configuration

## Technology Stack

- Python 3.9+
- paho-mqtt (MQTT client)
- requests (HTTP client for Ollama)
- numpy (numerical computation)
- jsonschema (configuration validation)
- flask (optional web UI)
- pytest (testing framework)

## Import Structure

Components within a layer communicate freely, but inter-layer communication only
goes through the designated coordinator for that layer. For example:

- Device Interface Layer components can talk to each other
- But only MQTCommunicationManager (coordinator) can talk to
  FuzzyProcessingPipeline (coordinator above it)

## Testing

Unit tests are located in the `tests/` directory, mirroring this structure for
clear test-to-source mapping.
