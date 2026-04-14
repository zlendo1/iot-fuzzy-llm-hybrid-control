# Problem Specification and Recommendations

**IoT Fuzzy-LLM Hybrid Control System — Zijad Lenda's Master Thesis**

Review date: April 7, 2026

## 1. Overview

During testing of the system's Docker deployment, several issues of varying
severity were identified. Some were resolved during the review, while others
require intervention by the student. This document categorizes problems by
status (resolved / open) and severity (critical / significant / improvement).

## 2. Resolved Problems

The following problems were identified and resolved during testing. The student
should review and understand the changes made.

### 2.1 Protobuf File Generation in Dockerfile

**Severity:** Critical — system completely non-functional

**File:** `docker/app/Dockerfile`

**Problem:** Generated protobuf files (`*_pb2.py`, `*_pb2_grpc.py`) were
excluded from the git repository via `.gitignore`, and the Dockerfile did not
have a step to generate them during the build. As a result, the gRPC server in
the app container could not start any service, the web container could not
establish a connection, and Streamlit displayed "Application is not running".

**Solution:** Added a step in the Dockerfile that installs `grpcio-tools` in the
builder stage, compiles `.proto` files, runs the `fix_protobuf_imports.py`
script, and copies the generated files into the final image.

**Recommendation:** Consider adding protobuf generation to
`docker/ollama/Dockerfile` as well, or creating a separate build stage shared
between services. Alternatively, remove `*_pb2*.py` from `.gitignore` and commit
the generated files.

### 2.2 Host Configuration for Docker Network

**Severity:** Critical — MQTT and Ollama connection impossible

**Files:** `config/mqtt_config.json`, `config/llm_config.json`

**Problem:** Config files had hardcoded `"host": "localhost"`. In a Docker
environment, `localhost` refers to the container itself, not other services in
the network. Environment variables (`MQTT_HOST`, `OLLAMA_HOST`) set in
`docker-compose.yml` are not used because the code reads directly from JSON
configuration.

**Temporary solution:** Replaced `"localhost"` with `"mosquitto"` / `"ollama"`
in the config files.

**Recommendation for permanent solution:** Modify `MQTTClientConfig.from_dict()`
and `OllamaConnectionConfig.from_dict()` so that environment variables take
priority over JSON configuration. Note: `OllamaConnectionConfig` already
implements this pattern, but `MQTTClientConfig` does not.

### 2.3 Qwen3 Thinking Mode in LLM Responses

**Severity:** Critical — rules are not evaluated

**Files:** `src/control_reasoning/ollama_client.py`,
`src/control_reasoning/response_parser.py`

**Problem:** The Qwen3 model uses "thinking mode" by default — it emits
`<think>...</think>` blocks before the response. `ResponseParser` was not aware
of this format, so the entire response (including the thinking block) was
treated as text for parsing, resulting in "Malformed LLM response" warnings and
a complete absence of actions.

**Solution:** (a) Added `"think": False` parameter to the Ollama API payload to
disable thinking mode; (b) Added a `_strip_thinking()` function as a safety net
to remove residual `<think>` blocks.

**Recommendation:** Add unit tests for `ResponseParser` covering responses with
thinking blocks, empty responses, and responses without `device_id`.

### 2.4 Imprecise LLM Responses (Missing device_id)

**Severity:** Significant — commands are not generated correctly

**File:** `config/prompt_template.txt`

**Problem:** The original prompt template did not specify the response format
precisely enough. The small model (`qwen3:0.6b`) generated responses like
`ACTION: turn_on, temperature=22` (without `device_id`) instead of the expected
`ACTION: ac_living_room, turn_on, temperature=22`.

**Solution:** The prompt template was expanded with an explicit list of
available devices and their `device_id`s, more examples, and clearer
instructions that `device_id` is mandatory.

**Recommendation:** Consider dynamically generating the device list in the
prompt from the `devices.json` registry, instead of hardcoding it in the
template.

## 3. Open Problems

### 3.1 Actuators Always Displayed as Offline

**Severity:** Significant

**Problem:** `DeviceMonitor.record_activity()` is called exclusively in
`MQTTCommunicationManager._handle_sensor_message()`, meaning only for sensors
that send MQTT messages. Actuators never send messages back to the system, so
their status remains `UNKNOWN`/`OFFLINE`.

**Possible approaches for resolution:**

- Subscribe to actuator state topics (e.g., `home/living_room/ac/state`) and
  call `record_activity()` when an actuator publishes its state.
- Consider an actuator `ONLINE` as soon as a command has been successfully sent
  to it via MQTT — call `record_activity()` in the `send_command()` method.
