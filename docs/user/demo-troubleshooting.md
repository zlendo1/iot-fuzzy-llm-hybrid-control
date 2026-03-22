# Demo Troubleshooting Guide

This document covers common issues that may occur during the demo and their
solutions.

## Quick Diagnostics

```bash
# Check all services
make ps

# View recent logs
make logs | tail -100

# Check specific service
docker-compose logs app --tail 50
docker-compose logs mosquitto --tail 50
docker-compose logs ollama --tail 50
```

## Common Issues

### 1. Services Not Starting

**Symptom**: `make up` fails or containers exit immediately

**Causes & Solutions**:

| Cause                    | Solution                                         |
| ------------------------ | ------------------------------------------------ |
| Port already in use      | `lsof -i :1883` / `lsof -i :11434`, kill proc    |
| Docker not running       | Start Docker Desktop or `systemctl start docker` |
| Insufficient memory      | Close other apps, need ~4GB free                 |
| Previous state corrupted | `make clean-docker && make build`                |

```bash
# Full reset
make down
make clean-docker
make build
make up
```

### 2. MQTT Connection Failed

**Symptom**: "Connection refused" or "Unable to connect to MQTT broker"

**Causes & Solutions**:

| Cause               | Solution                                         |
| ------------------- | ------------------------------------------------ |
| Mosquitto not ready | Wait 10s after startup, check `make ps`          |
| Wrong hostname      | Use `localhost` for local, `mosquitto` in Docker |
| Auth failed         | Check mqtt_config.json credentials               |
| Firewall blocking   | Allow port 1883                                  |

```bash
# Test MQTT connectivity
mosquitto_pub -h localhost -p 1883 -t test -m "hello"
mosquitto_sub -h localhost -p 1883 -t test

# Check Mosquitto logs
docker-compose logs mosquitto
```

### 3. LLM Not Responding

**Symptom**: Rules not triggering, "LLM timeout" errors

**Causes & Solutions**:

| Cause             | Solution                                     |
| ----------------- | -------------------------------------------- |
| Model not pulled  | `make pull-model`                            |
| Ollama overloaded | Wait, or increase timeout in llm_config.json |
| Insufficient RAM  | Close other apps, need ~2GB for model        |
| Wrong model name  | Verify model name in llm_config.json         |

```bash
# Check Ollama status
curl http://localhost:11434/

# List available models
curl http://localhost:11434/api/tags

# Pull model manually
docker-compose exec ollama ollama pull qwen3:0.6b

# Test inference directly
curl http://localhost:11434/api/generate -d '{
  "model": "qwen3:0.6b",
  "prompt": "Say hello",
  "stream": false
}'
```

### 4. Rules Not Triggering

**Symptom**: Sensor data published but no commands generated

**Causes & Solutions**:

| Cause               | Solution                                              |
| ------------------- | ----------------------------------------------------- |
| Rules disabled      | `python3 -m src.interfaces rule list` to check status |
| Wrong sensor topic  | Verify topic matches devices.json                     |
| Fuzzy threshold     | Value may not meet membership threshold               |
| LLM parsing failure | Check logs for response parsing errors                |

```bash
# Verify rules are loaded
python3 -m src.interfaces rule list
```

### 5. Commands Not Published

**Symptom**: LLM generates action but no MQTT message sent

**Causes & Solutions**:

| Cause               | Solution                                     |
| ------------------- | -------------------------------------------- |
| Validation failed   | Check logs for "validation failed" messages  |
| Device not found    | Verify device_id in devices.json             |
| Rate limited        | Wait 1 minute, check rate limit settings     |
| Command not allowed | Check safety whitelist in system_config.json |

```bash
# Subscribe to all command topics
mosquitto_sub -h localhost -t 'home/+/+/set' -v

# Check command validation logs
grep -i "validation" logs/system.log
```

### 6. Slow Performance

**Symptom**: End-to-end latency > 5 seconds

**Causes & Solutions**:

