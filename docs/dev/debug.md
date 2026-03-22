# Debug

______________________________________________________________________

This file is made with the intent of documenting bugs that were found.

1. `python -m src.interfaces.cli` and `iot-fuzzy-llm` behave differently

   - Problem: `python -m src.interfaces.cli` correctly interracts with system,
     but `iot-fuzzy-llm` doesn't seem to be connected to the system, showing
     UNINITIALIZED state when running application
   - Expected: These two commands behaving identically, with the latter
     basically being a binary shortcut for the former.
   - Resolved: NO

2. `python -m src.interfaces.cli` throws runtime warning

   - Issue: Command throws "<frozen runpy>:128: RuntimeWarning:
     'src.interfaces.cli' found in sys.modules after import of package
     'src.interfaces', but prior to execution of 'src.interfaces.cli'; this may
     result in unpredictable behaviour"
   - Expected: No runtime error
   - Resolved: NO

3. Missing "Start system" application button in web UI

   - Issue: When system is in STOPPED state, the button to start the system is
     missing
   - Expected: This button should be there when the system is in STOPPED state
   - Resolved: NO

4. Application logs missing categories

   - Issue: Logs only have the 'system' log category
   - Expected: Categories for every seperate component plus 'system' (all)
     should be present
   - Resolved: NO

5. Application logs showing old irrelevant logs

   - Issue: Application logs showing logs of previous system starts
   - Expected: Only showing logs from this systems start
   - Resolved: NO

6. Deprecated "System Control" tab in web UI

   - Issue: "System Control" tab contains irrelevant "System Shutdown" button
   - Expected: "System Control" should be removed, "System Status" segment
     should be moved to "Dashboard" as "Status" with status, uptime and version
     being shown as UI elements (not just JSON text)
   - Resolved: NO
