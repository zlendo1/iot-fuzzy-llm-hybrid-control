# Configuration Directory

This directory contains all configuration files for the Fuzzy-LLM Hybrid IoT
Management System. All configuration files are in JSON format as specified in
the Architecture Design Document (ADD).

## Structure

- `membership_functions/` - JSON files defining fuzzy membership functions for
  each sensor type
- `devices.json` - Sensor and actuator device definitions
- `mqtt_config.json` - MQTT broker connection settings
- `llm_config.json` - Ollama LLM service configuration
- `system_config.json` - System-wide settings including processing, logging, and
  safety parameters
- `prompt_template.txt` - Template for constructing LLM prompts

## Configuration Principles

- All configuration is file-based with JSON schemas for validation
- Configuration Manager loads these files at system startup
- Changes to configuration files trigger automatic reload (optional)
- Timestamped backups are created automatically before modifications
- No database required - files are sufficient for the expected data scale

## Design Decision

As noted in DD-04 of the ADD, JSON was chosen because it is:

- Human-readable and universally supported
- Schema-validatable
- Does not require code execution (unlike Python config files)
