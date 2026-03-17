"""Main Streamlit application entry point with multi-page navigation.

This module provides the Streamlit app configuration and navigation structure
for the Fuzzy-LLM IoT Management System web interface.
"""

from __future__ import annotations

import streamlit as st


PAGES = [
    st.Page(
        "src/interfaces/web/pages/dashboard.py",
        title="Dashboard",
        icon=":material/dashboard:",
    ),
    st.Page(
        "src/interfaces/web/pages/devices.py",
        title="Devices",
        icon=":material/devices_other:",
    ),
    st.Page("src/interfaces/web/pages/rules.py", title="Rules", icon=":material/rule:"),
    st.Page(
        "src/interfaces/web/pages/config.py", title="Config", icon=":material/settings:"
    ),
    st.Page(
        "src/interfaces/web/pages/membership_editor.py",
        title="Membership Editor",
        icon=":material/functions:",
    ),
    st.Page(
        "src/interfaces/web/pages/logs.py", title="Logs", icon=":material/description:"
    ),
    st.Page(
        "src/interfaces/web/pages/system_control.py",
        title="System Control",
        icon=":material/tune:",
    ),
]


def main() -> None:
    """Initialize and run the Streamlit multi-page application."""
    nav = st.navigation(PAGES)
    nav.run()


if __name__ == "__main__":
    main()