| Cause           | Solution                                       |
| --------------- | ---------------------------------------------- |
| Large model     | Use smaller model (qwen3:0.6b)                 |
| CPU throttling  | Check CPU usage, close background apps         |
| Memory swapping | Check RAM usage, increase available memory     |
| Cold model      | First inference is slow, subsequent are faster |

```bash
# Monitor resource usage
docker stats

# Warm up the model
curl http://localhost:11434/api/generate -d '{
  "model": "qwen3:0.6b",
  "prompt": "test",
  "stream": false
}'
```

### 7. Configuration Errors

**Symptom**: System won't start, "Configuration error" messages

**Causes & Solutions**:

| Cause             | Solution                                         |
| ----------------- | ------------------------------------------------ |
| Invalid JSON      | Validate JSON syntax: `python -m json.tool file` |
| Schema violation  | Run `python3 -m src.interfaces config validate`  |
| Missing file      | Check all required configs exist                 |
| Permission denied | Check file permissions: `ls -la config/`         |

```bash
# Validate all configs
python3 -m src.interfaces config validate
```

### 8. Membership Function Issues

**Symptom**: Unexpected linguistic descriptions

**Causes & Solutions**:

| Cause              | Solution                                  |
| ------------------ | ----------------------------------------- |
| Wrong value range  | Check universe_of_discourse in MF config  |
| Overlapping terms  | Review term parameters, adjust boundaries |
| Threshold too high | Lower confidence_threshold (default 0.1)  |

```bash
# Test fuzzification manually
python -c "
from src.data_processing.fuzzy_engine import FuzzyEngine
from pathlib import Path

engine = FuzzyEngine()
engine.load_configs_from_directory(Path('config/membership_functions'))
result = engine.fuzzify('temperature', 32.0)
print(result)
"
```

### 9. gRPC Connection Issues

**Symptom**: "Connection refused" on port 50051, "gRPC server unavailable"

**Causes & Solutions**:

| Cause                      | Solution                                        |
| -------------------------- | ----------------------------------------------- |
| System not started         | Run `iot-fuzzy-llm start` or `make up`          |
| App container unresponsive | Check status with `make ps`, restart if needed  |
| Wrong host/port            | Verify with `--grpc-host` and `--grpc-port`     |
| Firewall blocking 50051    | Ensure port 50051 is open for local connections |

```bash
# Check if port 50051 is listening
netstat -tlnp | grep 50051

# Verify app container health
make ps

# Test connection with verbose output
iot-fuzzy-llm -v status
```

## Log Analysis

### Finding Errors

```bash
# All errors
grep -i "error" logs/system.log

# Recent errors
tail -1000 logs/system.log | grep -i "error"

# Rule evaluation issues
grep "rule_evaluation" logs/system.log

# LLM responses
grep "llm_response" logs/system.log
```

### Timing Analysis

```bash
# Find slow operations
grep "elapsed" logs/system.log | sort -t'=' -k2 -rn | head -20

# LLM latency
grep "inference_time" logs/system.log
```

## Recovery Procedures

### Full System Reset

```bash
make down
make clean-docker
rm -rf logs/*
rm rules/active_rules.json
make build
make up
make pull-model
```

### Partial Reset (Keep Model)

```bash
make down
rm -rf logs/*
make up
```

### Rule Reset Only

```bash
rm rules/active_rules.json
# Rules will start empty on next startup
```

## Getting Help

1. **Check logs first**: Most issues are visible in system logs
2. **Verify prerequisites**: Docker, Python 3.9+, sufficient RAM
3. **Test components individually**: MQTT, Ollama, then full system
4. **Simplify the scenario**: Test with single sensor/rule first

## Environment Variables

| Variable    | Default   | Description                 |
| ----------- | --------- | --------------------------- |
| LOG_LEVEL   | INFO      | DEBUG, INFO, WARNING, ERROR |
| MQTT_HOST   | localhost | MQTT broker hostname        |
| OLLAMA_HOST | localhost | Ollama service hostname     |

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
make restart
```
