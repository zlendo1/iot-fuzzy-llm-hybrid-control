# Bin Directory

This directory is reserved for startup and setup scripts for the Fuzzy-LLM
Hybrid IoT Management System.

## Purpose

Will contain executable scripts for:

- System startup and shutdown
- Initial installation and dependency setup
- Service management
- Development/production mode selection

## Current Status

This directory is currently empty. The system can be started using:

```bash
# Via Python module
python -m src.main

# Via Docker
docker compose up -d

# Via Make
make run
```

## Planned Scripts

Future implementations may include:

- `start.sh` - Main system startup script
- `stop.sh` - Graceful system shutdown
- `setup.sh` - Initial installation and configuration
- `install_dependencies.sh` - Install Python dependencies
- `install_ollama.sh` - Setup Ollama service and download models
- `install_mosquitto.sh` - Setup MQTT broker
- `status.sh` - Check system status and health

## Integration with Systemd

These scripts can be integrated with system service managers (systemd, init.d)
for automatic startup on boot and proper daemonization.