- Introduce a special status for actuators (e.g., `COMMANDED`) indicating that
  the device received a command but has not confirmed its state.

### 3.2 Missing Actuator State Display in Web Interface

**Severity:** Significant

**Problem:** The Devices page only displays online/offline status, type,
location, and a button for sending commands. There is no indication of the
current actuator state — for example, whether the AC is on, at what temperature,
whether the light is on, what the blinds position is, etc.

**Possible approaches for resolution:**

- Add state tracking for actuators — when sending a command, remember the last
  command and display it in the UI ("Last command: set_temperature=22").
- If a feedback loop with state topics is implemented (point 3.1), display the
  confirmed actuator state.
- On the Devices page, display input fields for actuators (e.g., slider for
  temperature, toggle for on/off) instead of a simple dropdown.

### 3.3 Missing Device Simulator

**Severity:** Improvement

**Problem:** The system has no built-in simulator for testing without real
devices. During the review, a script `scripts/simulate_devices.py` was created
that simulates all sensors from the configuration and responds to actuator
commands.

**Recommendations:**

- Integrate the simulator as an optional Docker service in `docker-compose.yml`
  (e.g., a simulator profile started with
  `docker compose --profile simulator up`).
- The simulator should publish actuator states on the appropriate state topics
  after receiving a command, thereby closing the feedback loop.
- Consider adding configurable scenarios (e.g., "summer morning", "winter
  night") for demonstrating different rule reactions.

### 3.4 MQTTClientConfig Does Not Use Environment Variables

**Severity:** Significant

**Problem:** `OllamaConnectionConfig.from_dict()` correctly reads `OLLAMA_HOST`
and `OLLAMA_PORT` environment variables with priority over JSON configuration.
However, `MQTTClientConfig.from_dict()` does not — it always reads from the JSON
file. This means the same configuration cannot be used for both local
development (`localhost`) and Docker (`mosquitto`) without manually editing the
file.

**Recommendation:** Apply the same pattern as in `OllamaConnectionConfig`:
`host = os.environ.get("MQTT_HOST") or config_data["broker"]["host"]`.

### 3.5 Trivial Docker Healthcheck for App Container

**Severity:** Improvement

**Problem:** The healthcheck for the app container is
`python -c "import sys; sys.exit(0)"`, which always returns success even when
the gRPC server is not running or the application is in an error state. This
masks real problems — during testing, the container was "healthy" even though
the gRPC server was not working.

**Recommendation:** Replace with a meaningful healthcheck, for example a gRPC
health check or HTTP status endpoint:
`python -c "import grpc; ch = grpc.insecure_channel('localhost:50051'); grpc.channel_ready_future(ch).result(timeout=5)"`.

### 3.6 Small LLM Model Reliability (qwen3:0.6b)

**Severity:** Significant

**Problem:** The 0.6B parameter model occasionally generates responses that are
not in the expected format — it omits `device_id`, adds explanations after the
`ACTION` line, or incorrectly interprets rule conditions. Even with the improved
prompt template, small models are inherently less reliable for structured
responses.

**Recommendations:**

- Add retry logic in `RuleProcessingPipeline._evaluate_single_rule()` — if the
  response is `MALFORMED`, retry (max 2–3 times).
- Implement a fallback parser that attempts to extract `device_id` from the rule
  text if the LLM omits it from the response.
- Consider using a larger model (e.g., `qwen3:1.7b`) if hardware resources allow
  — configuration for a fallback model already exists in `llm_config.json`.
- Add logging of raw LLM responses (at `DEBUG` level) for easier problem
  diagnosis.

## 4. Summary

| #   | Problem                                  | Severity    | Status    |
| --- | ---------------------------------------- | ----------- | --------- |
| 2.1 | Protobuf files missing from Docker image | Critical    | Resolved  |
| 2.2 | Hardcoded localhost in config files      | Critical    | Temporary |
| 2.3 | Qwen3 thinking mode breaks parser        | Critical    | Resolved  |
| 2.4 | LLM omits device_id from responses       | Significant | Resolved  |
| 3.1 | Actuators always offline                 | Significant | Open      |
| 3.2 | No actuator state display in UI          | Significant | Open      |
| 3.3 | Missing device simulator                 | Improvement | Open      |
| 3.4 | MQTT config doesn't use env variables    | Significant | Open      |
| 3.5 | Trivial Docker healthcheck               | Improvement | Open      |
| 3.6 | Small LLM model reliability              | Significant | Open      |

**Note:** Problems marked as "Temporary" have a workaround but require a
permanent solution in the code. Changes marked as "Resolved" have been applied
directly to the project source files and need to be committed to the repository.
