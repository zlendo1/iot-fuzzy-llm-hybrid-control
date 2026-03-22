# Debug

______________________________________________________________________

This file documents bugs that were found and their resolution status.

## 1. CLI binary mismatch

- **Problem**: `python -m src.interfaces.cli` correctly interacts with system,
  but `iot-fuzzy-llm` doesn't seem to be connected to the system, showing
  UNINITIALIZED state when running application
- **Expected**: These two commands behaving identically, with the latter
  basically being a binary shortcut for the former.
- **Resolved**: YES — Removed eager imports from `src/interfaces/__init__.py`

## 2. CLI RuntimeWarning on execution

- **Problem**: `python -m src.interfaces.cli` throws RuntimeWarning:
  `'src.interfaces.cli' found in sys.modules after import of package 'src.interfaces', but prior to execution of 'src.interfaces.cli'`
- **Expected**: No runtime warning
- **Resolved**: YES — Same fix as #1 (eager imports in `__init__.py`)

## 3. Missing Start button in web UI

- **Problem**: When system is in STOPPED state, the button to start the system
  is missing
- **Expected**: Start button should be visible when the system is in STOPPED
  state
- **Resolved**: YES — Fixed state check from `"idle"` to `"stopped"` in
  `dashboard.py`

## 4. Missing log categories

- **Problem**: Logs only have the 'system' log category
- **Expected**: All categories (system, commands, sensors, errors, rules) should
  be present
- **Resolved**: YES — `GetLogCategories` now returns all `LogCategory` enum
  values instead of only categories with existing entries

## 5. Old logs shown from previous sessions

- **Problem**: Application logs showing logs of previous system starts
- **Expected**: Only showing logs from the current system session
- **Resolved**: YES — Log entries are now filtered by servicer creation
  timestamp (`_session_start`)

## 6. Deprecated System Control tab

- **Problem**: "System Control" tab contains irrelevant "System Shutdown" button
- **Expected**: "System Control" should be removed, status info moved to
  "Dashboard" as proper UI elements (status, uptime, version)
- **Resolved**: YES — Removed `system_control.py`, added System Overview section
  to Dashboard with Status/Version/Uptime metrics and Start/Stop buttons
