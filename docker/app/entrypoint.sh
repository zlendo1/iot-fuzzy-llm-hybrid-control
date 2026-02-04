#!/bin/bash
set -e

handle_signal() {
    echo "Received shutdown signal, gracefully stopping..."
    kill -TERM "$APP_PID" 2>/dev/null
    wait "$APP_PID"
    exit 0
}

trap handle_signal SIGTERM SIGINT

echo "Starting IoT Fuzzy-LLM application..."
echo "MQTT Broker: ${MQTT_HOST:-mosquitto}:${MQTT_PORT:-1883}"
echo "Ollama Service: ${OLLAMA_HOST:-ollama}:${OLLAMA_PORT:-11434}"

exec "$@"
