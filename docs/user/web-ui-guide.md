# Web UI Guide

## Fuzzy-LLM Hybrid IoT Management System — Streamlit Web Interface

**Document Status:** Active\
**Last Updated:** 2026-03-17

This guide covers how to use the browser-based web interface for the Fuzzy-LLM
Hybrid IoT Management System. The web UI is built with Streamlit and provides a
visual alternative to the command-line interface for monitoring, configuring,
and controlling the system.

______________________________________________________________________

## Table of Contents

1. [Overview](#1-overview)
2. [Starting the Web UI](#2-starting-the-web-ui)
3. [Navigation](#3-navigation)
4. [Pages](#4-pages)
   - [4.1 Dashboard](#41-dashboard)
   - [4.2 Devices](#42-devices)
   - [4.3 Rules](#43-rules)
   - [4.4 Config](#44-config)
   - [4.5 Membership Editor](#45-membership-editor)
   - [4.6 Logs](#46-logs)
   - [4.7 System Control](#47-system-control)
5. [Common Workflows](#5-common-workflows)
6. [CLI vs Web UI](#6-cli-vs-web-ui)
7. [Troubleshooting](#7-troubleshooting)

______________________________________________________________________

## 1. Overview

The Web UI is a **Streamlit-based browser dashboard** that runs alongside the
IoT management system. It is an additional interface — not a replacement for the
CLI. Both can be used simultaneously.

### When to Use the Web UI

| Situation                             | Recommended Interface |
| ------------------------------------- | --------------------- |
| Monitoring live sensor readings       | Web UI                |
| Quick rule add/enable/disable         | Web UI                |
| Editing JSON config with validation   | Web UI                |
| Adjusting fuzzy membership functions  | Web UI                |
| Scripting, automation, SSH sessions   | CLI                   |
| JSON output for external tools        | CLI                   |
| Headless edge-device deployments      | CLI                   |
| Complex rule queries with tag filters | CLI                   |

### Key Capabilities

- **Live sensor monitoring** — auto-refreshing metric tiles for all connected
  sensors
- **Device registry** — browse all registered sensors and actuators with
  filtering
- **Rule management** — add, enable/disable, and delete natural language rules
- **Configuration editing** — edit `devices.json`, `mqtt_config.json`, and
  `llm_config.json` directly in the browser
- **Membership function editing** — edit fuzzy membership functions per sensor
  type
- **Log viewer** — browse JSON log files with category and level filters
- **System control** — inspect system status and initiate shutdown

> [!NOTE]
> The Web UI connects to a running system instance via the **bridge** module. If
> the system has not been started, most pages will show a warning and limited
> functionality. Start the system first with `python -m src.main` or
> `docker compose up -d`.

______________________________________________________________________

## 2. Starting the Web UI

### Prerequisites

Before launching the Web UI, ensure:

1. The system is installed (see [Installation Guide](installation-guide.md))
2. Configuration files are in place (`config/` directory)
3. The IoT management system is running (see [User Guide](user-guide.md))

### Launch Commands

Run the following from the **project root directory**:

```bash
# Standard launch — opens browser at http://localhost:8501
streamlit run src/interfaces/web/streamlit_app.py

# Custom port
streamlit run src/interfaces/web/streamlit_app.py --server.port 8502

# Headless — do not auto-open a browser window
streamlit run src/interfaces/web/streamlit_app.py --server.headless true

# Accessible from other machines on the network
streamlit run src/interfaces/web/streamlit_app.py --server.address 0.0.0.0
```

### Docker

When using Docker Compose, the web UI is not started automatically. Run it
separately after the other services are up:

```bash
# Start core services
docker compose up -d

# Start the Web UI (from host, pointing at running system)
streamlit run src/interfaces/web/streamlit_app.py
```

### Accessing the UI

Once started, open your browser at:

```
http://localhost:8501
```

You should see the Dashboard page with the left-side navigation panel.

______________________________________________________________________

## 3. Navigation

The Web UI uses a **sidebar navigation** panel on the left side of the browser
window. It lists all seven pages with their icons.

| Page              | Icon | Purpose                          |
| ----------------- | ---- | -------------------------------- |
| Dashboard         | 📊   | Live sensor readings overview    |
| Devices           | 🖥️   | Device registry browser          |
| Rules             | 📋   | Natural language rule management |
| Config            | ⚙️   | JSON configuration editor        |
| Membership Editor | ƒ    | Fuzzy membership function editor |
| Logs              | 📄   | Log file browser and search      |
| System Control    | 🎚️   | System status and shutdown       |

Click any page name in the sidebar to navigate to it. The sidebar can be
collapsed by clicking the `×` button at the top of the panel.

> [!NOTE]
> Each page checks that the system bridge is initialized before rendering its
> content. If you see a red error banner, start the IoT system first.

______________________________________________________________________

## 4. Pages

### 4.1 Dashboard

**Purpose:** Real-time overview of all sensor readings from connected IoT
devices.

> 📸 _Screenshot: Dashboard page showing metric tiles for temperature, humidity,
> and motion sensors with Auto-refresh toggle enabled._

#### Key Features

- **Auto-refresh toggle** — When enabled, the sensor tiles refresh automatically
  every second without a full page reload.
- **Zone filter** — Narrow the display to sensors in a specific physical zone
  (e.g., `living_room`, `bedroom`).
- **Type filter** — Show only sensors of a specific class: `temperature`,
  `humidity`, `light_level`, or `motion`.
- **Metric tiles** — Each sensor is displayed as a labelled metric card showing
  the latest value (with unit) and the timestamp of the last update.
- **No-data state** — If no readings have arrived yet, an info banner prompts
  you to start the system.

#### Reading the Display

Each sensor tile shows:

- **Label**: the sensor ID (e.g., `temp_living_room`)
- **Value**: the most recent reading with its unit (e.g., `23.50 °C`)
- **Caption**: timestamp of when the reading was last received

#### Common Workflow

1. Navigate to **Dashboard** in the sidebar.
2. Enable **Auto-refresh (1s)** to watch live data.
3. Use the **zone** or **type** filters if you have many sensors.
4. Watch metric tiles update in real time as MQTT messages arrive.

______________________________________________________________________

### 4.2 Devices

**Purpose:** Browse and inspect all devices registered in the system, including
both sensors and actuators.

> 📸 _Screenshot: Devices page showing type and zone filter dropdowns with a list
> of expanded device cards._

#### Key Features

- **Type filter** — Show all devices, sensors only, or actuators only.
- **Zone filter** — Filter by physical location. Options are populated
  dynamically from the device registry.
- **Device count** — A count badge shows how many devices match the current
  filter out of the total registered (`Showing X of Y devices`).
- **Expandable device cards** — Each device is shown as a collapsed card. Click
  to expand and see:
  - **Type** (`sensor` or `actuator`)
  - **Class** (e.g., `temperature`, `thermostat`, `light`)
  - **Zone** — the physical location
  - **Status badge** — connectivity status indicator

#### Common Workflow

1. Navigate to **Devices**.
2. Leave filters at `All` to see every registered device.
3. Click a device card to expand it and inspect its type, class, and zone.
4. Use **Filter by type → sensor** to see only sensors, then check their
   classes.

> [!NOTE]
> The Devices page requires the system bridge to be initialized. If the device
> registry is unavailable, a warning message is shown. Start the system with
> `python -m src.main` first.

______________________________________________________________________

### 4.3 Rules

**Purpose:** Manage natural language automation rules — add new rules, toggle
them on or off, and delete rules that are no longer needed.

> 📸 _Screenshot: Rules page with the "Add Rule" text input at the top and a list
> of existing rules in collapsible cards below._

#### Key Features

- **Add Rule form** — A text input and button at the top of the page. Type a
  natural language rule and click **Add Rule** to save it. A short unique ID is
  generated automatically.
- **Rule list** — All existing rules are shown as expandable cards, each
  displaying the rule ID and rule text.
- **Enable / Disable toggle** — Each rule card has an **Enabled** toggle.
  Flipping it immediately persists the change.
- **Delete button** — Each rule card has a **Delete** button. Clicking it
  removes the rule immediately (no confirmation dialog).

#### Rule Text Format

Rules are plain English sentences describing a condition and an action:

```
If the living room temperature is hot, turn on the air conditioner
When motion is detected in the hallway and the light level is dark, turn on the hallway light
If bedroom humidity is high, activate the ventilation fan
```

The LLM interprets these rules at evaluation time, so phrasing is flexible.

#### Common Workflow — Add a Rule

1. Navigate to **Rules**.
2. Type your rule in the **Rule text** field (e.g.,
   `If bedroom is cold, turn on heater`).
3. Click **Add Rule**. A success message shows the generated rule ID.
4. The new rule appears in the list below with **Enabled** set to `on`.

#### Common Workflow — Disable a Rule Temporarily

1. Navigate to **Rules**.
2. Find the rule in the list and expand its card.
3. Flip the **Enabled** toggle to off.
4. The rule is preserved but will be skipped during evaluation.

______________________________________________________________________

### 4.4 Config

**Purpose:** Edit the three core JSON configuration files directly in the
browser without leaving the UI.

> 📸 _Screenshot: Config page showing three tabs (Devices, MQTT, LLM) with a JSON
> text area and Save button._

#### Key Features

- **Three tabs** — Devices, MQTT, and LLM. Each tab is independent.
- **JSON text area** — The current configuration is loaded and displayed as
  formatted JSON. Edit it directly.
- **Save button** — Validates the JSON syntax and writes the file. A success or
  error message is shown.
- **Backup on save** — The system saves a backup of the previous configuration
  before overwriting.
- **Syntax validation** — If the JSON is malformed, an error message shows the
  exact parse error and the save is aborted.

#### Configuration Files

| Tab     | File                      | Contains                                               |
| ------- | ------------------------- | ------------------------------------------------------ |
| Devices | `config/devices.json`     | Sensor and actuator definitions, MQTT topics           |
| MQTT    | `config/mqtt_config.json` | Broker address, port, authentication, QoS settings     |
| LLM     | `config/llm_config.json`  | Ollama model name, base URL, timeout, context settings |

#### Common Workflow — Update MQTT Broker Address

1. Navigate to **Config** and click the **MQTT** tab.
2. Locate the `"host"` field in the JSON and change the value.
3. Click **Save mqtt**.
4. Restart the system for the change to take effect
   (`iot-fuzzy-llm stop && iot-fuzzy-llm start`).

> [!WARNING]
> Saving an invalid device configuration can prevent the system from starting.
> Always keep a backup or use version control before making significant changes.

______________________________________________________________________

### 4.5 Membership Editor

**Purpose:** Inspect and edit the fuzzy membership function definitions that
control how raw sensor values are mapped to linguistic terms like "hot",
"comfortable", or "cold".

> 📸 _Screenshot: Membership Editor showing the temperature sensor selected, a
> JSON viewer displaying the membership function definitions, and a text area
> for editing._

#### Key Features

- **Sensor type selector** — Choose from `temperature`, `humidity`,
  `light_level`, or `motion`.
- **JSON viewer** — The current membership function file is rendered as a
  structured JSON tree for easy reading.
- **Edit text area** — The same data is shown below as editable text. Modify the
  parameters directly.
- **Save button** — Validates the JSON and writes to
  `config/membership_functions/{sensor_type}.json`.

#### Membership Function Structure

Each file defines linguistic terms for a sensor type. For example, for
temperature:

```json
{
  "cold": { "type": "trapezoidal", "params": [0, 0, 15, 20] },
  "comfortable": { "type": "triangular", "params": [15, 22, 28] },
  "hot": { "type": "trapezoidal", "params": [25, 30, 50, 50] }
}
```

- **cold**, **comfortable**, **hot** — the linguistic terms the LLM uses in
  rules
- **type** — the shape of the membership function (`triangular`, `trapezoidal`,
  `gaussian`)
- **params** — the boundary points for the function shape

#### Common Workflow — Adjust Temperature Thresholds

1. Navigate to **Membership Editor**.
2. Select **temperature** from the sensor type dropdown.
3. Review the current thresholds in the JSON viewer.
4. In the edit area, change the `params` values for `"hot"` if your environment
   runs warmer.
5. Click **Save**.
6. The fuzzy engine will use the new thresholds on the next sensor reading.

> [!NOTE]
> Changes take effect immediately for new sensor readings. The running system
> does not need to be restarted.

______________________________________________________________________

### 4.6 Logs

**Purpose:** Browse and search the system's JSON log files to diagnose issues,
monitor activity, and audit rule evaluations.

> 📸 _Screenshot: Logs page with category dropdown set to "rules", level filter
> set to "INFO", search box, and a dataframe table of log entries._

#### Key Features

- **Category selector** — Choose which log file to read:

  | Category   | File                 | Contains                            |
  | ---------- | -------------------- | ----------------------------------- |
  | `system`   | `logs/system.json`   | General system events and lifecycle |
  | `commands` | `logs/commands.json` | Actuator commands sent to devices   |
  | `sensors`  | `logs/sensors.json`  | Sensor readings received via MQTT   |
  | `errors`   | `logs/errors.json`   | Error messages from all components  |
  | `rules`    | `logs/rules.json`    | Rule evaluations and LLM responses  |

- **Level filter** — Show entries at or above a severity level: `ALL`, `DEBUG`,
  `INFO`, `WARNING`, `ERROR`, `CRITICAL`.

- **Search box** — Filter by keyword in the log message field. Case-insensitive.

- **Refresh button** — Re-reads the log file from disk.

- **Entry count** — Shows how many entries match the current filter.

- **Dataframe table** — Displays log entries in a scrollable table with columns:
  `timestamp`, `level`, `logger`, `message`.

#### Common Workflow — Find Rule Evaluation Errors

1. Navigate to **Logs**.
2. Select **rules** from the category dropdown.
3. Set level filter to **ERROR**.
4. Click **Refresh**.
5. Browse the table for failed rule evaluations or LLM parsing errors.

#### Common Workflow — Search for a Specific Device

1. Navigate to **Logs**.
2. Select **sensors** or **commands** category.
3. Type the device ID (e.g., `temp_living_room`) in the **Search** box.
4. The table updates to show only entries mentioning that device.

______________________________________________________________________

### 4.7 System Control

**Purpose:** Inspect the full system status — state, readiness, component
availability, and initialization steps — and optionally shut the system down.

> 📸 _Screenshot: System Control page showing State: RUNNING, Ready: True,
> component checklist, collapsible initialization steps, and the Shutdown System
> button with confirmation checkbox._

#### Key Features

- **State and readiness** — Displays the current orchestrator state (e.g.,
  `RUNNING`, `INITIALIZING`, `STOPPED`) and whether the system is ready to
  process sensor readings.
- **Component checklist** — A ✅/❌ list of all system components (e.g.,
  `config_manager`, `device_registry`, `fuzzy_engine`, `ollama_client`,
  `mqtt_client`) and their availability.
- **Initialization steps** — An expandable panel listing all 10 initialization
  steps with completion status and any error messages.
- **Shutdown button** — Shuts down the running IoT management system. Requires
  checking the **Confirm shutdown** checkbox first to prevent accidental
  shutdown.

#### Interpreting System State

| State          | Meaning                                                    |
| -------------- | ---------------------------------------------------------- |
| `INITIALIZING` | System is starting up, steps are completing in sequence    |
| `RUNNING`      | System is fully operational, processing sensor readings    |
| `STOPPED`      | System is not running; start it with `iot-fuzzy-llm start` |
| `ERROR`        | A component failed during initialization                   |

#### Common Workflow — Verify System is Healthy

1. Navigate to **System Control**.
2. Check that **State** shows `RUNNING` and **Ready** shows `True`.
3. Expand **Initialization Steps** to confirm all 10 steps completed (✅).
4. Check the component list — all components should show ✅.

#### Common Workflow — Shutdown the System

1. Navigate to **System Control**.
2. Check the **Confirm shutdown** checkbox.
3. Click **Shutdown System**.
4. A success message confirms the shutdown.

> [!WARNING]
> Shutting down the system stops all MQTT subscriptions, sensor processing, and
> rule evaluation. Devices will no longer receive automated commands until the
> system is restarted.

______________________________________________________________________

## 5. Common Workflows

### Initial Setup and Verification

1. Install the system (see [Installation Guide](installation-guide.md)).
2. Start the core system:
   ```bash
   python -m src.main
   # or
   docker compose up -d
   ```
3. Launch the Web UI:
   ```bash
   streamlit run src/interfaces/web/streamlit_app.py
   ```
4. Open `http://localhost:8501` in your browser.
5. Navigate to **System Control** and verify State = `RUNNING`, Ready = `True`.
6. Navigate to **Dashboard** to confirm sensor readings are arriving.

### Adding Your First Automation Rule

1. Navigate to **Rules**.
2. In the **Add Rule** field, type a natural language rule:
   ```
   If the living room temperature is hot and humidity is high, turn on the air conditioner
   ```
3. Click **Add Rule**. Note the generated rule ID in the success message.
4. Scroll down to find your new rule in the list and verify it is **Enabled**.
5. Navigate to **Logs → rules** to watch the rule being evaluated.

### Modifying Fuzzy Thresholds for a New Environment

1. Navigate to **Membership Editor**.
2. Select the sensor type you want to adjust (e.g., `temperature`).
3. Review the current JSON. Note the `params` boundaries for each term.
4. In the edit area, adjust the `params` for the term you want to change:
   - Lower the `"hot"` threshold if your environment is warmer than default.
   - Raise the `"cold"` threshold if your space rarely reaches cold
     temperatures.
5. Click **Save**.
6. Verify changes with the **Dashboard** — the linguistic description logged in
   **Logs → rules** should reflect your updated thresholds.

### Diagnosing Why a Rule Is Not Triggering

1. Navigate to **System Control** — confirm the system is `RUNNING`.
2. Navigate to **Dashboard** — confirm the relevant sensor is reporting
   readings.
3. Navigate to **Rules** — confirm the relevant rule is **Enabled**.
4. Navigate to **Logs → rules** — look for evaluations of the rule and check the
   LLM output.
5. Navigate to **Logs → errors** — check for any processing errors.
6. Navigate to **Membership Editor** — verify the sensor type thresholds are set
   appropriately for the current values.

______________________________________________________________________

## 6. CLI vs Web UI

Both interfaces expose the same underlying system. Choose based on your context.

| Feature                   | CLI                   | Web UI                     |
| ------------------------- | --------------------- | -------------------------- |
| Sensor monitoring         | `sensor status`       | Dashboard (live, visual)   |
| Device list               | `device list`         | Devices page               |
| Add a rule                | `rule add "..."`      | Rules page → Add Rule      |
| Enable/disable rule       | `rule enable/disable` | Rules page → toggle        |
| Delete rule               | `rule delete`         | Rules page → Delete button |
| Edit configuration        | Text editor + reload  | Config page (in-browser)   |
| Edit membership functions | Text editor           | Membership Editor page     |
| View logs                 | `log tail --category` | Logs page                  |
| System status             | `status`              | System Control page        |
| Shutdown system           | `stop`                | System Control → Shutdown  |
| JSON/scripting output     | `--format json`       | Not supported              |
| Tag-based rule filtering  | `rule list --tag`     | Not supported              |
| SSH / headless access     | ✅ Native             | ❌ Requires browser        |
| Visual metric display     | ❌ Text only          | ✅ Metric tiles            |
| Auto-refresh monitoring   | Manual re-run         | ✅ 1-second auto-refresh   |

______________________________________________________________________

## 7. Troubleshooting

### Port Already in Use

**Symptom:** Streamlit shows `Address already in use` on startup.

**Solution:**

```bash
# Use a different port
streamlit run src/interfaces/web/streamlit_app.py --server.port 8502

# Or find and kill the process using port 8501
lsof -ti:8501 | xargs kill -9
```

### "Bridge not initialized" Error Banner

**Symptom:** Pages show a red error banner saying the bridge is not initialized.

**Cause:** The IoT management system is not running.

**Solution:**

```bash
# Start the system
python -m src.main

# Or with Docker
docker compose up -d

# Then refresh the browser page
```

### Session State Reset (All Readings Disappear)

**Symptom:** After navigating away and back to the Dashboard, all sensor tiles
are empty and show "No sensor readings yet".

**Cause:** Streamlit session state is reset when you reload the page or open a
new tab. The in-memory sensor queue does not persist across sessions.

**Solution:** This is expected behaviour. Readings will repopulate within
seconds once the system resumes sending MQTT messages. Enable **Auto-refresh**
to see them appear automatically.

### No Sensor Data on Dashboard

**Symptom:** Dashboard shows "No sensor readings yet" even though the system is
running.

**Checklist:**

1. Verify the system is `RUNNING` — navigate to **System Control**.
2. Check that MQTT is connected — look for `mqtt_client: ✅` in the component
   list.
3. Verify devices have sensors with the correct MQTT topics in **Config →
   Devices**.
4. Check **Logs → sensors** for any incoming readings.
5. Check **Logs → errors** for MQTT connection errors.

### Config Save Fails with "Invalid JSON"

**Symptom:** Clicking Save in the Config page shows a red "Invalid JSON" error.

**Solution:**

- Check for trailing commas after the last item in an object or array (not valid
  in JSON).
- Check for missing quotes around string values.
- Use a linter such as `python -m json.tool` to identify the exact error:
  ```bash
  echo '{ "host": "localhost", }' | python -m json.tool
  ```

### Membership Editor Shows "Membership file not found"

**Symptom:** After selecting a sensor type, a yellow warning appears.

**Cause:** The membership function file does not exist for that sensor type.

**Solution:**

```bash
# Create the missing file (adjust sensor type as needed)
cp config/membership_functions/temperature.json \
   config/membership_functions/my_sensor_type.json
# Then edit it in the Membership Editor
```

______________________________________________________________________

## See Also

- [User Guide (CLI)](user-guide.md) — Full CLI reference
- [Installation Guide](installation-guide.md) — System installation
- [Configuration Guide](configuration-guide.md) — All configuration options
- [Example Rules](example-rules.md) — Natural language rule patterns
- [Demo Walkthrough](demo-walkthrough.md) — Step-by-step demo
- [Troubleshooting](demo-troubleshooting.md) — Additional issue solutions
