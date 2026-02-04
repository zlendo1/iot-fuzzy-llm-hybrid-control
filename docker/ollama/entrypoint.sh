#!/bin/bash
set -e

MODEL_NAME="${OLLAMA_MODEL:-qwen3:0.6b}"
PULL_ON_START="${OLLAMA_PULL_ON_START:-true}"

/bin/ollama serve &
OLLAMA_PID=$!

sleep 5

wait_for_ollama() {
    local max_attempts=30
    local attempt=0
    while [ $attempt -lt $max_attempts ]; do
        if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 1
    done
    return 1
}

if wait_for_ollama; then
    echo "Ollama service is ready"
    
    if [ "$PULL_ON_START" = "true" ]; then
        if ! ollama list | grep -q "$MODEL_NAME"; then
            echo "Pulling model: $MODEL_NAME"
            ollama pull "$MODEL_NAME"
            echo "Model $MODEL_NAME pulled successfully"
        else
            echo "Model $MODEL_NAME already exists"
        fi
    fi
else
    echo "ERROR: Ollama service failed to start"
    exit 1
fi

wait $OLLAMA_PID
