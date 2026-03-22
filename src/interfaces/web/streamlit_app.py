"""Main Streamlit application entry point with multi-page navigation.

This module provides the Streamlit app configuration and navigation structure
for the Fuzzy-LLM IoT Management System web interface.
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

SCRIPT_DIR = Path(__file__).parent

PAGES = [
    st.Page(
        SCRIPT_DIR / "pages" / "dashboard.py",
        title="Dashboard",
        icon=":material/dashboard:",
    ),
    st.Page(
        SCRIPT_DIR / "pages" / "devices.py",
        title="Devices",
        icon=":material/devices_other:",
    ),
    st.Page(SCRIPT_DIR / "pages" / "rules.py", title="Rules", icon=":material/rule:"),
    st.Page(
        SCRIPT_DIR / "pages" / "config.py", title="Config", icon=":material/settings:"
    ),
    st.Page(
        SCRIPT_DIR / "pages" / "membership_editor.py",
        title="Membership Editor",
        icon=":material/functions:",
    ),
    st.Page(
        SCRIPT_DIR / "pages" / "logs.py", title="Logs", icon=":material/description:"
    ),
]


def main() -> None:
    """Initialize and run the Streamlit multi-page application."""
    nav = st.navigation(PAGES)
    nav.run()


if __name__ == "__main__":
    main()
