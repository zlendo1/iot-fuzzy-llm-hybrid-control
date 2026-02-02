# Bin Directory

This directory contains startup and setup scripts for the Fuzzy-LLM Hybrid IoT
Management System.

## Purpose

Provides executable scripts for:

- System startup and shutdown
- Initial installation and dependency setup
- Service management
- Development/production mode selection

## Example Scripts

- `start.sh` - Main system startup script
- `stop.sh` - Graceful system shutdown
- `setup.sh` - Initial installation and configuration
- `install_dependencies.sh` - Install Python dependencies
- `install_ollama.sh` - Setup Ollama service and download models
- `install_mosquitto.sh` - Setup MQTT broker
- `status.sh` - Check system status and health

## Usage

Scripts should be executable and can be called directly from the command line:

```bash
./bin/setup.sh
./bin/start.sh
```

## Integration with Systemd

These scripts can be integrated with system service managers (systemd, init.d)
for automatic startup on boot and proper daemonization.
